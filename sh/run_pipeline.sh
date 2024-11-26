#!/bin/bash

# Ensure script exits on error
set -e

echo "Stopping all running containers..."
docker stop $(docker ps -q) || echo "No running containers to stop."

echo "Removing all containers..."
docker rm $(docker ps -aq) || echo "No containers to remove."

echo "Cleaning up unused Docker resources..."
docker system prune -f --volumes || echo "No resources to clean."

echo "Building and starting LLM service..."
cd /path/to/llm
docker-compose down
docker-compose up --build -d

echo "Building and starting nuXmv service..."
cd /path/to/nuXmv
docker-compose down
docker-compose up --build -d

echo "Building and starting chatbot service..."
cd /path/to/chat_bots
docker-compose down
docker-compose up --build -d

echo "All services are up and running!"

# Optional: Print the status of all running containers
docker ps
