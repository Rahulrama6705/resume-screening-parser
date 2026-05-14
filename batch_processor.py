#!/usr/bin/env python3
"""
Batch process all resumes from the Unical Resumes folder.
"""

import os
import json
from pathlib import Path
from extractor import extract_text
from preprocess import normalize_resume_text
from llm_extractor import OllamaExtractor
from search_engine import SearchEngine

def process_all_resumes(input_dir, output_dir="extracted_data", max_resumes=None):
    """Process all resumes in a directory."""
    
    search_engine = SearchEngine(output_dir)
    extractor = OllamaExtractor()
    
    # Get all resume files
    resume_extensions = ('.pdf', '.docx', '.txt')
    resume_files = []
    
    for file in os.listdir(input_dir):
        if file.lower().endswith(resume_extensions):
            resume_files.append(file)
    
    resume_files.sort()
    if max_resumes:
        resume_files = resume_files[:max_resumes]
    
    print(f"Found {len(resume_files)} resumes to process")
    print("-" * 60)
    
    processed = 0
    failed = 0
    
    for idx, filename in enumerate(resume_files, 1):
        file_path = os.path.join(input_dir, filename)
        
        try:
            print(f"[{idx}/{len(resume_files)}] Processing: {filename[:50]}...", end=" ")
            
            # Extract text
            text = extract_text(file_path)
            if not text:
                print("FAILED (no text extracted)")
                failed += 1
                continue
            
            # Preprocess
            cleaned_text = normalize_resume_text(text)
            
            # Extract fields
            extracted_data = extractor.extract_fields(text[:2000])
            
            # Save to database
            search_engine.save_candidate(extracted_data)
            
            print("OK")
            processed += 1
            
        except Exception as e:
            print(f"ERROR: {str(e)[:30]}")
            failed += 1
    
    print("-" * 60)
    print(f"Processed: {processed}/{len(resume_files)}")
    print(f"Failed: {failed}")
    print(f"Total candidates in database: {search_engine.get_candidate_count()}")


if __name__ == "__main__":
    import sys
    
    input_dir = "/Users/rahulrama/Desktop/resume-screening-parser/Unical Resumes"
    max_resumes = int(sys.argv[1]) if len(sys.argv) > 1 else None
    
    
    process_all_resumes(input_dir, max_resumes=max_resumes)
