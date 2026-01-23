# LLM Monitoring with Guardrails

A Python prototype for monitoring LLM conversations and detecting toxic language using guardrails-ai. This system supports both batch processing of historical data and real-time Kafka-based input for pre-filtering user messages before they reach an LLM.

## Features

- **Toxic Language Detection**: Uses guardrails-ai with ToxicLanguage validator
- **Severity Classification**: Automatically classifies violations as LOW, MEDIUM, or HIGH
- **Multi-output**: Logs violations to both console and file (JSONL format)
- **Configurable Thresholds**: Adjust toxicity detection sensitivity
- **Two Input Modes**:
  - **Batch Mode**: Process CSV files for historical analysis
  - **Kafka Input Mode**: Real-time pre-filtering of user messages via Kafka
- **Alert Aggregation**: Time-windowed alert generation from violations
- **Dockerized Architecture**: Fully containerized with horizontal scaling support
- **Horizontally Scalable**: Run multiple guardrails processors in parallel
- **Test Dataset**: Includes sample conversations for quick testing

## Project Structure

```
LLM-Monitoring-guardrails/
├── src/
│   ├── config.py                    # Configuration management
│   ├── main.py                      # Batch mode entry point
│   ├── guardrail_input_processor.py # Kafka input mode entry point
│   ├── alert_consumer.py            # Alert aggregation service
│   ├── kafka/
│   │   ├── conversation_consumer.py # Kafka consumer for input messages
│   │   └── violation_producer.py    # Kafka producer for violations
│   ├── alert/
│   │   ├── window_tracker.py        # Sliding window for violations
│   │   └── alert_generator.py       # Alert generation logic
│   ├── models/
│   │   ├── conversation.py          # Conversation data model
│   │   ├── violation.py             # Violation data model
│   │   └── alert.py                 # Alert data model
│   └── processors/
│       ├── dataset_loader.py        # Load conversation data from CSV
│       └── guardrail_processor.py   # ToxicLanguage detection
├── scripts/
│   ├── mock_conversation_producer.py # Test producer for Kafka input
│   └── fast_ingest_lmsys.py        # Fast LMSYS dataset ingestion
├── data/
│   └── raw/
│       └── conversations.csv        # Test dataset
├── tests/
│   └── test_guardrail_processor.py  # Unit tests
├── outputs/                          # Generated outputs (gitignored)
│   ├── violations.jsonl             # Batch mode violations
│   ├── kafka_violations.jsonl       # Kafka mode violations
│   └── alerts.jsonl                 # Generated alerts
├── dashboard/                        # Streamlit monitoring dashboard
│   ├── app.py                       # Main dashboard application
│   ├── config.py                    # Dashboard configuration
│   ├── components/                  # UI components
│   │   ├── metrics.py               # KPI metric cards
│   │   ├── charts.py                # Plotly charts
│   │   ├── tables.py                # Data tables
│   │   └── filters.py               # Sidebar filters
│   └── data/                        # Data loading/processing
│       ├── loader.py                # JSONL file loading
│       └── processor.py             # Data transformations
├── start.sh                         # Automated startup script
├── stop.sh                          # Shutdown script
├── status.sh                        # Status checker
├── run_dashboard.sh                 # Dashboard launch script
├── docker-compose.yml               # Multi-container orchestration
├── Dockerfile.guardrails            # Guardrails processor container
├── Dockerfile.alert-consumer        # Alert consumer container
├── .dockerignore                    # Docker build exclusions
├── prepare_lmsys_dataset.py         # LMSYS dataset preparation
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
└── README.md
```

## Installation

### Prerequisites

- **Docker & Docker Compose**: Required for running Kafka and containerized services
- **Python 3.8 or higher**: For local development and dataset ingestion
- **pip package manager**: Python package installer
- **Virtual environment**: Recommended for local development

### Docker Installation

If you don't have Docker installed:

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install docker.io docker-compose
sudo systemctl start docker
sudo usermod -aG docker $USER  # Add user to docker group
# Log out and back in for group changes to take effect
```

**macOS:**
- Download and install [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)

**Windows:**
- Download and install [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)

### Setup Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/TipsyPanda/LLM-Monitoring-guardrails.git
   cd LLM-Monitoring-guardrails
   ```

2. **Create and activate virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install ToxicLanguage validator**:
   ```bash
   guardrails hub install hub://guardrails/toxic_language --quiet
   ```

