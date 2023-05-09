Feminicide Story Processor
==========================

Grab stories from various archives, run them against "feminicide story" classifiers, post results to a 
central server.

Install for Development
-----------------------

1. Install Python v3.10.0 or higher (we typically use conda or pyenv for this)
2. Install Python requirements: `pip install -r requirements.txt`
3. Install rabbitmq: on MacOS do `brew install rabbitmq`
4. Install postgres: on MacOS do `brew install postgresql`
5. Create a database called "mc-story-processor" in Postgres, then run `alembic upgrade head`
6. `cp .env.template .env` and fill in the appropriate info for each setting in that file
7. Run `pytest` on the command line to run all the automated tests and verify your setup is working

Note that some of the models use [tensorflow_text](https://pypi.org/project/tensorflow-text/), which is hard to 
install on Apple-silicon MacOS machines. For that platform you'll need to download and install the appropriate
[`tensorflow_text-2.10.0-cp310-cp310-macosx_11_0_arm64.whl`](https://github.com/sun1638650145/Libraries-and-Extensions-for-TensorFlow-for-Apple-Silicon/releases/download/v2.10/tensorflow_text-2.10.0-cp310-cp310-macosx_11_0_arm64.whl)
from the helpful repo of [prebuilt tensorflow wheels for Apple Silicon](https://github.com/sun1638650145/Libraries-and-Extensions-for-TensorFlow-for-Apple-Silicon/releases/). 

Running
-------

To fill up the queue with new stories based on the monitor config, execute `run-fetch-PROVIDER.sh`.

To start the workers that process queued up jobs to classify and post story results, execute `run-workers.sh`.

To run the small admin web server, execute `run-server.sh`.

### Tips

* To empty out your local queue while developing, visit `http://localhost:15672/` the and click "delete/purge"
on the Queues tab.

Deploying
---------

To build a release:

1. Edit `processor.VERSION` based on semantic versioning norms
2. Update the `CHANGELOG.md` file with a note about what changed
3. Commit those changes and tag the repo with the version number from step 1

This is built to deploy via a SAAS platform, like Heroku. We deploy via [dokku](https://dokku.com). Whatever your deploy
platform, make sure to create environment variables there for each setting in the `.env.template`.

See `doc/deploying.md` for full info on deploying to dokku.
