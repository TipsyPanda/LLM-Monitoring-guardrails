# Quick Start Guide

## After Machine Restart

### Option 1: Automated Startup (Recommended)
```bash
cd ~/LLM-Monitoring-guardrails
./start.sh
```

This script automatically:
- ✓ Checks if you're in the right directory
- ✓ Verifies virtual environment exists
- ✓ Activates virtual environment (if not already)
- ✓ Checks Python dependencies are installed
- ✓ Verifies Docker is installed and accessible
- ✓ Creates .env file if missing
- ✓ Starts Docker containers if not running
- ✓ Waits for Kafka to be ready
- ✓ Offers to start the alert consumer

### Option 2: Manual Startup
```bash
# 1. Navigate to project
cd ~/LLM-Monitoring-guardrails

# 2. Activate virtual environment
source venv/bin/activate

# 3. Start Docker containers
docker compose up -d

# 4. Wait a few seconds for Kafka to be ready
sleep 10

# 5. Start services (in separate terminals)
# Terminal 1:
python -m src.alert_consumer

# Terminal 2:
python -m src.main
```

## Utility Scripts

### Check Status
```bash
./status.sh
```
Shows:
- Virtual environment status
- Docker containers status
- Kafka connectivity
- Running Python processes
- Output file statistics
- Dataset information

### Stop All Services
```bash
./stop.sh
```
Cleanly stops:
- Docker containers
- Optionally removes Docker volumes

## Quick Commands

```bash
# Check everything is running
./status.sh

# Start everything
./start.sh

# Stop everything
./stop.sh

# View Kafka UI
# Open in browser: http://localhost:8080

# View logs
tail -f outputs/violations.jsonl
tail -f outputs/alerts.jsonl

# Check Docker containers
docker compose ps

# Stop Docker containers only
docker compose down

# Restart Docker containers
docker compose restart
```

## Typical Workflow

### First Time Setup
```bash
cd ~/LLM-Monitoring-guardrails
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./start.sh
```

### After Machine Restart
```bash
cd ~/LLM-Monitoring-guardrails
./start.sh
```

### Daily Use
```bash
# Check status
./status.sh

# If services not running
./start.sh

# When done working
./stop.sh
```

## Troubleshooting

### Docker Permission Error
```bash
sudo usermod -aG docker $USER
newgrp docker
# Or log out and back in
```

### Kafka Not Starting
```bash
# Remove old containers and volumes
docker compose down -v
docker compose up -d
```

### Port Already in Use
```bash
# Check what's using port 9092
sudo lsof -i :9092

# Check what's using port 8080
sudo lsof -i :8080
```

### Virtual Environment Issues
```bash
# Remove and recreate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Directory Structure

```
LLM-Monitoring-guardrails/
├── start.sh              # Main startup script
├── stop.sh               # Shutdown script
├── status.sh             # Status checker
├── quick-start.sh        # Wrapper with venv activation
├── docker-compose.yml    # Kafka infrastructure
├── .env                  # Configuration (created from .env.example)
├── data/raw/             # Input dataset
├── outputs/              # Output files
│   ├── violations.jsonl  # Detected violations
│   └── alerts.jsonl      # Generated alerts
├── src/
│   ├── main.py          # Main processor
│   ├── alert_consumer.py # Alert consumer service
│   ├── kafka/           # Kafka producer
│   └── alert/           # Alert logic
└── venv/                # Python virtual environment
```

## Environment Variables

Edit `.env` to customize:
```bash
# Data
DATASET_PATH=data/raw/conversations.csv
TOXICITY_THRESHOLD=0.5
OUTPUT_DIR=outputs

# Kafka
KAFKA_ENABLED=true
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=guardrail.violations

# Alerts
ALERT_WINDOW_SIZE_SECONDS=300
ALERT_OUTPUT_FILE=outputs/alerts.jsonl
ALERT_CONSUMER_GROUP=alert-consumer-group
```
