import datetime as dt
from typing import List, Dict
import logging
import copy
import sys

from sqlalchemy.sql import func
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

import processor
from processor.database.models import Story

Session = sessionmaker(bind=processor.engine)

logger = logging.getLogger(__name__)


def add_stories(source_story_list: List[Dict], project: Dict, source: str) -> List[Dict]:
    """
    Logging: Track metadata about all the stories we process we, so we can audit it later (like a log file).
    :param source_story_list:
    :param project:
    :param source:
    :return: list of ids of objects inserted
    """
    new_source_story_list = copy.copy(source_story_list)
    now = dt.datetime.now()
    for mc_story in new_source_story_list:
        db_story = Story.from_source(mc_story, source)
        db_story.project_id = project['id']
        db_story.model_id = project['language_model_id']
        db_story.queued_date = now
        db_story.above_threshold = False
        mc_story['db_story'] = db_story
    # now insert in batch to the database
    session = Session()
    session.add_all([s['db_story'] for s in new_source_story_list])
    session.commit()
    # only keep ones that inserted correctly
    new_source_story_list = [s for s in new_source_story_list if ('db_story' in s) and s['db_story'].id]
    for s in new_source_story_list:
        s['log_db_id'] = s['db_story'].id  # keep track of the db id, so we can use it later to update this story
        s['stories_id'] = s['db_story'].id
    if source != processor.SOURCE_MEDIA_CLOUD:
        # these stories don't have a stories_id, which we use later, so set it to the id and save
        session = Session()
        for s in new_source_story_list:
            session.query(Story).filter_by(id=s['log_db_id']).update({"stories_id": s['log_db_id']})
        session.commit()
    for s in new_source_story_list:  # free the DB objects back for GC
        del s['db_story']
    return new_source_story_list


def update_stories_processed_date_score(stories: List) -> None:
    """
    Logging: Once we have run the stories through the classifier models we want to save the scores.
    :param stories:
    :return:
    """
    now = dt.datetime.now()
    session = Session()
    for s in stories:
        session.query(Story).filter_by(id=s['log_db_id']).update({
            "model_score": s['model_score'],
            "model_1_score": s['model_1_score'],
            "model_2_score": s['model_2_score'],
            "processed_date": now,
        })
    session.commit()


def update_stories_above_threshold(stories: List) -> None:
    """
    Logging: Also keep track which stories were above the classifier score threshold on the project right now.
    Ones above should be sent to the server.
    :param stories:
    :return:
    """
    session = Session()
    for s in stories:
        session.query(Story).filter_by(id=s['log_db_id']).update({"above_threshold": True})
    session.commit()


def update_stories_posted_date(stories: List) -> None:
    """
    Logging: Keep track of when we sent stories above threshold to the main server.
    :param stories:
    :return:
    """
    now = dt.datetime.now()
    session = Session()
    for s in stories:
        session.query(Story).filter_by(id=s['log_db_id']).update({"posted_date": now})
    session.commit()


def recent_stories(project_id: int, above_threshold: bool, limit: int = 5) -> List[Story]:
    """
    UI: show a list of the most recent stories we have processed
    :param project_id:
    :param above_threshold:
    :param limit:
    :return:
    """
    earliest_date = dt.date.today() - dt.timedelta(days=7)
    session = Session()
    q = session.query(Story).\
        filter(Story.project_id == project_id). \
        filter(Story.above_threshold == above_threshold). \
        filter(Story.published_date > earliest_date). \
        order_by(func.random()). \
        limit(limit).all()
    stories = [s for s in q]
    return stories


def stories_by_processed_day(project_id: int, above_threshold: bool, is_posted: bool, limit: int = 30) -> List:
    """
    Ui: chart of how many stories we processed each day.
    :param project_id:
    :param above_threshold:
    :param is_posted:
    :param limit:
    :return:
    """
    earliest_date = dt.date.today() - dt.timedelta(days=limit)
    query = "select processed_date::date as day, count(1) as stories from stories " \
            "where (project_id={}) and (above_threshold is {}) and (processed_date is not Null) " \
            "and processed_date >= '{}'::DATE " \
            .format(project_id, 'True' if above_threshold else 'False', earliest_date)
    if is_posted is not None:
        query += "and posted_date {} Null ".format("is not" if is_posted else "is")
    query += "group by 1 order by 1 DESC"
    return _run_query(query)


def stories_by_published_day(project_id: int = None, platform: str = None, above_threshold: bool = None,
                             limit: int = 30) -> List:
    """
    UI: chart of stories we processed by date of publication
    :param project_id:
    :param platform:
    :param above_threshold:
    :param limit:
    :return:
    """
    earliest_date = dt.date.today() - dt.timedelta(days=limit)
    clauses = []
    if project_id is not None:
        clauses.append("(project_id={})".format(project_id))
    if platform is not None:
        clauses.append("(source='{}')".format(platform))
    if above_threshold is not None:
        clauses.append("(above_threshold is {})".format('True' if above_threshold else 'False'))
    query = "select published_date::date as day, count(1) as stories from stories " \
            "where (published_date is not Null) and (published_date >= '{}'::DATE) and {} " \
            "group by 1 order by 1 DESC".format(earliest_date, " AND ".join(clauses))
    return _run_query(query)


def _run_query(query: str) -> List:
    data = []
    with processor.engine.begin() as connection:
        result = connection.execute(text(query))
        for row in result:
            data.append(row)
    return data


def _run_count_query(query: str) -> int:
    data = _run_query(query)
    return data[0][0]


def unposted_above_story_count(project_id: int) -> int:
    """
    UI: How many stories about threshold have *not* been sent to main server (should be zero!).
    :param project_id:
    :return:
    """
    query = "select count(1) from stories where project_id={} and posted_date is Null and above_threshold is True".\
        format(project_id)
    return _run_count_query(query)


def posted_above_story_count(project_id: int) -> int:
    """
    UI: How many stories above threshold have we sent to the main server (like all should be)
    :param project_id:
    :return:
    """
    query = "select count(1) from stories " \
            "where project_id={} and posted_date is not Null and above_threshold is True".\
        format(project_id)
    return _run_count_query(query)


def below_story_count(project_id: int) -> int:
    """
    UI: How many stories total were below threshold (should be same as uposted_stories)
    :param project_id:
    :return:
    """
    query = "select count(1) from stories where project_id={} and above_threshold is False".\
        format(project_id)
    return _run_count_query(query)


def unposted_stories(project_id: int):
    """
    How many stories were not posted to hte main server (should be same as below_story_count)
    :param project_id:
    :return:
    """
    query = "select * from stories " \
            "where project_id={} and posted_date is Null and above_threshold is True".format(project_id)
    """
    session = Session()
    q = session.query(Story). \
        filter(Story.project_id == project_id). \
        filter(Story.above_threshold is True). \
        filter(Story.posted_date is None)
    return q.all()
    """
    return _run_query(query)