5. **Set up environment variables** (optional):
   ```bash
   # Windows
   copy .env.example .env

   # macOS/Linux
   cp .env.example .env
   ```

   Edit [.env](.env) to customize configuration if needed.

## Quick Start

### Automated Startup (Recommended)

Use the provided shell scripts for easy startup and management:

```bash
cd ~/LLM-Monitoring-guardrails
./start.sh
```

The `start.sh` script automatically:
- Checks if you're in the right directory
- Verifies virtual environment exists
- Activates virtual environment (if not already)
- Checks Python dependencies are installed
- Verifies Docker is installed and accessible
- Creates .env file if missing
- Starts Docker containers if not running
- Waits for Kafka to be ready
- Offers to start the alert consumer

### Utility Scripts

| Script | Description |
|--------|-------------|
| `./start.sh` | Start all services (Kafka, processors) |
| `./stop.sh` | Stop all services, optionally remove Docker volumes |
| `./status.sh` | Check status of all components |
| `./run_dashboard.sh` | Launch the monitoring dashboard |

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

Cleanly stops Docker containers and optionally removes volumes.

### Quick Commands

**Docker (Recommended):**
```bash
# Start all services (build first time)
docker compose up --build

# Start in background
docker compose up --build -d

# Scale guardrails processors
docker compose up --scale guardrails-processor=3 -d

# View logs
docker compose logs -f guardrails-processor
docker compose logs -f alert-consumer

# Check status
docker compose ps

# Stop services
docker compose down

# Stop and remove all data
docker compose down -v
```

**Ingesting Data:**
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Ingest LMSYS dataset to Kafka
python prepare_lmsys_dataset.py --kafka --sample-size 1000

# Or use mock producer
python scripts/mock_conversation_producer.py --mode random --interval 2
```

**Monitoring:**
```bash
# Kafka UI (topics, messages, consumer groups)
open http://localhost:8080

# View outputs
cat outputs/alerts.jsonl | jq .
cat outputs/kafka_violations.jsonl | jq .

# Dashboard
./run_dashboard.sh
# Then open http://localhost:8501
```

**Legacy Scripts:**
```bash
# Automated startup script (local development mode)
./start.sh

# Check everything is running
./status.sh

# Stop everything
./stop.sh
```

## Usage

### Docker Deployment (Recommended)

The recommended way to run the system is using Docker Compose, which provides a fully containerized, horizontally scalable architecture.

#### Start All Services

```bash
# Build and start all services (Kafka + Guardrails + Alerts)
docker compose up --build

# Or run in detached mode (background)
docker compose up --build -d
```

This starts:
- **Kafka & Zookeeper**: Message broker infrastructure
- **Guardrails Processor(s)**: Consume from `llm.conversations`, detect toxicity, produce to `guardrail.violations`
- **Alert Consumer**: Aggregates violations into time-windowed alerts
- **Kafka UI**: Web interface at http://localhost:8080

#### Verify Services Are Running

```bash
# Check all containers
docker compose ps

# Watch guardrails processor logs
docker compose logs -f guardrails-processor

# Watch alert consumer logs
docker compose logs -f alert-consumer

# View all logs
docker compose logs -f
```

#### Ingest Test Data

From your host machine (with virtual environment activated):

```bash
# Ingest LMSYS dataset directly to Kafka
python prepare_lmsys_dataset.py --kafka --sample-size 100

# Or use the mock producer
python scripts/mock_conversation_producer.py --mode random --interval 2
```

#### Check Outputs

```bash
# View generated alerts
cat outputs/alerts.jsonl

# View violations
cat outputs/kafka_violations.jsonl
```

#### Horizontal Scaling

Scale the number of guardrails processors to handle higher throughput:

```bash
# Scale to 3 processors
docker compose up --scale guardrails-processor=3 -d

# Scale to 5 processors
docker compose up --scale guardrails-processor=5 -d

# Scale back to 1
docker compose up --scale guardrails-processor=1 -d
```

Kafka consumer groups automatically distribute work across instances. Each processor joins the same consumer group (`guardrail-input-processor-group`) and Kafka rebalances partitions across them.

#### Stop Services

```bash
# Stop and remove containers
docker compose down

