"""OCR Service: PDF rendering + PaddleOCR text extraction."""
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pymupdf
from paddleocr import PaddleOCR


@dataclass
class OCRBlock:
    """One text block detected by OCR."""
    text: str
    confidence: float
    bbox: list[list[float]]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]


@dataclass
class OCRPageResult:
    """Result of OCR on a single page."""
    page_number: int
    width: int
    height: int
    blocks: list[OCRBlock] = field(default_factory=list)
    elapsed_s: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "page_number": self.page_number,
            "width": self.width,
            "height": self.height,
            "elapsed_s": round(self.elapsed_s, 2),
            "blocks": [
                {
                    "text": b.text,
                    "confidence": b.confidence,
                    "bbox": [[float(coord) for coord in point] for point in b.bbox],  # <--- تبدیل به float
                }
                for b in self.blocks
            ],
        }


class OCRService:
    """Encapsulates PaddleOCR with mobile models (from P0 benchmark)."""

    def __init__(self, lang: str = "en") -> None:
        base_dir = r"C:\Projects\ai-english-tutor\models"
        
        self._ocr = PaddleOCR(
            lang=lang,
            # ✅ مسیر پوشه را بدهید
            text_detection_model_dir=fr"{base_dir}\PP-OCRv5_mobile_det",
            text_recognition_model_dir=fr"{base_dir}\PP-OCRv5_mobile_rec",
            # ✅ نام مدل را هم صریحاً بگویید تا با محتوای پوشه هماهنگ باشد
            text_detection_model_name="PP-OCRv5_mobile_det",
            text_recognition_model_name="PP-OCRv5_mobile_rec",
            use_textline_orientation=False,
            device="cpu",
            enable_mkldnn=False,
            use_doc_unwarping=False,
            use_doc_orientation_classify=False,
        )

    def render_pdf_page(self, pdf_path: Path, page_num: int, dpi: int = 250) -> tuple[Path, int, int]:
        """Render a single PDF page to PNG. Returns (path, width, height)."""
        doc = pymupdf.open(pdf_path)
        page = doc[page_num]
        mat = pymupdf.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        
        out_path = Path(os.getenv("STORAGE_ROOT", r"C:\Projects\ai-english-tutor\storage")) / f"temp_page_{page_num + 1:04d}.png"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        pix.save(out_path)
        doc.close()
        return out_path, pix.width, pix.height

    def run_ocr(self, image_path: Path) -> list[OCRBlock]:
        """Run OCR on an image file, return extracted blocks."""
        result = list(self._ocr.predict(str(image_path)))
        blocks: list[OCRBlock] = []
        if not result:
            return blocks

        for res in result:
            # PaddleOCR 3.x returns dict-like objects
            data = res if isinstance(res, dict) else (res.json if hasattr(res, "json") else {})
            texts = data.get("rec_texts", [])
            scores = data.get("rec_scores", [])
            boxes = data.get("rec_boxes", [])  # list of [x1,y1,x2,y2] or polygons

            for txt, sc, box in zip(texts, scores, boxes):
                # Convert box to polygon if it's a rectangle
                if len(box) == 4 and not isinstance(box[0], list):
                    x1, y1, x2, y2 = box
                    polygon = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
                else:
                    polygon = box
                
                blocks.append(OCRBlock(
                    text=str(txt),
                    confidence=float(sc),
                    bbox=[[float(coord) for coord in point] for point in polygon], # <--- تبدیل به float
                ))
        return blocks

    def process_page(self, pdf_path: Path, page_num: int, dpi: int = 250) -> OCRPageResult:
        """Full pipeline for one page: render + OCR."""
        t0 = time.time()
        img_path, w, h = self.render_pdf_page(pdf_path, page_num, dpi)
        blocks = self.run_ocr(img_path)
        elapsed = time.time() - t0
        
        # Cleanup temp image
        if img_path.exists():
            img_path.unlink()

        return OCRPageResult(
            page_number=page_num + 1,
            width=w,
            height=h,
            blocks=blocks,
            elapsed_s=elapsed,
        )