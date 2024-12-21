from __future__ import absolute_import

import logging

from celery import Celery

from processor import BROKER_URL

logger = logging.getLogger(__name__)

# we use celery to support parallel processing of stories in need of classification
app = Celery(
    "feminicide-story-processor",
    broker=BROKER_URL,
    backend="db+sqlite:///celery-backend.db",
    include=[
        "processor.tasks",
        "processor.tasks.classification",
        "processor.tasks.alerts",
        "processor.tasks.delete_old_data",
    ],
)

app.conf.timezone = "UTC"

# tweaks to try and fix problem related to losing connection to broker (RabbitMQ on production)
app.conf.broker_heartbeat = 60
app.conf.broker_pool_limit = 10  # based on some google-ing
app.conf.broker_connection_timeout = 60  # Increase timeout
app.conf.worker_prefetch_multiplier = 1  # Reduce prefetch for better load balancing