# Stop and remove containers + volumes (reset Kafka data)
docker compose down -v
```

### Local Development Mode

For local development without Docker, you can run services manually:

#### Batch Mode (CSV Processing)

Process a CSV dataset and generate violation alerts:

```bash
python -m src.main
```

**Expected Output**:
```
2025-01-15 10:30:00 | INFO | Starting conversation processing...
2025-01-15 10:30:05 | WARNING | [HIGH] Violation in conv_003 | Labels: insult, toxicity
2025-01-15 10:30:07 | WARNING | [HIGH] Violation in conv_005 | Labels: threat, toxicity

==================================================
Processing Complete!
Total conversations: 8
Total violations: 3
==================================================
```

#### Kafka Input Mode (Manual Setup)

**1. Start Kafka infrastructure:**
```bash
docker compose up -d zookeeper kafka kafka-ui
```

**2. Start the guardrail input processor (Terminal 1):**
```bash
python -m src.guardrail_input_processor
```

**3. Start the alert consumer (Terminal 2):**
```bash
python -m src.alert_consumer
```

**4. Send test messages with the mock producer (Terminal 3):**
```bash
# Random mix (30% toxic, 70% clean)
python scripts/mock_conversation_producer.py --mode random --interval 2

# Only toxic messages
python scripts/mock_conversation_producer.py --mode toxic --interval 1

# Replay CSV file through Kafka
python scripts/mock_conversation_producer.py --mode csv --csv-path data/raw/conversations.csv
```

**Mock Producer Options:**
| Option | Description |
|--------|-------------|
| `--mode random` | 30% toxic, 70% clean messages (default) |
| `--mode toxic` | Only toxic messages |
| `--mode clean` | Only clean messages |
| `--mode csv` | Replay existing CSV file |
| `--interval 2` | Seconds between messages (default: 2) |
| `--count 10` | Send only N messages (default: infinite) |

**Kafka UI:**
Monitor messages at http://localhost:8080

### Run Tests

```bash
pytest tests/ -v
```

## Monitoring Dashboard

A Streamlit-based dashboard for visualizing violations, alerts, and toxicity metrics in real-time.

### Starting the Dashboard

```bash
./run_dashboard.sh
```

The dashboard will be available at **http://localhost:8501**

### Dashboard Features

| Feature | Description |
|---------|-------------|
| **Metric Cards** | Total violations, alerts, high severity counts |
| **Time Series Charts** | Violations and alerts over time by severity/danger level |
| **Label Distribution** | Horizontal bar chart of toxicity label frequency |
| **Severity Breakdown** | Pie charts showing severity and danger level distribution |
| **Score Heatmap** | Visual heatmap of toxicity scores across categories |
| **Interactive Tables** | Paginated, sortable tables for violations and alerts |

### Sidebar Filters

- **Data Source**: Filter by batch (CSV), Kafka (real-time), or both
- **Date Range**: Select start and end dates
- **Severity Levels**: Filter by LOW, MEDIUM, HIGH
- **Toxicity Labels**: Filter by specific toxicity categories
- **Conversation Search**: Search by conversation ID
- **Minimum Score**: Set threshold for toxicity score
- **Auto Refresh**: Enable automatic refresh (5-300 seconds)

### Dashboard Layout

```
+------------------------------------------+
|        LLM Monitoring Dashboard          |
+------------------------------------------+
| SIDEBAR      |   MAIN CONTENT            |
| - Source     | +------------------------+|
| - Date Range | |  METRIC CARDS          ||
| - Severity   | | [Total][High][Med][Low]||
| - Labels     | +------------------------+|
| - Refresh    | +------------------------+|
|              | |  TIME SERIES CHARTS    ||
|              | |  Violations | Alerts   ||
|              | +------------------------+|
|              | +----------+-------------+|
|              | | TOXICITY | SEVERITY   ||
|              | | BAR CHART| PIE CHART  ||
|              | +----------+-------------+|
|              | +------------------------+|
|              | |  DATA TABLES (Tabs)    ||
|              | |  Violations | Alerts   ||
|              | +------------------------+|
+------------------------------------------+
```

### Manual Dashboard Start

If you prefer to run directly with Streamlit:

```bash
source venv/bin/activate
streamlit run dashboard/app.py --server.port 8501
```

## Configuration

Configuration can be adjusted via environment variables or [src/config.py](src/config.py):

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `TOXICITY_THRESHOLD` | `0.5` | Minimum toxicity score to flag (0-1) |
| `OUTPUT_DIR` | `outputs` | Directory for output files |

### Batch Mode Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DATASET_PATH` | `data/raw/conversations.csv` | Path to conversation dataset |
| `KAFKA_ENABLED` | `true` | Send violations to Kafka in batch mode |

