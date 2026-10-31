#!/usr/bin/env bash

python manage.py migrate --noinput &&
python manage.py collectstatic --noinput &
python manage.py qcluster &
#!/bin/sh
set -e

gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}