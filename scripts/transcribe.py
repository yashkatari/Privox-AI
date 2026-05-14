#!/usr/bin/env python3
"""
Transcribe all 15 test audio files and show per-file WER + errors.
Helps identify which files/categories have issues.
"""

import os
import json
import string
from jiwer import wer
import sys

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stt.streaming_whisper import transcribe_with_model, load_whisper_model

def normalize_text(text):
    """Normalize text: lowercase, remove punctuation, strip whitespace."""
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    return ' '.join(text.split())  # normalize whitespace

# Load references
with open("stt-d/references.json") as f:
    references = json.load(f)

# Load medium model once
print("[Transcribe] Loading Whisper medium model...")
model = load_whisper_model("medium")
print("[Transcribe] Ready.\n")

# Collect results by category
results = {"clean": [], "noisy": [], "background": []}

dirs_to_scan = [
    ("stt-d/clean", "clean"),
    ("stt-d/noisy", "noisy"),
    ("stt-d/background", "background")
]

for dir_path, category in dirs_to_scan:
    print(f"\n{'='*60}")
    print(f"📁 Category: {category.upper()}")
    print(f"{'='*60}")
    
    files = sorted([f for f in os.listdir(dir_path) if f.endswith(".wav")])
    
    for audio_file in files:
        audio_path = os.path.join(dir_path, audio_file)
        
        # Get reference
        ref_text = references.get(audio_file, "")
        
        # Transcribe using the model
        hyp_text = transcribe_with_model(audio_path, model)
        
        # Normalize for WER calculation
        ref_norm = normalize_text(ref_text)
        hyp_norm = normalize_text(hyp_text)
        
        # Calculate WER
        file_wer = wer(ref_norm, hyp_norm) * 100
        
        # Store
        results[category].append({
            "file": audio_file,
            "reference": ref_text,
            "hypothesis": hyp_text,
            "wer": file_wer
        })
        
        # Print
        match = "✅" if file_wer < 5 else "⚠️" if file_wer < 15 else "❌"
        print(f"\n{match} {audio_file} | WER: {file_wer:.2f}%")
        print(f"   REF: {ref_text}")
        print(f"   HYP: {hyp_text}")
        if file_wer > 0:
            print(f"   Normalized REF: {ref_norm}")
            print(f"   Normalized HYP: {hyp_norm}")

# Summary
print(f"\n\n{'='*60}")
print("📊 SUMMARY BY CATEGORY")
print(f"{'='*60}")

for category in ["clean", "noisy", "background"]:
    cat_results = results[category]
    if not cat_results:
        continue
    
    wers = [r["wer"] for r in cat_results]
    avg_wer = sum(wers) / len(wers)
    max_wer = max(wers)
    
    print(f"\n{category.upper()}:")
    print(f"  Avg WER:  {avg_wer:.2f}%")
    print(f"  Max WER:  {max_wer:.2f}%")
    print(f"  Files:    {len(cat_results)}")
    
    # Show worst files
    worst = sorted(cat_results, key=lambda x: x["wer"], reverse=True)[:2]
    if worst:
        print(f"  Worst performers:")
        for r in worst:
            print(f"    - {r['file']}: {r['wer']:.2f}%")

print("\n✅ Detailed report complete!")

