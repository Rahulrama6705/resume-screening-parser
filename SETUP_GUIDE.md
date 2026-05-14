# Setup Guide - Resume Screening ATS Dashboard

Complete step-by-step instructions to set up and run the resume screening system.

## Prerequisites

- **OS**: macOS (M1 optimized)
- **Python**: 3.8 or higher
- **Ollama**: Already installed on your system
- **Disk Space**: ~500MB
- **RAM**: 4GB minimum (8GB recommended)

## Step 1: Install Ollama Model

Ollama is already installed. Pull the required model:

```bash
ollama pull phi3:mini
```

Verify it's installed:
```bash
ollama list
```

You should see `phi3:mini` in the list.

## Step 2: Clone or Set Up Project Directory

The project is located at:
```
/Users/rahulrama/Desktop/resume-screening-parser/
```

## Step 3: Create Python Virtual Environment

```bash
cd /Users/rahulrama/Desktop/resume-screening-parser
python3 -m venv venv
```

## Step 4: Activate Virtual Environment

```bash
source venv/bin/activate
```

You should see `(venv)` prefix in your terminal.

## Step 5: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `streamlit` - Web dashboard
- `pymupdf` - PDF text extraction
- `python-docx` - DOCX file support
- `requests` - HTTP client for Ollama

## Step 6: Prepare Resume Folder

Place your resumes in the `Unical Resumes/` folder:

```
Unical Resumes/
├── resume1.pdf
├── resume2.pdf
├── resume3.docx
└── resume4.txt
```

Supported formats:
- `.pdf` (PDF files)
- `.docx` (Microsoft Word)
- `.txt` (Plain text)

## Step 7: Process Resumes (Optional - Database Already Prepared)

If you want to reprocess all resumes:

```bash
source venv/bin/activate
python3 batch_processor.py
```

This will:
1. Extract text from each resume
2. Parse fields (name, email, skills, experience, etc.)
3. Normalize specializations (CSE, AI, ML, ECE, etc.)
4. Store in SQLite database
5. Show progress and statistics

**Note**: Processing 100 resumes takes ~10-15 minutes.

## Step 8: Start the Dashboard

```bash
source venv/bin/activate
streamlit run streamlit_app.py
```

The app will start and display:
```
Local URL: http://localhost:8501
Network URL: http://192.168.1.x:8501
```

Open your browser and go to `http://localhost:8501`

## Step 9: Using the Dashboard

### Main Features:

**1. Upload New Resume**
- Click "Browse Files" in the Upload section
- Select a PDF, DOCX, or TXT file
- System automatically extracts and stores data

**2. Search Candidates**
- Use filter options on the left sidebar:
  - **Skills**: Multi-select for technical skills
  - **Experience**: Min/Max years (0-50)
  - **Education Degree**: B.Tech, MBA, etc.
  - **Education Specialization**: CSE, AI, ML, ECE, etc.
  - **Current Location**: City selection with synonyms
  - **Current Company**: Company name
  - **Salary Range**: Current and expected (LPA)

**3. View Results**
- Candidate cards show key details
- Click on a candidate to see full resume preview
- AI analysis section provides hiring insights

**4. Resume Preview**
- Full resume text in categorical order
- Contact information
- Experience details
- Education with GPA
- Skills and certifications
- Projects

## Troubleshooting

### Issue: Ollama Connection Error
**Error**: `ConnectionError: Failed to connect to Ollama`

**Solution**:
```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Run the app
cd /Users/rahulrama/Desktop/resume-screening-parser
source venv/bin/activate
streamlit run streamlit_app.py
```

### Issue: UI Shows Blank Page
**Error**: Page loads but shows only title and no filters

**Solution**:
- Make sure to use `streamlit run` (not `python`)
- Clear browser cache (Ctrl+Shift+Delete)
- Try a different browser
- Check console for errors (F12)

### Issue: No Module Named 'streamlit'
**Error**: `ModuleNotFoundError: No module named 'streamlit'`

**Solution**:
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Resume Not Extracted Properly
**Error**: Candidate name or skills not showing correctly

**Solution**:
- Ensure resume is a valid PDF, DOCX, or TXT
- Try a different resume to verify system works
- Some corrupted PDFs may fail extraction

### Issue: Search Returns No Results
**Error**: Applied filters but get 0 candidates

