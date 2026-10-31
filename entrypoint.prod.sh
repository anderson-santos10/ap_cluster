#!/bin/sh
set -eu

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# [::] na imagem Debian (bindv6only=0) escuta IPv4 e IPv6.
# Um segundo bind em 0.0.0.0 falha no Linux com endereço já em uso.
exec gunicorn config.wsgi:application --bind "[::]:${PORT:-8080}"
