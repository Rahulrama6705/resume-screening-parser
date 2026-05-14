from typing import Dict


class SRSAutoFiller:
    """Auto-fill SRS (Software Requirements Specification) form fields."""
    
    @staticmethod
    def fill_form(extracted_data: Dict) -> Dict:
        """Map extracted resume data to SRS form fields."""
        education_parts = [
            extracted_data.get("education_degree", ""),
            extracted_data.get("education_specialization", ""),
            extracted_data.get("education_type", ""),
        ]
        education_value = " | ".join([p for p in education_parts if p])

        srs_form = {
            # Personal Information
            "applicant_name": extracted_data.get("name", ""),
            "email_address": extracted_data.get("email", ""),
            "phone_number": extracted_data.get("phone", ""),
            "date_of_birth": extracted_data.get("dob", ""),
            
            # Professional Information
            "current_company": extracted_data.get("current_company", extracted_data.get("company", "")),
            "job_category": extracted_data.get("category", ""),
            "years_experience": extracted_data.get("experience_years", extracted_data.get("experience", "")),
            
            # Education
            "education": education_value or extracted_data.get("education", ""),
            "gpa_cgpa": extracted_data.get("gpa", ""),
            
            # Skills and Expertise
            "technical_skills": ", ".join(extracted_data.get("skills", [])),
            "certifications": ", ".join(extracted_data.get("certifications", [])),
            
            # Projects and Portfolio
            "projects": ", ".join(extracted_data.get("projects", [])),
            "linkedin_url": extracted_data.get("linkedin", ""),
            "github_url": extracted_data.get("github", ""),
            
            # Metadata
            "form_submission_date": "",
            "status": "auto_filled",
            "processed": True
        }
        
        return srs_form
    
    @staticmethod
    def validate_form(form_data: Dict) -> Dict:
        """Validate form data - lenient to allow partial data."""
        validation = {
            "is_valid": True,
            "missing_fields": [],
            "warnings": [],
            "filled_fields": 0
        }
        
        # Optional fields - just warn if missing
        optional_fields = [
            "applicant_name",
            "email_address", 
            "phone_number",
            "current_company",
            "years_experience",
            "technical_skills",
            "education"
        ]
        
        filled_count = 0
        for field in optional_fields:
            if form_data.get(field):
                filled_count += 1
            else:
                validation["missing_fields"].append(field)
        
        validation["filled_fields"] = filled_count
        
        # Only mark invalid if almost no data
        if filled_count < 2:
            validation["is_valid"] = False
        
        # Validate email format if present
        email = form_data.get("email_address", "")
        if email and "@" not in email:
            validation["warnings"].append("Invalid email format - may need manual review")
        
        # Validate phone format if present
        phone = form_data.get("phone_number", "")
        if phone and len(phone.replace("-", "").replace(" ", "").replace("+", "")) < 7:
            validation["warnings"].append("Phone number too short - may need manual review")
        
        return validation
