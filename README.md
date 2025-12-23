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
│   └── mock_conversation_producer.py # Test producer for Kafka input
├── data/
│   └── raw/
│       └── conversations.csv        # Test dataset
├── tests/
│   └── test_guardrail_processor.py  # Unit tests
├── outputs/                          # Generated outputs (gitignored)
│   ├── violations.jsonl             # Batch mode violations
│   ├── kafka_violations.jsonl       # Kafka mode violations
│   └── alerts.jsonl                 # Generated alerts
├── docker-compose.yml               # Kafka infrastructure
├── requirements.txt                  # Python dependencies
├── .env.example                     # Environment variables template
└── README.md
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

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

## Usage

### Batch Mode (CSV Processing)

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

### Kafka Input Mode (Real-time Pre-filtering)

Pre-filter user messages before they reach an LLM. Messages are consumed from Kafka, checked through guardrails, and violations are published to a violations topic.

**1. Start Kafka infrastructure:**
```bash
docker compose up -d
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

### Larger Datasets

For testing with real conversation data, consider:

1. **LMSYS Chatbot Arena** (33K conversations):
   ```bash
   pip install datasets
   python -c "from datasets import load_dataset; dataset = load_dataset('lmsys/chatbot_arena_conversations')"
   ```

2. **Create synthetic data** with known toxic examples for validation

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

### Data Flow

```
KAFKA INPUT MODE (real-time pre-filtering):
User Message --> llm.conversations (Kafka) --> GuardrailInputProcessor --> guardrail.violations (Kafka) --> AlertConsumer --> alerts.jsonl

BATCH MODE (historical analysis):
CSV File --> DatasetLoader --> GuardrailProcessor --> guardrail.violations (Kafka) --> AlertConsumer --> alerts.jsonl
```

### Kafka Topics

| Topic | Description |
|-------|-------------|
| `llm.conversations` | Input: User messages to be checked before reaching LLM |
| `guardrail.violations` | Output: Detected toxic content violations |

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

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'guardrails'`
- **Solution**: Ensure you've activated the virtual environment and run `pip install -r requirements.txt`

**Issue**: `guardrails hub install` fails
- **Solution**: Check internet connection and try again. May need to run as administrator on Windows.

**Issue**: `No such file or directory: 'data/raw/conversations.csv'`
- **Solution**: Verify the dataset file exists. You may need to create it or update `DATASET_PATH`.

**Issue**: Tests fail with model download errors
- **Solution**: First run may download ML models (detoxify). Ensure internet connection is stable.

**Issue**: Kafka connection refused
- **Solution**: Ensure Docker containers are running: `docker compose up -d`

**Issue**: `NoBrokersAvailable` error
- **Solution**: Wait a few seconds after starting Kafka, or check `docker compose logs kafka`

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

## Contributing

This is a school project prototype. For production use, consider:
- More robust error handling
- Batch processing for large datasets
- Database integration for violation storage
- Authentication and authorization
- Rate limiting and monitoring

## Contact

**Author**: TipsyPanda (yannick.schmid@gmail.com)
**GitHub**: https://github.com/TipsyPanda/LLM-Monitoring-guardrails