### Kafka Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka broker address |
| `KAFKA_TOPIC` | `guardrail.violations` | Output topic for violations |
| `KAFKA_INPUT_TOPIC` | `llm.conversations` | Input topic for user messages |
| `KAFKA_INPUT_CONSUMER_GROUP` | `guardrail-input-processor-group` | Consumer group for input processor |

### Alert Consumer Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ALERT_WINDOW_SIZE_SECONDS` | `300` | Time window for alert aggregation (5 min) |
| `ALERT_OUTPUT_FILE` | `outputs/alerts.jsonl` | Alert output file |
| `ALERT_CONSUMER_GROUP` | `alert-consumer-group` | Consumer group for alerts |

## Dataset Format

The system expects CSV files with the following columns:

```csv
conversation_id,text,timestamp,speaker
conv_001,"Hello, how can I help?",2025-01-15T10:30:00,agent
conv_001,"I need help with my order",2025-01-15T10:30:15,user
```

**Required fields**:
- `conversation_id`: Unique identifier for the conversation
- `text`: The message text to analyze
- `timestamp`: ISO 8601 format timestamp
- `speaker`: Either "user" or "agent" (optional)

### Using Your Own Dataset

1. Place your CSV file in [data/raw/](data/raw/)
2. Update `DATASET_PATH` in [.env](.env) or [src/config.py](src/config.py)
3. Run the processor: `python -m src.main`

### LMSYS Chatbot Arena Dataset

The system includes a built-in script to download and ingest the LMSYS Chatbot Arena dataset (33K real conversations) directly into Kafka:

```bash
# Download and send to Kafka (default behavior)
python prepare_lmsys_dataset.py --sample-size 1000

# Send only user messages (skip agent responses)
python prepare_lmsys_dataset.py --sample-size 1000 --user-only

# Save to CSV instead of Kafka
python prepare_lmsys_dataset.py --sample-size 1000 --csv

# Both Kafka and CSV
python prepare_lmsys_dataset.py --sample-size 1000 --kafka --csv

# Just analyze without ingesting
python prepare_lmsys_dataset.py --sample-size 100 --analyze-only
```

**Options:**
- `--sample-size N`: Download only N conversations (default: all ~33K)
- `--kafka`: Send directly to Kafka `llm.conversations` topic
- `--csv`: Save to CSV file
- `--user-only`: Only send user messages (skip agent responses)
- `--analyze-only`: Show statistics without saving

**Requirements:**
```bash
pip install datasets
```

### Other Dataset Options

1. **Create synthetic data** with known toxic examples for validation
2. **Use your own CSV** with the required format (see above)

## How It Works

### Toxicity Detection

The system uses two complementary approaches:

1. **Guardrails-AI**: Primary validation using the ToxicLanguage validator
   - Threshold-based detection
   - Sentence-level analysis
   - Raises exceptions on violations

2. **Detoxify**: Detailed toxicity scoring
   - Provides 7 toxicity categories:
     - `toxicity` - General toxic language
     - `severe_toxicity` - Extremely toxic
     - `obscene` - Obscene language
     - `threat` - Threatening language
     - `insult` - Insults
     - `identity_attack` - Attacks on identity
     - `sexual_explicit` - Sexual content
   - Scores range from 0 to 1

### Severity Classification

Violations are classified into three levels:

- **HIGH**: `severe_toxicity`, `threat`, or `identity_attack` > 0.7
- **MEDIUM**: Any score > 0.6 OR multiple violations (2+)
- **LOW**: Any score > threshold (default 0.5)

## Development

### Project Architecture

- **Models** ([src/models/](src/models/)): Data structures for conversations and violations
- **Processors** ([src/processors/](src/processors/)): Core business logic
  - `DatasetLoader`: Loads and parses CSV data
  - `GuardrailProcessor`: Detects toxic language and classifies severity
- **Main** ([src/main.py](src/main.py)): Orchestrates the processing pipeline

### Adding New Features

To add new guardrails:

