#! /usr/bin/env bash
set -e

celery -A config.celery beat --loglevel=info