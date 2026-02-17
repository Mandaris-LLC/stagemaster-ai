#!/bin/bash
# Local development startup script
#run with --build to rebuild

set -e

echo "Starting local development environment..."
docker compose -f docker-compose.yml -f docker-compose.local.yml --profile local up "$@"

#docker compose -f docker-compose.yml -f docker-compose.local.yml --profile local down
#docker network prune -f