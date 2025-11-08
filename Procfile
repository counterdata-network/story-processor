worker: celery -A processor worker -l info --concurrency=4
fetcher-wm: python -m scripts.queue_wayback_stories
fetcher-nc: python -m scripts.queue_newscatcher_stories
fetcher-mc: python -m scripts.queue_mediacloud_stories
fetcher-nd: python -m scripts.queue_newsdata_stories
