#!/usr/bin/env python3
"""System verification script."""

import sys
import os
import json
import requests
from pathlib import Path

def print_header(text):
    """Print formatted header."""
    print("\n" + "="*60)
    print(text)
    print("="*60)

def check_modules():
    """Check Python module imports."""
    print("\nChecking module imports...")
    try:
        import extractor
        import preprocess
        import llm_extractor
        import parser
        import search_engine
        from fastapi import FastAPI
        import streamlit
        import pdfplumber
        print("  ✓ All modules imported successfully")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False

def check_database():
    """Check candidate database."""
    print("\nChecking candidate database...")
    try:
        from search_engine import SearchEngine
        se = SearchEngine()
        count = se.get_candidate_count()
        print(f"  ✓ Database: {count} candidates stored")
        return True
    except Exception as e:
        print(f"  ✗ Database error: {e}")
        return False

def check_ollama():
    """Check Ollama connection."""
    print("\nChecking Ollama...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json()
            models_list = [m['name'] for m in models.get('models', [])]
            if 'phi3:mini' in models_list:
                print(f"  ✓ Ollama connected, phi3:mini available")
                return True
            else:
                print(f"  ✗ Ollama connected but phi3:mini not found")
                print(f"    Available: {', '.join(models_list)}")
                return False
        else:
            print(f"  ✗ Ollama HTTP error: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Ollama error: {e}")
        return False

def check_llm():
    """Check LLM extractor."""
    print("\nChecking LLM extractor...")
    try:
        from llm_extractor import OllamaExtractor
        llm = OllamaExtractor()
        print("  ✓ LLM extractor initialized")
        return True
    except Exception as e:
        print(f"  ✗ LLM extractor error: {e}")
        return False

def check_srs():
    """Check SRS form filling."""
    print("\nChecking SRS form filler...")
    try:
        from parser import SRSAutoFiller
        test_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+91 9999999999",
            "skills": ["Python", "AWS"]
        }
        form = SRSAutoFiller.fill_form(test_data)
        validation = SRSAutoFiller.validate_form(form)
        print(f"  ✓ SRS form filling working")
        return True
    except Exception as e:
        print(f"  ✗ SRS form error: {e}")
        return False

def check_sample():
    """Check sample candidate data."""
    print("\nChecking sample candidate...")
    try:
        data_dir = Path("extracted_data")
        json_files = list(data_dir.glob("*.json"))
        if json_files:
            with open(json_files[0], 'r') as f:
                candidate = json.load(f)
            print(f"  ✓ Sample: {candidate.get('name', 'N/A')} ({candidate.get('email', 'N/A')})")
            return True
        else:
            print("  ⚠ No candidates in database yet")
            return True
    except Exception as e:
        print(f"  ✗ Data access error: {e}")
        return False

if __name__ == "__main__":
    print_header("RESUME PARSER SYSTEM - VERIFICATION")
    
    results = {
        "Modules": check_modules(),
        "Database": check_database(),
        "Ollama": check_ollama(),
        "LLM": check_llm(),
        "SRS": check_srs(),
        "Sample Data": check_sample()
    }
    
    print_header("VERIFICATION SUMMARY")
    for check, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {check}")
    
    all_passed = all(results.values())
    print("\n" + "="*60)
    if all_passed:
        print("STATUS: ALL SYSTEMS OPERATIONAL")
    else:
        print("STATUS: SOME CHECKS FAILED - SEE DETAILS ABOVE")
    print("="*60 + "\n")
    
    sys.exit(0 if all_passed else 1)
