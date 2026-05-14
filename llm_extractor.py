import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import requests


SKILLS_PATH = Path(__file__).with_name("skills_master.json")

# Specialization normalization mapping
# Maps various resume text to canonical specialization codes
# Engineering disciplines - strict exact matching
SPECIALIZATION_MAPPING = {
    # ===== Computer Science variants =====
    "computer science": ["CSE"],
    "computer science engineering": ["CSE"],
    "cse": ["CSE"],
    "cs": ["CSE"],
    "btech cse": ["CSE"],
    "b.tech cse": ["CSE"],
    
    # ===== Artificial Intelligence (STANDALONE) =====
    "artificial intelligence": ["AI"],
    "artificial intelligence engineering": ["AI"],
    "ai": ["AI"],
    "btech ai": ["AI"],
    "b.tech ai": ["AI"],
    
    # ===== Machine Learning (STANDALONE) =====
    "machine learning": ["ML"],
    "machine learning engineering": ["ML"],
    "ml": ["ML"],
    "btech ml": ["ML"],
    "b.tech ml": ["ML"],
    
    # ===== Combined AI + ML (should split into both) =====
    "artificial intelligence and machine learning": ["AI", "ML"],
    "machine learning and artificial intelligence": ["AI", "ML"],
    "ai and ml": ["AI", "ML"],
    "ml and ai": ["AI", "ML"],
    "ai/ml": ["AI", "ML"],
    "ai & ml": ["AI", "ML"],
    "aiml": ["AI", "ML"],
    "ai&ml": ["AI", "ML"],
    "artificial intelligence and ml": ["AI", "ML"],  # New variant
    "ai and machine learning": ["AI", "ML"],  # New variant
    "btech aiml": ["AI", "ML"],
    "b.tech aiml": ["AI", "ML"],
    
    # ===== Electronics and Communication Engineering (ECE) =====
    "electronics and communication": ["ECE"],
    "electronics and communication engineering": ["ECE"],
    "electronics & communication": ["ECE"],
    "electronics & communication engineering": ["ECE"],
    "electronics and communications": ["ECE"],
    "electronics and communications engineering": ["ECE"],
    "ece": ["ECE"],
    "e&c": ["ECE"],
    "ec": ["ECE"],
    "btech ece": ["ECE"],
    "b.tech ece": ["ECE"],
    
    # ===== Electrical and Electronics Engineering (EEE) =====
    "electrical and electronics": ["EEE"],
    "electrical and electronics engineering": ["EEE"],
    "electrical & electronics": ["EEE"],
    "electrical & electronics engineering": ["EEE"],
    "electrical engineering": ["EEE"],
    "eee": ["EEE"],
    "e&e": ["EEE"],
    "btech eee": ["EEE"],
    "b.tech eee": ["EEE"],
    
    # ===== Information Technology =====
    "information technology": ["IT"],
    "information technology engineering": ["IT"],
    "it": ["IT"],
    "btech it": ["IT"],
    "b.tech it": ["IT"],
    
    # ===== Data Science =====
    "data science": ["Data Science"],
    "data science engineering": ["Data Science"],
    "ds": ["Data Science"],
    "btech ds": ["Data Science"],
    "b.tech ds": ["Data Science"],
    
    # ===== Mechanical Engineering =====
    "mechanical engineering": ["Mechanical"],
    "mechanical": ["Mechanical"],
    "me": ["Mechanical"],
    "btech mechanical": ["Mechanical"],
    "b.tech mechanical": ["Mechanical"],
    
    # ===== Civil Engineering =====
    "civil engineering": ["Civil"],
    "civil": ["Civil"],
    "ce": ["Civil"],
    "btech civil": ["Civil"],
    "b.tech civil": ["Civil"],
    
    # ===== Cybersecurity =====
    "cybersecurity": ["Cybersecurity"],
    "cyber security": ["Cybersecurity"],
    "btech cybersecurity": ["Cybersecurity"],
    "b.tech cybersecurity": ["Cybersecurity"],
}

