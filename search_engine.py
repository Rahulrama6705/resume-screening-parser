import json
import math
import os
import re
from pathlib import Path

from extractor import extract_text
from preprocess import normalize_resume_text
from typing import List, Dict, Any, Optional

from database import Database
from models import normalize_candidate


class SearchEngine:
    def __init__(self, data_dir: str = "extracted_data", db: Optional[Database] = None):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.db = db or Database()
        self._bootstrap_from_json()
        self.extraction_version = "2026-05-06b"

    def _bootstrap_from_json(self) -> None:
        stats = self.db.get_stats()
        if stats["total_candidates"] > 0:
            return
        for json_file in self.data_dir.glob("*.json"):
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)
                file_stat = json_file.stat()
                self.db.insert_candidate(
                    data,
                    source_file=str(json_file),
                    file_mtime=file_stat.st_mtime,
                    file_size=file_stat.st_size,
                )
            except (OSError, json.JSONDecodeError):
                continue

    def sync_resumes_folder(self, folder: str, extractor) -> int:
        """Scan resume folder and process new/changed files."""
        resume_dir = Path(folder)
        if not resume_dir.exists():
            return 0

        processed = 0
        for path in resume_dir.glob("*"):
            if path.suffix.lower() not in [".pdf", ".docx", ".txt"]:
                continue

            file_stat = path.stat()
            record = self.db.get_upload_by_path(str(path))
            if record and record.get("file_mtime") == file_stat.st_mtime and record.get("file_size") == file_stat.st_size:
                candidate = self.db.get_candidate(record.get("candidate_id", ""))
                if candidate and candidate.get("skills") and record.get("extraction_version") == self.extraction_version:
                    continue

            resume_text = extract_text(str(path))
            cleaned_text = normalize_resume_text(resume_text)
            extracted = extractor.extract_fields(cleaned_text)
            if record and record.get("candidate_id"):
                extracted["candidate_id"] = record["candidate_id"]
            if not extracted.get("name"):
                extracted["name"] = path.stem.replace("_", " ").strip()
            self.save_candidate(
                extracted,
                source_file=str(path),
                filename=f"{path.stem}.json",
                file_mtime=file_stat.st_mtime,
                file_size=file_stat.st_size,
                extraction_version=self.extraction_version,
            )
            processed += 1

        return processed

    def save_candidate(
        self,
        candidate_data: Dict[str, Any],
        filename: str = None,
        source_file: str = None,
        file_mtime: float = None,
        file_size: int = None,
        extraction_version: str = None,
    ) -> str:
        """Save candidate data to JSON and SQLite."""
        candidate = normalize_candidate(candidate_data)

        if not filename:
            name = candidate.get("name", "candidate").replace(" ", "_").lower() or "candidate"
            email_part = candidate.get("email", "unknown").split("@")[0] if candidate.get("email") else "unknown"
            timestamp = candidate.get("uploaded_at", "").replace(":", "").replace("-", "")[-6:] or "000000"
            filename = f"{name}_{email_part}_{timestamp}.json"

        filepath = self.data_dir / filename
        with open(filepath, "w") as f:
            json.dump(candidate, f, indent=2)

        candidate_id = self.db.insert_candidate(
            candidate,
            source_file=source_file or str(filepath),
            file_mtime=file_mtime,
            file_size=file_size,
            extraction_version=extraction_version,
        )
        return candidate_id

    def load_all_candidates(self) -> List[Dict[str, Any]]:
        return self.db.get_all_candidates()

    def search_by_skill(self, skill: str) -> List[Dict[str, Any]]:
        return self.db.search_candidates({"skills": [skill]})

    def search_by_name(self, name: str) -> List[Dict[str, Any]]:
        return self.db.search_candidates({"name": name})

    def search_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        return self.db.get_candidate_by_email(email)

    def search_by_category(self, category: str) -> List[Dict[str, Any]]:
        return self.db.search_candidates({"education_specialization": [category]})

    def search_by_experience(self, min_years: int = 0, max_years: int = 100) -> List[Dict[str, Any]]:
        return self.db.search_candidates({"experience_min": min_years, "experience_max": max_years})

    def search_with_filters(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        debug_enabled = os.getenv("ATS_DEBUG") == "1"
        candidates = self.db.search_candidates(filters)

        if debug_enabled:
            print(f"[ATS_DEBUG] Initial candidates: {len(candidates)}")
            print(f"[ATS_DEBUG] Filters: {filters}")

        candidates = self._apply_skill_filter(candidates, filters.get("skills", []), match_all=True)
        candidates = self._apply_keyword_filter(candidates, filters.get("name", ""))

        if debug_enabled:
            print(f"[ATS_DEBUG] After skill filter: {len(candidates)}")

        if not candidates and filters.get("skills"):
            relaxed = dict(filters)
            relaxed["skills"] = []
            candidates = self.db.search_candidates(relaxed)
            candidates = self._apply_skill_filter(candidates, filters.get("skills", []), match_all=False)
            candidates = self._apply_keyword_filter(candidates, filters.get("name", ""))
            if debug_enabled:
                print(f"[ATS_DEBUG] After relaxed skill filter: {len(candidates)}")

        if not candidates:
            candidates = self._relax_filters(filters, debug_enabled)

        candidates = self._dedupe_candidates(candidates)
        return self._rank_candidates(candidates, filters)

    def get_candidate_count(self) -> int:
        return self.db.get_stats()["total_candidates"]

    def _rank_candidates(self, candidates: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        skills_query = [s.lower() for s in filters.get("skills", [])]
        query_terms = self._build_query_terms(filters)

        docs = []
        for candidate in candidates[:200]:
            resume_preview = candidate.get("resume_text", "")[:400]
            doc = " ".join(
                [
                    candidate.get("summary", ""),
                    resume_preview,
                    " ".join(candidate.get("skills", [])),
                ]
            )
            docs.append(doc)

        tfidf_scores = self._tfidf_rank(query_terms, docs)

        ranked = []
        for idx, candidate in enumerate(candidates[:200]):
            overlap = self._skill_overlap(skills_query, candidate.get("skills", []))
            tfidf_score = tfidf_scores[idx] if idx < len(tfidf_scores) else 0.0
            match_score = round((0.7 * tfidf_score + 0.3 * overlap) * 100, 2)
            candidate["match_score"] = match_score
            ranked.append(candidate)

        ranked.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        ranked.extend(candidates[200:])
        return ranked

    def _build_query_terms(self, filters: Dict[str, Any]) -> str:
        terms = []
        for key in ["name", "current_company", "current_location"]:
            if filters.get(key):
                terms.append(filters[key])
        for key in ["education_degree", "education_specialization", "education_type"]:
            if filters.get(key):
                terms.extend(filters[key])
        terms.extend(filters.get("skills", []))
        return " ".join([t for t in terms if t])

    def _skill_overlap(self, skills_query: List[str], candidate_skills: List[str]) -> float:
        if not skills_query:
            return 0.0
        cand_text = " ".join(candidate_skills).lower()
        matched = sum(1 for s in skills_query if s.lower() in cand_text)
        return matched / len(skills_query)

    def _tfidf_rank(self, query: str, docs: List[str]) -> List[float]:
        if not query or not docs:
            return [0.0] * len(docs)

        tokenized_docs = [self._tokenize(doc) for doc in docs]
        tokenized_query = self._tokenize(query)
        if not tokenized_query:
            return [0.0] * len(docs)

        df = {}
        for tokens in tokenized_docs:
            unique = set(tokens)
            for token in unique:
                df[token] = df.get(token, 0) + 1

        idf = {t: math.log((len(docs) + 1) / (df_t + 1)) + 1 for t, df_t in df.items()}

        query_vec = self._tfidf_vector(tokenized_query, idf)
        query_norm = self._vector_norm(query_vec)
        if query_norm == 0:
            return [0.0] * len(docs)

        scores = []
        for tokens in tokenized_docs:
            doc_vec = self._tfidf_vector(tokens, idf)
            score = self._cosine_similarity(query_vec, query_norm, doc_vec)
            scores.append(score)
        return scores

    def _tfidf_vector(self, tokens: List[str], idf: Dict[str, float]) -> Dict[str, float]:
        tf = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1
        total = len(tokens) or 1
        return {t: (count / total) * idf.get(t, 0.0) for t, count in tf.items()}

    def _vector_norm(self, vec: Dict[str, float]) -> float:
        return math.sqrt(sum(v * v for v in vec.values()))

    def _cosine_similarity(self, q_vec: Dict[str, float], q_norm: float, d_vec: Dict[str, float]) -> float:
        if not d_vec:
            return 0.0
        dot = 0.0
        for token, q_val in q_vec.items():
            dot += q_val * d_vec.get(token, 0.0)
        d_norm = self._vector_norm(d_vec)
        return dot / (q_norm * d_norm) if d_norm else 0.0

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[a-zA-Z0-9\+\.#]+", text.lower())

    def _apply_skill_filter(
        self,
        candidates: List[Dict[str, Any]],
        skills: List[str],
        match_all: bool = True,
    ) -> List[Dict[str, Any]]:
        if not skills:
            return candidates

        normalized = [s.strip().lower() for s in skills if s.strip()]
        if not normalized:
            return candidates

        synonyms = {
            "ai/ml": ["ai", "ml", "machine learning", "artificial intelligence"],
            "ml": ["machine learning", "ml"],
            "ai": ["artificial intelligence", "ai"],
        }

        filtered = []
        for candidate in candidates:
            skill_text = " ".join(candidate.get("skills", [])).lower()
            resume_text = (candidate.get("resume_text", "") or "")[:800].lower()
            combined = f"{skill_text} {resume_text}".strip()
            if not combined:
                continue

            matched_terms = 0
            for term in normalized:
                variants = synonyms.get(term, [term])
                if any(variant in combined for variant in variants):
                    matched_terms += 1
                elif match_all:
                    matched_terms = -1
                    break

            if match_all and matched_terms == len(normalized):
                filtered.append(candidate)
            elif not match_all and matched_terms > 0:
                filtered.append(candidate)
        return filtered

    def _relax_filters(self, filters: Dict[str, Any], debug_enabled: bool) -> List[Dict[str, Any]]:
        relax_steps = [
            ("current_salary_min", None),
            ("current_salary_max", None),
            ("expected_salary_min", None),
            ("expected_salary_max", None),
            ("education_type", []),
            # NOTE: DO NOT relax education_specialization - user explicitly selected it
            # ("education_specialization", []),  # REMOVED
            # NOTE: DO NOT relax education_degree - user explicitly selected it
            # ("education_degree", []),  # REMOVED
            ("current_company", ""),
            ("name", ""),
            # NOTE: current_location is NOT relaxed - strict location matching required
        ]

        relaxed = dict(filters)
        for field, reset_value in relax_steps:
            relaxed[field] = reset_value
            candidates = self.db.search_candidates(relaxed)
            candidates = self._apply_skill_filter(candidates, relaxed.get("skills", []), match_all=False)
            candidates = self._apply_keyword_filter(candidates, relaxed.get("name", ""))
            if candidates:
                if debug_enabled:
                    print(f"[ATS_DEBUG] Relaxed {field} -> results: {len(candidates)}")
                return candidates

        # If still no results, return empty (don't fall back to ALL candidates)
        return []

    def _dedupe_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        unique = []
        for candidate in candidates:
            email = (candidate.get("email") or "").strip().lower()
            phone = (candidate.get("phone") or "").strip()
            name = (candidate.get("name") or "").strip().lower()
            resume_key = (candidate.get("resume_text") or "")[:200].strip().lower()
            key = email or f"{name}|{phone}" or resume_key or candidate.get("candidate_id")
            if key in seen:
                continue
            seen.add(key)
            unique.append(candidate)
        return unique

    def _apply_keyword_filter(self, candidates: List[Dict[str, Any]], keyword: str) -> List[Dict[str, Any]]:
        if not keyword:
            return candidates
        term = keyword.lower().strip()
        if not term:
            return candidates

        filtered = []
        for candidate in candidates:
            haystack = " ".join(
                [
                    candidate.get("name", ""),
                    candidate.get("summary", ""),
                    candidate.get("current_company", ""),
                    candidate.get("education_degree", ""),
                    candidate.get("education_specialization", ""),
                    " ".join(candidate.get("skills", [])),
                    (candidate.get("resume_text") or "")[:600],
                ]
            ).lower()
            if term in haystack:
                filtered.append(candidate)

        return filtered if filtered else candidates
