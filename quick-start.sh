#!/bin/bash

# Quick Start Wrapper - Source this file to activate venv and run startup checks
# Usage: source quick-start.sh  OR  . quick-start.sh

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✓ Virtual environment activated"
else
    echo "✗ Virtual environment not found! Creating..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✓ Virtual environment created and activated"
fi

# Run the main startup script
./start.sh
