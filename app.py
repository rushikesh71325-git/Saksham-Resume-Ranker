import gradio as gr
import os
import time
import json
import pandas as pd
from precompute import precompute
from rank import rank_candidates

def convert_json_to_jsonl(json_path, jsonl_path):
    """Converts a standard JSON array file into a JSONL file."""
    with open(json_path, 'r', encoding='utf-8') as fin:
        data = json.load(fin)
    with open(jsonl_path, 'w', encoding='utf-8') as fout:
        for item in data:
            fout.write(json.dumps(item) + "\n")

def run_pipeline(input_file):
    """
    Runs the precompute and rank pipeline on the uploaded file.
    If no file is uploaded, uses the default mini_candidates.jsonl.
    """
    if input_file is not None:
        candidates_path = input_file.name
        # If the user uploaded a pure .json array file, convert it to .jsonl
        if candidates_path.endswith('.json'):
            temp_jsonl = "converted_input.jsonl"
            convert_json_to_jsonl(candidates_path, temp_jsonl)
            candidates_path = temp_jsonl
    else:
        candidates_path = "mini_candidates.jsonl"
        if not os.path.exists(candidates_path):
            return None, gr.update(visible=False), "Error: Please upload a candidate file."

    features_path = "temp_features.jsonl"
    out_csv_path = "saksham_submission.csv"
    
    start_time = time.time()
    
    try:
        # Stage 1: Pre-compute (Extract Features)
        precompute(candidates_path, features_path)
        
        # Stage 2: Rank
        rank_candidates(features_path, candidates_path, out_csv_path)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Read the CSV to display in the UI
        df = pd.read_csv(out_csv_path)
        
        status_msg = f"✅ Pipeline completed successfully in {elapsed:.2f} seconds!"
        # Return the DataFrame, activate the Download Button with the file, and update status
        return df, gr.DownloadButton(value=out_csv_path, visible=True), status_msg
        
    except Exception as e:
        return None, gr.update(visible=False), f"❌ Error during processing: {str(e)}"

# Define the Gradio Interface
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🏆 Saksham Resume Ranker")
    gr.Markdown(
        "Upload a sample `candidates.jsonl` or `.json` file to see the two-stage ranking pipeline in action. "
        "The system will pre-compute features, detect honeypots, and output a ranked CSV with dynamic reasoning."
    )
    
    with gr.Row():
        with gr.Column():
            file_input = gr.File(label="Upload candidates file (Optional)", file_types=[".jsonl", ".json", ".gz"])
            run_btn = gr.Button("Run Ranking Pipeline", variant="primary")
            status_text = gr.Markdown("Waiting for input...")
            
    with gr.Row():
        output_file = gr.DownloadButton("Download Ranked CSV", visible=False)
        
    with gr.Row():
        output_df = gr.Dataframe(label="Top Candidates Preview", interactive=False, wrap=True)

    # Actions
    run_btn.click(
        fn=run_pipeline,
        inputs=[file_input],
        outputs=[output_df, output_file, status_text]
    )

if __name__ == "__main__":
    demo.launch()
