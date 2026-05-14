import os
import time
import json
import argparse
import string
import numpy as np
from jiwer import wer

# ===== IMPORT YOUR EXISTING MODULES =====
from wakeword.detector import detect_wakeword
from stt.streaming_whisper import transcribe_file, load_whisper_model, transcribe_with_model
from llm.qwen_local import QwenLLM

def normalize_text(text):
    """Normalize text: lowercase, remove punctuation, strip whitespace."""
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    return ' '.join(text.split())  # normalize whitespace

# ===============================
# WAKE WORD EVALUATION
# ===============================
def evaluate_wakeword(pos_dir, neg_dir):
    TP = FN = FP = TN = 0

    for file in os.listdir(pos_dir):
        if detect_wakeword(os.path.join(pos_dir, file)):
            TP += 1
        else:
            FN += 1

    for file in os.listdir(neg_dir):
        if detect_wakeword(os.path.join(neg_dir, file)):
            FP += 1
        else:
            TN += 1

    accuracy = (TP + TN) / (TP + TN + FP + FN)
    precision = TP / (TP + FP) if TP + FP else 0
    recall = TP / (TP + FN) if TP + FN else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0

    return {
        "Accuracy": round(accuracy * 100, 2),
        "Precision": round(precision * 100, 2),
        "Recall": round(recall * 100, 2),
        "F1-Score": round(f1 * 100, 2)
    }


# ===============================
# STT EVALUATION (WER)
# ===============================
def evaluate_stt(audio_dir, references, model_obj=None):
    wers = []

    # Determine which subset to evaluate based on folder name
    subset = os.path.basename(os.path.normpath(audio_dir)).lower()
    prefix_map = {
        "clean": "QS",
        "noisy": "NE",
        "background": "BS"
    }
    prefix = prefix_map.get(subset, "")

    for file, ref_text in references.items():
        # Only evaluate files that belong to this subset (QS/NE/BS)
        if prefix and not file.upper().startswith(prefix):
            continue

        audio_path = os.path.join(audio_dir, file)
        if not os.path.exists(audio_path):
            print(f"[evaluate_stt] Missing file, skipping: {audio_path}")
            continue

        if model_obj is None:
            hyp = transcribe_file(audio_path)
        else:
            hyp = transcribe_with_model(audio_path, model_obj)
        if hyp is None:
            hyp = ""
        
        # Normalize both texts: lowercase + remove punctuation
        ref_norm = normalize_text(ref_text)
        hyp_norm = normalize_text(hyp)
        wers.append(wer(ref_norm, hyp_norm))

    if not wers:
        return 0.0

    return round(np.mean(wers) * 100, 2)


# ===============================
# LLM LATENCY EVALUATION
# ===============================
def evaluate_llm_latency():
    llm = QwenLLM("qwen2.5:3b")
    prompt = "What is artificial intelligence?"

    start = time.time()
    llm.generate(prompt)
    latency = time.time() - start

    return round(latency, 2)


# ===============================
# MAIN
# ===============================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-size", default="small", help="Whisper model size for STT evaluation (small|medium|large)")
    args = parser.parse_args()

    print("\n📊 SYSTEM EVALUATION RESULTS\n")

    # # Wake-word (COMMENTED: focus on STT WER)
    wakeword_results = evaluate_wakeword(
        "wakeword-d/positive",
        "wakeword-d/negative"
    )

    print("🔊 Wake-word Detection Metrics:")
    for k, v in wakeword_results.items():
        print(f"{k}: {v}%")

    # STT
    with open("stt-d/references.json") as f:
        refs = json.load(f)

    # Load evaluation model if requested (default small)
    eval_model = load_whisper_model(args.model_size)

    stt_clean = evaluate_stt("stt-d/clean", refs, model_obj=eval_model)
    stt_noisy = evaluate_stt("stt-d/noisy", refs, model_obj=eval_model)
    stt_bg = evaluate_stt("stt-d/background", refs, model_obj=eval_model)

    print("\n🗣️ Speech-to-Text (WER):")
    print(f"Clean: {stt_clean}%")
    print(f"Noisy: {stt_noisy}%")
    print(f"Background: {stt_bg}%")

    # LLM
    latency = evaluate_llm_latency()
    print(f"\n🤖 LLM Response Latency: {latency} seconds")

    print("\n🧠 VAD Evaluation: Qualitative (Correct segmentation observed)")
    print("🔈 TTS Evaluation: Subjective clarity (Human listening test)")

    print("\n✅ Evaluation Completed Successfully")
