#!/bin/bash

# Development script for live-reload container setup
# This avoids rebuilding the entire Docker image on each code change

echo "🚀 Starting development environment with live reload..."

# Build the base image once
docker-compose build api-dev

# Start the development stack
docker-compose up api-dev redis

echo "✅ Development environment started"
echo "📝 Your code changes will be reflected immediately without rebuilding"
echo "🔗 API available at http://localhost:8080"