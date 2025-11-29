# LLM Monitoring with Guardrails

A Python prototype for monitoring LLM conversations and detecting toxic language using guardrails-ai. This system processes historical conversation data, detects violations, classifies them by severity (low/medium/high), and generates alerts.

## Features

- **Toxic Language Detection**: Uses guardrails-ai with ToxicLanguage validator
- **Severity Classification**: Automatically classifies violations as LOW, MEDIUM, or HIGH
- **Multi-output**: Logs violations to both console and file (JSONL format)
- **Configurable Thresholds**: Adjust toxicity detection sensitivity
- **Test Dataset**: Includes sample conversations for quick testing
- **Extensible**: Ready for Phase 2 Kafka integration

## Project Structure

```
LLM-Monitoring-guardrails/
├── src/
│   ├── config.py                    # Configuration management
│   ├── main.py                      # Main execution pipeline
│   ├── models/
│   │   ├── conversation.py          # Conversation data model
│   │   └── violation.py             # Violation/alert data model
│   └── processors/
│       ├── dataset_loader.py        # Load conversation data
│       └── guardrail_processor.py   # ToxicLanguage detection
├── data/
│   └── raw/
│       └── conversations.csv        # Test dataset (8 samples)
├── tests/
│   └── test_guardrail_processor.py  # Unit tests
├── outputs/                          # Generated violations (gitignored)
│   └── violations.jsonl
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

### Run the Prototype

Process the test dataset and generate violation alerts:

```bash
python -m src.main
```

### Expected Output

**Console output**:
```
2025-01-15 10:30:00 | INFO | Starting conversation processing...
2025-01-15 10:30:05 | WARNING | [HIGH] Violation in conv_003 | Labels: insult, toxicity
2025-01-15 10:30:07 | WARNING | [HIGH] Violation in conv_005 | Labels: threat, toxicity
2025-01-15 10:30:09 | WARNING | [MEDIUM] Violation in conv_007 | Labels: insult, obscene

==================================================
Processing Complete!
Total conversations: 8
Total violations: 3
Severity breakdown:
  LOW: 0
  MEDIUM: 1
  HIGH: 2

Results saved to: outputs/violations.jsonl
==================================================
```

**File output** ([outputs/violations.jsonl](outputs/violations.jsonl)):
```json
{"conversation_id": "conv_003", "timestamp": "2025-01-15T10:10:00", "original_text": "You're an idiot...", "severity": "high", ...}
{"conversation_id": "conv_005", "timestamp": "2025-01-15T10:20:00", "original_text": "I will destroy...", "severity": "high", ...}
```

### Run Tests

```bash
pytest tests/ -v
```

## Configuration

Configuration can be adjusted via environment variables or [src/config.py](src/config.py):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATASET_PATH` | `data/raw/conversations.csv` | Path to conversation dataset |
| `TOXICITY_THRESHOLD` | `0.5` | Minimum toxicity score to flag (0-1) |
| `OUTPUT_DIR` | `outputs` | Directory for violation logs |
| `HIGH_SEVERITY_THRESHOLD` | `0.7` | Threshold for HIGH severity |
| `MEDIUM_SEVERITY_THRESHOLD` | `0.6` | Threshold for MEDIUM severity |

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

## Phase 2: Kafka Integration (Planned)

Future enhancements will include:

- **Kafka Producer**: Stream violations to Kafka topics
- **Kafka Consumer**: Real-time alert aggregation
- **Docker Compose**: Local Kafka setup for development
- **Time-windowed Analysis**: Alert aggregation over time periods
- **Dashboard**: Real-time monitoring interface

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
