#!/bin/sh
set -e

echo "Starting backend entrypoint..."

echo "Running Alembic migrations..."
alembic upgrade head

echo "Migrations completed."

echo "Starting application..."
exec "$@"
