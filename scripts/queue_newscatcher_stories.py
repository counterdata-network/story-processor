# ruff: noqa: E402

import datetime as dt
import itertools
import logging
import math
import sys
import time
from typing import Dict, List

import dateparser

# Disable loggers prior to package imports
import processor

processor.disable_package_loggers()

import mcmetadata as metadata
import mcmetadata.urls as urls

import processor.database as database
import processor.database.projects_db as projects_db
import processor.database.stories_db as stories_db
import processor.fetcher as fetcher
import processor.projects as projects
import scripts.newscatcher_api as newscatcher_api
import scripts.tasks as tasks
from processor.classifiers import download_models

POOL_SIZE = 16  # parallel fetch for story URL lists (by project)
PAGE_SIZE = 200
RATE_LIMIT = 1
DEFAULT_DAY_OFFSET = 0
DEFAULT_DAY_WINDOW = 4  # don't look for stories that are too old
MAX_STORIES_PER_PROJECT = (
    100  # can't process all the stories for queries that are too big (keep this low)
)
MAX_CALLS_PER_SEC = 1  # throttle calls to newscatcher to avoid rate limiting
DELAY_SECS = 1 / MAX_CALLS_PER_SEC

# create requests session
requests_session = newscatcher_api.create_session()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def load_projects() -> List[Dict]:
    project_list = projects.load_project_list(
        force_reload=True, overwrite_last_story=False
    )
    projects_with_countries = projects.with_countries(project_list)
    if len(projects_with_countries) == 0:
        raise RuntimeError(
            "No projects with countries ({} projects total) - bailing".format(
                len(project_list)
            )
        )
    logger.info(
        "  Found {} projects, checking {} with countries set".format(
            len(project_list), len(projects_with_countries)
        )
    )
    # return [p for p in projects_with_countries if p['id'] == 166]
    # return projects_with_countries[16:18]
    return projects_with_countries


def _fetch_results(
    project: Dict, start_date: dt.datetime, end_date: dt.datetime, page: int = 1
) -> Dict:
    terms_no_curlies = project["search_terms"].replace("“", '"').replace("”", '"')

    # fetch stories and return results
    results = newscatcher_api.search_stories(
        terms_no_curlies,
        language=project["language"],
        countries=[project["newscatcher_country"]],
        start_date=start_date,
        end_date=end_date,
        page_size=PAGE_SIZE,
        page=page,
        session=requests_session,
    )
    if results is not None:
        return results
    else:
        return dict(
            total_hits=0
        )  # a mockup of no results if fails, so we can handle transient errors better


def _project_story_worker(p: Dict) -> List[Dict]:
    project_stories = []
    try:
        db_session_maker = database.get_session_maker()
        # here start_date ignores last query history, since sort is by relevancy; we're relying on robust URL de-duping
        # to make sure we don't double up on stories (and keeping MAX_STORIES_PER_PROJECT low)
        start_date, end_date = projects.query_start_end_dates(
            p,
            db_session_maker,
            DEFAULT_DAY_OFFSET,
            DEFAULT_DAY_WINDOW,
            processor.SOURCE_NEWSCATCHER,
        )
        page_number = 1
        # fetch first page to get total hits, and use results
        current_page = _fetch_results(p, start_date, end_date, page_number)
        total_hits = current_page["total_hits"]
        logger.info(
            "Project {}/{} - {} total stories (since {})".format(
                p["id"], p["title"], total_hits, start_date
            )
        )
        skipped_dupes = 0  # how many URLs do we filter out because they're already in the DB for this project recently
        if total_hits > 0:
            # list recent urls to filter so we don't fetch text extra if we've recently proceses already
            # (and will be filtered out by add_stories call in later post-text-fetch step)
            with db_session_maker() as db_session:
                already_processed_normalized_urls = (
                    stories_db.project_story_normalized_urls(db_session, p, 14)
                )
            # query page by page
            latest_pub_date = dt.datetime.now() - dt.timedelta(weeks=50)
            page_count = math.ceil(total_hits / PAGE_SIZE)
            keep_going = True
            while keep_going:
                logger.debug(
                    "  {} - page {}: {} stories".format(
                        p["id"], page_number, len(current_page["articles"])
                    )
                )
                # track the latest date so we can use it tomorrow
                page_latest_pub_date = [
                    dateparser.parse(s["published_date"])
                    for s in current_page["articles"]
                ]
                latest_pub_date = max(latest_pub_date, max(page_latest_pub_date))
                # prep all the articles
                for item in current_page["articles"]:
                    if len(project_stories) > MAX_STORIES_PER_PROJECT:
                        break
                    real_url = item["link"]
                    # skip URLs we've processed recently
                    if (
                        urls.normalize_url(real_url)
                        in already_processed_normalized_urls
                    ):
                        skipped_dupes += 1
                        continue
                    # removing this check for now, because I'm not sure if stories are ordered consistently
                    info = dict(
                        url=real_url,
                        source_publish_date=item["published_date"],
                        title=item["title"],
                        source=processor.SOURCE_NEWSCATCHER,
                        project_id=p["id"],
                        language=p["language"],
                        authors=item["authors"],
                        media_url=urls.canonical_domain(real_url),
                        media_name=urls.canonical_domain(real_url),
                        # too bad there isn't somewhere we can store the `id` (string)
                    )
                    project_stories.append(info)
                if keep_going:  # check after page is processed
                    keep_going = (page_number < page_count) and (
                        len(project_stories) <= MAX_STORIES_PER_PROJECT
                    )
                    if keep_going:
                        page_number += 1
                        time.sleep(DELAY_SECS)
                        current_page = _fetch_results(
                            p, start_date, end_date, page_number
                        )
                        # stay below rate limiting
            logger.info(
                "  project {} - {} valid stories (skipped {}) (after {})".format(
                    p["id"], len(project_stories), skipped_dupes, start_date
                )
            )
            with db_session_maker() as db_session:
                # note - right now this latest pub date isn't used, because the sort is by relevancy within the
                # default time window
                projects_db.update_history(
                    db_session, p["id"], latest_pub_date, processor.SOURCE_NEWSCATCHER
                )
    except Exception as e:
        # log error and continue on your way
        logger.exception(f"Failed to process stories for project {p['id']}: {e}")
    return project_stories[:MAX_STORIES_PER_PROJECT]


