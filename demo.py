#!/usr/bin/env python3
"""Quick demo of the resume parser system."""

import os
import json
from pathlib import Path

def print_section(title):
    """Print section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def demo_extraction():
    """Demo resume extraction."""
    print_section("DEMO 1: Resume Text Extraction")
    
    from extractor import extract_text
    
    resume_path = "/Users/rahulrama/Desktop/resume-screening-parser/Unical Resumes/AKSHAYA.pdf"
    
    print(f"\nFile: AKSHAYA.pdf")
    text = extract_text(resume_path)
    print(f"Extracted: {len(text)} characters")
    print(f"Preview:\n{text[:300]}...")

def demo_preprocessing():
    """Demo text preprocessing."""
    print_section("DEMO 2: Text Preprocessing")
    
    from preprocess import normalize_resume_text, extract_keywords
    
    sample_text = "Hello, I have 5+ years of Python  &  AWS experience! LinkedIn: https://linkedin.com"
    
    print(f"\nOriginal:\n{sample_text}")
    
    cleaned = normalize_resume_text(sample_text)
    print(f"\nCleaned:\n{cleaned}")
    
    keywords = extract_keywords(sample_text)
    print(f"\nExtracted Keywords: {', '.join(keywords)}")

def demo_llm_extraction():
    """Demo LLM field extraction."""
    print_section("DEMO 3: LLM Field Extraction")
    
    from extractor import extract_text
    from preprocess import normalize_resume_text
    from llm_extractor import OllamaExtractor
    
    resume_path = "/Users/rahulrama/Desktop/resume-screening-parser/Unical Resumes/Amar_Resumek1.pdf"
    
    print(f"\nProcessing: Amar_Resumek1.pdf")
    print("Extracting fields with phi3:mini...")
    
    text = extract_text(resume_path)
    cleaned = normalize_resume_text(text)
    
    extractor = OllamaExtractor()
    result = extractor.extract_fields(text[:2000])
    
    print(f"\nExtracted Fields:")
    print(f"  Name: {result.get('name')}")
    print(f"  Email: {result.get('email')}")
    print(f"  Phone: {result.get('phone')}")
    print(f"  Skills: {', '.join(result.get('skills', [])[:5])}")
    if len(result.get('skills', [])) > 5:
        print(f"           ... and {len(result.get('skills', [])) - 5} more")
    print(f"  Experience: {result.get('experience')}")
    print(f"  Education: {result.get('education')}")

def demo_srs_form():
    """Demo SRS form filling."""
    print_section("DEMO 4: SRS Auto-Fill")
    
    from parser import SRSAutoFiller
    
    test_data = {
        "name": "Amar Kumar",
        "email": "amar.kumar@example.com",
        "phone": "+91 9876543210",
        "company": "TCS",
        "skills": ["Python", "AWS", "Docker", "SQL"],
        "experience": "5 years",
        "education": "BTech CSE",
        "category": "Senior Software Engineer"
    }
    
    print(f"\nCandidate Data:")
    print(f"  Name: {test_data['name']}")
    print(f"  Email: {test_data['email']}")
    print(f"  Skills: {', '.join(test_data['skills'])}")
    
    form = SRSAutoFiller.fill_form(test_data)
    validation = SRSAutoFiller.validate_form(form)
    
    print(f"\nSRS Form Fields Auto-Filled:")
    print(f"  applicant_name: {form['applicant_name']}")
    print(f"  email_address: {form['email_address']}")
    print(f"  phone_number: {form['phone_number']}")
    print(f"  current_company: {form['current_company']}")
    print(f"  technical_skills: {form['technical_skills']}")
    print(f"  job_category: {form['job_category']}")
    print(f"  years_experience: {form['years_experience']}")
    
    print(f"\nValidation:")
    print(f"  Is Valid: {validation['is_valid']}")
    if validation['missing_fields']:
        print(f"  Missing: {', '.join(validation['missing_fields'])}")

def demo_search():
    """Demo candidate search."""
    print_section("DEMO 5: Candidate Database Search")
    
    from search_engine import SearchEngine
    
    se = SearchEngine()
    
    print(f"\nTotal Candidates: {se.get_candidate_count()}")
    
    print(f"\nSearch by Skill: Python")
    python_devs = se.search_by_skill("Python")
    print(f"  Found: {len(python_devs)} candidates")
    for candidate in python_devs[:3]:
        print(f"    - {candidate.get('name')} ({candidate.get('email')})")
    
    print(f"\nSearch by Name: Aishwarya")
    aishwarya_results = se.search_by_name("Aishwarya")
    print(f"  Found: {len(aishwarya_results)} candidates")
    for candidate in aishwarya_results:
        print(f"    - {candidate.get('name')} ({candidate.get('email')})")

def demo_analysis():
    """Demo AI analysis generation."""
    print_section("DEMO 6: AI-Generated Analysis")
    
    from search_engine import SearchEngine
    from llm_extractor import OllamaExtractor
    
    se = SearchEngine()
    extractor = OllamaExtractor()
    
    candidates = se.load_all_candidates()
    if candidates:
        candidate = candidates[0]
        print(f"\nGenerating analysis for: {candidate.get('name')}")
        
        analysis = extractor.generate_analysis(candidate)
        print(f"\nAI Analysis:")
        print(f"  {analysis}")

def main():
    """Run all demos."""
    print("\n" + "#"*70)
    print("#" + " "*68 + "#")
    print("#" + "  RESUME PARSER SYSTEM - LIVE DEMO".center(68) + "#")
    print("#" + " "*68 + "#")
    print("#"*70)
    
    try:
        demo_extraction()
        demo_preprocessing()
        demo_llm_extraction()
        demo_srs_form()
        demo_search()
        demo_analysis()
        
        print_section("DEMO COMPLETE")
        print("\nAll systems working perfectly!")
        print("\nNext Steps:")
        print("  1. Run Streamlit UI: streamlit run streamlit_app.py")
        print("  2. Run FastAPI: python main.py")
        print("  3. Batch process: python batch_processor.py [count]")
        print("\n" + "="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    sys.path.insert(0, '/Users/rahulrama/Desktop/resume_parser_system')
    main()
