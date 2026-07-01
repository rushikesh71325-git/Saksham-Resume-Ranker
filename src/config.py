"""
Configuration file for the Redrob Hackathon Candidate Ranker.
Contains all scoring weights, keyword sets, and threshold values.
"""

# ---------------------------------------------------------
# SCORING WEIGHTS (Total = 1.0)
# ---------------------------------------------------------
WEIGHTS = {
    "role_fit": 0.25,          # How well the title/domain matches "AI/ML Engineer"
    "career_substance": 0.30,  # Evidence of building ranking/retrieval/recommendation in prod
    "tech_depth": 0.20,        # Specific required skills (embeddings, vector DBs, Python, eval)
    "behavioral": 0.15,        # Availability, activity, and responsiveness signals
    "location": 0.05,          # Noida/Pune/Delhi/Mumbai/Hyderabad preference
    "education": 0.05          # Modest bump for tier-1/tier-2 and CS degrees
}

# ---------------------------------------------------------
# ROLE / TITLE MATCHING
# ---------------------------------------------------------
TARGET_TITLES = [
    "ai engineer", "machine learning engineer", "ml engineer", 
    "applied scientist", "data scientist", "search engineer", 
    "recommendation engineer", "backend engineer" # if they do ML
]

ANTI_TITLES = [
    "hr manager", "marketing manager", "content writer", 
    "operations manager", "accountant", "graphic designer", 
    "civil engineer", "mechanical engineer", "sales executive",
    "customer support"
]

# ---------------------------------------------------------
# KEYWORDS (Substance & Tech Depth)
# ---------------------------------------------------------
# We look for these in career_history.description (evidence of doing the work)
SUBSTANCE_KEYWORDS = [
    "retrieval", "ranking", "recommendation", "recsys", "rag", 
    "hybrid search", "semantic search", "embedding", "vector search",
    "production", "scale", "ab testing", "a/b testing", "deployed"
]

# Specific skills from the JD (Weighted)
TECH_SKILLS_REQUIRED = {
    "sentence-transformers": 1.0,
    "bge": 1.0,
    "e5": 1.0,
    "openai embeddings": 1.0,
    "pinecone": 1.0, 
    "weaviate": 1.0, 
    "qdrant": 1.0, 
    "milvus": 1.0, 
    "opensearch": 1.0, 
    "elasticsearch": 1.0, 
    "faiss": 1.0,
    "python": 1.0,
    "ndcg": 1.0, 
    "mrr": 1.0, 
    "map": 1.0
}

TECH_SKILLS_PREFERRED = {
    "lora": 0.5, 
    "qlora": 0.5, 
    "peft": 0.5, 
    "llm fine-tuning": 0.5,
    "xgboost": 0.5, 
    "learning-to-rank": 0.5, 
    "ltr": 0.5,
    "distributed systems": 0.5
}

# ---------------------------------------------------------
# LOCATION PREFERENCES
# ---------------------------------------------------------
TARGET_LOCATIONS = [
    "pune", "noida", "hyderabad", "mumbai", "delhi", "ncr", "gurgaon"
]

# ---------------------------------------------------------
# PENALTIES & HONEYPOT THRESHOLDS
# ---------------------------------------------------------
PENALTIES = {
    "pure_consulting": 0.5,    # Multiply score by 0.5 if only consulting companies found
    "high_notice_period": 0.8, # Notice period > 60 days
    "inactive": 0.3,           # Last active > 90 days ago
    "no_response": 0.5         # Recruiter response rate < 0.2
}

CONSULTING_COMPANIES = [
    "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini", "mindtree"
]

HONEYPOT_EXPERT_DURATION_THRESHOLD = 0  # If skill is 'expert' but duration is 0
HONEYPOT_CAREER_DATE_MISMATCH = True
