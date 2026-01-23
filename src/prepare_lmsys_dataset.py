#!/usr/bin/env python3
"""
LMSYS Chatbot Arena Dataset Preparation Script

Downloads the LMSYS chatbot arena conversations dataset and converts it
to the format expected by the LLM monitoring system.

Usage:
    python prepare_lmsys_dataset.py [--sample-size N] [--output-path PATH]
    python prepare_lmsys_dataset.py --kafka [--sample-size N]
"""

import argparse
import pandas as pd
from datetime import datetime
import sys
import os
import json
from pathlib import Path
from loguru import logger

try:
    from datasets import load_dataset
except ImportError:
    print("Error: 'datasets' library not installed")
    print("Install with: pip install datasets")
    sys.exit(1)

try:
    from kafka import KafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logger.warning("kafka-python not installed. Kafka output will not be available.")

from src.config import KafkaInputConfig


def download_lmsys_dataset(sample_size=None):
    """
    Download LMSYS chatbot arena conversations dataset
    
    Args:
        sample_size: Number of conversations to sample (None = all)
    
    Returns:
        HuggingFace dataset
    """
    print("Downloading LMSYS chatbot arena dataset...")
    print("This may take a few minutes on first run...")
    
    dataset = load_dataset('lmsys/chatbot_arena_conversations', split='train')
    
    print(f"✓ Downloaded {len(dataset)} conversations")
    
    if sample_size:
        print(f"Sampling {sample_size} conversations...")
        dataset = dataset.shuffle(seed=42).select(range(min(sample_size, len(dataset))))
    
    return dataset


def convert_to_monitoring_format(dataset):
    """
    Convert LMSYS dataset to monitoring system format
    
    Expected output format:
    - conversation_id: Unique identifier
    - text: Message content
    - timestamp: ISO 8601 timestamp
    - speaker: 'user' or 'agent'
    
    Args:
        dataset: HuggingFace dataset
    
    Returns:
        pandas DataFrame
    """
    print("Converting dataset to monitoring format...")
    
    rows = []
    
    for idx, example in enumerate(dataset):
        # LMSYS format has:
        # - question_id: conversation identifier
        # - conversation_a: list of conversation turns for model A
        # - conversation_b: list of conversation turns for model B
        # - tstamp: timestamp
        
        conversation_id = example.get('question_id', f'conv_{idx}')
        base_timestamp = example.get('tstamp', datetime.now().timestamp())
        
        # Process conversation_a (if exists)
        conv_a = example.get('conversation_a', [])
        if conv_a:
            for turn_idx, turn in enumerate(conv_a):
                # Each turn has 'role' and 'content'
                role = turn.get('role', 'user')
                content = turn.get('content', '')
                
                if content:  # Only add non-empty messages
                    # Map roles: 'user' -> 'user', 'assistant' -> 'agent'
                    speaker = 'user' if role == 'user' else 'agent'
                    
                    # Create timestamp with slight offset per turn
                    timestamp = datetime.fromtimestamp(base_timestamp + turn_idx)
                    
                    rows.append({
                        'conversation_id': f"{conversation_id}_a",
                        'text': content,
                        'timestamp': timestamp.isoformat(),
                        'speaker': speaker
                    })
        
        # Process conversation_b (if exists)
        conv_b = example.get('conversation_b', [])
        if conv_b:
            for turn_idx, turn in enumerate(conv_b):
                role = turn.get('role', 'user')
                content = turn.get('content', '')
                
                if content:
                    speaker = 'user' if role == 'user' else 'agent'
                    timestamp = datetime.fromtimestamp(base_timestamp + turn_idx + 0.5)
                    
                    rows.append({
                        'conversation_id': f"{conversation_id}_b",
                        'text': content,
                        'timestamp': timestamp.isoformat(),
                        'speaker': speaker
                    })
    
    df = pd.DataFrame(rows)
    print(f"✓ Converted {len(df)} messages from {df['conversation_id'].nunique()} conversations")
    
    return df


def send_to_kafka(df, bootstrap_servers, topic, user_only=False):
    """
    Send dataset directly to Kafka

    Args:
        df: pandas DataFrame with conversations
        bootstrap_servers: Kafka bootstrap servers
        topic: Kafka topic name
        user_only: If True, only send user messages
    """
    if not KAFKA_AVAILABLE:
        logger.error("Kafka library not available. Install with: pip install kafka-python")
        return False

    logger.info(f"Initializing Kafka producer: {bootstrap_servers}, topic: {topic}")

    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers.split(','),
        acks='all',
        batch_size=16384,
        linger_ms=10,
        compression_type='lz4',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    # Filter to user messages only if requested
    filtered_df = df[df['speaker'] == 'user'] if user_only else df
    total_messages = len(filtered_df)

    logger.info(f"Sending {total_messages} messages to Kafka...")
    start_time = datetime.now()
    sent_count = 0
    error_count = 0

    try:
        for _, row in filtered_df.iterrows():
            try:
                conversation = {
                    'conversation_id': row['conversation_id'],
                    'text': row['text'],
                    'timestamp': row['timestamp'],
                    'speaker': row['speaker']
                }

                producer.send(
                    topic,
                    key=conversation['conversation_id'].encode('utf-8'),
                    value=conversation
                )
                sent_count += 1

                if sent_count % 1000 == 0:
                    logger.info(f"Sent {sent_count}/{total_messages} messages...")

            except Exception as e:
                error_count += 1
                if error_count <= 10:
                    logger.error(f"Failed to send message: {e}")

        # Flush all pending messages
        logger.info("Flushing pending messages...")
        producer.flush()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("\n" + "="*60)
        logger.info("Kafka Ingestion Complete!")
        logger.info("="*60)
        logger.info(f"Total messages sent: {sent_count}")
        logger.info(f"Total errors: {error_count}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Throughput: {sent_count/duration:.2f} messages/second")
        logger.info("="*60)

        return True

    except KeyboardInterrupt:
        logger.info("\nIngestion interrupted by user")
        return False
    except Exception as e:
        logger.error(f"Error during Kafka ingestion: {e}")
        return False
    finally:
        producer.close()


