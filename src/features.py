import re
from datetime import datetime
from typing import Dict, Any, List, Tuple
from src.config import (
    TARGET_TITLES, ANTI_TITLES, SUBSTANCE_KEYWORDS, 
    TECH_SKILLS_REQUIRED, TECH_SKILLS_PREFERRED, TARGET_LOCATIONS,
    CONSULTING_COMPANIES, HONEYPOT_EXPERT_DURATION_THRESHOLD
)

def parse_date(date_str: str) -> datetime:
    """Safely parse a date string."""
    if not date_str:
        return datetime.now()
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return datetime.now()

def check_honeypot(candidate: Dict[str, Any]) -> bool:
    """
    Detects logically impossible profiles (honeypots).
    Returns True if the profile is likely a honeypot.
    """
    # 1. Expert skills with 0 duration
    for skill in candidate.get("skills", []):
        if skill.get("proficiency") == "expert" and skill.get("duration_months", 0) <= HONEYPOT_EXPERT_DURATION_THRESHOLD:
            return True
            
    # 2. Date/Tenure impossibilities
    total_career_months = 0
    for job in candidate.get("career_history", []):
        # Check if start date is in the future
        start = parse_date(job.get("start_date"))
        if start > datetime.now():
            return True
        
        # Accumulate career months
        total_career_months += job.get("duration_months", 0)
    
    # 3. YOE mismatch (e.g. 10 years YOE but only 2 years in career history)
    claimed_yoe_months = candidate.get("profile", {}).get("years_of_experience", 0) * 12
    # Allow some leeway for unlisted jobs, but if claimed is MASSIVELY higher than listed, it's suspect.
    # Actually, a better honeypot check from the spec: "8 years of experience at a company founded 3 years ago" 
    # Since we don't have company founding dates, we focus on massive mismatches.
    if claimed_yoe_months > (total_career_months + 60): # 5 years missing is weird
        pass # We won't strictly enforce this without being sure, to avoid false positives.

    # 4. Anti-title with crazy AI skills
    title = str(candidate.get("profile", {}).get("current_title", "")).lower()
    is_anti_title = any(at in title for at in ANTI_TITLES)
    if is_anti_title:
        # Check if they have an impossible number of AI skills despite being an HR manager
        ai_skills_count = sum(1 for s in candidate.get("skills", []) if s.get("name", "").lower() in TECH_SKILLS_REQUIRED)
        if ai_skills_count > 5:
            return True # HR Manager with 6+ core AI skills is a trap

    return False

def extract_role_fit(candidate: Dict[str, Any]) -> float:
    """Evaluate how well the candidate's titles match the ML/AI domain."""
    score = 0.0
    title = str(candidate.get("profile", {}).get("current_title", "")).lower()
    
    # Current title match
    if any(t in title for t in TARGET_TITLES):
        score += 1.0
    elif any(at in title for at in ANTI_TITLES):
        score -= 1.0 # Heavy penalty for completely unrelated current roles
        
    # Historical titles
    past_ml_roles = 0
    for job in candidate.get("career_history", []):
        job_title = str(job.get("title", "")).lower()
        if any(t in job_title for t in TARGET_TITLES):
            past_ml_roles += 1
            
    if past_ml_roles > 0 and score <= 0:
        score += 0.5 # They did ML in the past at least
        
    return max(0.0, min(1.0, (score + 1) / 2)) # Normalize to 0-1

def extract_career_substance(candidate: Dict[str, Any]) -> float:
    """Evaluate if they have actually built ranking/retrieval systems in prod."""
    score = 0.0
    descriptions = " ".join([str(job.get("description", "")) for job in candidate.get("career_history", [])]).lower()
    
    matches = sum(1 for keyword in SUBSTANCE_KEYWORDS if keyword in descriptions)
    score = min(1.0, matches / 5.0) # Cap at 5 strong keywords
    
    # Penalty for pure consulting
    companies = " ".join([str(job.get("company", "")) for job in candidate.get("career_history", [])]).lower()
    product_company = True
    # If ALL companies are consulting
    if all(any(c in str(job.get("company", "")).lower() for c in CONSULTING_COMPANIES) for job in candidate.get("career_history", [])):
        product_company = False
        
    if not product_company:
        score *= 0.5
        
    return score

def extract_tech_depth(candidate: Dict[str, Any]) -> float:
    """Evaluate technical skills (proficiency and duration)."""
    score = 0.0
    max_possible = 10.0 # Arbitrary normalization ceiling
    
    proficiency_multiplier = {
        "expert": 1.2,
        "advanced": 1.0,
        "intermediate": 0.6,
        "beginner": 0.2
    }
    
    for skill in candidate.get("skills", []):
        name = str(skill.get("name", "")).lower()
        prof = proficiency_multiplier.get(skill.get("proficiency", "beginner"), 0.2)
        dur = min(60, skill.get("duration_months", 0)) / 12.0 # Cap at 5 years (5.0)
        
        weight = TECH_SKILLS_REQUIRED.get(name, TECH_SKILLS_PREFERRED.get(name, 0.0))
        if weight > 0:
            # Score = weight * proficiency * sqrt(years) to balance long-time low-prof vs short-time high-prof
            score += weight * prof * (dur ** 0.5)
            
    return min(1.0, score / max_possible)

def extract_behavioral_score(candidate: Dict[str, Any]) -> float:
    """Evaluate candidate availability and engagement."""
    signals = candidate.get("redrob_signals", {})
    score = 1.0 # Start perfect, deduct for red flags, add for green flags
    
    # 1. Recency
    last_active = parse_date(signals.get("last_active_date"))
    days_since_active = (datetime.now() - last_active).days
    # Adjust for dataset being from future/past - we'll use a relative date if possible, 
    # but let's assume the max date in the dataset is "now".
    # Since we can't do that easily per row, we'll just check if it's within 60 days of a fixed point.
    # Actually, it's safer to just penalize VERY old dates or use the open_to_work_flag.
    
    if not signals.get("open_to_work_flag", False):
        score -= 0.2
        
    # 2. Responsiveness
    response_rate = signals.get("recruiter_response_rate", 0.0)
    if response_rate < 0.2:
        score -= 0.4
    elif response_rate > 0.7:
        score += 0.2
        
    # 3. Notice Period
    notice = signals.get("notice_period_days", 60)
    if notice > 60:
        score -= 0.3
    elif notice <= 30:
        score += 0.2
        
    return max(0.0, min(1.0, score))

def extract_location_fit(candidate: Dict[str, Any]) -> float:
    """Evaluate location and relocation willingness."""
    loc = str(candidate.get("profile", {}).get("location", "")).lower()
    willing = candidate.get("redrob_signals", {}).get("willing_to_relocate", False)
    
    if any(t in loc for t in TARGET_LOCATIONS):
        return 1.0
    elif willing:
        return 0.8
    else:
        return 0.0

def generate_features(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """Generates all features for a single candidate."""
    is_honeypot = check_honeypot(candidate)
    
    if is_honeypot:
        # Fast path for honeypots
        return {
            "candidate_id": candidate.get("candidate_id"),
            "role_fit": 0.0,
            "career_substance": 0.0,
            "tech_depth": 0.0,
            "behavioral": 0.0,
            "location_fit": 0.0,
            "is_honeypot": True
        }
        
    return {
        "candidate_id": candidate.get("candidate_id"),
        "role_fit": extract_role_fit(candidate),
        "career_substance": extract_career_substance(candidate),
        "tech_depth": extract_tech_depth(candidate),
        "behavioral": extract_behavioral_score(candidate),
        "location_fit": extract_location_fit(candidate),
        "is_honeypot": False
    }
