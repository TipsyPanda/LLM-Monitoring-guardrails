#!/usr/bin/env python3
"""
LMSYS Chatbot Arena Dataset Preparation Script

Downloads the LMSYS chatbot arena conversations dataset and converts it
to the format expected by the LLM monitoring system.

Usage:
    python prepare_lmsys_dataset.py [--sample-size N] [--output-path PATH]
"""

import argparse
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

try:
    from datasets import load_dataset
except ImportError:
    print("Error: 'datasets' library not installed")
    print("Install with: pip install datasets")
    sys.exit(1)


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
        help='Output CSV file path'
    )
    parser.add_argument(
        '--analyze-only', action='store_true',
        help='Only show statistics, do not save file'
    )
    
    args = parser.parse_args()
    
    # Download dataset
    dataset = download_lmsys_dataset(sample_size=args.sample_size)
    
    # Convert to monitoring format
    df = convert_to_monitoring_format(dataset)
    
    # Show statistics
    analyze_dataset(df)
    
    # Save to CSV
    if not args.analyze_only:
        output_path = Path(args.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(output_path, index=False)
        print(f"✓ Saved dataset to: {output_path}")
        print(f"  File size: {output_path.stat().st_size / (1024*1024):.2f} MB")
    else:
        print("\n(Dataset not saved - analyze-only mode)")
    
    print("\n" + "="*60)
    print("Next Steps:")
    print("="*60)
    print("1. Use with mock producer:")
    print(f"   python scripts/mock_conversation_producer.py --mode csv --csv-path {args.output_path}")
    print("\n2. Or use the fast ingestion script:")
    print(f"   python scripts/fast_ingest_lmsys.py --csv-path {args.output_path}")
    print("="*60)


if __name__ == "__main__":
    main()
