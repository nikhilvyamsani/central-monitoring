#!/bin/bash

# Build and push multi-platform Docker image
echo "Building multi-platform Docker image..."

# Create buildx builder if it doesn't exist
docker buildx create --name multiarch --use 2>/dev/null || docker buildx use multiarch

# Build and push for multiple architectures
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag nikhilvyamsani/my-monitor:latest \
  --push \
  .

echo "Multi-platform image built and pushed successfully!"
echo "Pull with: docker pull nikhilvyamsani/my-monitor:latest"