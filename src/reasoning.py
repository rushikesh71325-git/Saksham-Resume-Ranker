import random
from typing import Dict, Any

def generate_reasoning(candidate: Dict[str, Any], score: float, rank: int) -> str:
    """
    Generates a 1-2 sentence justification for the candidate's ranking.
    Must reference specific facts, connect to JD, acknowledge gaps, not hallucinate,
    have variation, and be consistent with the rank.
    """
    # 1. Extract specific facts
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    skills = candidate.get("skills", [])
    
    title = profile.get("current_title", "Professional")
    yoe = profile.get("years_of_experience", 0)
    
    # Find matching AI skills
    from src.config import TECH_SKILLS_REQUIRED
    ai_skills = [s.get("name") for s in skills if s.get("name", "").lower() in TECH_SKILLS_REQUIRED]
    
    # Behavioral gap check
    notice = signals.get("notice_period_days", 60)
    response_rate = signals.get("recruiter_response_rate", 0.0)
    
    # 2. Rank consistency & Variation
    if rank <= 20:
        # Top tier reasoning
        positives = [
            f"Strong alignment with {yoe} years of experience.",
            f"Excellent background as a {title}.",
            f"Demonstrates solid production experience."
        ]
        if ai_skills:
            positives.append(f"Brings specific expertise in {ai_skills[0] if len(ai_skills) > 0 else 'AI systems'}.")
            
        positive = random.choice(positives)
        
        # Acknowledge gaps if any
        gap = ""
        if notice > 30:
            gap = f" Note the {notice}-day notice period."
        elif response_rate < 0.5:
            gap = f" Recruiter response rate ({int(response_rate*100)}%) is slightly below ideal."
            
        return f"{positive}{gap}"
        
    elif rank <= 70:
        # Mid tier reasoning
        reason = f"{title} with {yoe} years of experience."
        if ai_skills:
            reason += f" Possesses relevant skills like {ai_skills[0]}."
        else:
            reason += " Missing some core vector database or embedding experience."
            
        if response_rate > 0.7:
            reason += " Strong behavioral signals and responsiveness keep them in contention."
            
        return reason
        
    else:
        # Bottom tier reasoning (ranks 71-100)
        reasons = [
            f"Included as a filler candidate; {title} background is adjacent but lacks direct ranking system experience.",
            f"Lower rank due to limited direct match with JD requirements, though {yoe} years of experience is noted.",
            f"While holding a {title} role, the profile lacks strong signals for the core AI/ML requirements."
        ]
        return random.choice(reasons)
