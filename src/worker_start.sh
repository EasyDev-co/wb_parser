#! /usr/bin/env bash
set -e

celery -A config.celery beat -l info --detach
celery -A config.celery worker -l info