import datetime as dt
import json
import logging
import os
import sys
import time
from typing import Dict, List

import dateparser
import pytz
import requests

import processor.apiclient as apiclient
import processor.classifiers as classifiers
import processor.database as database
import processor.database.projects_db as projects_db
from processor import (
    FEMINICIDE_API_KEY,
    SOURCE_MEDIA_CLOUD,
    VERSION,
    path_to_log_dir,
)

logger = logging.getLogger(__name__)

_all_projects = None  # acts as a singleton because we only load it once (after we update it from central server)

REALLY_POST = False  # helpful debug flag - set to False and we don't post results to central server TMP
LOG_LAST_POST_TO_FILE = (
    True  # helpful for storing traces of JSON sent to mail server locally
)


def _path_to_config_file() -> str:
    return os.path.join(classifiers.CONFIG_DIR, "projects.json")


def with_countries(all_projects: List[Dict]) -> List[Dict]:
    return [
        p
        for p in all_projects
        if (p["newscatcher_country"] is not None) and len(p["newscatcher_country"]) == 2
    ]


def load_project_list(
    force_reload: bool = False,
    overwrite_last_story=False,
    download_if_missing: bool = False,
) -> List[Dict]:
    """
    Treats config like a singleton that is lazy-loaded once the first time this is called.
    :param force_reload: Override the default behaviour and load the config from file system again.
    :param overwrite_last_story: Update the last processed story to the latest from the server (useful for reprocessing
                                 stories and other debugging)
    :param download_if_missing: If the file is missing try to download it as a backup plan
    :return: list of configurations for projects to query about
    """
    global _all_projects
    if _all_projects and not force_reload:
        return _all_projects
    try:
        file_exists = os.path.exists(_path_to_config_file())
        if force_reload or (
            download_if_missing and not file_exists
        ):  # grab the latest config file from main server
            projects_list = apiclient.get_projects_list()
            with open(_path_to_config_file(), "w") as f:
                json.dump(projects_list, f)
                file_exists = True  # we might have just created it for the first time
            logger.info(
                "  updated config file from main server - {} projects".format(
                    len(projects_list)
                )
            )
            if len(projects_list) == 0:
                raise RuntimeError(
                    "Fetched empty project list was empty - bailing unhappily"
                )
        # load and return the (perhaps updated) locally cached file
        if file_exists:
            with open(_path_to_config_file(), "r") as f:
                _all_projects = json.load(f)
        else:
            _all_projects = []
        Session = database.get_session_maker()
        with Session() as session:
            for project in _all_projects:
                project_history = projects_db.get_history(session, project["id"])
                if (project_history is None) or overwrite_last_story:
                    projects_db.add_history(session, project["id"])
                    logger.info(
                        "    added/overwrote {} to local history".format(project["id"])
                    )
        return _all_projects
    except Exception as e:
        # bail completely if we can't load the config file
        logger.error("Can't load config file - dying ungracefully")
        logger.exception(e)
        sys.exit(1)


