from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any
import uuid


REQUIRED_FIELDS = [
    "candidate_id",
    "name",
    "email",
    "phone",
    "skills",
    "experience_years",
    "current_company",
    "current_location",
    "education_degree",
    "education_specialization",
    "education_type",
    "current_salary",
    "expected_salary",
    "projects",
    "certifications",
    "summary",
    "resume_text",
    "uploaded_at",
]


@dataclass
class Candidate:
    candidate_id: str
    name: str = ""
    email: str = ""
    phone: str = ""
    skills: List[str] = field(default_factory=list)
    experience_years: float = 0.0
    current_company: str = ""
    current_location: str = ""
    education_degree: str = ""
    education_specialization: str = ""
    education_type: str = ""
    current_salary: float = 0.0
    expected_salary: float = 0.0
    projects: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    summary: str = ""
    resume_text: str = ""
    uploaded_at: str = ""

    @staticmethod
    def new_id() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def now_iso() -> str:
        return datetime.utcnow().isoformat()


def normalize_candidate(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure candidate dict has all required fields with proper types."""
    normalized = {k: data.get(k, "") for k in REQUIRED_FIELDS}

    if not normalized["candidate_id"]:
        normalized["candidate_id"] = Candidate.new_id()
    if not normalized["uploaded_at"]:
        normalized["uploaded_at"] = Candidate.now_iso()

    # Normalize list fields
    for list_field in ["skills", "projects", "certifications"]:
        value = normalized.get(list_field, [])
        if isinstance(value, str):
            value = [v.strip() for v in value.split(",") if v.strip()]
        elif not isinstance(value, list):
            value = []

        cleaned = []
        for item in value:
            if isinstance(item, str):
                cleaned.append(item.strip())
            elif isinstance(item, dict) and item.get("name"):
                cleaned.append(str(item["name"]).strip())
            elif item is not None:
                cleaned.append(str(item).strip())
        normalized[list_field] = [v for v in cleaned if v]

    # Normalize numeric fields
    for num_field in ["experience_years", "current_salary", "expected_salary"]:
        value = normalized.get(num_field, 0)
        try:
            normalized[num_field] = float(value) if value not in ["", None] else 0.0
        except (ValueError, TypeError):
            normalized[num_field] = 0.0

    # Ensure string fields
    for str_field in [
        "name",
        "email",
        "phone",
        "current_company",
        "current_location",
        "education_degree",
        "education_specialization",
        "education_type",
        "summary",
        "resume_text",
    ]:
        value = normalized.get(str_field, "")
        normalized[str_field] = value if isinstance(value, str) else str(value)

    if not normalized["current_company"]:
        normalized["current_company"] = "Other"
    if not normalized["current_location"]:
        normalized["current_location"] = "Other"

    return normalized
