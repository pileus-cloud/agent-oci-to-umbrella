#!/bin/bash
set -e

# Docker Setup Script for OCI to Umbrella BYOD Transfer Agent

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================="
echo "OCI to Umbrella BYOD Transfer Agent"
echo "Docker Setup Script"
echo -e "==================================================${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

echo -e "${GREEN}✓ Docker is installed${NC}"

# Check if Docker Compose is available
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
    echo -e "${GREEN}✓ Docker Compose (V2) is available${NC}"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
    echo -e "${GREEN}✓ Docker Compose (V1) is available${NC}"
else
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi
echo ""

# Create required directories
echo "Creating required directories..."
mkdir -p config logs state
echo -e "${GREEN}✓ Created directories: config/, logs/, state/${NC}"
echo ""

# Check if config file exists
if [ ! -f "config/config.yaml" ]; then
    echo -e "${YELLOW}Configuration file not found${NC}"
    if [ -f "config.template.yaml" ]; then
        echo "Copying config template..."
        cp config.template.yaml config/config.yaml
        echo -e "${GREEN}✓ Copied config.template.yaml to config/config.yaml${NC}"
        echo ""
        echo -e "${YELLOW}IMPORTANT: Edit config/config.yaml with your settings:${NC}"
        echo "  1. OCI configuration (namespace, bucket, prefix)"
        echo "  2. S3 configuration (bucket_path, region)"
        echo "  3. Agent settings (poll_interval, lookback_days)"
        echo ""
        echo "Update log and state paths:"
        echo -e "${BLUE}  logging:${NC}"
        echo -e "${BLUE}    file: \"/logs/agent.log\"${NC}"
        echo -e "${BLUE}  state:${NC}"
        echo -e "${BLUE}    file: \"/state/state.json\"${NC}"
        echo ""
    else
        echo -e "${RED}Error: config.template.yaml not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Configuration file exists: config/config.yaml${NC}"
    echo ""
fi

# Check credentials
echo "Checking credentials..."
CREDS_OK=true

if [ ! -d "$HOME/.oci" ] || [ ! -f "$HOME/.oci/config" ]; then
    echo -e "${YELLOW}⚠ OCI credentials not found at ~/.oci/config${NC}"
    CREDS_OK=false
else
    echo -e "${GREEN}✓ OCI credentials found${NC}"
fi

if [ ! -d "$HOME/.aws" ] || [ ! -f "$HOME/.aws/credentials" ]; then
    echo -e "${YELLOW}⚠ AWS credentials not found at ~/.aws/credentials${NC}"
    CREDS_OK=false
else
    echo -e "${GREEN}✓ AWS credentials found${NC}"
fi
echo ""

if [ "$CREDS_OK" = false ]; then
    echo -e "${YELLOW}Please set up your credentials before running the agent:${NC}"
    echo ""
    echo "OCI credentials:"
    echo "  mkdir -p ~/.oci"
    echo "  nano ~/.oci/config"
    echo ""
    echo "AWS credentials:"
    echo "  mkdir -p ~/.aws"
    echo "  nano ~/.aws/credentials"
    echo ""
fi

# Build Docker image
echo -e "${BLUE}Building Docker image...${NC}"
$DOCKER_COMPOSE build
echo -e "${GREEN}✓ Docker image built successfully${NC}"
echo ""

# Show next steps
echo -e "${BLUE}=================================================="
echo "Setup Complete!"
echo -e "==================================================${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Edit configuration (if not done):"
echo -e "   ${BLUE}nano config/config.yaml${NC}"
echo ""
echo "2. Test configuration:"
echo -e "   ${BLUE}$DOCKER_COMPOSE run --rm agent-oci-to-umbrella test --config /config/config.yaml${NC}"
echo ""
echo "3. Run one-time sync:"
echo -e "   ${BLUE}$DOCKER_COMPOSE run --rm agent-oci-to-umbrella sync --config /config/config.yaml${NC}"
echo ""
echo "4. Start the agent (daemon mode):"
echo -e "   ${BLUE}$DOCKER_COMPOSE up -d${NC}"
echo ""
echo "5. View logs:"
echo -e "   ${BLUE}$DOCKER_COMPOSE logs -f${NC}"
echo ""
echo "6. Check status:"
echo -e "   ${BLUE}$DOCKER_COMPOSE ps${NC}"
echo ""
echo "7. Stop the agent:"
echo -e "   ${BLUE}$DOCKER_COMPOSE down${NC}"
echo ""
echo -e "${BLUE}==================================================${NC}"
