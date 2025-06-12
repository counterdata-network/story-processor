#!/bin/sh
# -E, send task events that can be captured by monitors and celery log
# -P solo (optional), implement solo pools since Windows does not allow process forking only spawning
celery -A processor worker -l info --concurrency=4 -E -P solo

