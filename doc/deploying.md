Deploying
=========

This is built to deploy via [dokku](http://dokku.viewdocs.io/dokku/). This takes a few rounds of configuration to set up
correctly. There are a few components:
* The fetcher app - ingest stories from Media Cloud and queues them up processing
* The logging DB - to help us interrogate and debug, we keep track of stories as they move through the pipeline in a DB
* The worker queue - this holds batches of stories needing classification & posting to the central server
* The queue monitor - lets us keep an eye on queue servicing speeds
* External [News-Entity-Server install](https://github.com/dataculturegroup/news-entity-server) - you need a url to an install of that service running

Create the Dokku apps
---------------------

1. [install Dokku](http://dokku.viewdocs.io/dokku/getting-started/installation/)
2. install the [Dokku rabbitmq plugin](https://github.com/dokku/dokku-rabbitmq)
3. install the [Dokku postgres plugin](https://github.com/dokku/dokku-postgres)
4. setup rabbitmq queues:
  * `dokku rabbitmq:create story-processor-q-nc`
  * `dokku rabbitmq:create story-processor-q-mc`
5. setup a postgres database: `dokku postgres:create story-processor-db`
6. create an app:
  * `dokku apps:create story-processor-mc`
  * `dokku apps:create story-processor-nc`
7. link the app to the rabbit queue:
  * `dokku rabbitmq:link story-processor-q-nc story-processor-nc`
  * `dokku rabbitmq:link story-processor-q-mc story-processor-mc`
8. link the app to the postgres database:
  * `dokku postgres:link story-processor-db story-processor-nc`
  * `dokku postgres:link story-processor-db story-processor-mc`
9. setup the configuration on the dokku app:
  * `dokku config:set story-processor-nc MC_API_KEY=1234 BROKER_URL=http://my.rabbitmq.url SENTRY_DSN=https://mydsn@sentry.io/123 CONFIG_FILE_URL=https://my.server/api/projects.json`
  * `dokku config:set story-processor-mc MC_API_KEY=1234 BROKER_URL=http://my.rabbitmq.url SENTRY_DSN=https://mydsn@sentry.io/123 CONFIG_FILE_URL=https://my.server/api/projects.json`

Release the worker app
----------------------

1. grab the code: `git clone git@github.mit.edu:data-feminism-lab/feminicide-mc-story-processor.git`
2. add a remote:
  * `git remote add prod-nc dokku@feminicide.friends.mediacloud.org:story-processor-nc`
  * `git remote add prod-mc dokku@feminicide.friends.mediacloud.org:story-processor-mc`
3. push the code to the server:
  * `git push prod-nc master`
  * `git push prod-mc master`
4. scale it to get a worker (dokku doesn't add one by default):
  * `dokku ps:scale story-processor-nc worker=1`
  * `dokku ps:scale story-processor-mc worker=1`

Setup the fetcher
-----------------

1. scale it to get a fetcher (dokku doesn't add one by default): `dokku ps:scale story-processor fetcher=1` (this will run the script once)
2. add a cron job something like this to fetch new stories every night: `0 8 * * * dokku --rm run story-processor fetcher-ga /app/run-fetch-googlealerts.sh >> /var/tmp/story-processor-cron.log 2>&1`

Setup Database Backups
----------------------

The local logging database is useful for future interrogation, so we back it up.

1. `dokku postgres:backup-auth story-processor-db AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY`
2. `dokku postgres:backup-schedule story-processor-db "0 9 * * *" df-server-backup`
