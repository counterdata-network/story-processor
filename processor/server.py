import logging
from flask import render_template, jsonify
import json
from typing import Dict

from processor import create_flask_app, VERSION
from processor.projects import load_project_list

logger = logging.getLogger(__name__)

app = create_flask_app()


# render helper, see https://stackoverflow.com/questions/34646055/encoding-json-inside-flask-template
def as_pretty_json(value:Dict) -> str:
    return json.dumps(value, indent=4, separators=(',', ': '))
app.jinja_env.filters['as_pretty_json'] = as_pretty_json


@app.route("/", methods=['GET'])
def home():
    config = load_project_list()
    return render_template('home.html', config=config, version=VERSION)


@app.route("/update-config", methods=['POST'])
def update_config():
    config = load_project_list(force_reload=True)
    return jsonify(config)


if __name__ == "__main__":
    app.debug = True
    app.run()
