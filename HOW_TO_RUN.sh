#!/bin/bash

cat << 'EOF'

╔════════════════════════════════════════════════════════════════════════════╗
║                    HOW TO RUN THE PYTHON FILES                             ║
╚════════════════════════════════════════════════════════════════════════════╝

⚠️  IMPORTANT: Always activate the virtual environment first!

═══════════════════════════════════════════════════════════════════════════════

OPTION 1: Using the Wrapper Script (EASIEST) 🎯

cd /Users/rahulrama/Desktop/resume-screening-parser
./run.sh verify.py
./run.sh demo.py
./run.sh batch_processor.py 10

═══════════════════════════════════════════════════════════════════════════════

OPTION 2: Manual (Step-by-Step) 🔧

Step 1: Open Terminal
Step 2: Navigate to folder:
        cd /Users/rahulrama/Desktop/resume-screening-parser

Step 3: Activate environment:
        source venv/bin/activate
        
Step 4: Run any Python file:
        python3 verify.py
        python3 demo.py
        python3 batch_processor.py 10

═══════════════════════════════════════════════════════════════════════════════

AVAILABLE PYTHON FILES & WHAT THEY DO:

📋 STANDALONE SCRIPTS (Run these, they produce output):

   1. verify.py
      Purpose: Check if everything is working
      Command: ./run.sh verify.py
      Output: System status report
      Time: ~5 seconds

   2. demo.py  
      Purpose: Show all features working
      Command: ./run.sh demo.py
      Output: Live demonstration of features
      Time: ~30-60 seconds

   3. batch_processor.py
      Purpose: Process multiple resumes at once
      Command: ./run.sh batch_processor.py 20
      Command: ./run.sh batch_processor.py [number]
      Output: Progress of each resume
      Time: 30-60 seconds per resume

🚀 INTERACTIVE SERVERS (Run these, they stay running):

   4. main.py
      Purpose: Start FastAPI backend
      Command: ./run.sh main.py
      Output: "Uvicorn running on http://0.0.0.0:8000"
      Access: http://localhost:8000/docs
      Stop: Press Ctrl+C

   5. streamlit_app.py
      Purpose: Start web UI interface
      Command: ./run.sh streamlit_app.py
      OR: streamlit run streamlit_app.py
      Output: "You can now view your Streamlit app..."
      Access: http://localhost:8501
      Stop: Press Ctrl+C

🔧 CONFIGURATION FILES (Don't run these):

   6. extractor.py         - Module (imported by others)
   7. preprocess.py        - Module (imported by others)
   8. llm_extractor.py     - Module (imported by others)
   9. parser.py            - Module (imported by others)
   10. search_engine.py    - Module (imported by others)

═══════════════════════════════════════════════════════════════════════════════

QUICK REFERENCE:

┌─────────────────────────────────────────────────────────────────────────────┐
│ What You Want To Do                           │ Command                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ Check everything works                        │ ./run.sh verify.py            │
│ See live demo                                 │ ./run.sh demo.py              │
│ Process 20 resumes                            │ ./run.sh batch_processor.py 20│
│ Process all resumes                           │ ./run.sh batch_processor.py   │
│ Start API server                              │ ./run.sh main.py              │
│ Launch web interface                          │ ./run.sh streamlit_app.py     │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════

EXPECTED OUTPUT EXAMPLES:

Running verify.py:
   ✓ All modules imported successfully
   ✓ Database: 28 candidates stored
   ✓ Ollama connected, phi3:mini available
   ... (shows system status)

Running demo.py:
   ====== DEMO 1: Resume Text Extraction ======
   File: AKSHAYA.pdf
   Extracted: 2253 characters
   ... (shows 6 different demos)

Running batch_processor.py 5:
   Found 5 resumes to process
   [1/5] Processing: file1.pdf... OK
   [2/5] Processing: file2.pdf... OK
   ... (processes each resume)

═══════════════════════════════════════════════════════════════════════════════

TROUBLESHOOTING:

❌ "ModuleNotFoundError: No module named 'xyz'"
   → Activate environment: source venv/bin/activate
   → Verify environment: python3 -c "import xyz"

❌ "Command not found: python3"
   → Try: python verify.py (instead of python3)
   → Or: /usr/bin/python3 verify.py

❌ "No output when running script"
   → Check if you activated venv: source venv/bin/activate
   → Check if you're in correct directory
   → Add verbosity: python3 -u verify.py

❌ "FastAPI/Streamlit won't start"
   → Make sure ports 8000/8501 are free
   → Kill other Python processes
   → Try different port: streamlit run streamlit_app.py --server.port 8502

═══════════════════════════════════════════════════════════════════════════════

RECOMMENDED WORKFLOW:

1. First time setup:
   cd /Users/rahulrama/Desktop/resume-screening-parser
   source venv/bin/activate

2. Verify system:
   ./run.sh verify.py

3. See it working:
   ./run.sh demo.py

4. Process resumes:
   ./run.sh batch_processor.py 10

5. Launch UI:
   ./run.sh streamlit_app.py

═══════════════════════════════════════════════════════════════════════════════
EOF
