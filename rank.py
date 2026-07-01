import json
import gzip
import argparse
import time
from typing import Dict, Any, List

from src.config import WEIGHTS
from src.reasoning import generate_reasoning

def calculate_score(features: Dict[str, Any]) -> float:
    """Calculates the final score based on precomputed features and weights."""
    if features.get("is_honeypot", False):
        return 0.0 # Push honeypots to the very bottom
        
    score = (
        features.get("role_fit", 0.0) * WEIGHTS["role_fit"] +
        features.get("career_substance", 0.0) * WEIGHTS["career_substance"] +
        features.get("tech_depth", 0.0) * WEIGHTS["tech_depth"] +
        features.get("behavioral", 0.0) * WEIGHTS["behavioral"] +
        features.get("location_fit", 0.0) * WEIGHTS["location"]
    )
    
    return score

def load_candidates_for_reasoning(input_path: str, top_ids: set) -> Dict[str, Any]:
    """Loads only the full JSON of the top 100 candidates to generate reasoning."""
    top_candidates = {}
    open_fn = gzip.open if input_path.endswith('.gz') else open
    mode = 'rt' if input_path.endswith('.gz') else 'r'
    
    with open_fn(input_path, mode, encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            cand = json.loads(line)
            cid = cand["candidate_id"]
            if cid in top_ids:
                top_candidates[cid] = cand
                if len(top_candidates) == len(top_ids):
                    break # Found all of them
    return top_candidates

def rank_candidates(features_path: str, candidates_path: str, out_path: str):
    """
    Fast ranking step that must complete in < 5 minutes on CPU.
    """
    start_time = time.time()
    scored_candidates = []
    
    # 1. Load and score precomputed features
    with open(features_path, 'r', encoding='utf-8') as f:
        for line in f:
            features = json.loads(line)
            score = calculate_score(features)
            # Round score to match the CSV output format so ties are correctly identified during sorting
            score = round(score, 4)
            scored_candidates.append({
                "candidate_id": features["candidate_id"],
                "score": score
            })
            
    # 2. Sort by score (descending), tie-break by candidate_id (ascending)
    scored_candidates.sort(key=lambda x: (-x["score"], x["candidate_id"]))
    
    # 3. Take top 100
    top_100 = scored_candidates[:100]
    top_ids = {c["candidate_id"] for c in top_100}
    
    # 4. Generate Reasoning
    # To do this without Hallucination, we need the original facts for the top 100.
    # We re-read the original file just for these 100 to get exact titles/skills.
    # This is fast because we only parse JSON until we find our 100 IDs.
    original_data = load_candidates_for_reasoning(candidates_path, top_ids)
    
    # 5. Write CSV
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("candidate_id,rank,score,reasoning\n")
        for i, cand in enumerate(top_100):
            rank = i + 1
            cid = cand["candidate_id"]
            score = cand["score"]
            
            # Formatting score exactly (e.g. 4 decimal places)
            score_str = f"{score:.4f}"
            
            orig_cand = original_data.get(cid, {})
            reasoning = generate_reasoning(orig_cand, score, rank)
            
            # Escape quotes in CSV reasoning
            reasoning_escaped = reasoning.replace('"', '""')
            
            f.write(f'{cid},{rank},{score_str},"{reasoning_escaped}"\n')
            
    end_time = time.time()
    print(f"Ranking complete in {end_time - start_time:.2f} seconds.")
    print(f"Output saved to {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fast ranking using precomputed features.")
    parser.add_argument("--features", default="precomputed_features.jsonl", help="Path to precomputed features")
    parser.add_argument("--candidates", default="candidates.jsonl.gz", help="Original candidates file (for reasoning facts)")
    parser.add_argument("--out", default="submission.csv", help="Output CSV path")
    args = parser.parse_args()
    
    rank_candidates(args.features, args.candidates, args.out)
