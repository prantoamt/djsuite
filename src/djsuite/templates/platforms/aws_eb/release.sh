#!/bin/sh
# Runs setup steps like migrations, static collection, etc.
set -e


# Copy appropriate nginx config
if [ "$APP_ROLE" = "worker" ]; then
  echo "Skipping post-deploy hook for worker env"
  exit 0
fi

# Normal hook logic here...
echo "Running post-deploy hook for API"
pdm run collectstatic --noinput
pdm run migrate
pdm run createsu
