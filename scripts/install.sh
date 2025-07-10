#!/bin/bash

# Docker Compose Install Script for PSN AI Guide Bot
# This script checks for Docker installation and runs the application

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Function to check if Docker is installed
check_docker_installed() {
    if command -v docker &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to check if Docker is running
check_docker_running() {
    if docker info &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to detect Docker Compose command
get_docker_compose_command() {
    # Try modern Docker Compose (docker compose)
    if docker compose version &> /dev/null; then
        echo "docker compose"
    # Fall back to legacy Docker Compose (docker-compose)
    elif docker-compose --version &> /dev/null; then
        echo "docker-compose"
    else
        echo ""
    fi
}

echo -e "${CYAN}=== PSN AI Guide Bot Setup ===${NC}"
echo ""

# Check if Docker is installed
echo -e "${YELLOW}Checking Docker installation...${NC}"
if ! check_docker_installed; then
    echo -e "${RED}Docker is not installed.${NC}"
    echo -e "${WHITE}Please install Docker from: https://docs.docker.com/get-docker/${NC}"
    echo -e "${WHITE}After installation, restart this script.${NC}"
    exit 1
else
    echo -e "${GREEN}Docker is installed.${NC}"
fi

# Check if Docker is running
echo -e "${YELLOW}Checking if Docker is running...${NC}"
if ! check_docker_running; then
    echo -e "${RED}Docker is not running.${NC}"
    echo -e "${WHITE}Please start Docker and then re-run this script.${NC}"
    exit 1
else
    echo -e "${GREEN}Docker is running.${NC}"
fi

# Detect Docker Compose command
echo -e "${YELLOW}Detecting Docker Compose...${NC}"
COMPOSE_CMD=$(get_docker_compose_command)
if [ -z "$COMPOSE_CMD" ]; then
    echo -e "${RED}Docker Compose not found.${NC}"
    echo -e "${WHITE}Please ensure Docker Compose is installed.${NC}"
    exit 1
else
    echo -e "${GREEN}Using: $COMPOSE_CMD${NC}"
fi

# Navigate to docker directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_PATH="$PROJECT_ROOT/docker"

if [ ! -d "$DOCKER_PATH" ]; then
    echo -e "${RED}Docker directory not found at: $DOCKER_PATH${NC}"
    echo -e "${WHITE}Please ensure you are running this script from the scripts/ directory.${NC}"
    exit 1
fi

echo -e "${YELLOW}Navigating to docker directory...${NC}"
cd "$DOCKER_PATH" || {
    echo -e "${RED}Failed to navigate to docker directory: $DOCKER_PATH${NC}"
    exit 1
}

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}docker-compose.yml not found in docker directory.${NC}"
    exit 1
fi

echo -e "${GREEN}Found docker-compose.yml${NC}"
echo ""

# Ask user about run mode
echo -e "${CYAN}Choose run mode:${NC}"
echo -e "${WHITE}1. Foreground (see logs, press Ctrl+C to stop)${NC}"
echo -e "${WHITE}2. Background (detached, runs in background)${NC}"
echo ""

while true; do
    read -p "Enter your choice (1 or 2): " choice
    case $choice in
        1|2) break;;
        *) echo "Please enter 1 or 2.";;
    esac
done

RUN_DETACHED=false
if [ "$choice" = "2" ]; then
    RUN_DETACHED=true
fi

# Stop any existing containers
echo -e "${YELLOW}Stopping any existing containers...${NC}"
if $COMPOSE_CMD -p psn-ai-guide-bot down --remove-orphans &> /dev/null; then
    echo -e "${GREEN}Cleaned up existing containers.${NC}"
else
    echo -e "${BLUE}No existing containers to stop.${NC}"
fi

# Start the application
echo ""
if $RUN_DETACHED; then
    echo -e "${YELLOW}Starting application in background...${NC}"
    if $COMPOSE_CMD -p psn-ai-guide-bot up -d; then
        echo -e "${GREEN}Application started successfully!${NC}"
        echo ""
        echo -e "${CYAN}Useful commands:${NC}"
        echo -e "${WHITE}- Check status: $COMPOSE_CMD -p psn-ai-guide-bot ps${NC}"
        echo -e "${WHITE}- View logs: $COMPOSE_CMD -p psn-ai-guide-bot logs -f${NC}"
        echo -e "${WHITE}- Stop app: $COMPOSE_CMD -p psn-ai-guide-bot down${NC}"
    else
        echo -e "${RED}Failed to start application.${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}Starting application in foreground...${NC}"
    echo -e "${BLUE}Press Ctrl+C to stop the application${NC}"
    echo ""
    if ! $COMPOSE_CMD -p psn-ai-guide-bot up; then
        echo -e "${RED}Failed to start application.${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}Setup complete!${NC}"