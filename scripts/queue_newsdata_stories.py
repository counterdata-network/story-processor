# ruff: noqa: E402

import datetime as dt
import logging
import multiprocessing
import sys
import time
from typing import Dict, List

import dateparser

# Disable loggers prior to package imports
import processor

processor.disable_package_loggers()

import mcmetadata.urls as urls
from newsdataapi import NewsDataApiClient

import processor.database as database
import processor.database.projects_db as projects_db
import processor.database.stories_db as stories_db
import processor.projects as projects
import processor.tasks.classification as classification_tasks
import scripts.tasks as tasks
from processor import NEWSDATA_API_KEY
from processor.classifiers import download_models

POOL_SIZE = 16  # parallel fetch for story URL lists (by project)
PAGE_SIZE = 100
DAY_OFFSET = 0
DAY_WINDOW = 2  # don't look for stories that are too old
MAX_STORIES_PER_PROJECT = (
    2000  # can't process all the stories for queries that are too big (keep this low)
)
MAX_CALLS_PER_SEC = 1  # throttle calls to NewsData to avoid rate limiting
DELAY_SECS = 1 / MAX_CALLS_PER_SEC  # may need to be further adjusted

# initialize api client, maybe do this in processor initialization?
newsdata_api = NewsDataApiClient(apikey=NEWSDATA_API_KEY)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def load_projects_task() -> List[Dict]:
    project_list = projects.load_project_list(
        force_reload=True, overwrite_last_story=False
    )
    logger.info("  Checking {} projects".format(len(project_list)))
    # return [p for p in project_list if p['id'] == 166]
    return project_list


