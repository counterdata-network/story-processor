Change Log
==========

Here is a history of what was changed in each version. 

### v4.2.5

* Remove extra Media Cloud parameter that has been deprecated 

### v4.2.4

* Tweak to catch up on Media Cloud stories after re-indexing 

### v4.2.3

* Enable Media Cloud on all projects 

### v4.2.2

* add normalized_url to story table to support deduplication, fixing a bug where normalized (ie. unclickable) URLs were 
  being stored in URL field for Media Cloud fetcher 

### v4.2.1

* minor bug and log msg fixes

### v4.2.0

* enable media cloud for selected groups to pilot

### v4.1.2

* tweak run configuration to do more often but smaller batches

### v4.1.1

* fix bugs related to duplicate fetching of URLs and mis-reported story counts in notifications

### v4.1.0

* add unique index on project-url
* normalize URL and use that for multiple layers of project-url deduplication

### v4.0.4

* handle RabbitMQ message too big failure

### v4.0.3

* Fix date bugs on MC paging query
* Protection around projects without start_date
* Tweak story query windows to account for catchup for last few weeks

### v4.0.2

* Remove debug limit used for testing new MC client

### v4.0.1

* Fix bug related to sending new MC stories to main server

### v4.0.0

* First pass at new Media Cloud Online News Archive support
* Support tracking latest-fetched story separately based on source
* Update dependencies

### v3.6.2

* Migrate mediacloud fetcher off of Prefect and prep to remove it completely.

### v3.6.1

* Redo database indexes to speed up dashboard queries.

### v3.6.0

* Refactoring newscatcher and wayback-machine processors to use Scrapy for content fetch parallelization instead of prefect. 

### v3.5.1

* Bump up dependency versions to keep up to date on things

### v3.5.0

* Support sending updates to Slack as a file upload instead of a giant post

### v3.4.6

* Redo database session management to try and fix production out-of-connections errors 

### v3.4.5

* Fix naming on WM task that conflicted with another task

### v3.4.4

* Better error handling for Newscatcher, longer window of days to search within

### v3.4.3

* More work on SQLalchemy v2 integration to fix web dashboard

### v3.4.2

* Fix query results architecture to work on dashboard errors

### v3.4.1

* Upgrade sklearn to try and fix deploy compilation crash

### v3.4.0

* Upgrade to prefect v2

### v3.3.1

* Tweaks to support more staggered multiple runs throughout day.
* Increase max DB pool size to support overlapping runs.

### v3.3.0

* Add slack integration for notifications (text parallels email notifications)  

### v3.2.1

* Fix bug that was ignoring KO entity types.  

### v3.2.0

* Added support for KO language model, based on different embeddings vectorizer  

### v3.1.3

* Use new `newscatcher_country` field 

### v3.1.2

* Fix chart query problem 

### v3.1.1

* Add published date chart back in to homepage and project page 

### v3.1.0

* Fixes to project history charts (so they match new-ish homepage ones more)

### v3.0.16

* More debugging

### v3.0.15

* Tweak URLs
* Add in debugging messages

### v3.0.14

* Add new chart showing posting volume by day to homepage

### v3.0.13

* Fix homepage dashboard queries to support debugging better

### v3.0.12

* Chunk posting results to main server to avoid 413 errors
* Upgrade dependencies
* Reduce errors on web dashboard after redeployment

### v3.0.11

* Update dependencies to fix title parsing bugs

### v3.0.10

* More logging when a model isn't found
 
### v3.0.9

* Logging and bug fix

### v3.0.8

* Fix serialization in `queue_unprocessed` script

### v3.0.7

* Update script that can post classified-but-unposted stories

### v3.0.6

* Replace curly quotes in queries.

### v3.0.5

* Skip WM project story fetch if query syntax error, but keep going 

### v3.0.4

