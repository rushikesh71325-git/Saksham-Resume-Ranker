import json
import gzip
import os
import argparse
from tqdm import tqdm
from src.features import generate_features

def precompute(input_path: str, output_path: str):
    """
    Reads the candidates.jsonl (or .gz), extracts features, 
    and saves to a clean precomputed format.
    """
    print(f"Starting pre-computation from {input_path}...")
    
    # Handle gzipped files transparently
    open_fn = gzip.open if input_path.endswith('.gz') else open
    mode = 'rt' if input_path.endswith('.gz') else 'r'
    
    processed = 0
    honeypots = 0
    
    with open_fn(input_path, mode, encoding='utf-8') as fin, \
         open(output_path, 'w', encoding='utf-8') as fout:
             
        for line in tqdm(fin, desc="Extracting features"):
            if not line.strip():
                continue
                
            candidate = json.loads(line)
            features = generate_features(candidate)
            
            if features.get("is_honeypot"):
                honeypots += 1
                
            fout.write(json.dumps(features) + "\n")
            processed += 1
            
    print(f"\nPre-computation complete!")
    print(f"Total candidates processed: {processed}")
    print(f"Honeypots detected (and flagged): {honeypots}")
    print(f"Features saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pre-compute candidate features offline.")
    parser.add_argument("--input", default="candidates.jsonl.gz", help="Path to candidates.jsonl or .gz")
    parser.add_argument("--output", default="precomputed_features.jsonl", help="Output features file")
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file {args.input} not found.")
        print("Please download the dataset or point to the correct path.")
        exit(1)
        
    precompute(args.input, args.output)
