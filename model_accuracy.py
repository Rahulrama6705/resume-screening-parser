#!/usr/bin/env python3
"""
Model Accuracy Analytics - Run from terminal
Usage: python3 model_accuracy.py
"""

import json
import os
from pathlib import Path
from extractor import extract_text_from_pdf, extract_text_from_docx
from llm_extractor import OllamaExtractor

def calculate_accuracy():
    """Calculate extraction accuracy for all resumes in dataset."""
    
    print("\n" + "="*70)
    print("📊 MODEL ACCURACY ANALYTICS - PHI3:MINI")
    print("="*70 + "\n")
    
    resume_dir = "Unical Resumes"
    extracted_dir = "extracted_data"
    
    if not os.path.exists(resume_dir):
        print("❌ Resume folder 'Unical Resumes' not found!")
        return
    
    # Get all resume files
    files = []
    for ext in ['*.pdf', '*.docx', '*.txt']:
        files.extend(Path(resume_dir).glob(ext))
    
    if not files:
        print("❌ No resumes found in Unical Resumes folder!")
        return
    
    print(f"📁 Found {len(files)} resumes\n")
    
    # Extractor
    extractor = OllamaExtractor()
    
    # Metrics
    metrics = {
        "name": [],
        "email": [],
        "phone": [],
        "skills": [],
        "experience": [],
        "education": [],
        "company": []
    }
    
    # Process each resume
    for idx, resume_file in enumerate(sorted(files)[:50], 1):  # First 50 for speed
        resume_name = resume_file.name
        
        # Extract text
        if resume_file.suffix.lower() == '.pdf':
            text = extract_text_from_pdf(str(resume_file))
        elif resume_file.suffix.lower() == '.docx':
            text = extract_text_from_docx(str(resume_file))
        else:
            try:
                with open(resume_file, 'r') as f:
                    text = f.read()
            except:
                continue
        
        if not text or len(text) < 50:
            continue
        
        # Extract fields
        result = extractor.extract_fields(text)
        
        # Track completeness
        metrics["name"].append(1 if result.get('name') else 0)
        metrics["email"].append(1 if result.get('email') else 0)
        metrics["phone"].append(1 if result.get('phone') else 0)
        metrics["skills"].append(1 if result.get('skills') else 0)
        metrics["experience"].append(1 if result.get('experience') else 0)
        metrics["education"].append(1 if result.get('education') else 0)
        metrics["company"].append(1 if result.get('company') else 0)
        
        # Progress
        print(f"  [{idx}] {resume_name[:40]:<40} ✓")
    
    # Calculate accuracy percentages
    print("\n" + "="*70)
    print("📈 FIELD EXTRACTION ACCURACY")
    print("="*70 + "\n")
    
    total = len([x for x in metrics["name"]])
    
    if total == 0:
        print("❌ No data to analyze")
        return
    
    accuracy_scores = {}
    for field, values in metrics.items():
        if values:
            accuracy = (sum(values) / len(values)) * 100
            accuracy_scores[field] = accuracy
            bar_length = int(accuracy / 5)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            print(f"  {field.upper():<12} │{bar}│ {accuracy:>6.1f}%")
    
    # Overall accuracy
    print("\n" + "-"*70)
    overall = sum(accuracy_scores.values()) / len(accuracy_scores) if accuracy_scores else 0
    bar_length = int(overall / 5)
    bar = "█" * bar_length + "░" * (20 - bar_length)
    print(f"  {'OVERALL':<12} │{bar}│ {overall:>6.1f}%")
    print("-"*70 + "\n")
    
    # Performance summary
    print("📊 SUMMARY")
    print("-"*70)
    print(f"  Total Resumes Processed: {total}")
    print(f"  Model: phi3:mini (Ollama)")
    print(f"  Extraction Method: LLM + Regex Fallback")
    print("\n")
    
    # Field-specific insights
    print("🔍 FIELD-SPECIFIC INSIGHTS")
    print("-"*70)
    
    high_accuracy = [f for f, v in accuracy_scores.items() if v >= 80]
    low_accuracy = [f for f, v in accuracy_scores.items() if v < 60]
    
    if high_accuracy:
        print(f"  ✅ Strong fields (≥80%): {', '.join([f.title() for f in high_accuracy])}")
    
    if low_accuracy:
        print(f"  ⚠️  Weak fields (<60%): {', '.join([f.title() for f in low_accuracy])}")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    try:
        calculate_accuracy()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")
        import traceback
        traceback.print_exc()
