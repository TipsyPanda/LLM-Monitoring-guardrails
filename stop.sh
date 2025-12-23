#!/bin/bash

# Stop Script for LLM Monitoring Guardrails
# Cleanly stops all running services

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  LLM Monitoring Guardrails - Shutdown${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Stop Docker containers
echo -e "${BLUE}Stopping Docker containers...${NC}"
docker compose down

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Docker containers stopped"
else
    echo -e "${RED}✗${NC} Failed to stop Docker containers"
fi

# Check if any Python processes are still running
echo -e "\n${BLUE}Checking for running Python processes...${NC}"
ALERT_CONSUMER=$(pgrep -f "src.alert_consumer" || echo "")
MAIN_PROCESSOR=$(pgrep -f "src.main" || echo "")

if [ -n "$ALERT_CONSUMER" ]; then
    echo -e "${YELLOW}⚠${NC}  Alert consumer still running (PID: $ALERT_CONSUMER)"
    echo -e "   You may need to press Ctrl+C in that terminal"
fi

if [ -n "$MAIN_PROCESSOR" ]; then
    echo -e "${YELLOW}⚠${NC}  Main processor still running (PID: $MAIN_PROCESSOR)"
    echo -e "   You may need to press Ctrl+C in that terminal"
fi

if [ -z "$ALERT_CONSUMER" ] && [ -z "$MAIN_PROCESSOR" ]; then
    echo -e "${GREEN}✓${NC} No Python processes running"
fi

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Shutdown complete!${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Optional: Clean up volumes
read -p "Do you want to remove Docker volumes (this will delete Kafka data)? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\n${YELLOW}Removing Docker volumes...${NC}"
    docker compose down -v
    echo -e "${GREEN}✓${NC} Docker volumes removed"
fi