1. Install the validator: `guardrails hub install hub://guardrails/<validator-name>`
2. Import in [guardrail_processor.py](src/processors/guardrail_processor.py)
3. Add to the Guard chain: `self.guard.use(NewValidator(...))`

## Architecture

### Docker Container Architecture

The system runs as multiple Docker containers orchestrated by Docker Compose:

```
┌─────────────────────────────────────────────────────────────┐
│                        Host Machine                          │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Docker Compose Network                     │ │
│  │                                                          │ │
│  │  ┌──────────────┐      ┌──────────────┐                │ │
│  │  │  Zookeeper   │◄─────┤    Kafka     │                │ │
│  │  │  :2181       │      │  :9092/:29092│                │ │
│  │  └──────────────┘      └───────┬──────┘                │ │
│  │                                 │                        │ │
│  │                        ┌────────┴────────┐              │ │
│  │                        │                 │              │ │
│  │                   Topic: llm.conversations              │ │
│  │                        │                 │              │ │
│  │         ┌──────────────┼─────────────────┼────────┐    │ │
│  │         │              │                 │        │    │ │
│  │  ┌──────▼───────┐ ┌───▼──────────┐ ┌───▼─────┐  │    │ │
│  │  │ Guardrails-1 │ │ Guardrails-2 │ │  ...    │  │    │ │
│  │  │ Processor    │ │ Processor    │ │ (scale) │  │    │ │
│  │  │ (Container)  │ │ (Container)  │ │         │  │    │ │
│  │  └──────┬───────┘ └───┬──────────┘ └───┬─────┘  │    │ │
│  │         │              │                 │        │    │ │
│  │         └──────────────┼─────────────────┘        │    │ │
│  │                        │                          │    │ │
│  │                Topic: guardrail.violations        │    │ │
│  │                        │                          │    │ │
│  │                  ┌─────▼────────┐                │    │ │
│  │                  │    Alert     │                │    │ │
│  │                  │   Consumer   │                │    │ │
│  │                  │ (Container)  │                │    │ │
│  │                  └──────┬───────┘                │    │ │
│  │                         │                         │    │ │
│  │                  outputs/alerts.jsonl            │    │ │
│  │                                                   │    │ │
│  │  ┌──────────────┐                                │    │ │
│  │  │   Kafka UI   │                                │    │ │
│  │  │   :8080      │                                │    │ │
│  │  └──────────────┘                                │    │ │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
│  Exposed Ports:                                           │
│    - Kafka: localhost:9092 (external)                     │
│    - Kafka UI: localhost:8080                             │
│    - Zookeeper: localhost:2181                            │
└────────────────────────────────────────────────────────────┘
```

**Key Features:**
- **Horizontal Scaling**: Run 1-N guardrails processors by scaling the container
- **Automatic Load Balancing**: Kafka consumer groups distribute partitions across processors
- **Fault Tolerance**: Containers restart on failure
- **Internal Networking**: Services communicate via Docker network (`kafka:29092`)
- **Volume Mounts**: Outputs persist to host `./outputs/` directory

### Data Flow

```
DOCKER MODE (containerized, scalable):
User Message
  → llm.conversations (Kafka topic)
  → Guardrails Processor Container(s) [1-N instances]
  → guardrail.violations (Kafka topic)
  → Alert Consumer Container
  → outputs/alerts.jsonl

BATCH MODE (local processing):
CSV File
  → DatasetLoader
  → GuardrailProcessor
  → guardrail.violations (Kafka, optional)
  → AlertConsumer
  → outputs/violations.jsonl
```

### Kafka Topics

| Topic | Description |
|-------|-------------|
| `llm.conversations` | Input: User messages to be checked before reaching LLM |
| `guardrail.violations` | Output: Detected toxic content violations |

### Consumer Groups

| Consumer Group | Service | Instances | Purpose |
|----------------|---------|-----------|---------|
| `guardrail-input-processor-group` | Guardrails Processor | 1-N | Scales horizontally; Kafka distributes partitions |
| `alert-consumer-group` | Alert Consumer | 1 | Single aggregator for time-windowed alerts |

### Message Formats

**Input Message (llm.conversations):**
```json
{
  "conversation_id": "conv_abc123",
  "text": "User message content",
  "timestamp": "2025-01-15T10:30:00",
  "speaker": "user"
}
```