def _process_project_task(args: Dict) -> Dict:
    p = args
    Session = database.get_session_maker()
    # build a time frame to search in
    start_date, end_date = projects.query_start_end_dates(
        p,
        Session,
        DAY_OFFSET,
        DAY_WINDOW,
        processor.SOURCE_NEWSDATA,
    )
    # Newsdata.io takes strings as parameters and not datetime objects
    from_date = start_date.strftime("%Y-%m-%d")
    to_date = end_date.strftime("%Y-%m-%d")

    project_email_message = ""
    logger.info("Checking project {}/{}".format(p["id"], p["title"]))
    logger.debug(
        "  {} stories/page up to {}".format(PAGE_SIZE, MAX_STORIES_PER_PROJECT)
    )
    project_email_message += "Project {} - {}:\n".format(p["id"], p["title"])

    terms_no_curlies = p["search_terms"].replace("“", '"').replace("”", '"')

    # see how many stories and fetch them page by page
    story_count = 0
    page_count = 0
    more_stories = True
    page_token = None
    latest_pub_date = dt.datetime.now() - dt.timedelta(weeks=50)  # a while ago
    while more_stories and (story_count < MAX_STORIES_PER_PROJECT):
        try:
            # fetch stories and return results
            response = newsdata_api.archive_api(
                q=terms_no_curlies,  # query limit may have changed (listed as <=512 characters in updated documentation)
                language=p["language"].lower(),
                from_date=from_date,
                to_date=to_date,
                full_content=True,  # make sure to collect full text
                size=PAGE_SIZE,
                page=page_token,
            )
            page_of_stories = response["results"]
            total_stories = response["totalResults"]
            page_token = response["nextPage"]
            logger.info("  Project {}: {} total stories".format(p["id"], total_stories))
            if page_of_stories:
                logger.info(
                    "    {} - page {}: ({}) stories".format(
                        p["id"], page_count, len(page_of_stories)
                    )
                )
                skipped_dupes = 0  # how many URLs do we filter out because they're already in the DB for this project recently
                already_processed_normalized_urls = set()
                if total_stories > 0:
                    # list recent urls to filter so we don't fetch text extra if we've recently proceses already
                    # (and will be filtered out by add_stories call in later paost-text-fetch step)
                    with Session() as db_session:
                        already_processed_normalized_urls = (
                            stories_db.project_story_normalized_urls(db_session, p, 14)
                        )
                page_latest_pub_date = [
                    dateparser.parse(s["pubDate"]) for s in page_of_stories
                ]
                latest_pub_date = max(latest_pub_date, max(page_latest_pub_date))

                for s in page_of_stories:
                    if story_count >= MAX_STORIES_PER_PROJECT:
                        break
                    real_url = s["link"]
                    # skip URLs we've processed recently
                    if (
                        urls.normalize_url(real_url)
                        in already_processed_normalized_urls
                    ):
                        skipped_dupes += 1
                        continue
                    s["source"] = processor.SOURCE_NEWSDATA
                    s["publish_date"] = str(s["pubDate"])
                    s["project_id"] = p["id"]
                    s["authors"] = ", ".join(s["creator"]) if s.get("creator") else None
                    s["story_text"] = s["content"]
                    s["url"] = real_url
                    s["media_name"] = s["source_name"]
                    s["media_id"] = s["source_id"]
                    s["media_url"] = s["source_url"]
                page_count += 1
                # and log that we got and queued them all
                with Session() as session:
                    stories_to_queue = stories_db.add_stories(
                        session, page_of_stories, p, processor.SOURCE_NEWSDATA
                    )
                    story_count += len(stories_to_queue)
                    classification_tasks.classify_and_post_worker.delay(
                        p, stories_to_queue
                    )
                    # important to write this update now, because we have queued up the task to process these stories
                    # the task queue will manage retrying with the stories if it fails with this batch
                    projects_db.update_history(
                        session,
                        p["id"],
                        latest_pub_date,  # this will be interpreted next time as GMT, so make sure it is(!)
                        processor.SOURCE_NEWSDATA,
                    )
                    more_stories = page_token is not None
                time.sleep(DELAY_SECS)
            else:
                more_stories = False
        except Exception as e:
            logger.error(
                "  Couldn't count/retrieve stories in project {}. Skipping project for now. {}".format(
                    p["id"], e
                )
            )
            project_email_message += (
                "    failed to count and/or retrieve stories with {}\n\n".format(e)
            )
            return dict(
                email_text=project_email_message,
                stories=story_count,
                pages=page_count,
            )

    logger.info(
        "  queued {} stories for project {}/{} (in {} pages)".format(
            story_count, p["id"], p["title"], page_count
        )
    )
    #  add a summary to the email we are generating
    warnings = ""
    if story_count > (
        MAX_STORIES_PER_PROJECT * 0.8
    ):  # try to get our attention in the email
        warnings += "(⚠️️️ query might be too broad)"
    project_email_message += "    found {} new stories (over {} pages) {}\n\n".format(
        story_count, page_count, warnings
    )
    return dict(
        email_text=project_email_message,
        stories=story_count,
        pages=page_count,
    )


def process_projects_in_parallel(projects_list: List[Dict], pool_size: int):
    args_list = [p for p in projects_list]
    with multiprocessing.Pool(pool_size) as pool:
        results = pool.map(_process_project_task, args_list)
    return results


if __name__ == "__main__":
    logger.info("Starting {} story fetch job".format(processor.SOURCE_NEWSDATA))

    # important to do because there might be new models on the server!
    logger.info("  Checking for any new models we need")
    models_downloaded = download_models()
    logger.info(f"    models downloaded: {models_downloaded}")
    if not models_downloaded:
        sys.exit(1)

    start_time = time.time()

    # 1. list all the project we need to work on
    projects_list = load_projects_task()

    # 2. process all the projects (in parallel)
    logger.info(f"Processing project in parallel {POOL_SIZE}")
    project_results = process_projects_in_parallel(projects_list, POOL_SIZE)

    # 3. send email/slack_msg with results of operations
    logger.info(f"Total stories queued: {sum([p['stories'] for p in project_results])}")
    tasks.send_project_list_slack_message(
        project_results,
        processor.SOURCE_NEWSDATA,
        start_time,
    )
    tasks.send_project_list_email(
        project_results,
        processor.SOURCE_NEWSDATA,
        start_time,
    )
