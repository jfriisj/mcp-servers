#!/bin/bash
# ============================================================================
# Docker Hub Push Script for Optimized Whisper Server
# ============================================================================

# Configuration - UPDATE THIS WITH YOUR DOCKER HUB USERNAME
DOCKERHUB_USERNAME="yourusername"  # <-- CHANGE THIS
IMAGE_NAME="whisper-server-gpu"
LOCAL_IMAGE="whisper-server-whisper-api:latest"
VERSION="1.0"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Whisper Server - Docker Hub Push${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check if username is still default
if [ "$DOCKERHUB_USERNAME" == "yourusername" ]; then
    echo -e "${YELLOW}⚠️  Please edit this script and set your Docker Hub username${NC}"
    echo -e "${YELLOW}   Edit line 6: DOCKERHUB_USERNAME=\"your-actual-username\"${NC}"
    exit 1
fi

# Check if user is logged in
echo -e "${BLUE}🔐 Checking Docker Hub authentication...${NC}"
if ! docker info 2>/dev/null | grep -q "Username"; then
    echo -e "${YELLOW}⚠️  Not logged in to Docker Hub. Running 'docker login'...${NC}"
    docker login
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}❌ Login failed. Exiting.${NC}"
        exit 1
    fi
fi

# Check if local image exists
echo -e "${BLUE}🔍 Checking if local image exists...${NC}"
if ! docker images | grep -q "whisper-server-whisper-api"; then
    echo -e "${YELLOW}❌ Local image not found. Please build it first:${NC}"
    echo -e "   docker compose build"
    exit 1
fi

# Show image size
SIZE=$(docker images whisper-server-whisper-api:latest --format "{{.Size}}")
echo -e "${GREEN}✅ Found image: $LOCAL_IMAGE (Size: $SIZE)${NC}"
echo ""

# Tag images
echo -e "${BLUE}🏷️  Tagging images...${NC}"
docker tag $LOCAL_IMAGE $DOCKERHUB_USERNAME/$IMAGE_NAME:latest
echo -e "   ✅ Tagged as: $DOCKERHUB_USERNAME/$IMAGE_NAME:latest"

docker tag $LOCAL_IMAGE $DOCKERHUB_USERNAME/$IMAGE_NAME:v$VERSION
echo -e "   ✅ Tagged as: $DOCKERHUB_USERNAME/$IMAGE_NAME:v$VERSION"

docker tag $LOCAL_IMAGE $DOCKERHUB_USERNAME/$IMAGE_NAME:optimized
echo -e "   ✅ Tagged as: $DOCKERHUB_USERNAME/$IMAGE_NAME:optimized"
echo ""

# Push images
echo -e "${BLUE}📤 Pushing to Docker Hub...${NC}"
echo -e "${YELLOW}   This will take 10-30 minutes for a $SIZE image${NC}"
echo ""

echo -e "${BLUE}Pushing 'latest' tag...${NC}"
docker push $DOCKERHUB_USERNAME/$IMAGE_NAME:latest

echo -e "${BLUE}Pushing 'v$VERSION' tag...${NC}"
docker push $DOCKERHUB_USERNAME/$IMAGE_NAME:v$VERSION

echo -e "${BLUE}Pushing 'optimized' tag...${NC}"
docker push $DOCKERHUB_USERNAME/$IMAGE_NAME:optimized

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}✅ Successfully pushed to Docker Hub!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${BLUE}📦 View your image at:${NC}"
echo -e "   https://hub.docker.com/r/$DOCKERHUB_USERNAME/$IMAGE_NAME"
echo ""
echo -e "${BLUE}📥 Others can pull with:${NC}"
echo -e "   docker pull $DOCKERHUB_USERNAME/$IMAGE_NAME:latest"
echo ""
echo -e "${BLUE}🎯 Available tags:${NC}"
echo -e "   - latest"
echo -e "   - v$VERSION"
echo -e "   - optimized"
echo ""
