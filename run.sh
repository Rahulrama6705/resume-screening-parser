#!/bin/bash

# Wrapper script to run Python files with proper environment

cd /Users/rahulrama/Desktop/resume-screening-parser

# Activate virtual environment
source venv/bin/activate

# Get the Python file to run
SCRIPT=$1

if [ -z "$SCRIPT" ]; then
    echo "Usage: ./run.sh <script.py> [args]"
    echo ""
    echo "Available scripts:"
    echo "  run.sh verify.py          - System verification"
    echo "  run.sh demo.py            - Live demo"
    echo "  run.sh batch_processor.py [count] - Batch process resumes"
    echo "  run.sh main.py            - FastAPI server"
    echo "  run.sh streamlit_app.py   - Streamlit UI"
    exit 1
fi

# Run the script with all arguments
python3 "$@"
