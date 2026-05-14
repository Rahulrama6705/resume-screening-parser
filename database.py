import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from models import normalize_candidate


DB_PATH = Path("candidates.db")

# City synonyms mapping
CITY_SYNONYMS = {
    "Bangalore": ["Bangalore", "Bengaluru", "Blr"],
    "Hyderabad": ["Hyderabad", "Hyd", "Secunderabad"],
    "Chennai": ["Chennai", "Madras"],
    "Mumbai": ["Mumbai", "Bombay"],
    "Pune": ["Pune", "Poona"],
    "Delhi": ["Delhi", "New Delhi"],
    "Gurgaon": ["Gurgaon", "Gurugram"],
    "Noida": ["Noida", "New Okhla"],
    "Kolkata": ["Kolkata", "Calcutta"],
    "Ahmedabad": ["Ahmedabad"],
}

def get_canonical_city(user_input: str) -> str:
    """Convert user input (Bangalore/Bengaluru) to canonical city name."""
    user_input = user_input.strip().lower()
    for canonical, synonyms in CITY_SYNONYMS.items():
        if any(user_input == syn.lower() for syn in synonyms):
            return canonical
    return user_input  # Return as-is if not in synonyms


def specialization_matches(db_specialization: str, filter_specialization: str) -> bool:
    """Check if database specialization matches filter specialization.
    
    Database specializations are pipe-separated (e.g., "AI|ML", "CSE")
    Filter specialization is a single code (e.g., "AI", "CSE")
    
    Returns True if filter matches any specialization in db_specialization.
    """
    if not db_specialization or not filter_specialization:
        return False
    
    # Split pipe-separated values from database
    db_specs = [s.strip() for s in db_specialization.split("|")]
    
    # Check if filter matches any specialization
    return filter_specialization.strip() in db_specs


