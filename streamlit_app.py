import json
from pathlib import Path
from typing import List, Dict, Any

import streamlit as st

from extractor import extract_text
from preprocess import normalize_resume_text
from llm_extractor import OllamaExtractor
from search_engine import SearchEngine
from database import CITY_SYNONYMS


st.set_page_config(page_title="Recruiter ATS Dashboard", layout="wide", initial_sidebar_state="expanded")

extractor = OllamaExtractor()
search_engine = SearchEngine()

SKILLS_PATH = Path("skills_master.json")

# Get canonical city names for dropdown (not synonyms)
CANONICAL_CITIES = sorted(list(CITY_SYNONYMS.keys())) + ["Other"]

SKILLS_PATH = Path("skills_master.json")


def load_skills_master() -> List[str]:
    if not SKILLS_PATH.exists():
        return []
    try:
        data = json.loads(SKILLS_PATH.read_text())
        skills = data.get("skills", [])
        return sorted({s.strip() for s in skills if isinstance(s, str) and s.strip()})
    except (json.JSONDecodeError, OSError):
        return []


def format_lpa(value: float) -> str:
    return f"₹ {value:.1f} LPA" if value and value > 0 else "N/A"


def skill_tags(skills: List[str]) -> str:
    tags = []
    for skill in skills[:12]:
        tags.append(f"<span class='skill-tag'>{skill}</span>")
    return " ".join(tags) if tags else "<span class='badge'>No skills listed</span>"


def parse_resume_sections(resume_text: str) -> Dict[str, List[str]]:
    """Parse resume text into categorical sections."""
    sections = {
        "Contact Information": [],
        "Career Objective": [],
        "Education": [],
        "Experience": [],
        "Skills": [],
        "Certifications": [],
        "Projects": [],
        "Other": []
    }
    
    if not resume_text:
        return sections
    
    lines = resume_text.split('\n')
    current_section = "Other"
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Detect section headers
        upper_line = line.upper()
        if any(keyword in upper_line for keyword in ["EMAIL", "PHONE", "CONTACT"]):
            current_section = "Contact Information"
        elif any(keyword in upper_line for keyword in ["OBJECTIVE", "SUMMARY", "PROFILE"]):
            current_section = "Career Objective"
        elif any(keyword in upper_line for keyword in ["EDUCATION", "ACADEMIC", "QUALIFICATION"]):
            current_section = "Education"
        elif any(keyword in upper_line for keyword in ["EXPERIENCE", "EMPLOYMENT", "INTERNSHIP", "WORK"]):
            current_section = "Experience"
        elif any(keyword in upper_line for keyword in ["SKILL", "TECHNICAL", "PROFICIENCY"]):
            current_section = "Skills"
        elif any(keyword in upper_line for keyword in ["CERTIFICATION", "AWARD", "ACHIEVEMENT"]):
            current_section = "Certifications"
        elif any(keyword in upper_line for keyword in ["PROJECT"]):
            current_section = "Projects"
        
        # Add line to current section if not a header
        if not any(keyword in upper_line for keyword in ["CONTACT", "EMAIL", "PHONE", "OBJECTIVE", "SUMMARY", 
                                                          "PROFILE", "EDUCATION", "ACADEMIC", "QUALIFICATION",
                                                          "EXPERIENCE", "EMPLOYMENT", "INTERNSHIP", "WORK",
                                                          "SKILL", "TECHNICAL", "PROFICIENCY", "CERTIFICATION", 
                                                          "AWARD", "ACHIEVEMENT", "PROJECT"]):
            if line and current_section in sections:
                sections[current_section].append(line)
    
    return sections


