#!/usr/bin/env bashio
set -e

ML_API_TOKEN=$(bashio::config 'obico_api_secret')
PORT=$(bashio::addon.port 3333)
export ML_API_TOKEN
export ML_USE_GPU=$(bashio::config 'use_gpu')
export GUNICORN_TIMEOUT=$(bashio::config 'gunicorn_timeout')

venv/bin/gunicorn \
  --bind "0.0.0.0:$PORT" \
  --workers "${GUNICORN_WORKERS:-1}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --error-logfile - \
  --log-level info \
  wsgi
