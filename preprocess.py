import re


def clean_text(text):
    """Clean and normalize text while preserving line breaks."""
    if not text:
        return ""

    text = text.replace("\r", "\n")
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        line = re.sub(r"[ \t]+", " ", line).strip()
        if line:
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def normalize_resume_text(text):
    """Normalize resume text for LLM processing."""
    text = clean_text(text)
    
    # Remove URLs but keep the domain
    text = re.sub(r'https?://[^\s]+', '', text)
    
    # Handle common abbreviations
    replacements = {
        r'\bbtw\b': 'by the way',
        r'\bexp\b': 'experience',
        r'\byrs\b': 'years',
        r'\bmo\b': 'months',
        r'\bqa\b': 'quality assurance',
    }
    
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text


def extract_keywords(text):
    """Extract potential keywords for analysis."""
    keywords = set()
    
    # Common skill keywords
    skill_patterns = [
        r'\b(python|java|javascript|typescript|c\+\+|c#|go|rust|kotlin)\b',
        r'\b(react|vue|angular|django|flask|fastapi|spring|springboot)\b',
        r'\b(aws|azure|gcp|docker|kubernetes|jenkins|gitlab|github)\b',
        r'\b(sql|mongodb|postgresql|mysql|redis|elasticsearch)\b',
        r'\b(ml|ai|machine learning|deep learning|nlp|cv)\b',
    ]
    
    for pattern in skill_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        keywords.update(matches)
    
    return list(keywords)