**Violation Message (guardrail.violations):**
```json
{
  "conversation_id": "conv_abc123",
  "timestamp": "2025-01-15T10:30:00",
  "original_text": "Toxic message...",
  "severity": "high",
  "toxicity_labels": ["toxicity", "insult"],
  "toxic_sentences": ["Toxic message..."],
  "metadata": {"scores": {"toxicity": 0.95}}
}
```

## Troubleshooting

### Docker Issues

**Issue**: Docker containers fail to start
- **Solution**: Check Docker daemon is running:
  ```bash
  sudo systemctl status docker
  sudo systemctl start docker  # If not running
  ```

**Issue**: `docker compose` command not found
- **Solution**: Use `docker-compose` (with hyphen) on older Docker versions:
  ```bash
  docker-compose up --build
  ```

**Issue**: Permission denied when accessing Docker
- **Solution**: Add your user to the docker group:
  ```bash
  sudo usermod -aG docker $USER
  newgrp docker
  # Or log out and back in
  ```

**Issue**: Containers crash immediately after starting
- **Solution**: Check logs for specific errors:
  ```bash
  docker compose logs guardrails-processor
  docker compose logs alert-consumer
  docker compose logs kafka
  ```

**Issue**: "Cannot connect to Kafka" from containers
- **Solution**: Containers must use `kafka:29092` not `localhost:9092`. Check environment variables in docker-compose.yml.

**Issue**: Build fails with "no space left on device"
- **Solution**: Clean up Docker images and volumes:
  ```bash
  docker system prune -a
  docker volume prune
  ```

**Issue**: Slow first build (~2-3GB image)
- **Solution**: This is normal. ML models (torch, transformers, detoxify) are large. Subsequent builds use cached layers.

**Issue**: Models downloading during container runtime
- **Solution**: First run downloads detoxify models to container. They persist in the container until rebuilt.

**Issue**: Scaling doesn't increase throughput
- **Solution**:
  1. Ensure Kafka topic has enough partitions (1 partition = max 1 consumer)
  2. Check partition assignment: `docker exec llm-guardrails-kafka kafka-consumer-groups --describe --group guardrail-input-processor-group --bootstrap-server localhost:9092`

### Application Issues

**Issue**: `ModuleNotFoundError: No module named 'guardrails'`
- **Solution**: Ensure you've activated the virtual environment and run `pip install -r requirements.txt`

**Issue**: `guardrails hub install` fails
- **Solution**: Check internet connection and try again. May need to run as administrator on Windows.

**Issue**: `No such file or directory: 'data/raw/conversations.csv'`
- **Solution**: Verify the dataset file exists. You may need to create it or update `DATASET_PATH`.

**Issue**: Tests fail with model download errors
- **Solution**: First run may download ML models (detoxify). Ensure internet connection is stable.

**Issue**: Kafka connection refused (local development)
- **Solution**: Ensure Docker containers are running: `docker compose up -d`

**Issue**: `NoBrokersAvailable` error
- **Solution**: Wait a few seconds after starting Kafka, or check `docker compose logs kafka`

**Issue**: Port already in use (9092 or 8080)
- **Solution**: Check what's using the port:
  ```bash
  sudo lsof -i :9092
  sudo lsof -i :8080
  ```

**Issue**: Virtual environment issues
- **Solution**: Remove and recreate:
  ```bash
  rm -rf venv
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

## Production Considerations

This system provides a solid foundation for production use with Docker containerization and horizontal scaling. For full production deployment, consider:

**Already Implemented:**
- ✅ Docker containerization
- ✅ Horizontal scaling for guardrails processors
- ✅ Kafka-based message queue for reliability
- ✅ Consumer groups for load balancing
- ✅ Automatic restart on failure
- ✅ Volume mounts for persistent outputs

**Additional Recommendations:**
- Kafka replication factor > 1 for high availability
- Resource limits in docker-compose.yml (CPU/memory)
- Health checks for all services
- Prometheus/Grafana for metrics and monitoring
- Log aggregation (ELK stack, Loki)
- Authentication for Kafka (SASL/SSL)
- Database integration for long-term violation storage
- API gateway for external access
- Kubernetes deployment for cloud scaling

## Contact

**Author**: TipsyPanda (yannick.schmid@gmail.com)
**GitHub**: https://github.com/TipsyPanda/LLM-Monitoring-guardrails
