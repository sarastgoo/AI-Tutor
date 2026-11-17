# bench_whisper.py
# Benchmark faster-whisper small int8 on sample audio

import time
import json
import os
import glob
import psutil
from datetime import datetime

PROJECT_ROOT = r"C:\Projects\ai-english-tutor"
AUDIO_DIR = os.path.join(PROJECT_ROOT, "scripts", "fixtures")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "benchmark-results")
os.makedirs(RESULTS_DIR, exist_ok=True)

def get_ram_mb():
    return psutil.Process().memory_info().rss / (1024 * 1024)

def get_duration(path):
    """Get audio duration using av library directly (compatible with av>=12)."""
    import av
    with av.open(path, mode="r") as container:
        if container.duration is not None:
            return float(container.duration) / av.time_base
        # Fallback: iterate streams
        for stream in container.streams:
            if stream.duration is not None and stream.time_base is not None:
                return float(stream.duration * stream.time_base)
    return 0.0

def main():
    print("=== STT Benchmark: faster-whisper small int8 ===")
    print(f"Start: {datetime.now().isoformat()}")
    print()

    audio_files = sorted(glob.glob(os.path.join(AUDIO_DIR, "*.mp3")))
    if not audio_files:
        print(f"ERROR: No audio files in {AUDIO_DIR}")
        return
    print(f"Found {len(audio_files)} audio files")

    test_files = audio_files[:2]
    print(f"Testing: {[os.path.basename(f) for f in test_files]}")
    print()

    # Init model
    print("Loading faster-whisper small int8...")
    t0 = time.time()
    from faster_whisper import WhisperModel
    model = WhisperModel("small", device="cpu", compute_type="int8")
    init_time = time.time() - t0
    print(f"Init: {init_time:.1f} s")

    results = {"init_time_s": round(init_time, 2), "files": []}
    total_audio_s = 0
    total_proc_s = 0

    for path in test_files:
        try:
            duration = get_duration(path)
        except Exception as e:
            print(f"  WARN: Could not read duration for {os.path.basename(path)}: {e}")
            duration = 0

        print(f"\n{os.path.basename(path)} ({duration:.1f} s)...")
        t0 = time.time()
        segments, info = model.transcribe(path, beam_size=5, language="en")
        segs = list(segments)
        elapsed = time.time() - t0
        total_audio_s += duration
        total_proc_s += elapsed
        rtf = elapsed / duration if duration > 0 else 0

        text = " ".join(s.text.strip() for s in segs)
        results["files"].append({
            "file": os.path.basename(path),
            "duration_s": round(duration, 2),
            "process_s": round(elapsed, 2),
            "rtf": round(rtf, 3),
            "segments": len(segs),
            "text_sample": text[:300],
        })
        print(f"  Processed in {elapsed:.2f} s (RTF={rtf:.3f})")
        print(f"  First 200 chars: {text[:200]}")

    results["summary"] = {
        "total_audio_s": round(total_audio_s, 2),
        "total_process_s": round(total_proc_s, 2),
        "overall_rtf": round(total_proc_s / total_audio_s, 3) if total_audio_s > 0 else None,
    }
    results["ram_peak_mb"] = round(get_ram_mb(), 0)
    results["timestamp"] = datetime.now().isoformat()

    print()
    print("=== Summary ===")
    print(json.dumps(results["summary"], indent=2))

    out_path = os.path.join(RESULTS_DIR, "whisper-benchmark.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to: {out_path}")

if __name__ == "__main__":
    main()