def fetch_project_stories(project_list: List[Dict]) -> List[Dict]:
    """
    Fetch stories in parallel by project. Efficient because it is mostly IO-bound. Would be smarter to use async calls
    here but I don't think the underlying API call is async compatible yet.
    :param project_list:
    :return:
    """
    lists_of_stories = []

    for project in project_list:
        # Call the story worker with the same session to avoid creating new connections
        stories = _project_story_worker(project)
        lists_of_stories.append(stories)

    # Flatten list of lists of stories into one big list
    combined_stories = [s for s in itertools.chain.from_iterable(lists_of_stories)]

    logger.info(
        "Fetched {} total URLs from {}".format(
            len(combined_stories), processor.SOURCE_NEWSCATCHER
        )
    )

    return combined_stories


def fetch_text(stories: List[Dict]) -> List[Dict]:
    stories_to_return = []

    def handle_parse(response_data: Dict):
        # called for each story that successfully is fetched by Scrapy
        nonlocal stories, stories_to_return
        # note that the url might be from multiple stories, so we need to process it for all of them
        matching_input_stories = [
            s for s in stories if s["url"] == response_data["original_url"]
        ]
        for (
            s
        ) in (
            matching_input_stories
        ):  # find all matches, which could be with different URLs from different projects
            story_metadata = metadata.extract(s["url"], response_data["content"])
            s["story_text"] = story_metadata["text_content"]
            s["publish_date"] = story_metadata[
                "publication_date"
            ]  # this is a date object
            logger.debug(f"Handled URL: {s['url']}")
            stories_to_return.append(s)

    # download them all in parallel... will take a while (make it only unique URLs first)
    fetcher.fetch_all_html(list(set([s["url"] for s in stories])), handle_parse, 1)
    logger.info(
        "Fetched text for {} stories (failed on {})".format(
            len(stories_to_return), len(stories) - len(stories_to_return)
        )
    )
    return stories_to_return


if __name__ == "__main__":
    logger.info("Starting {} story fetch job".format(processor.SOURCE_NEWSCATCHER))

    # important to do because there might be new models on the server!
    logger.info("  Checking for any new models we need")
    models_downloaded = download_models()
    logger.info(f"    models downloaded: {models_downloaded}")
    if not models_downloaded:
        sys.exit(1)

    start_time = time.time()

    # 1. list all the project we need to work on
    projects_list = load_projects()

    # 2. fetch all the urls from for each project from newscatcher (in parallel)
    all_stories = fetch_project_stories(projects_list)
    unique_url_count = len(set([s["url"] for s in all_stories]))
    logger.info(
        "Found {} total stories, {} unique URLs".format(
            len(all_stories), unique_url_count
        )
    )

    # 3. fetch webpage text and parse all the stories (use scrapy to do this in parallel, dropping stories that fail)
    stories_with_text = fetch_text(all_stories)
    logger.info(
        "Fetched {} stories with text, from {} attempted URLs".format(
            len(stories_with_text), unique_url_count
        )
    )

    # 4. post batches of stories for classification
    results_data = tasks.queue_stories_for_classification(
        projects_list, stories_with_text, processor.SOURCE_NEWSCATCHER
    )

    # 5. send email/slack_msg with results of operations
    tasks.send_combined_slack_message(
        results_data, processor.SOURCE_NEWSCATCHER, start_time
    )
    tasks.send_combined_email(results_data, processor.SOURCE_NEWSCATCHER, start_time)
