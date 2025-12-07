@echo off
echo === Building Dell Fan Controller Docker Image ===
echo.

set DOCKER_BUILDKIT=0
set COMPOSE_DOCKER_CLI_BUILD=0

docker-compose build --no-cache

echo.
echo Build complete!
echo Run "docker-compose up -d" to start the container.
