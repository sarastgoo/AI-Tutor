"""Quick OCR test on the fixture PDF."""
import json
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.services.ocr_service import OCRService


def main():
    pdf_path = Path(r"C:\Projects\ai-english-tutor\scripts\fixtures\Book.pdf")
    if not pdf_path.exists():
        print(f"ERROR: PDF not found at {pdf_path}")
        return 1

    print("Initializing OCR service...")
    ocr = OCRService(lang="en")

    print(f"Processing pages 1-3 of {pdf_path.name}...")
    results = []
    for page_num in range(3):
        print(f"  Page {page_num + 1}...", end="", flush=True)
        res = ocr.process_page(pdf_path, page_num, dpi=250)
        print(f" {len(res.blocks)} blocks in {res.elapsed_s:.2f}s")
        results.append(res.to_dict())

    out_path = Path(r"C:\Projects\ai-english-tutor\benchmark-results\p2_ocr_test.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to {out_path}")
    print("\nSample from Page 1:")
    for b in results[0]["blocks"][:5]:
        print(f"  [{b['confidence']:.2f}] {b['text'][:80]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())