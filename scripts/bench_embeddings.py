# bench_embeddings.py
# Benchmark multilingual-e5-small: speed and correctness on CPU

import time
import json
import os
import psutil
from datetime import datetime

RESULTS_DIR = r"C:\Projects\ai-english-tutor\benchmark-results"
os.makedirs(RESULTS_DIR, exist_ok=True)

def get_ram_mb():
    return psutil.Process().memory_info().rss / (1024 * 1024)

def main():
    print("=== Embeddings Benchmark: multilingual-e5-small ===")
    print(f"Start: {datetime.now().isoformat()}")
    print()

    from sentence_transformers import SentenceTransformer

    # Load model
    print("Loading model (this may download ~470 MB on first run)...")
    t0 = time.time()
    model = SentenceTransformer("intfloat/multilingual-e5-small")
    load_time = time.time() - t0
    print(f"Model loaded in {load_time:.1f} s")
    print(f"Embedding dimension: {model.get_sentence_embedding_dimension()}")
    print(f"Peak RAM after load: {get_ram_mb():.0f} MB")
    print()

    # Sample passages
    passages = [
        f"passage: This is a sample English textbook passage number {i}. "
        f"It discusses grammar, vocabulary, and comprehension exercises for learners."
        for i in range(100)
    ]
    query = "query: What does the passage say about grammar exercises?"

    # Warm up
    print("Warming up...")
    _ = model.encode(["query: warmup"], show_progress_bar=False)
    print()

    # Benchmark batch sizes
    results = {"load_time_s": round(load_time, 2), "dimension": model.get_sentence_embedding_dimension(), "batches": {}}

    for batch_size in [1, 8, 32]:
        print(f"Batch size {batch_size}: encoding 100 passages...")
        t0 = time.time()
        embeddings = model.encode(passages, batch_size=batch_size, show_progress_bar=False)
        elapsed = time.time() - t0
        per_100 = elapsed
        results["batches"][batch_size] = {
            "time_100_passages_s": round(elapsed, 2),
            "passages_per_s": round(100 / elapsed, 2),
        }
        print(f"  {elapsed:.2f} s ({100/elapsed:.1f} passages/s)")
        print(f"  Shape: {embeddings.shape}")

    # Query embedding
    t0 = time.time()
    q_emb = model.encode([query], show_progress_bar=False)
    results["query_time_s"] = round(time.time() - t0, 4)

    # Verify e5 prefix correctness: query vs passage should be different
    sim = model.similarity(q_emb, embeddings[0:1]).item()
    results["sample_similarity"] = round(sim, 4)

    results["ram_peak_mb"] = round(get_ram_mb(), 0)
    results["timestamp"] = datetime.now().isoformat()

    print()
    print("=== Summary ===")
    print(json.dumps(results, indent=2))

    out_path = os.path.join(RESULTS_DIR, "embeddings-benchmark.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to: {out_path}")

if __name__ == "__main__":
    main()