def normalize_specializations(raw_text: str) -> List[str]:
    """Normalize specialization text to canonical codes.
    
    Handles:
    - Exact matches (computer science → CSE)
    - Partial matches (B.Tech ECE → ECE)
    - Multi-tag specializations (AI and ML → [AI, ML])
    - Missing/invalid specializations → [Other]
    
    Args:
        raw_text: Raw specialization text from resume (e.g., "B.Tech Electronics and Communication")
        
    Returns:
        List of normalized specialization codes (e.g., ["AI", "ML"])
    """
    if not raw_text:
        return ["Other"]
    
    raw_text = raw_text.strip().lower()
    
    # Direct mapping lookup (exact match)
    if raw_text in SPECIALIZATION_MAPPING:
        return SPECIALIZATION_MAPPING[raw_text]
    
    # Try to find matches by searching for key terms
    # Process in order of specificity (longer keys first)
    sorted_keys = sorted(SPECIALIZATION_MAPPING.keys(), key=len, reverse=True)
    
    for key in sorted_keys:
        if key in raw_text and len(key) > 2:  # Avoid single/double char matches
            return SPECIALIZATION_MAPPING[key]
    
    # No match found
    return ["Other"]


class OllamaExtractor:
    def __init__(self, model: str = "phi3:mini", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.skills_master = self._load_skills_master()
        self._llm_enabled = True

    def extract_fields(self, resume_text: str) -> Dict:
        """Extract structured candidate fields using LLM + regex + skills master."""
        resume_text = resume_text or ""

        regex_data = self._regex_extract(resume_text)
        merged = dict(regex_data)
        merged["skills"] = self._extract_skills(resume_text, [])

        merged["resume_text"] = resume_text.strip()
        merged["uploaded_at"] = datetime.utcnow().isoformat()
        if not merged.get("candidate_id"):
            merged["candidate_id"] = str(uuid.uuid4())

        # Backward compatibility fields
        merged["company"] = merged.get("current_company", "")
        merged["experience"] = str(merged.get("experience_years", "")) if merged.get("experience_years") else ""
        education_parts = [
            merged.get("education_degree", ""),
            merged.get("education_specialization", ""),
            merged.get("education_type", ""),
        ]
        merged["education"] = " | ".join([p for p in education_parts if p])

        return merged

    def _llm_extract_skills(self, resume_text: str) -> List[str]:
        """Optional LLM-only skill extraction. Returns empty list if unavailable."""
        if not self._llm_enabled:
            return []
        text = resume_text[:1500]
        prompt = (
            "Extract only technical skills from the resume. "
            "Return a JSON array of strings. No extra text.\n\n"
            f"RESUME:\n{text}\n\n"
            "JSON:\n[\"Python\", \"AWS\", \"Docker\"]"
        )

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False, "temperature": 0.1},
                timeout=25,
            )
        except requests.RequestException:
            self._llm_enabled = False
            return []

        if response.status_code != 200:
            self._llm_enabled = False
            return []

        resp_text = response.json().get("response", "")
        start = resp_text.find("[")
        end = resp_text.rfind("]")

        if start == -1 or end == -1 or end <= start:
            self._llm_enabled = False
            return []

        json_str = resp_text[start : end + 1]
        try:
            skills = json.loads(json_str)
        except json.JSONDecodeError:
            self._llm_enabled = False
            return []

        return [s.strip() for s in skills if isinstance(s, str) and s.strip()]

    def _regex_extract(self, text: str) -> Dict:
        """Regex-based extraction for key fields."""
        result = {
            "candidate_id": "",
            "name": "",
            "email": "",
            "phone": "",
            "skills": [],
            "experience_years": 0.0,
            "current_company": "",
            "current_location": "",
            "education_degree": "",
            "education_specialization": "",
            "education_type": "",
            "current_salary": 0.0,
            "expected_salary": 0.0,
            "projects": [],
            "certifications": [],
            "summary": "",
            "resume_text": "",
            "uploaded_at": "",
        }

        name_patterns = [
            r"^\s*Name\s*:\s*([A-Za-z][A-Za-z\s]{2,50})",
            r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)$",
            r"^([A-Z][A-Za-z\s]{2,40})$",
        ]
        blacklist = {
            "work experience",
            "experience",
            "education",
            "skills",
            "projects",
            "certifications",
            "summary",
            "profile",
            "objective",
            "professional summary",
        }
        for pattern in name_patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                candidate_name = match.group(1).strip()
                if candidate_name.lower() in blacklist:
                    continue
                result["name"] = candidate_name
                break

        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        if email_match:
            result["email"] = email_match.group(0)

        phone_patterns = [
            r"(?:\+91|0)?[6789]\d{9}",
            r"\+\d{1,3}[\s]?\d{5,14}",
            r"\(\+?\d{1,3}\)\s?\d{3,4}[\s.-]?\d{3,4}[\s.-]?\d{4}",
        ]
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                result["phone"] = match.group(0).strip()
                break

        result["experience_years"] = self._extract_experience_years(text)
        result["current_company"] = self._extract_company(text)
        result["current_location"] = self._extract_location(text)

        degree, specialization, edu_type = self._extract_education(text)
        result["education_degree"] = degree
        result["education_specialization"] = specialization
        result["education_type"] = edu_type

        result["current_salary"] = self._extract_salary(text, expected=False)
        result["expected_salary"] = self._extract_salary(text, expected=True)

        result["projects"] = self._extract_section_items(text, ["projects", "project"])
        result["certifications"] = self._extract_section_items(text, ["certifications", "certification"])

        return result

    def _load_skills_master(self) -> List[str]:
        if not SKILLS_PATH.exists():
            return []
        try:
            data = json.loads(SKILLS_PATH.read_text())
            skills = data.get("skills", [])
        except (json.JSONDecodeError, OSError):
            skills = []
        return [s.strip() for s in skills if isinstance(s, str) and s.strip()]

    def _extract_skills(self, text: str, llm_skills: List[str]) -> List[str]:
        skills_found = []

        for skill in llm_skills or []:
            if isinstance(skill, str) and skill.strip():
                skills_found.append(skill.strip())

        normalized_text = text.lower()
        lower_text = text.lower()
        for skill in self.skills_master:
            skill_lower = skill.lower()
            if self._skill_in_text(skill, skill_lower, lower_text):
                skills_found.append(skill)

        # Skills section quick parse
        skills_section = self._extract_section_block(text, ["skills", "technical skills"])
        if skills_section:
            tokens = re.split(r"[,•|/;\n]", skills_section)
            for token in tokens:
                token = token.strip()
                if token:
                    normalized = self._normalize_skill_token(token, normalized_text)
                    if normalized:
                        skills_found.extend(normalized)
                    else:
                        skills_found.append(token)

        # Add keyword-based fallback
        keyword_hits = re.findall(
            r"\b(python|java|c\+\+|aws|azure|docker|kubernetes|qt|qml|linux|sql|react|fastapi|machine learning|ai|ml)\b",
            lower_text,
            flags=re.IGNORECASE,
        )
        for hit in keyword_hits:
            normalized = self._normalize_skill_token(hit, normalized_text)
            if normalized:
                skills_found.extend(normalized)

        unique = []
        seen = set()
        for skill in skills_found:
            key = skill.lower()
            if key not in seen:
                unique.append(skill)
                seen.add(key)
        return unique

    def _skill_in_text(self, skill: str, skill_lower: str, lower_text: str) -> bool:
        if skill_lower in ["c++", "c#", "node.js", ".net"]:
            pattern = re.escape(skill_lower)
            return re.search(pattern, lower_text) is not None
        if skill_lower in ["react", "reactjs"]:
            return "react" in lower_text
        if skill_lower in ["node.js", "nodejs"]:
            return "node" in lower_text
        return re.search(r"\b" + re.escape(skill_lower) + r"\b", lower_text) is not None

    def _normalize_skill_token(self, token: str, lower_text: str) -> List[str]:
        token_clean = token.strip().lower()
        stopwords = {"skills", "technical skills", "tools", "languages"}
        if token_clean in stopwords or len(token_clean) < 2:
            return []

        mappings = {
            "reactjs": "React",
            "react.js": "React",
            "nodejs": "Node.js",
            "node.js": "Node.js",
            "ml": "Machine Learning",
            "ai": "AI",
            "ai/ml": "AI/ML",
            "c plus plus": "C++",
            "cplusplus": "C++",
            "c sharp": "C#",
            "qt/qml": "Qt",
        }

        if token_clean in mappings:
            return [mappings[token_clean]]

        if "machine learning" in token_clean:
            return ["Machine Learning"]
        if "deep learning" in token_clean:
            return ["Deep Learning"]
        if "data science" in token_clean:
            return ["Data Science"]
        if "embedded" in token_clean and "c" in token_clean:
            return ["Embedded C"]

        if any(skill.lower() == token_clean for skill in self.skills_master):
            return [token.strip()]

        return []

    def _extract_experience_years(self, text: str) -> float:
        """Extract total years of experience from resume text."""
        
        # Strategy 1: Look for explicit "X years of experience" mentions
        explicit_patterns = [
            r"(\d+(?:\.\d+)?)\s*(?:\+)?\s*years?\s+of\s+(?:professional\s+)?experience",
            r"experience\s*(?::|=)?\s*(\d+(?:\.\d+)?)\s*(?:\+)?\s*years?",
            r"with\s+(\d+(?:\.\d+)?)\s*(?:\+)?\s*years?\s+of\s+experience",
            r"(\d+(?:\.\d+)?)\s*(?:\+)?\s*(?:yrs?|years?)\s+(?:exp|experience|of\s+exp)",
            r"approximately\s+(\d+(?:\.\d+)?)\s*years?",
            r"about\s+(\d+(?:\.\d+)?)\s*years?",
        ]
        
        for pattern in explicit_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except (ValueError, IndexError):
                    continue
        
        # Strategy 2: Look for experience range like "3y 2m" or "3.5 years"
        range_pattern = r"(\d+)(?:y|years?)\s*(?:\d+)?(?:m|months?)?|(\d+\.\d+)\s*(?:years?|yrs?)"
        match = re.search(range_pattern, text[:500], re.IGNORECASE)
        if match:
            try:
                years = match.group(1) or match.group(2)
                return float(years)
            except (ValueError, IndexError, TypeError):
                pass
        
        # Strategy 3: Look for "X years" in professional summary section
        summary_pattern = r"(?:professional\s+)?summary.*?(\d+(?:\.\d+)?)\s*(?:\+)?\s*years?"
        match = re.search(summary_pattern, text[:800], re.IGNORECASE | re.DOTALL)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, IndexError):
                pass
        
        # Strategy 4: Look for dates to calculate experience
        # Pattern: "2020 - 2024" or "Jan 2020 - Dec 2024"
        date_pattern = r"(20\d{2})\s*(?:–|-|to)\s*(20\d{2})"
        matches = re.findall(date_pattern, text)
        if matches:
            try:
                years_list = [int(end) - int(start) for start, end in matches]
                total_exp = max(years_list)  # Take longest tenure
                if total_exp > 0 and total_exp <= 70:
                    return float(total_exp)
            except (ValueError, IndexError):
                pass
        
        # Strategy 5: Check if it's clearly a fresher
        fresher_keywords = ["fresher", "recent graduate", "graduate", "entry level", "newly graduated"]
        if any(keyword in text.lower()[:500] for keyword in fresher_keywords):
            return 0.0
        
        # Strategy 6: Look for any year mention in first 1000 chars
        # Take the maximum reasonable value
        all_matches = re.findall(r"(\d+(?:\.\d+)?)\s*(?:\+)?\s*(?:years|yrs|year)", text[:1000], re.IGNORECASE)
        if all_matches:
            try:
                years = [float(m) for m in all_matches]
                # Filter out unreasonable numbers (> 70 years is probably not experience)
                years = [y for y in years if 0 <= y <= 70]
                return max(years) if years else 0.0
            except ValueError:
                pass
        
        # No experience found - could be fresher
        return 0.0

    def _extract_company(self, text: str) -> str:
        """Extract current/most recent company from resume."""
        
        # Common role keywords to look for  after company names
        role_keywords = (
            "Software Engineer", "Developer", "Systems Engineer", "Data Scientist",
            "QA Engineer", "DevOps", "Cloud Engineer", "Backend", "Frontend",
            "Full Stack", "Intern", "Associate", "Analyst", "Manager", "Senior",
            "Lead", "Technical", "Architect", "Consultant", "Specialist",
            "Trainee", "Apprentice", "Fresher"
        )
        
        # Strategy 1: Look for "at CompanyName" pattern (most reliable)
        at_pattern = r"at\s+([A-Za-z0-9\s&'().,\-]+?)(?:\n|,|$)"
        matches = re.findall(at_pattern, text, re.IGNORECASE)
        for match in matches:
            company = match.strip().rstrip('.,;:-')
            if self._is_valid_company_name(company):
                return company
        
        # Strategy 2: Look for "Company – Role" pattern in experience section
        exp_section_pattern = r"(?:WORK\s+EXPERIENCE|PROFESSIONAL\s+EXPERIENCE|EXPERIENCE|EMPLOYMENT|INTERNSHIP)[:\s]*(.*?)(?=\n(?:EDUCATION|SKILLS|PROJECTS|CERTIFICATIONS|$))"
        exp_match = re.search(exp_section_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if exp_match:
            exp_section = exp_match.group(1)
            lines = exp_section.split('\n')
            
            # Process first few lines of experience section
            for line in lines[:15]:
                line = line.strip()
                if not line or len(line) < 3:
                    continue
                
                # Look for "CompanyName – Position" or "CompanyName | Position"
                for sep in ['–', '—', '|', ' - ']:
                    if sep in line:
                        parts = line.split(sep, 1)
                        potential_company = parts[0].strip()
                        
                        if self._is_valid_company_name(potential_company):
                            return potential_company
                
                # Check if line contains role keyword and extract company from before it
                for role in role_keywords:
                    if role.lower() in line.lower():
                        idx = line.lower().find(role.lower())
                        potential_company = line[:idx].strip()
                        potential_company = potential_company.rstrip('–—|-,: \t')
                        
                        if self._is_valid_company_name(potential_company):
                            return potential_company
        
        # Strategy 3: Look for explicit mentions with "working"/"currently"
        explicit_patterns = [
            r"(?:currently\s+(?:working|employed)\s+(?:at|with))\s*[:\-]?\s*([A-Za-z0-9\s&'().,\-]{3,100}?)(?:\n|$)",
            r"(?:current\s+)?employer\s*[:\-]\s*([A-Za-z0-9\s&'().,\-]{3,100}?)(?:\n|$)",
        ]
        
        for pattern in explicit_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                company = match.group(1).strip().rstrip('.,;:-')
                if self._is_valid_company_name(company):
                    return company
        
        return ""
    
    def _is_valid_company_name(self, text: str) -> bool:
        """Check if text looks like a company name."""
        if not text or len(text.strip()) < 2:
            return False
        
        text = text.strip()
        lower_text = text.lower()
        
        # Exclude common non-company strings
        excluded = [
            "other", "n/a", "na", "company", "self", "self employed",
            "freelance", "unknown", "same", "current", "my", "own",
            "various", "multiple", "different", "working", "employed",
            "experience", "education", "project", "skill", "languages",
            "and", "or", "the", "a", "an", "is", "as"
        ]
        
        if lower_text in excluded:
            return False
        
        # Allow if it has common company indicators
        company_indicators = ["Inc", "Ltd", "Pvt", "LLC", "Corp", "Pvt Ltd", "AG", "GmbH", "SA", "&"]
        if any(indicator in text for indicator in company_indicators):
            return True
        
        # Allow multi-word names (likely companies)
        words = text.split()
        if len(words) >= 2:
            # Check that it doesn't look like a description
            description_words = ["developing", "working", "building", "managing", "leading", "handling"]
            if not any(word.lower() in description_words for word in words):
                return True
        
        # Allow single words that are capitalized (proper nouns) and not generic words
        if len(words) == 1:
            generic_words = ["engineer", "developer", "analyst", "manager", "lead", "senior", "junior"]
            if text[0].isupper() and lower_text not in generic_words:
                return True
        
        # Allow if matches patterns like "Google", "Microsoft", "Apple", "Amazon"
        if len(text) >= 3 and text[0].isupper():
            return True
        
        return False

    def _extract_location(self, text: str) -> str:
        # City synonyms mapping
        city_synonyms = {
            "Bangalore": ["Bangalore", "Bengaluru", "Blr"],
            "Hyderabad": ["Hyderabad", "Hyd", "Secunderabad"],
            "Chennai": ["Chennai", "Madras"],
            "Mumbai": ["Mumbai", "Bombay"],
            "Pune": ["Pune", "Poona"],
            "Delhi": ["Delhi", "New Delhi", "Noida", "Gurgaon", "Gurugram"],
            "Gurgaon": ["Gurgaon", "Gurugram"],
            "Noida": ["Noida", "New Okhla"],
            "Kolkata": ["Kolkata", "Calcutta"],
            "Ahmedabad": ["Ahmedabad"],
        }

        # Search for city mentions (prioritized by canonical name)
        for canonical_city, synonyms in city_synonyms.items():
            for synonym in synonyms:
                if re.search(rf"\b{re.escape(synonym)}\b", text, re.IGNORECASE):
                    return canonical_city

        return "Other"

    def _extract_education(self, text: str) -> (str, str, str):
        """Extract education degree, specialization(s), and education type.
        
        Returns:
            degree: Single degree (B.Tech, B. Tech, MBA, etc.)
            specializations: Pipe-separated normalized specializations (e.g., "AI|ML" or "CSE")
            education_type: Empty string (removed as per user request)
        """
        # Degree patterns that handle both "B.Tech" and "B. Tech" formats
        degree_patterns = [
            (r"B\.[\s]?Tech", "B.Tech"),
            (r"B\.[\s]?E", "B.E"),
            (r"M\.[\s]?Tech", "M.Tech"),
            (r"M\.[\s]?Sc", "M.Sc"),
            (r"B\.[\s]?Sc", "B.Sc"),
            (r"MBA", "MBA"),
            (r"MCA", "MCA"),
            (r"PhD", "PhD"),
        ]
        
        degree = ""
        for pattern, degree_name in degree_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                degree = degree_name
                break

        # Extract raw specialization text from resume
        # Look for degree followed by specialization
        # Updated pattern to handle "B. Tech CSE 2021" format
        spec_pattern = r"(?:B\.[\s]?Tech|B\.[\s]?E|M\.[\s]?Tech|MBA|MCA|B\.[\s]?Sc|M\.[\s]?Sc|PhD)[\s\.]*(?:in\s+)?([A-Za-z\s&./\-]+?)(?:,|;|\||-|–|$|\n|[0-9])"
        spec_match = re.search(spec_pattern, text, re.IGNORECASE)
        raw_specialization = spec_match.group(1).strip() if spec_match else ""
        
        # If not found with regex, search for keywords in text
        if not raw_specialization:
            # Look for education-related sections
            edu_section = re.search(
                r"(?:education|qualifications?|academics?|degree)[\s\n]+(.*?)(?:\n\n|skills?|experience)",
                text,
                re.IGNORECASE | re.DOTALL
            )
            if edu_section:
                raw_specialization = edu_section.group(1)[:200]  # Take first 200 chars
        
        # Normalize specializations (returns list, e.g., ["AI", "ML"])
        normalized_specs = normalize_specializations(raw_specialization)
        
        # Join multiple specializations with pipe separator
        specializations_str = "|".join(normalized_specs) if normalized_specs else "Other"
        
        # Education type removed as per user request
        education_type = ""
        
        return degree, specializations_str, education_type

    def _extract_salary(self, text: str, expected: bool) -> float:
        keyword = "expected" if expected else "current"
        pattern = rf"{keyword}.*?(\d+(?:\.\d+)?)\s*(?:lpa|lakhs|lakh)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return 0.0

        general_pattern = r"(\d+(?:\.\d+)?)\s*(?:lpa|lakhs|lakh)"
        match = re.search(general_pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return 0.0

        return 0.0

    def _extract_section_block(self, text: str, headers: List[str]) -> str:
        lines = text.splitlines()
        for i, line in enumerate(lines):
            for header in headers:
                if re.search(rf"^{header}\b", line.strip(), re.IGNORECASE):
                    block = "\n".join(lines[i + 1 : i + 5])
                    return block.strip()
        return ""

    def _extract_section_items(self, text: str, headers: List[str]) -> List[str]:
        block = self._extract_section_block(text, headers)
        if not block:
            return []
        items = []
        for line in block.splitlines():
            cleaned = line.strip("•- ").strip()
            if cleaned:
                items.append(cleaned)
        return items

    def generate_analysis(self, extracted_data: Dict) -> str:
        if not self._llm_enabled:
            name = extracted_data.get("name", "Candidate")
            experience = extracted_data.get("experience_years", 0)
            return f"{name} has {experience} years of experience and is available for review."
        name = extracted_data.get("name", "Candidate")
        skills = ", ".join(extracted_data.get("skills", [])[:8])
        experience = extracted_data.get("experience_years", 0)
        company = extracted_data.get("current_company", "")
        location = extracted_data.get("current_location", "")

        prompt = (
            "Write a concise recruiter-style summary (2-3 sentences). "
            "Focus on strengths, key skills, and fit. No bullet points.\n"
            f"Name: {name}\nSkills: {skills}\nExperience: {experience} years\n"
            f"Company: {company}\nLocation: {location}\n"
        )

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False, "temperature": 0.2},
                timeout=45,
            )
        except requests.RequestException:
            self._llm_enabled = False
            return f"{name} is available for recruiter review."

        if response.status_code != 200:
            self._llm_enabled = False
            return f"{name} is available for recruiter review."

        summary = response.json().get("response", "").strip()
        return summary or f"{name} is available for recruiter review."
