Feminicide Story Processor
===========================

Grab stories from various archives, run them against bespoke classifiers created wth activist groups, post results to a 
central server. Part of the larger [Data Against Feminicide / Datos Contra El Feminicidio](http://datoscontrafeminicidio.net) project.

### Related Academic Papers and Presentations
- Bhargava, R., Suresh, H., Dogan, A.L., So, W., Suárez Val, H. Fumega, S., D’Ignazio, C. [_News as Data for Activists: 
a case study in feminicide counterdata production_](https://github.com/browninstitute/c-plus-j-website/raw/main/proceedings/Session9Group2.pdf). 
2022 Conference + Journalism Conference (C+J22).

- Suresh, H., Dogan, A. L., Movva, R., Bhargava, R., So, W., Martinez Cuba, A., Taurino, G., García-Montes, 
M., Cruxen, I., & D’Ignazio, C. (2022). [_Towards Intersectional Feminist and Participatory ML: A Case Study in 
Supporting Feminicide Counterdata Collection_](https://dl.acm.org/doi/10.1145/3531146.3533132). 2022 Conference on 
Fairness, Accountability and Transparency (FAccT22).

- D'Ignazio, C., Cruxên, I., Val, H. S., Cuba, A. M., García-Montes, M., Fumega, S., Suresh, H. & So, W. (2022). [_Feminicide 
and counterdata production: Activist efforts to monitor and challenge gender-related violence_](https://www.cell.com/patterns/pdf/S2666-3899(22)00127-1.pdf).
 Patterns, 3(7).

Install for Development
-----------------------
- Install Python v3.10.0 or higher (we typically use conda or pyenv for this)
- Install Python package requirements: `pip install -r requirements.txt`
- Additionally install the dev dependencies through: `pip install -r requirements-dev.txt` or `pip install -r requirements*` to install all python dependencies 
- Configure pre-commit hooks using `pre-commit install`
- Create a database called "mc-story-processor" in Postgres, then run `alembic upgrade head`
- `cp .env.template .env` and fill in the appropriate info for each setting in that file 
- Run `pytest` on the command line to run all the automated tests and verify your setup is working
- Required servcies:
  - Mac 
    - Install rabbitmq: on MacOS do `brew install rabbitmq`
    - Install postgres: on MacOS do `brew install postgresql`
  - Windows: Use `docker-compose.yml` to spin up instances automatically
    - Create a folder `docker-conf` (first time only) 
    - To start rabbitmq, postgres: `docker compose up -d` 

## Instructions for MacOS on Apple Silicon

Verified on M2 and M3:

1. install brew
2. install miniforge (with brew)
3. installed wget (with brew)
4. Installed tensorflow 2.10.0: `python -m pip install tensorflow-macos==2.10.0` (from [Apple's docs](https://developer.apple.com/metal/tensorflow-plugin/)). 
5. Download tensorflow-text: [`tensorflow_text-2.10.0-cp310-cp310-macosx_11_0_arm64.whl`](https://github.com/sun1638650145/Libraries-and-Extensions-for-TensorFlow-for-Apple-Silicon/releases/download/v2.10/tensorflow_text-2.10.0-cp310-cp310-macosx_11_0_arm64.whl)
from the helpful repo of [prebuilt tensorflow wheels for Apple Silicon](https://github.com/sun1638650145/Libraries-and-Extensions-for-TensorFlow-for-Apple-Silicon/releases/). 
6. Install that via `python -m pip install [filename]`
7. Comment out all the tensorflow packages in requirements.txt
8. Install the reqs via `python -m pip install -r requirements.txt`
9. Install the dev reqs via `python -m pip install -r requirements-dev.txt`
10. Set up your env vars are indicated above
11. Run scripts/download-models.sh to install the latest models
12. Run `pytest` to verify everything is working
 
 
Running
-------

To start the workers that process queued up jobs to classify and post story results, execute `run-workers.sh`.

To delete old files specifically files older than 62 days ago, execute `run-delete-files.sh`.

Developer Tools
---------------

1. Pre-commit hooks have been enabled through the `pre-commit` package and its configuration is at `pyproject.toml`
2. Configuration for all the developer tools (linter, formatter, pre-commit, etc.) are managed through `pyproject.toml`
3. `Ruff` linter can be enabled as a plugin on PyCharm for real-time linting experience
4. `Black` formatter can be configured to run alongside development through: `PyCharm Settings -> Tools -> Black`

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
