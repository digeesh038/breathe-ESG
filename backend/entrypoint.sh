#!/usr/bin/env sh
# Production entrypoint: apply migrations, then exec the given command (gunicorn
# or celery). Migrations run here (not at build) because they need the live DB.
set -e

echo "Running migrations..."
python manage.py migrate --noinput

exec "$@"
