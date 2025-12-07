#!/bin/bash
echo "=== Building Dell Fan Controller Docker Image ==="
echo

export DOCKER_BUILDKIT=0
export COMPOSE_DOCKER_CLI_BUILD=0

docker-compose build --no-cache

echo
echo "Build complete!"
echo "Run 'docker-compose up -d' to start the container."
