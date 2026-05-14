from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from pathlib import Path

from extractor import extract_text
from preprocess import normalize_resume_text
from llm_extractor import OllamaExtractor
from parser import SRSAutoFiller
from search_engine import SearchEngine

app = FastAPI(title="Resume Parser API", version="1.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
extractor = OllamaExtractor()
search_engine = SearchEngine()

UPLOAD_DIR = Path("Unical Resumes")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Resume Parser API",
        "version": "1.0"
    }


@app.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    """Upload and process a resume."""
    try:
        # Save uploaded file
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Extract text
        resume_text = extract_text(str(file_path))
        
        if not resume_text:
            raise HTTPException(status_code=400, detail="Could not extract text from file")
        
        # Preprocess
        cleaned_text = normalize_resume_text(resume_text)
        
        # Extract fields using LLM
        extracted_data = extractor.extract_fields(cleaned_text)
        
        # Fill SRS form
        srs_form = SRSAutoFiller.fill_form(extracted_data)
        
        # Validate form
        validation = SRSAutoFiller.validate_form(srs_form)
        
        file_stat = file_path.stat()
        candidate_id = search_engine.save_candidate(
            extracted_data,
            source_file=str(file_path),
            file_mtime=file_stat.st_mtime,
            file_size=file_stat.st_size,
            extraction_version=search_engine.extraction_version,
        )
        
        return {
            "success": True,
            "filename": file.filename,
            "extracted_data": extracted_data,
            "srs_form": srs_form,
            "validation": validation,
            "candidate_id": candidate_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract_resume")
async def extract_resume(file: UploadFile = File(...)):
    """Extract and analyze resume without SRS form."""
    try:
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        resume_text = extract_text(str(file_path))
        
        if not resume_text:
            raise HTTPException(status_code=400, detail="Could not extract text from file")
        
        cleaned_text = normalize_resume_text(resume_text)
        extracted_data = extractor.extract_fields(cleaned_text)
        
        # Generate AI analysis
        analysis = extractor.generate_analysis(extracted_data)
        
        file_stat = file_path.stat()
        candidate_id = search_engine.save_candidate(
            extracted_data,
            source_file=str(file_path),
            file_mtime=file_stat.st_mtime,
            file_size=file_stat.st_size,
            extraction_version=search_engine.extraction_version,
        )
        
        return {
            "success": True,
            "filename": file.filename,
            "extracted_data": extracted_data,
            "analysis": analysis,
            "candidate_id": candidate_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/candidates")
async def get_all_candidates():
    """Get all processed candidates."""
    candidates = search_engine.load_all_candidates()
    return {
        "total": len(candidates),
        "candidates": candidates
    }


@app.post("/search/filters")
async def search_with_filters(filters: dict):
    """Search candidates using structured filters."""
    results = search_engine.search_with_filters(filters)
    return {
        "count": len(results),
        "results": results
    }


@app.get("/search/skill/{skill}")
async def search_by_skill(skill: str):
    """Search candidates by skill."""
    results = search_engine.search_by_skill(skill)
    return {
        "skill": skill,
        "count": len(results),
        "results": results
    }


@app.get("/search/name/{name}")
async def search_by_name(name: str):
    """Search candidates by name."""
    results = search_engine.search_by_name(name)
    return {
        "name": name,
        "count": len(results),
        "results": results
    }


@app.get("/search/email/{email}")
async def search_by_email(email: str):
    """Search candidate by email."""
    candidate = search_engine.search_by_email(email)
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    return {
        "email": email,
        "candidate": candidate
    }


@app.get("/search/category/{category}")
async def search_by_category(category: str):
    """Search candidates by job category."""
    results = search_engine.search_by_category(category)
    return {
        "category": category,
        "count": len(results),
        "results": results
    }


@app.get("/stats")
async def get_statistics():
    """Get system statistics."""
    stats = search_engine.db.get_stats()
    top_skills = search_engine.db.get_top_skills(limit=10)
    return {
        "total_candidates": stats["total_candidates"],
        "total_uploads": stats["total_uploads"],
        "avg_experience": stats["avg_experience"],
        "extraction_accuracy": stats["extraction_accuracy"],
        "top_skills": [skill for skill, _ in top_skills]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
