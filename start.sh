#!/bin/bash

# Quick Start Script for LLM Monitoring Guardrails
# This script checks prerequisites and starts all services

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  LLM Monitoring Guardrails - Startup${NC}"
echo -e "${BLUE}========================================${NC}\n"

# 1. Check if we're in the correct directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml not found!${NC}"
    echo "Please run this script from the project root directory."
    exit 1
fi
echo -e "${GREEN}✓${NC} In project directory"

# 2. Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Error: Virtual environment not found!${NC}"
    echo "Please create it with: python3 -m venv venv"
    exit 1
fi
echo -e "${GREEN}✓${NC} Virtual environment exists"

# 3. Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠${NC}  Virtual environment not activated"
    echo -e "   Activating now..."
    source venv/bin/activate
    echo -e "${GREEN}✓${NC} Virtual environment activated"
else
    echo -e "${GREEN}✓${NC} Virtual environment already activated"
fi

# 4. Check if required Python packages are installed
echo -e "\n${BLUE}Checking Python dependencies...${NC}"
if ! python -c "import kafka" 2>/dev/null; then
    echo -e "${YELLOW}⚠${NC}  kafka-python not installed"
    echo -e "   Installing dependencies..."
    pip install -r requirements.txt -q
    echo -e "${GREEN}✓${NC} Dependencies installed"
else
    echo -e "${GREEN}✓${NC} Python dependencies installed"
fi

# 5. Check Docker installation
if ! command -v docker &> /dev/null; then
    echo -e "\n${RED}Error: Docker is not installed!${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker is installed"

# 6. Check Docker permissions
if ! docker ps &> /dev/null; then
    echo -e "${RED}Error: Cannot connect to Docker daemon!${NC}"
    echo "Please ensure:"
    echo "  1. Docker service is running: sudo systemctl start docker"
    echo "  2. Your user is in docker group: sudo usermod -aG docker \$USER"
    echo "  3. Log out and back in, or run: newgrp docker"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker permissions OK"

# 7. Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "\n${YELLOW}⚠${NC}  .env file not found"
    echo -e "   Creating from .env.example..."
    cp .env.example .env
    echo -e "${GREEN}✓${NC} Created .env file"
else
    echo -e "${GREEN}✓${NC} .env file exists"
fi

# 8. Check if Docker containers are running
echo -e "\n${BLUE}Checking Docker containers...${NC}"
CONTAINERS_RUNNING=$(docker compose ps --services --filter "status=running" | wc -l)

if [ "$CONTAINERS_RUNNING" -eq 3 ]; then
    echo -e "${GREEN}✓${NC} All 3 Kafka containers are running"
    echo "   - Zookeeper: $(docker inspect -f '{{.State.Status}}' llm-guardrails-zookeeper 2>/dev/null || echo 'unknown')"
    echo "   - Kafka: $(docker inspect -f '{{.State.Status}}' llm-guardrails-kafka 2>/dev/null || echo 'unknown')"
    echo "   - Kafka UI: $(docker inspect -f '{{.State.Status}}' llm-guardrails-kafka-ui 2>/dev/null || echo 'unknown')"
else
    echo -e "${YELLOW}⚠${NC}  Kafka containers not running (found: $CONTAINERS_RUNNING/3)"
    echo -e "   Starting Docker containers..."
    docker compose up -d

    # Wait for Kafka to be ready
    echo -e "   Waiting for Kafka to be ready..."
    sleep 10
    echo -e "${GREEN}✓${NC} Docker containers started"
fi

# 9. Verify Kafka is accessible
echo -e "\n${BLUE}Verifying Kafka connectivity...${NC}"
if timeout 5 bash -c 'cat < /dev/null > /dev/tcp/localhost/9092' 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Kafka broker is accessible on localhost:9092"
else
    echo -e "${YELLOW}⚠${NC}  Kafka broker not yet ready (may need a few more seconds)"
fi

# 10. Check if data directory exists
if [ ! -d "data/raw" ]; then
    echo -e "\n${YELLOW}⚠${NC}  Data directory not found"
    echo "   Creating data/raw directory..."
    mkdir -p data/raw
    echo -e "${GREEN}✓${NC} Created data/raw directory"
fi

# 11. Check if dataset exists
if [ ! -f "data/raw/conversations.csv" ]; then
    echo -e "\n${YELLOW}⚠${NC}  conversations.csv not found in data/raw/"
    echo "   Please add your dataset to data/raw/conversations.csv"
fi

# Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Environment ready!${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "${BLUE}Next steps:${NC}"
echo -e "  1. ${YELLOW}Terminal 1${NC} - Start alert consumer:"
echo -e "     ${GREEN}python -m src.alert_consumer${NC}"
echo -e ""
echo -e "  2. ${YELLOW}Terminal 2${NC} - Run main processor:"
echo -e "     ${GREEN}python -m src.main${NC}"
echo -e ""
echo -e "  3. ${YELLOW}Kafka UI${NC} - View messages:"
echo -e "     ${GREEN}http://localhost:8080${NC}"
echo -e ""
echo -e "${BLUE}========================================${NC}\n"

# Ask if user wants to start services
read -p "Do you want to start the alert consumer now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\n${BLUE}Starting alert consumer...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}\n"
    python -m src.alert_consumer
fi
