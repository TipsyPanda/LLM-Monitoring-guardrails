#!/bin/bash

# Status Check Script for LLM Monitoring Guardrails
# Displays the current state of all services

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  LLM Monitoring Guardrails - Status${NC}"
echo -e "${BLUE}========================================${NC}\n"

# 1. Virtual Environment
echo -e "${BLUE}Virtual Environment:${NC}"
if [ -n "$VIRTUAL_ENV" ]; then
    echo -e "  ${GREEN}✓${NC} Activated: $VIRTUAL_ENV"
else
    echo -e "  ${YELLOW}⚠${NC} Not activated (run: source venv/bin/activate)"
fi

# 2. Docker Service
echo -e "\n${BLUE}Docker:${NC}"
if docker ps &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} Docker daemon running"
else
    echo -e "  ${RED}✗${NC} Docker daemon not accessible"
fi

# 3. Docker Containers
echo -e "\n${BLUE}Docker Containers:${NC}"
if docker compose ps &> /dev/null; then
    ZOOKEEPER_STATUS=$(docker inspect -f '{{.State.Status}}' llm-guardrails-zookeeper 2>/dev/null || echo 'not found')
    KAFKA_STATUS=$(docker inspect -f '{{.State.Status}}' llm-guardrails-kafka 2>/dev/null || echo 'not found')
    KAFKA_UI_STATUS=$(docker inspect -f '{{.State.Status}}' llm-guardrails-kafka-ui 2>/dev/null || echo 'not found')

    if [ "$ZOOKEEPER_STATUS" = "running" ]; then
        echo -e "  ${GREEN}✓${NC} Zookeeper: $ZOOKEEPER_STATUS"
    else
        echo -e "  ${RED}✗${NC} Zookeeper: $ZOOKEEPER_STATUS"
    fi

    if [ "$KAFKA_STATUS" = "running" ]; then
        echo -e "  ${GREEN}✓${NC} Kafka: $KAFKA_STATUS"
    else
        echo -e "  ${RED}✗${NC} Kafka: $KAFKA_STATUS"
    fi

    if [ "$KAFKA_UI_STATUS" = "running" ]; then
        echo -e "  ${GREEN}✓${NC} Kafka UI: $KAFKA_UI_STATUS (http://localhost:8080)"
    else
        echo -e "  ${RED}✗${NC} Kafka UI: $KAFKA_UI_STATUS"
    fi
else
    echo -e "  ${RED}✗${NC} Cannot check container status"
fi

# 4. Kafka Connectivity
echo -e "\n${BLUE}Kafka Broker:${NC}"
if timeout 2 bash -c 'cat < /dev/null > /dev/tcp/localhost/9092' 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Accessible on localhost:9092"
else
    echo -e "  ${RED}✗${NC} Not accessible on localhost:9092"
fi

# 5. Python Processes
echo -e "\n${BLUE}Python Processes:${NC}"
ALERT_CONSUMER=$(pgrep -f "src.alert_consumer" || echo "")
MAIN_PROCESSOR=$(pgrep -f "src.main" || echo "")

if [ -n "$ALERT_CONSUMER" ]; then
    echo -e "  ${GREEN}✓${NC} Alert Consumer running (PID: $ALERT_CONSUMER)"
else
    echo -e "  ${YELLOW}⚠${NC} Alert Consumer not running"
fi

if [ -n "$MAIN_PROCESSOR" ]; then
    echo -e "  ${GREEN}✓${NC} Main Processor running (PID: $MAIN_PROCESSOR)"
else
    echo -e "  ${YELLOW}⚠${NC} Main Processor not running"
fi

# 6. Output Files
echo -e "\n${BLUE}Output Files:${NC}"
if [ -f "outputs/violations.jsonl" ]; then
    VIOLATION_COUNT=$(wc -l < outputs/violations.jsonl)
    echo -e "  ${GREEN}✓${NC} violations.jsonl: $VIOLATION_COUNT violations"
else
    echo -e "  ${YELLOW}⚠${NC} violations.jsonl not found"
fi

if [ -f "outputs/alerts.jsonl" ]; then
    ALERT_COUNT=$(wc -l < outputs/alerts.jsonl)
    echo -e "  ${GREEN}✓${NC} alerts.jsonl: $ALERT_COUNT alerts"
else
    echo -e "  ${YELLOW}⚠${NC} alerts.jsonl not found"
fi

# 7. Dataset
echo -e "\n${BLUE}Dataset:${NC}"
if [ -f "data/raw/conversations.csv" ]; then
    CONVERSATION_COUNT=$(wc -l < data/raw/conversations.csv)
    echo -e "  ${GREEN}✓${NC} conversations.csv: $((CONVERSATION_COUNT - 1)) conversations"
else
    echo -e "  ${YELLOW}⚠${NC} conversations.csv not found"
fi

echo -e "\n${BLUE}========================================${NC}\n"
