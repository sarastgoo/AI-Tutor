# bench_piper.py
# Benchmark Piper TTS English voice (compatible with piper-tts 1.8+)

import time
import json
import os
import urllib.request
import wave
import psutil
from datetime import datetime

PROJECT_ROOT = r"C:\Projects\ai-english-tutor"
RESULTS_DIR = os.path.join(PROJECT_ROOT, "benchmark-results")
VOICES_DIR = os.path.join(PROJECT_ROOT, "scripts", "voices")
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(VOICES_DIR, exist_ok=True)

VOICE_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium"
VOICE_NAME = "en_US-lessac-medium"
ONNX_PATH = os.path.join(VOICES_DIR, f"{VOICE_NAME}.onnx")
JSON_PATH = os.path.join(VOICES_DIR, f"{VOICE_NAME}.onnx.json")

def get_ram_mb():
    return psutil.Process().memory_info().rss / (1024 * 1024)

def download_if_missing():
    for url, path in [
        (f"{VOICE_BASE}/{VOICE_NAME}.onnx", ONNX_PATH),
        (f"{VOICE_BASE}/{VOICE_NAME}.onnx.json", JSON_PATH),
    ]:
        if not os.path.exists(path):
            print(f"Downloading {os.path.basename(path)}...")
            urllib.request.urlretrieve(url, path)
            print(f"  -> {path} ({os.path.getsize(path)//1024} KB)")

def main():
    print("=== TTS Benchmark: Piper en_US-lessac-medium ===")
    print(f"Start: {datetime.now().isoformat()}")
    print()

    download_if_missing()

    # Init
    print("Loading Piper...")
    t0 = time.time()
    from piper.voice import PiperVoice
    voice = PiperVoice.load(ONNX_PATH, config_path=JSON_PATH)
    init_time = time.time() - t0
    print(f"Init: {init_time:.1f} s")

    sentences = [
        "Hello, this is a test of the Piper text to speech system.",
        "The present perfect tense is used for actions that happened at an unspecified time before now.",
        "Learning English requires consistent practice and exposure to authentic materials.",
    ]

    results = {"init_time_s": round(init_time, 2), "sentences": []}
    total_chars = 0
    total_time = 0

    for i, text in enumerate(sentences, start=1):
        out_wav = os.path.join(RESULTS_DIR, f"piper_test_{i}.wav")
        print(f"\nSentence {i}: {len(text)} chars")
        
        t0 = time.time()
        # در نسخه ۱.۸، synthesize یک generator از AudioChunk برمی‌گرداند
        with wave.open(out_wav, "wb") as wav_file:
            # تنظیم پارامترهای WAV (نمونه‌برداری 22050 هرتز، 16 بیت، مونو)
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(22050)
            
            for audio_chunk in voice.synthesize(text):
                wav_file.writeframes(audio_chunk.audio_int16_bytes)
                
        elapsed = time.time() - t0
        size_kb = os.path.getsize(out_wav) // 1024
        total_chars += len(text)
        total_time += elapsed
        results["sentences"].append({
            "index": i,
            "chars": len(text),
            "time_s": round(elapsed, 2),
            "wav_size_kb": size_kb,
        })
        print(f"  Synth: {elapsed:.2f} s, {size_kb} KB")

    results["summary"] = {
        "total_chars": total_chars,
        "total_time_s": round(total_time, 2),
        "chars_per_s": round(total_chars / total_time, 2) if total_time > 0 else None,
    }
    results["ram_peak_mb"] = round(get_ram_mb(), 0)
    results["timestamp"] = datetime.now().isoformat()

    print()
    print("=== Summary ===")
    print(json.dumps(results["summary"], indent=2))

    out_path = os.path.join(RESULTS_DIR, "piper-benchmark.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to: {out_path}")

if __name__ == "__main__":
    main()