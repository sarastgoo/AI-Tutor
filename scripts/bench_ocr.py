# bench_ocr.py
# Benchmark PaddleOCR PP-OCRv5 mobile on the sample PDF (PaddleOCR 3.x API)

import time
import json
import os
import psutil
from datetime import datetime

PROJECT_ROOT = r"C:\Projects\ai-english-tutor"
PDF_PATH = os.path.join(PROJECT_ROOT, "scripts", "fixtures", "Book.pdf")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "benchmark-results")
os.makedirs(RESULTS_DIR, exist_ok=True)

def get_ram_mb():
    return psutil.Process().memory_info().rss / (1024 * 1024)

def render_pdf_page(pdf_path, page_num, dpi=250):
    import pymupdf
    doc = pymupdf.open(pdf_path)
    page = doc[page_num]
    mat = pymupdf.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    out_path = os.path.join(RESULTS_DIR, f"page_{page_num+1:04d}.png")
    pix.save(out_path)
    doc.close()
    return out_path, pix.width, pix.height

def extract_text_from_result(result):
    """Extract (text, confidence) pairs from PaddleOCR 3.x result object."""
    lines = []
    if not result:
        return lines

    for res in result:
        # PaddleOCR 3.x returns OCRResult objects (dict subclass)
        # The actual detection data is in 'res' key or directly in the dict
        data = {}
        if isinstance(res, dict):
            data = res
        elif hasattr(res, "json"):
            # OCRResult has .json property returning the dict
            try:
                data = res.json
            except Exception:
                data = {}
        elif hasattr(res, "__getitem__"):
            try:
                data = res["res"]
            except Exception:
                data = {}

        if not isinstance(data, dict):
            continue

        # Try common keys for text and scores
        texts = data.get("rec_texts") or data.get("texts") or []
        scores = data.get("rec_scores") or data.get("scores") or []
        for i, txt in enumerate(texts):
            sc = float(scores[i]) if i < len(scores) else 0.0
            lines.append({"text": str(txt), "confidence": round(sc, 3)})

    return lines

def main():
    print("=== OCR Benchmark: PaddleOCR PP-OCRv5 mobile (PaddleOCR 3.x) ===")
    print(f"Start: {datetime.now().isoformat()}")
    print()

    if not os.path.exists(PDF_PATH):
        print(f"ERROR: PDF not found at {PDF_PATH}")
        return

    # Render 3 pages
    print("Rendering pages 1, 2, 3 at 250 DPI...")
    pages = []
    for pn in [0, 1, 2]:
        path, w, h = render_pdf_page(PDF_PATH, pn, dpi=250)
        pages.append((path, w, h))
        print(f"  Page {pn+1}: {w}x{h} -> {path}")

    # Init OCR — force MOBILE models (lighter)
    print()
    print("Initializing PaddleOCR with mobile models...")
    t0 = time.time()
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(
        lang="en",
        text_detection_model_name="PP-OCRv5_mobile_det",
        text_recognition_model_name="PP-OCRv5_mobile_rec",
        use_textline_orientation=False,
        device="cpu",
        enable_mkldnn=False,   # avoid oneDNN bug on Windows
    )
    init_time = time.time() - t0
    print(f"Init: {init_time:.1f} s")

    # Warm-up
    print("Warm-up on page 1...")
    _ = list(ocr.predict(pages[0][0]))
    print()

    # Benchmark each page
    results = {"init_time_s": round(init_time, 2), "pages": []}
    total_boxes = 0
    total_chars = 0
    t_total = 0.0

    for i, (path, w, h) in enumerate(pages, start=1):
        print(f"Page {i} ({w}x{h})...")
        t0 = time.time()
        result = list(ocr.predict(path))
        elapsed = time.time() - t0
        t_total += elapsed

        lines = extract_text_from_result(result)

        n_boxes = len(lines)
        n_chars = sum(len(l["text"]) for l in lines)
        total_boxes += n_boxes
        total_chars += n_chars

        results["pages"].append({
            "page": i,
            "size": f"{w}x{h}",
            "time_s": round(elapsed, 2),
            "boxes": n_boxes,
            "chars": n_chars,
            "sample_text": [l["text"] for l in lines[:10]],
        })
        print(f"  {elapsed:.2f} s, {n_boxes} boxes, {n_chars} chars")
        for line in lines[:3]:
            print(f"    [{line['confidence']:.2f}] {line['text'][:80]}")

    results["summary"] = {
        "total_time_s": round(t_total, 2),
        "pages_per_minute": round(len(pages) / t_total * 60, 2) if t_total > 0 else None,
        "total_boxes": total_boxes,
        "total_chars": total_chars,
    }
    results["ram_peak_mb"] = round(get_ram_mb(), 0)
    results["timestamp"] = datetime.now().isoformat()

    print()
    print("=== Summary ===")
    print(json.dumps(results["summary"], indent=2))

    out_path = os.path.join(RESULTS_DIR, "ocr-benchmark.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to: {out_path}")

if __name__ == "__main__":
    main()