* Set timeout on request to main server to try and avoid project-list-download failures (they're taking a long time)

### v3.0.3

* Ignore some exceptions creating noise on Sentry
* Switch to Celery Sentry integration, which is more useful than Flask for this application
* Stop everything if the models are not loaded correctly

### v3.0.2

* Cleanup work on Wayback Machine integration

### v3.0.1

* Split queries too long for Wayback Machine

### v3.0.0

* First pass at discovering stories via the new Wayback Machine online news archive.
* Removes support for legacy Media Cloud story API.

### v2.4.3

* Update required libraries

### v2.4.2

* New homepage chart for stories above threshold across system over time

### v2.4.1

* Make newscatcher fetching a bit more robust

### v2.4.0

* Add model score histogram to project page

### v2.3.18

* Update Media Cloud fetching to use new log database id as main key for updating stories
* Fix bug limiting NewsCatcher stories`

### v2.3.17

* Update dependencies
* Fix date parsing bug

### v2.3.16

* Refactor database chain to be more consistent in use of log_db_id for lookups
* Make sure to add a stories_id if there isn't one there
* Add max stories per project to NewsCatcher fetcher

### v2.3.15

* Upgrade requirements

### v2.3.14

* Tweak to try and resolve missing stories_id issue on newscatcher-sourced stories

### v2.3.13

* Work on better error reporting 

### v2.3.12

* Remove debugging statements 

### v2.3.11

* Tweaking NewsCatcher ingest to work on odd behavior we're seeing

### v2.3.10

* More work on web dashboard errors

### v2.3.9

* Update dependencies to try and fix dashboard website timeout error on query to Media Cloud. 

### v2.3.8

* Add charts to show discovery/ingest by platform on homepage and project pages.
* Show list of recent URLs discovered by project.

### v2.3.7

* Change Media Cloud processor to err on the side of recentness over completeness, specifically by only querying
  for stories published within the last few days. This should ensure we don't fall too many days behind on projects
  that have lots of results. The downside is that for those projects it could miss stories each day.

### v2.3.6

* Work on dependency problems.

### v2.3.5

* Fix Media Cloud quert start date to avoid getting older stories by accident (because we need to reprocess older
  feeds to backfill some gaps in our main databse, and those would have new high processed_stories_id values).

### v2.3.4

* Fix logging for stories with no unique ID from their source

### v2.3.3

* Respect last check date in newscatcher fetching

### v2.3.2

* Small bug fixes to make it more robust

### v2.3.1

* Time how long a fetch takes, and include in email report
* Fixes for newscatcher integration

### v2.3.0

* Initial integration with newscatcher (triggered by having a filling in "country" property)

### v2.2.0

* Add entities to each story posted (via news-entity-server)

### 2.1.3

* Logging tweaks.

### 2.1.2

* Various small bug fixes for prod deployment.

### 2.1.1

* First work on support for 64 bit story ids.

### 2.1.0

* Check last processed URL within an RSS to make sure we don't re-process stories.

### 2.0.0

* Add initial support for fetching via Google Alerts RSS feeds.

### 1.8.4

* Update handling of Media Cloud crashes

### 1.8.3

* Fix a small no-data bug

### 1.8.2

* Run web server with multiple workers and gevent

### 1.8.1

* Work on making UI faster, and including more tracking info for debugging

### 1.8.0

* Full UI for monitoring story ingest and orocessing

### 1.7.4

* Fix web ui bugs related to first run of new deployment

### 1.7.3

* Add web-based UI for monitoring story volume

### 1.7.2

* Add logging of two separated chained model scores

### 1.7.1

* Upgrade python to latest
* Store last_processed_stories_id in new `projects` table to try and reduce reprocessing for projects with broad queries
  and few positive, above threshold, stories
* Disabled-for-now support for fetching and adding entities on this side

### 1.7.0

* Switch to parallel processing model (via Prefect + Dask)
* Parse and send entities to main server
* Hack to work with temporary Media Cloud database change

### 1.6.0

Supports chained language models.

### 1.5.3

Add warning emoji to email update for projects that are near max stories per day.

### 1.5.2

Update the support model chaining format, but not implementation yet.

### 1.5.1

Fix Sentry-related bug.

### 1.5.0

Switch to RabbitMQ, also log a LOT more to our local DB.

### 1.4.0

Add database for logging story state over to to make debugging across workers easier.

### 1.3.1

Fully integrate Sentry-based centralized logging. Integrate an embeddings model.

### 1.3.0

Load full model configuration from server.

### 1.2.3

More logging and removing queues.

### 1.2.2

More work on testing and logging to chase down bugs.

### 1.2.1

Cleaned up queries and added more debug logging.

### 1.2.0

Dynamically fetch models from server.

### 1.1.0

Add in new aapf models.

### 1.0.0

Add version number, update classifier models.

### (unnumbered)

Add API key-based authentication.

### (unnumbered)

Initial release.
