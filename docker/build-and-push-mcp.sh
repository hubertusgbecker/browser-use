#!/bin/bash
# Build and push browser-use MCP server Docker image to Docker Hub

set -e

DOCKER_USERNAME="hubertusgbecker"
IMAGE_NAME="browser-use"
TAG="mcp-latest"

echo "==================================================================="
echo "Building and Pushing Browser-Use MCP Server Docker Image"
echo "==================================================================="
echo ""

# Check if logged into Docker Hub
if ! docker info | grep -q "Username"; then
    echo "⚠️  Not logged into Docker Hub. Please run: docker login"
    exit 1
fi

echo "📦 Building Docker image..."
echo "   Image: ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}"
echo ""

# Build the image
docker build \
    -f Dockerfile.mcp.simple \
    -t ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG} \
    .

echo ""
echo "✅ Docker image built successfully!"
echo ""

# Also tag with version
VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
echo "📌 Tagging with version: ${VERSION}"
docker tag ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG} ${DOCKER_USERNAME}/${IMAGE_NAME}:mcp-v${VERSION}

echo ""
echo "🚀 Pushing to Docker Hub..."
echo ""

# Push both tags
docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}
docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:mcp-v${VERSION}

echo ""
echo "==================================================================="
echo "✅ Successfully pushed Docker images:"
echo "   - ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}"
echo "   - ${DOCKER_USERNAME}/${IMAGE_NAME}:mcp-v${VERSION}"
echo "==================================================================="
echo ""
echo "📋 To use the image:"
echo "   docker pull ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}"
echo "   docker-compose up -d"
echo ""