def render_candidate_card(candidate: Dict[str, Any]) -> None:
    name = candidate.get("name", "Unknown")
    experience = candidate.get("experience_years", 0)
    current_company = candidate.get("current_company") or "Other"
    location = candidate.get("current_location") or "Other"
    degree = candidate.get("education_degree", "")
    specialization = candidate.get("education_specialization", "")
    education = " | ".join([p for p in [degree, specialization] if p]) or "N/A"
    summary = candidate.get("summary", "")
    match_score = candidate.get("match_score", 0)

    st.markdown(
        f"""
        <div class='candidate-card'>
            <div class='card-header'>
                <div>
                    <div class='card-title'>{name}</div>
                    <div class='meta-row'>
                        <span>💼 {experience} yrs</span>
                        <span>💰 {format_lpa(candidate.get("current_salary", 0))}</span>
                        <span>📍 {location}</span>
                    </div>
                </div>
                <div class='match-badge'>Match {match_score}%</div>
            </div>
            <div style='display:flex; gap:24px; margin-top:12px;'>
                <div style='flex:3;'>
                    <div class='info-row'>
                        <span class='info-label'>Current</span>
                        <span class='info-value'>{current_company}</span>
                    </div>
                    <div class='info-row'>
                        <span class='info-label'>Education</span>
                        <span class='info-value'>{education}</span>
                    </div>
                    <div class='info-row'>
                        <span class='info-label'>Preferred location</span>
                        <span class='info-value'>{location}</span>
                    </div>
                    <div class='info-row'>
                        <span class='info-label'>Key skills</span>
                        <span class='info-value'>{skill_tags(candidate.get("skills", []))}</span>
                    </div>
                </div>
                <div class='side-card' style='flex:1;'>
                    <div class='info-row'>
                        <span class='info-label'>Email</span>
                        <span class='info-value'>{candidate.get("email", "N/A")}</span>
                    </div>
                    <div class='info-row'>
                        <span class='info-label'>Phone</span>
                        <span class='info-value'>{candidate.get("phone", "N/A")}</span>
                    </div>
                    <div class='info-row'>
                        <span class='info-label'>Expected</span>
                        <span class='info-value'>{format_lpa(candidate.get("expected_salary", 0))}</span>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if summary:
        st.caption(summary)

    action_col1, action_col2, action_col3 = st.columns([1, 1, 2])
    with action_col1:
        st.button("View phone number", key=f"phone_{candidate.get('candidate_id')}")
    with action_col2:
        st.button("Call candidate", key=f"call_{candidate.get('candidate_id')}")
    with action_col3:
        st.write("")

    with st.expander("Resume Preview"):
        resume_text = candidate.get("resume_text", "")
        preview = resume_text[:1200] + ("..." if len(resume_text) > 1200 else "")
        st.text(preview or "No resume text available")


st.markdown(
    """
    <style>
    .candidate-card {
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 18px;
        background: #ffffff;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    .card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
    }
    .card-title {
        font-size: 20px;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .meta-row {
        display: flex;
        gap: 16px;
        color: #6b7280;
        font-size: 13px;
    }
    .match-badge {
        background: #e0f2fe;
        color: #075985;
        padding: 6px 12px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
    }
    .info-row {
        display: grid;
        grid-template-columns: 150px 1fr;
        gap: 10px;
        margin: 6px 0;
    }
    .info-label {
        color: #6b7280;
        font-size: 12px;
    }
    .info-value {
        color: #111827;
        font-size: 13px;
    }
    .skill-tag {
        display: inline-block;
        background: #eef2ff;
        color: #3730a3;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        margin: 2px 4px 2px 0;
    }
    .badge {
        display: inline-block;
        background: #ecfeff;
        color: #155e75;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
    }
    .side-card {
        border-left: 1px solid #f1f5f9;
        padding-left: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


st.title("Enterprise AI-Powered Recruiter ATS Dashboard")
st.caption("Local LLM • Structured Search • Recruiter-Style Candidate Management")

if "synced_resumes" not in st.session_state:
    search_engine.sync_resumes_folder("Unical Resumes", extractor)
    st.session_state["synced_resumes"] = True

stats = search_engine.db.get_stats()
top_skills = search_engine.db.get_top_skills(limit=15)

st.subheader("Recruiter Search & Filters")

skills_master = load_skills_master()
degree_options = ["B.Tech", "B.E", "M.Tech", "MBA", "MCA", "B.Sc", "M.Sc", "PhD"]
specialization_options = [
    "CSE",  # Computer Science
    "IT",  # Information Technology
    "AI",  # Artificial Intelligence (separated from ML)
    "ML",  # Machine Learning (separated from AI)
    "Data Science",
    "ECE",  # Electronics and Communication Engineering
    "EEE",  # Electrical and Electronics Engineering
    "Mechanical",
    "Civil",
    "Electronics",
    "Cybersecurity",
    "Other",
]

default_cities = [
    "Hyderabad",
    "Bangalore",
    "Chennai",
    "Mumbai",
    "Pune",
    "Delhi",
    "Gurgaon",
    "Noida",
    "Kolkata",
    "Ahmedabad",
    "Other",
]
locations = sorted(set(default_cities + search_engine.db.get_distinct_values("current_location")))
companies = sorted(set(search_engine.db.get_distinct_values("current_company") + ["Other"]))

with st.form("filters_form"):
    row1 = st.columns(3)
    with row1[0]:
        name_query = st.text_input("Candidate Name")
    with row1[1]:
        selected_skills = st.multiselect("Skills", skills_master)
    with row1[2]:
        min_exp = st.number_input("Experience Min (Years)", min_value=0, max_value=50, value=0, step=1)
        max_exp = st.number_input("Experience Max (Years)", min_value=0, max_value=50, value=50, step=1)

    row2 = st.columns(2)
    with row2[0]:
        degrees = st.multiselect("Education Degree", degree_options)
    with row2[1]:
        specializations = st.multiselect("Education Specialization", specialization_options)

    row3 = st.columns(2)
    with row3[0]:
        location = st.selectbox("Current Location", [""] + CANONICAL_CITIES)
    with row3[1]:
        current_company = st.selectbox("Current Company", [""] + companies)

    row4 = st.columns(2)
    with row4[0]:
        curr_salary_min = st.number_input("Current Salary Min (LPA)", min_value=0, max_value=100, value=0, step=1)
        curr_salary_max = st.number_input("Current Salary Max (LPA)", min_value=0, max_value=100, value=0, step=1)
    with row4[1]:
        exp_salary_min = st.number_input("Expected Salary Min (LPA)", min_value=0, max_value=100, value=0, step=1)
        exp_salary_max = st.number_input("Expected Salary Max (LPA)", min_value=0, max_value=100, value=0, step=1)

    apply_filters = st.form_submit_button("Apply Filters")

exp_min = min_exp if min_exp != 0 else None
exp_max = max_exp if max_exp != 50 else None

if curr_salary_min <= 0 and curr_salary_max <= 0:
    curr_salary_min, curr_salary_max = (None, None)
elif curr_salary_max and curr_salary_min > curr_salary_max:
    curr_salary_min, curr_salary_max = (curr_salary_max, curr_salary_min)

if exp_salary_min <= 0 and exp_salary_max <= 0:
    exp_salary_min, exp_salary_max = (None, None)
elif exp_salary_max and exp_salary_min > exp_salary_max:
    exp_salary_min, exp_salary_max = (exp_salary_max, exp_salary_min)

filters = {
    "skills": selected_skills,
    "experience_min": exp_min,
    "experience_max": exp_max,
    "education_degree": degrees,
    "education_specialization": specializations,
    "education_type": [],
    "current_location": location,
    "current_company": current_company,
    "current_salary_min": curr_salary_min,
    "current_salary_max": curr_salary_max,
    "expected_salary_min": exp_salary_min,
    "expected_salary_max": exp_salary_max,
    "name": name_query,
}

if "active_filters" not in st.session_state:
    st.session_state["active_filters"] = filters

if apply_filters:
    st.session_state["active_filters"] = filters

results = search_engine.search_with_filters(st.session_state["active_filters"])

col1, col2 = st.columns(2)
with col1:
    st.metric("Total Candidates", stats["total_candidates"])
with col2:
    st.metric("Total Uploads", stats["total_uploads"])

st.subheader("Top Skills")
if top_skills:
    st.markdown(skill_tags([s for s, _ in top_skills]), unsafe_allow_html=True)
else:
    st.info("No skill data available yet.")

st.write(f"Found **{len(results)}** candidates")
for candidate in results[:50]:
    render_candidate_card(candidate)

if len(results) > 50:
    st.info("Showing top 50 results. Refine filters for more precision.")


st.divider()
st.subheader("Upload & Process Resume")

upload_col, preview_col = st.columns([2, 1])
with upload_col:
    uploaded_file = st.file_uploader("Upload Resume (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])
    generate_summary = st.checkbox("Generate AI Summary (optional)", value=False)

if uploaded_file:
    resumes_dir = Path("Unical Resumes")
    resumes_dir.mkdir(exist_ok=True)
    file_path = resumes_dir / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    with st.spinner("Extracting text..."):
        resume_text = extract_text(str(file_path))
        cleaned_text = normalize_resume_text(resume_text)

    with st.spinner("Extracting structured fields..."):
        extracted_data = extractor.extract_fields(cleaned_text)

    if generate_summary:
        with st.spinner("Generating AI summary..."):
            if not extracted_data.get("summary"):
                extracted_data["summary"] = extractor.generate_analysis(extracted_data)

    candidate_id = search_engine.save_candidate(
        extracted_data,
        source_file=str(file_path),
        file_mtime=file_path.stat().st_mtime,
        file_size=file_path.stat().st_size,
        extraction_version=search_engine.extraction_version,
    )

    st.success(f"Candidate stored in database: {candidate_id}")

    with preview_col:
        st.markdown("**Extracted Preview**")
        # Create a neat table for extracted data
        preview_data = {
            "Field": [
                "Name",
                "Email",
                "Phone",
                "Experience",
                "Current Company",
                "Location",
                "Education",
                "Current Salary",
                "Expected Salary",
            ],
            "Value": [
                extracted_data.get("name", "N/A"),
                extracted_data.get("email", "N/A"),
                extracted_data.get("phone", "N/A"),
                f"{extracted_data.get('experience_years', 0)} yrs",
                extracted_data.get("current_company", "Other") or "Other",
                extracted_data.get("current_location", "Other") or "Other",
                " | ".join([p for p in [
                    extracted_data.get("education_degree", ""),
                    extracted_data.get("education_specialization", "")
                ] if p]) or "N/A",
                format_lpa(extracted_data.get("current_salary", 0)),
                format_lpa(extracted_data.get("expected_salary", 0)),
            ]
        }
        import pandas as pd
        preview_df = pd.DataFrame(preview_data)
        st.dataframe(preview_df, use_container_width=True, hide_index=True)

    with st.expander("View Full Details"):
        st.subheader("Skills")
        skills = extracted_data.get("skills", [])
        if skills:
            st.write(", ".join(skills))
        else:
            st.write("No skills found")
        
        st.subheader("Certifications")
        certs = extracted_data.get("certifications", [])
        if certs:
            st.write(", ".join(certs))
        else:
            st.write("No certifications found")
        
        st.subheader("Projects")
        projects = extracted_data.get("projects", [])
        if projects:
            for project in projects:
                st.write(f"• {project}")
        else:
            st.write("No projects found")
        
        if extracted_data.get("summary"):
            st.subheader("AI Analysis")
            st.write(extracted_data.get("summary"))
        
        st.subheader("Resume Content")
        resume_text = extracted_data.get("resume_text") or ""
        if resume_text:
            # Parse resume into sections
            sections = parse_resume_sections(resume_text)
            
            for section_name, section_lines in sections.items():
                if section_lines:
                    with st.expander(f"📄 {section_name}", expanded=(section_name in ["Contact Information", "Skills", "Education"])):
                        # Create a table for display
                        if section_name == "Contact Information":
                            contact_data = []
                            for line in section_lines:
                                if "email" in line.lower():
                                    contact_data.append({"Type": "Email", "Details": line})
                                elif "phone" in line.lower():
                                    contact_data.append({"Type": "Phone", "Details": line})
                                else:
                                    contact_data.append({"Type": "Other", "Details": line})
                            if contact_data:
                                import pandas as pd
                                st.dataframe(pd.DataFrame(contact_data), use_container_width=True, hide_index=True)
                            else:
                                for line in section_lines:
                                    st.write(line)
                        else:
                            # Display as bullet points for other sections
                            for line in section_lines[:20]:  # Limit to 20 lines per section
                                st.write(f"• {line}")
                            if len(section_lines) > 20:
                                st.info(f"... and {len(section_lines) - 20} more items")
        else:
            st.info("No resume text available")