def post_results(project: Dict, stories: List[Dict]) -> None:
    """
    Send results back to the feminicide server. Raises an exception if this post fails.
    :param project:
    :param stories:
    :return:
    """
    if len(stories) > 0:  # don't bother posting if there are no stories above threshold
        data_to_send = dict(
            version=VERSION,
            project=project,  # send back project data too (even though id is in the URL) for redundancy
            stories=stories,
            apikey=FEMINICIDE_API_KEY,
        )
        # helpful logging for debugging (the last project post will written to a file)
        if LOG_LAST_POST_TO_FILE:
            with open(
                os.path.join(
                    path_to_log_dir,
                    "{}-posted-data-{}.json".format(
                        project["id"], time.strftime("%Y%m%d-%H%M%S")
                    ),
                ),
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(data_to_send, f, ensure_ascii=False, indent=4, default=str)
        # now post to server (if not in debug mode)
        if REALLY_POST:
            data_as_json_str = json.dumps(
                data_to_send, ensure_ascii=False, default=str
            )  # in case there is date
            data_as_sanitized_obj = json.loads(data_as_json_str)
            response = requests.post(
                project["update_post_url"], json=data_as_sanitized_obj
            )
            if not response.ok:
                raise RuntimeError(
                    "Tried to post to project {} but got an error code {}".format(
                        project["id"], response.status_code
                    )
                )
    else:
        logger.info("  no stories to send for project {}".format(project["id"]))


def remove_low_confidence_stories(
    confidence_threshold: float, stories: List[Dict]
) -> List[Dict]:
    """
    If the config has specified some threshold for which stories to send over, filter out those below the threshold.
    :param confidence_threshold:
    :param stories:
    :return: only those stories whose score was >= to the threshold
    """
    filtered = [s for s in stories if s["confidence"] >= confidence_threshold]
    logger.debug(
        "    kept {}/{} stories above {}".format(
            len(filtered), len(stories), confidence_threshold
        )
    )
    return filtered


def prep_stories_for_posting(project: Dict, stories: List[Dict]) -> List[Dict]:
    """
    Pull out just the info to send to the central feminicide server (we don't want to send it data it
    shouldn't see, or cannot use).
    :param project:
    :param stories:
    :return:
    """
    prepped_stories = []
    for s in stories:
        story = dict(
            source=s["source"],
            language=s["language"],
            media_id=s["media_id"] if "media_id" in s else None,
            media_url=s["media_url"],
            media_name=s["media_name"],
            publish_date=s["publish_date"],
            story_tags=s["story_tags"] if "story_tags" in s else None,
            title=s["title"],
            url=s["url"],
            # add in the entities we parsed out via news-entity-server
            entities=(
                s["entities"] if "entities" in s else None
            ),  # backwards compatible, in case some in queue are old
            # add in the probability from the model
            confidence=s["confidence"],
            # throw in some metadata for good measure
            log_db_id=s["log_db_id"],
            project_id=project["id"],
            language_model_id=project["language_model_id"],
        )
        prepped_stories.append(story)
    return prepped_stories


def classify_stories(project: Dict, stories: List[Dict]) -> Dict[str, List[float]]:
    """
    Run all the stories passed in through the appropriate classifier, based on the project config
    :param project:
    :param stories:
    :return: an array of confidence probabilities for this being a story about feminicide
    """
    classifier = classifiers.for_project(project)
    return classifier.classify(stories)


def query_start_end_dates(
    project: Dict,
    session_maker,
    day_offset: int,
    day_window: int,
    source: str,
) -> (dt.datetime, dt.datetime):
    """
    Do this all in UTC(!)
    :param project:
    :param session_maker:
    :param day_offset:
    :param day_window:
    :param source:
    :return:
    """
    utc = pytz.UTC
    # start with default window specified by user
    try:
        start_date = utc.localize(
            dt.datetime.now() - dt.timedelta(days=(day_offset + day_window))
        )
        project_start_date = dateparser.parse(
            project["start_date"]
        )  # in UTC, but marked as military 'Z' from RoR JSON
        start_date = max(
            project_start_date, start_date
        )  # make sure we look for stories after the project's start_date
    except Exception:
        logger.warning(
            f"Project {project['id']} has no start date, defaulting to recent one"
        )
    end_date = utc.localize(dt.datetime.now() - dt.timedelta(days=(day_offset)))
    # grab any history first about how we've queried this project before on each platform, so we can optimize queries
    # to reduce total volume and duplicate results
    history = None
    try:
        with session_maker() as session:
            history = projects_db.get_history(session, project["id"])
    except Exception as e:
        logger.error(
            "Couldn't get history for project {} - {}".format(project["id"], e)
        )
        logger.exception(e)
    # use history if we have any
    if history:
        # start date for MC is indexed_date, for NC/IA is default
        if history and (source == SOURCE_MEDIA_CLOUD):
            if (
                history.latest_date_mc
            ):  # if fetched from MC before then use that as filter
                start_date = utc.localize(history.latest_date_mc)  # PG stores in UTC
            else:
                start_date = utc.localize(
                    dt.datetime.now() - dt.timedelta(days=(day_offset + day_window))
                )
        else:
            # Some sources don't return results in order of date indexed, so you might want NOT use the date of the
            # latest story we fetched from them. In these cases we could see more duplicates, but are less likely to
            # miss things.
            start_date = utc.localize(
                dt.datetime.now() - dt.timedelta(days=(day_offset + day_window + 1))
            )
        end_date = utc.localize(dt.datetime.now() - dt.timedelta(days=day_offset))
    return start_date, end_date
