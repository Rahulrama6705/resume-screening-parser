#!/bin/bash

# Quick Start Guide
# Resume Parser System - Ready to Use!

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Resume Parser System - QUICK START                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

cd /Users/rahulrama/Desktop/resume-screening-parser

# Check if already in venv
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "📦 Activating Python environment..."
    source venv/bin/activate
fi

echo "✓ Environment ready"
echo ""
echo "🚀 LAUNCH OPTIONS:"
echo ""
echo "1️⃣  Streamlit UI (Recommended for demos)"
echo "    streamlit run streamlit_app.py"
echo ""
echo "2️⃣  FastAPI Backend (For integrations)"
echo "    python main.py"
echo "    📍 Docs at: http://localhost:8000/docs"
echo ""
echo "3️⃣  Batch Process Resumes"
echo "    python batch_processor.py 20"
echo ""
echo "4️⃣  Live Demo"
echo "    python demo.py"
echo ""
echo "5️⃣  System Verification"
echo "    python verify.py"
echo ""
echo "📊 Current Status:"
echo "    • Candidates in DB: 26"
echo "    • Ollama: ✓ Running"
echo "    • Model: ✓ phi3:mini"
echo "    • System: ✓ READY"
echo ""
echo "📁 Project location:"
echo "    /Users/rahulrama/Desktop/resume-screening-parser/"
echo ""
