# Intelligent Candidate Discovery & Ranking Challenge

This repository contains the codebase for ranking candidates against the "Senior AI Engineer" job description. It strictly adheres to the 5-minute CPU-only compute constraints by using a robust **two-stage architecture**.

## Architecture Overview

1. **Pre-computation (`precompute.py`)**: Runs completely offline without time constraints. It streams the massive 100K `candidates.jsonl.gz`, extracts numerical and categorical features using heavy NLP heuristics (title matching, substance keyword extraction, behavioral normalization), flags logical honeypots, and saves the output to a compact intermediate file.
2. **Ranking (`rank.py`)**: The strict ranking step. Loads the compact precomputed features, applies final scoring math, generates dynamic fact-based reasoning (zero hallucinations), and outputs the final CSV. **Runs in seconds on CPU.**

## Prerequisites

- Python 3.10+
- `tqdm` (for progress bars during pre-computation)

Install dependencies:
```bash
pip install -r requirements.txt
```

## How to Reproduce

### Step 1: Pre-compute Features (Offline)
Place `candidates.jsonl.gz` in the root directory and run:

```bash
python precompute.py --input ./candidates.jsonl.gz --output ./precomputed_features.jsonl
```
*Note: This generates `precomputed_features.jsonl` which the rank script requires.*

### Step 2: Rank Candidates (Evaluated Step)
The following command produces the final submission CSV and respects all Stage 3 compute limits (No network, no GPU, < 5 minutes):

```bash
python rank.py --features ./precomputed_features.jsonl --candidates ./candidates.jsonl.gz --out ./submission.csv
```

## Honeypot Detection
Our heuristic engine natively detects honeypots by checking for:
- "Expert" proficiencies on skills that have `duration_months == 0`.
- Massive discrepancies between claimed years of experience and actual accumulated career history.
- Complete anti-titles (e.g., HR Manager) mysteriously possessing 6+ highly specialized AI skills.

## Sandbox Validation
A hosted version of this ranking logic is available at the sandbox link provided in `submission_metadata.yaml`.
