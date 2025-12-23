#!/bin/bash

# Run the Streamlit Dashboard for LLM Monitoring Guardrails

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  LLM Monitoring Dashboard${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Navigate to project root
cd "$(dirname "$0")"

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓${NC} Virtual environment activated"
fi

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "Streamlit not found. Installing..."
    pip install streamlit plotly
fi

# Check if output files exist
if [ ! -d "outputs" ]; then
    echo "Warning: outputs/ directory not found"
    echo "Run the main processor first to generate data"
fi

echo -e "\n${GREEN}Starting dashboard...${NC}"
echo -e "Dashboard will be available at: ${BLUE}http://localhost:8501${NC}\n"

# Set PYTHONPATH to include project root for imports
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run Streamlit
streamlit run dashboard/app.py \
    --server.port 8501 \
    --server.headless true \
    --browser.gatherUsageStats false