def analyze_dataset(df):
    """Print dataset statistics"""
    print("\n" + "="*60)
    print("Dataset Statistics")
    print("="*60)
    print(f"Total messages: {len(df)}")
    print(f"Unique conversations: {df['conversation_id'].nunique()}")
    print(f"User messages: {len(df[df['speaker'] == 'user'])}")
    print(f"Agent messages: {len(df[df['speaker'] == 'agent'])}")
    print(f"\nDate range: {df['timestamp'].min()} to {df['timestamp'].max()}")

    # Sample messages
    print("\n" + "="*60)
    print("Sample Messages (first 3)")
    print("="*60)
    for idx, row in df.head(3).iterrows():
        print(f"\nConversation: {row['conversation_id']}")
        print(f"Speaker: {row['speaker']}")
        print(f"Text: {row['text'][:100]}...")
    print()


def main():
    parser = argparse.ArgumentParser(
        description='Prepare LMSYS dataset for LLM monitoring'
    )
    parser.add_argument(
        '--sample-size', type=int, default=None,
        help='Number of conversations to sample (default: all ~33K)'
    )
    parser.add_argument(
        '--output-path', type=str, default='data/raw/lmsys_conversations.csv',
        help='Output CSV file path (used when --csv flag is set)'
    )
    parser.add_argument(
        '--analyze-only', action='store_true',
        help='Only show statistics, do not save file or send to Kafka'
    )
    parser.add_argument(
        '--kafka', action='store_true',
        help='Send data directly to Kafka instead of saving to CSV'
    )
    parser.add_argument(
        '--csv', action='store_true',
        help='Save data to CSV file (can be used with --kafka to do both)'
    )
    parser.add_argument(
        '--user-only', action='store_true',
        help='Only send user messages to Kafka (skip agent responses)'
    )
    parser.add_argument(
        '--bootstrap-servers', type=str, default=None,
        help='Kafka bootstrap servers (default: from config)'
    )
    parser.add_argument(
        '--topic', type=str, default=None,
        help='Kafka topic (default: from config)'
    )

    args = parser.parse_args()

    # Default to Kafka if neither --kafka nor --csv is specified
    if not args.kafka and not args.csv and not args.analyze_only:
        args.kafka = True
        logger.info("No output mode specified, defaulting to --kafka")

    # Download dataset
    dataset = download_lmsys_dataset(sample_size=args.sample_size)

    # Convert to monitoring format
    df = convert_to_monitoring_format(dataset)

    # Show statistics
    analyze_dataset(df)

    if args.analyze_only:
        print("\n(Dataset not saved - analyze-only mode)")
        return

    # Send to Kafka
    if args.kafka:
        if not KAFKA_AVAILABLE:
            logger.error("Kafka output requested but kafka-python not installed")
            logger.error("Install with: pip install kafka-python")
            sys.exit(1)

        config = KafkaInputConfig()
        bootstrap_servers = args.bootstrap_servers or config.KAFKA_BOOTSTRAP_SERVERS
        topic = args.topic or config.KAFKA_INPUT_TOPIC

        logger.info(f"\nSending to Kafka topic: {topic}")
        success = send_to_kafka(
            df,
            bootstrap_servers=bootstrap_servers,
            topic=topic,
            user_only=args.user_only
        )

        if not success:
            logger.error("Kafka ingestion failed")
            sys.exit(1)

    # Save to CSV
    if args.csv:
        output_path = Path(args.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(output_path, index=False)
        print(f"\n✓ Saved dataset to: {output_path}")
        print(f"  File size: {output_path.stat().st_size / (1024*1024):.2f} MB")

    # Print next steps
    print("\n" + "="*60)
    print("Next Steps:")
    print("="*60)
    if args.kafka:
        print("✓ Data sent to Kafka topic: llm.conversations")
        print("  The guardrail processor should now process these conversations")
    if args.csv:
        print("\nAlternative ingestion methods:")
        print(f"1. Fast ingestion script:")
        print(f"   python scripts/fast_ingest_lmsys.py --csv-path {args.output_path}")
    print("="*60)


if __name__ == "__main__":
    main()
