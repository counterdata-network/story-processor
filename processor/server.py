import logging

import mediacloud.error
from flask import render_template, jsonify
import json
from typing import Dict, List
from itertools import chain
import requests.exceptions

from processor import create_flask_app, VERSION, get_mc_client, PLATFORMS, SOURCE_MEDIA_CLOUD
from processor.projects import load_project_list
import processor.database.stories_db as stories_db

logger = logging.getLogger(__name__)

app = create_flask_app()


# render helper, see https://stackoverflow.com/questions/34646055/encoding-json-inside-flask-template
def as_pretty_json(value: Dict) -> str:
    return json.dumps(value, indent=4, separators=(',', ': '))
app.jinja_env.filters['as_pretty_json'] = as_pretty_json


@app.route("/", methods=['GET'])
def home():
    projects = load_project_list()
    # show overall ingest over last two weeks
    data_for_graph = _prep_for_graph([stories_db.stories_by_published_day(platform=p, limit=30) for p in PLATFORMS],
                                     PLATFORMS)
    return render_template('home.html', projects=projects, version=VERSION, ingest_data=data_for_graph)


@app.route("/update-config", methods=['POST'])
def update_config():
    config = load_project_list(force_reload=True)
    return jsonify(config)


def _prep_for_graph(counts: List[List], names: List[str]) -> List[Dict]:
    cleaned_data = [{r['day'].strftime("%Y-%m-%d"): r['stories'] for r in series} for series in counts]
    dates = set(chain(*[series.keys() for series in cleaned_data]))
    stories_by_day_data = []
    for d in dates:  # need to make sure there is a pair of entries for each date
        for idx, series in enumerate(cleaned_data):
            stories_by_day_data.append(dict(
                date=d,
                type=names[idx],
                count=series[d] if d in series else 0
            ))
    return stories_by_day_data


@app.route("/projects/<project_id_str>/processed-by-day", methods=['GET'])
def project_processed_by_day(project_id_str):
    project_id = int(project_id_str)
    data = _prep_for_graph(
        [stories_db.stories_by_processed_day(project_id, True, None),
         stories_db.stories_by_processed_day(project_id, False, None)],
        ['above threshold', 'below threshold']
    )
    return jsonify(data)


@app.route("/projects/<project_id_str>/published-by-day", methods=['GET'])
def project_published_by_day(project_id_str):
    project_id = int(project_id_str)
    data = _prep_for_graph(
        [stories_db.stories_by_published_day(project_id=project_id, above_threshold=True),
         stories_db.stories_by_published_day(project_id=project_id, above_threshold=False)],
        ['above threshold', 'below threshold']
    )
    return jsonify(data)


@app.route("/projects/<project_id_str>/posted-by-day", methods=['GET'])
def project_posted_by_day(project_id_str):
    project_id = int(project_id_str)
    data = _prep_for_graph(
        [stories_db.stories_by_processed_day(project_id, True, True),
         stories_db.stories_by_processed_day(project_id, True, False)],
        ['sent to main server', 'not sent to main server']
    )
    return jsonify(data)


@app.route("/projects/<project_id_str>", methods=['GET'])
def a_project(project_id_str):
    project_id = int(project_id_str)
    # pull out the project info
    project = [p for p in load_project_list() if p['id'] == project_id][0]

    # show overall ingest over last two weeks
    data_for_graph = _prep_for_graph([stories_db.stories_by_published_day(platform=p, project_id=project_id, limit=30)
                                      for p in PLATFORMS], PLATFORMS)

    # show some recent story results
    stories_above = stories_db.recent_stories(project_id, True)
    stories_below = stories_db.recent_stories(project_id, False)
    # story_ids = list(set([s.stories_id for s in stories_above]) | set([s.stories_id for s in stories_below]))
    try:
        mc_story_ids = list(set([s.stories_id for s in stories_above if s.source == SOURCE_MEDIA_CLOUD])
                            | set([s.stories_id for s in stories_below if s.source == SOURCE_MEDIA_CLOUD]))
        mc = get_mc_client()
        if len(mc_story_ids) > 0:
            stories = mc.storyList("stories_id:({})".format(" ".join([str(s) for s in mc_story_ids])))
            story_lookup = {s['stories_id']: s for s in stories}
        else:
            story_lookup = {}
    except requests.exceptions.ReadTimeout as rte:
        # maybe Media Cloud is down?
        story_lookup = {}
        pass
    except mediacloud.error.MCException as mce:
        # we currently can't query for BIGINT story ids with a stories_id clause in the query
        story_lookup = {}
        pass

    # some other stats
    unposted_above_story_count = stories_db.unposted_above_story_count(project_id)
    posted_above_story_count = stories_db.posted_above_story_count(project_id)
    below_story_count = stories_db.below_story_count(project_id)
    try:
        above_threshold_pct = 100 * (unposted_above_story_count + posted_above_story_count) / below_story_count
    except ZeroDivisionError:
        above_threshold_pct = 100

    # render it all
    return render_template('project.html',
                           ingest_data=data_for_graph,
                           unposted_above_story_count=unposted_above_story_count,
                           above_threshold_pct=above_threshold_pct,
                           posted_above_story_count=posted_above_story_count,
                           below_story_count=below_story_count,
                           project=project,
                           stories_above=stories_above,
                           stories_below=stories_below,
                           story_lookup=story_lookup
                           )


if __name__ == "__main__":
    app.debug = True
    app.run()