**Solution**:
- Filters are strict (not fuzzy) - exact matches only
- Try removing some filters to broaden search
- Check database statistics (shown in app)
- Ensure at least one matching candidate exists

### Issue: Database File Missing
**Error**: `candidates.db not found`

**Solution**:
```bash
# Reprocess all resumes to create database
source venv/bin/activate
python3 batch_processor.py
```

## File Descriptions

### Python Modules

| File | Purpose |
|------|---------|
| `streamlit_app.py` | Web dashboard (main UI) |
| `batch_processor.py` | Process all resumes in batch |
| `extractor.py` | Extract text from PDF/DOCX/TXT |
| `preprocess.py` | Clean and normalize text |
| `llm_extractor.py` | Extract fields using regex + LLM |
| `database.py` | SQLite database operations |
| `search_engine.py` | Search and filtering logic |
| `models.py` | Data structures |
| `parser.py` | Resume parsing utilities |
| `main.py` | CLI entry point |

### Data Files

| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies |
| `candidates.db` | SQLite database (created automatically) |
| `skills_master.json` | Skill taxonomy |
| `README.md` | Project overview |
| `SETUP_GUIDE.md` | This file |

## Advanced Configuration

### Change Ollama Model

Edit `llm_extractor.py`:
```python
class OllamaExtractor:
    def __init__(self, model: str = "phi3:mini"):  # Change model here
        self.model = model
```

### Adjust Filter Strictness

Edit `database.py` - `search_candidates()` method to modify filter logic.

### Add Custom Specializations

Edit `llm_extractor.py` - `SPECIALIZATION_MAPPING` dictionary:
```python
SPECIALIZATION_MAPPING = {
    "your major": ["CODE"],
    ...
}
```

### Increase Processing Batch Size

Edit `batch_processor.py`:
```python
max_resumes = 200  # Process up to 200 resumes
```

## Performance Tips

1. **First Run**: Slower due to Ollama model loading (1-2 minutes)
2. **Batch Processing**: Resume extraction ~5-10 seconds per resume
3. **Search**: Database queries complete in <100ms
4. **UI Refresh**: Streamlit rebuilds on every filter change

## Database Management

### View Database Statistics

```bash
source venv/bin/activate
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect("candidates.db")
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM candidates")
print(f"Total candidates: {cursor.fetchone()[0]}")
conn.close()
EOF
```

### Backup Database

```bash
cp candidates.db candidates.db.backup
```

### Clear Database

```bash
rm candidates.db  # Delete database
python3 batch_processor.py  # Reprocess resumes
```

## Security Notes

- All data is stored locally (no cloud)
- Resume text stored in SQLite database
- Ollama runs on device (no external API calls)
- Network access only if accessing from other machines

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 4GB | 8GB+ |
| Disk Space | 500MB | 1GB |
| Python | 3.8 | 3.10+ |
| macOS | Monterey | Ventura+ |

## M1 Optimization

System is optimized for Apple Silicon M1:
- Native Python ARM64 build
- Ollama phi3:mini (1.4B parameters - fast)
- No heavy dependencies
- Memory-efficient SQLite
- Streaming response from LLM

## Next Steps

1. **Process Resumes**: Run `batch_processor.py` to populate database
2. **Explore Dashboard**: Open Streamlit and browse candidates
3. **Customize Filters**: Adjust education specializations as needed
4. **Add Resumes**: Upload new resumes through the UI
5. **Integrate**: Connect to HR systems (future enhancement)

## Support & Debugging

Enable debug mode:
```bash
export ATS_DEBUG=1
streamlit run streamlit_app.py
```

This shows:
- Number of candidates loaded
- Filters applied
- Query times
- Filter relaxation steps

## Uninstall / Clean Up

To completely remove:

```bash
# Remove virtual environment
rm -rf venv/

# Remove database
rm candidates.db

# Remove generated files
rm -rf __pycache__ .streamlit/
```

The project directory remains intact for reinstallation.

## Additional Resources

- **Ollama**: https://ollama.ai
- **Streamlit**: https://streamlit.io
- **SQLite**: https://www.sqlite.org
- **PyMuPDF**: https://pymupdf.readthedocs.io

---

**Last Updated**: May 2026
**Version**: 2.0
**Status**: Production Ready
