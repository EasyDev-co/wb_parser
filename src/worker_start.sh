#! /usr/bin/env bash
set -e

celery -A config.celery worker --loglevel=info -P gevent

