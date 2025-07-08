#!/bin/bash

# DahoPevi Docker Build and Push Script
# Usage: ./push-docker.sh [tag]

set -e

# Configuration
IMAGE_NAME="isaacgounton/dahopevi"
DEFAULT_TAG="v1.0"
TAG=${1:-$DEFAULT_TAG}

echo "🚀 Building DahoPevi Docker Image"
echo "Image: $IMAGE_NAME:$TAG"
echo "----------------------------------------"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build the image
echo "🔨 Building Docker image..."
docker build -t $IMAGE_NAME:$TAG .

# Push to Docker Hub
echo "📤 Pushing to Docker Hub..."
docker push $IMAGE_NAME:$TAG

echo "✅ Successfully built and pushed $IMAGE_NAME:$TAG"
echo "🌐 Available on Docker Hub: https://hub.docker.com/r/isaacgounton/dahopevi"

# Test the image locally
echo "🧪 Testing image locally..."
if docker run --rm $IMAGE_NAME:$TAG python --version; then
    echo "✅ Image test passed"
else
    echo "❌ Image test failed"
    exit 1
fi

echo "🎉 Build complete!"
echo ""
echo "To deploy locally:"
echo "  docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "To pull and use:"
echo "  docker pull $IMAGE_NAME:$TAG"