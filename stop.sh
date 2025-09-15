#!/bin/bash

echo "Stopping Instagram Image Service..."

# Stop the application container
echo "Stopping application container..."
docker stop instagram-service 2>/dev/null || true
docker rm instagram-service 2>/dev/null || true

# Stop LocalStack containers manually
echo "Stopping LocalStack..."
docker stop $(docker ps -q --filter "ancestor=localstack/localstack") 2>/dev/null || true
docker rm $(docker ps -aq --filter "ancestor=localstack/localstack") 2>/dev/null || true

# Clean up any dangling images (optional)
echo "Cleaning up..."
docker image prune -f > /dev/null 2>&1

echo "All services stopped successfully!"
echo ""
echo "To start again: ./start.sh"