class Database:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = Path(db_path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS candidates (
                    candidate_id TEXT PRIMARY KEY,
                    name TEXT,
                    email TEXT,
                    phone TEXT,
                    skills_json TEXT,
                    experience_years REAL,
                    current_company TEXT,
                    current_location TEXT,
                    education_degree TEXT,
                    education_specialization TEXT,
                    education_type TEXT,
                    current_salary REAL,
                    expected_salary REAL,
                    projects_json TEXT,
                    certifications_json TEXT,
                    summary TEXT,
                    resume_text TEXT,
                    uploaded_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS skills (
                    candidate_id TEXT,
                    skill TEXT,
                    PRIMARY KEY (candidate_id, skill)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS uploads (
                    upload_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_id TEXT,
                    filename TEXT,
                    file_path TEXT,
                    uploaded_at TEXT
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_skill ON skills(skill)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_name ON candidates(name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_company ON candidates(current_company)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_location ON candidates(current_location)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_experience ON candidates(experience_years)")
            self._ensure_upload_columns(conn)

    def _ensure_upload_columns(self, conn: sqlite3.Connection) -> None:
        columns = conn.execute("PRAGMA table_info(uploads)").fetchall()
        existing = {col["name"] for col in columns}
        if "file_mtime" not in existing:
            conn.execute("ALTER TABLE uploads ADD COLUMN file_mtime REAL")
        if "file_size" not in existing:
            conn.execute("ALTER TABLE uploads ADD COLUMN file_size INTEGER")
        if "extraction_version" not in existing:
            conn.execute("ALTER TABLE uploads ADD COLUMN extraction_version TEXT")

    def insert_candidate(
        self,
        data: Dict[str, Any],
        source_file: Optional[str] = None,
        file_mtime: Optional[float] = None,
        file_size: Optional[int] = None,
        extraction_version: Optional[str] = None,
    ) -> str:
        candidate = normalize_candidate(data)
        candidate_id = candidate["candidate_id"]

        with self._connect() as conn:
            # Check if candidate already exists (by name+email or email)
            # Skip if name is empty or contains common section headers
            name = candidate.get("name", "").strip()
            email = candidate.get("email", "").strip()
            
            # Skip extraction errors (these indicate bad name extraction)
            skip_names = {"", "Career Objective", "Technical Skills", "RESUME", "Experience"}
            if name.lower() in skip_names:
                # Skip saving this record - bad extraction
                return ""
            
            # Check for duplicate by email (email is unique identifier)
            if email:
                existing = conn.execute(
                    "SELECT candidate_id FROM candidates WHERE email = ?",
                    (email,)
                ).fetchone()
                if existing:
                    # Update existing instead of creating new
                    candidate_id = existing[0]
            
            # If still no email match, check by name+email combination
            elif name:
                existing = conn.execute(
                    "SELECT candidate_id FROM candidates WHERE name = ? AND phone = ?",
                    (name, candidate.get("phone", ""))
                ).fetchone()
                if existing:
                    candidate_id = existing[0]
            
            conn.execute(
                """
                INSERT OR REPLACE INTO candidates (
                    candidate_id, name, email, phone, skills_json, experience_years,
                    current_company, current_location, education_degree, education_specialization,
                    education_type, current_salary, expected_salary, projects_json,
                    certifications_json, summary, resume_text, uploaded_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    candidate_id,
                    candidate["name"],
                    candidate["email"],
                    candidate["phone"],
                    json.dumps(candidate["skills"]),
                    candidate["experience_years"],
                    candidate["current_company"],
                    candidate["current_location"],
                    candidate["education_degree"],
                    candidate["education_specialization"],
                    candidate["education_type"],
                    candidate["current_salary"],
                    candidate["expected_salary"],
                    json.dumps(candidate["projects"]),
                    json.dumps(candidate["certifications"]),
                    candidate["summary"],
                    candidate["resume_text"],
                    candidate["uploaded_at"],
                ),
            )

            conn.execute("DELETE FROM skills WHERE candidate_id = ?", (candidate_id,))
            for skill in candidate["skills"]:
                skill_val = skill.strip().lower()
                if skill_val:
                    conn.execute(
                        "INSERT OR IGNORE INTO skills (candidate_id, skill) VALUES (?, ?)",
                        (candidate_id, skill_val),
                    )

            if source_file:
                file_path = str(source_file)
                filename = Path(file_path).name
                conn.execute(
                    """
                    INSERT INTO uploads (candidate_id, filename, file_path, uploaded_at, file_mtime, file_size, extraction_version)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (candidate_id, filename, file_path, candidate["uploaded_at"], file_mtime, file_size, extraction_version),
                )

        return candidate_id

    def get_candidate(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM candidates WHERE candidate_id = ?", (candidate_id,)
            ).fetchone()
        return self._row_to_candidate(row) if row else None

    def get_candidate_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM candidates WHERE lower(email) = lower(?)", (email,)
            ).fetchone()
        return self._row_to_candidate(row) if row else None

    def get_all_candidates(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM candidates ORDER BY uploaded_at DESC").fetchall()
        return [self._row_to_candidate(row) for row in rows]

    def search_candidates(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        skill_filters = [s.strip().lower() for s in filters.get("skills", []) if s.strip()]
        candidate_ids = None

        if skill_filters:
            skill_matches = set()
            with self._connect() as conn:
                for skill in skill_filters:
                    rows = conn.execute(
                        "SELECT DISTINCT candidate_id FROM skills WHERE lower(skill) LIKE lower(?)",
                        (f"%{skill}%",),
                    ).fetchall()
                    skill_matches.update(row["candidate_id"] for row in rows)
            candidate_ids = list(skill_matches)
            if not candidate_ids:
                return []

        query = "SELECT * FROM candidates WHERE 1=1"
        params: List[Any] = []

        if candidate_ids is not None:
            query += f" AND candidate_id IN ({','.join(['?'] * len(candidate_ids))})"
            params.extend(candidate_ids)

        # name keyword handled in SearchEngine for flexible matching

        if filters.get("current_company"):
            if filters["current_company"].lower() == "other":
                query += " AND (current_company IS NULL OR current_company = '' OR current_company = 'Other')"
            else:
                query += " AND lower(current_company) LIKE lower(?)"
                params.append(f"%{filters['current_company']}%")

        if filters.get("current_location"):
            if filters["current_location"].lower() == "other":
                query += " AND (current_location IS NULL OR current_location = '' OR current_location = 'Other')"
            else:
                # Use exact match for location (not fuzzy)
                canonical_city = get_canonical_city(filters["current_location"])
                query += " AND current_location = ?"
                params.append(canonical_city)

        for field in ["education_degree"]:
            values = filters.get(field, [])
            if values:
                like_clauses = " OR ".join([f"lower({field}) = lower(?)" for _ in values])
                query += f" AND ({like_clauses})"
                params.extend(values)
        
        # Handle education_specialization with exact matching
        # Specializations are stored as pipe-separated (e.g., "AI|ML", "CSE")
        spec_values = filters.get("education_specialization", [])
        if spec_values:
            # Create a condition: (spec1 found OR spec2 found OR ...)
            # Use INSTR to find exact specialization in pipe-separated list
            spec_conditions = []
            for spec in spec_values:
                # Match exact specialization in pipe-separated list
                # Match patterns: "CSE", "CSE|", "|CSE", "|CSE|"
                spec_conditions.append(f"(education_specialization = ? OR education_specialization LIKE ? OR education_specialization LIKE ? OR education_specialization LIKE ?)")
                params.extend([spec, f"{spec}|%", f"%|{spec}", f"%|{spec}|%"])
            
            spec_clause = " OR ".join(spec_conditions)
            query += f" AND ({spec_clause})"

        exp_min, exp_max = filters.get("experience_min"), filters.get("experience_max")
        if exp_min is not None:
            query += " AND experience_years >= ?"
            params.append(exp_min)
        if exp_max is not None:
            query += " AND experience_years <= ?"
            params.append(exp_max)

        salary_min, salary_max = filters.get("current_salary_min"), filters.get("current_salary_max")
        if salary_min is not None and salary_max is not None:
            query += " AND current_salary > 0 AND current_salary BETWEEN ? AND ?"
            params.extend([salary_min, salary_max])

        exp_salary_min, exp_salary_max = filters.get("expected_salary_min"), filters.get(
            "expected_salary_max"
        )
        if exp_salary_min is not None and exp_salary_max is not None:
            query += " AND expected_salary > 0 AND expected_salary BETWEEN ? AND ?"
            params.extend([exp_salary_min, exp_salary_max])

        query += " ORDER BY uploaded_at DESC"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        return [self._row_to_candidate(row) for row in rows]

    def get_top_skills(self, limit: int = 15) -> List[Tuple[str, int]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT skill, COUNT(*) AS count
                FROM skills
                GROUP BY skill
                ORDER BY count DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [(row["skill"], row["count"]) for row in rows]

    def get_recent_uploads(self, limit: int = 5) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT uploads.filename, uploads.uploaded_at, candidates.name
                FROM uploads
                LEFT JOIN candidates ON candidates.candidate_id = uploads.candidate_id
                ORDER BY uploads.uploaded_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {"filename": row["filename"], "uploaded_at": row["uploaded_at"], "name": row["name"]}
            for row in rows
        ]

    def get_upload_by_path(self, file_path: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM uploads WHERE file_path = ? ORDER BY uploaded_at DESC LIMIT 1",
                (file_path,),
            ).fetchone()
        return dict(row) if row else None

    def get_distinct_values(self, field: str, limit: int = 100) -> List[str]:
        allowed = {
            "current_location",
            "current_company",
            "education_degree",
            "education_specialization",
            "education_type",
        }
        if field not in allowed:
            return []
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT DISTINCT {field}
                FROM candidates
                WHERE {field} IS NOT NULL AND {field} != ''
                ORDER BY {field}
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [row[field] for row in rows if row[field]]

    def get_stats(self) -> Dict[str, Any]:
        with self._connect() as conn:
            total_candidates = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
            total_uploads = conn.execute("SELECT COUNT(*) FROM uploads").fetchone()[0]
            avg_experience = conn.execute(
                "SELECT AVG(experience_years) FROM candidates WHERE experience_years > 0"
            ).fetchone()[0]

            rows = conn.execute(
                """
                SELECT name, email, phone, skills_json, experience_years, education_degree,
                       current_company, current_location
                FROM candidates
                """
            ).fetchall()

        filled = 0
        total = 0
        for row in rows:
            fields = [
                row["name"],
                row["email"],
                row["phone"],
                row["skills_json"],
                row["experience_years"],
                row["education_degree"],
                row["current_company"],
                row["current_location"],
            ]
            total += len(fields)
            for value in fields:
                if value not in [None, "", "[]", 0]:
                    filled += 1

        accuracy = (filled / total) * 100 if total else 0.0

        return {
            "total_candidates": total_candidates,
            "total_uploads": total_uploads,
            "avg_experience": round(avg_experience or 0.0, 2),
            "extraction_accuracy": round(accuracy, 2),
        }

    def _row_to_candidate(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "candidate_id": row["candidate_id"],
            "name": row["name"] or "",
            "email": row["email"] or "",
            "phone": row["phone"] or "",
            "skills": json.loads(row["skills_json"] or "[]"),
            "experience_years": row["experience_years"] or 0.0,
            "current_company": row["current_company"] or "",
            "current_location": row["current_location"] or "",
            "education_degree": row["education_degree"] or "",
            "education_specialization": row["education_specialization"] or "",
            "education_type": row["education_type"] or "",
            "current_salary": row["current_salary"] or 0.0,
            "expected_salary": row["expected_salary"] or 0.0,
            "projects": json.loads(row["projects_json"] or "[]"),
            "certifications": json.loads(row["certifications_json"] or "[]"),
            "summary": row["summary"] or "",
            "resume_text": row["resume_text"] or "",
            "uploaded_at": row["uploaded_at"] or "",
        }
