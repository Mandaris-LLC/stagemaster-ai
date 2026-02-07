#!/bin/bash
# Local development startup script

set -e

echo "Starting local development environment..."
docker compose -f docker-compose.yml -f docker-compose.local.yml --profile local up "$@"
