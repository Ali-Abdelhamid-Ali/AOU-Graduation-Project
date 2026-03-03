# multimodal_distill_cohere.py
# PDF folder -> image + nearby text context -> Cohere Command A Vision -> JSONL distilled chunks
# الهدف: كل صورة تتحول لـ "chunk نصي" (Context + Explanation) بحيث بعد كده مش محتاج الصورة للتدريب.

from __future__ import annotations

import os
import json
import base64
import hashlib
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

import fitz  # PyMuPDF
from PIL import Image

from dotenv import load_dotenv
from tqdm import tqdm

import cohere

# -----------------------------
# Settings
# -----------------------------
SUPPORTED_EXTS = {".pdf"}

# how much nearby text to keep
MAX_CONTEXT_CHARS = 2200

# distance threshold (PDF points) for "nearby"
NEAR_DIST = 160

# fallback: if nothing within NEAR_DIST, take K nearest text blocks
FALLBACK_NEAREST_BLOCKS = 8

# render quality
RENDER_DPI = 220

# Cohere model
COHERE_MODEL = "command-a-vision-07-2025"

# output json fields, keep conservative max tokens
MAX_TOKENS = 320

# Optional OCR (safe fallback if not installed)
USE_OCR = True


# -----------------------------
# Helpers
# -----------------------------
def safe_render_image(page: fitz.Page, img_rect: fitz.Rect, out_path: Path, dpi: int = 220) -> bool:
    """
    يحاول يحفظ صورة bbox بأمان.
    1) clip pixmap
    2) لو فشل: render الصفحة كاملة ثم crop
    يرجّع True لو نجح، False لو فشل.
    """
    try:
        # تأمين bbox داخل الصفحة
        page_rect = page.rect
        r = fitz.Rect(img_rect)
        r = r & page_rect  # intersection
        if r.is_empty or r.width < 2 or r.height < 2:
            return False

        # محاولة 1: clip مباشرة
        try:
            pix = page.get_pixmap(clip=r, dpi=dpi, alpha=False)
            if pix.width < 2 or pix.height < 2:
                raise RuntimeError("pixmap too small")
            pix.save(str(out_path))
            return True
        except Exception:
            pass

        # محاولة 2: render الصفحة كاملة ثم crop بالـ bbox
        mat = fitz.Matrix(dpi / 72.0, dpi / 72.0)
        full = page.get_pixmap(matrix=mat, alpha=False)

        # تحويل bbox لإحداثيات على الصورة المرسومة
        scale = dpi / 72.0
        x0 = int(max(0, r.x0 * scale))
        y0 = int(max(0, r.y0 * scale))
        x1 = int(min(full.width, r.x1 * scale))
        y1 = int(min(full.height, r.y1 * scale))

        if (x1 - x0) < 2 or (y1 - y0) < 2:
            return False

        # PyMuPDF pixmap has .samples -> bytes
        mode = "RGB" if full.n < 4 else "RGBA"
        img = Image.frombytes(mode, (full.width, full.height), full.samples)
        crop = img.crop((x0, y0, x1, y1)).convert("RGB")
        crop.save(out_path)
        return True

    except Exception:
        return False

def stable_id(*parts: str) -> str:
    h = hashlib.sha256("||".join(parts).encode("utf-8")).hexdigest()
    return h[:16]

def clamp_text(s: str, n: int) -> str:
    s = " ".join((s or "").split())
    return s[:n] if len(s) > n else s

def rect_center(r: fitz.Rect) -> Tuple[float, float]:
    return (float((r.x0 + r.x1) / 2), float((r.y0 + r.y1) / 2))

def l2(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5

def image_to_data_url(png_path: Path) -> str:
    # Cohere accepts image_url as a URL; data URL works in many SDK patterns.
    # If your account/config rejects data URLs, switch to hosting or file upload approach.
    b = png_path.read_bytes()
    b64 = base64.b64encode(b).decode("utf-8")
    return f"data:image/png;base64,{b64}"

def try_ocr_text(image_path: Path) -> str:
    if not USE_OCR:
        return ""
    try:
        # Preferred lightweight OCR option
        from rapidocr_onnxruntime import RapidOCR
        ocr = RapidOCR()
        img = Image.open(image_path).convert("RGB")
        res, _ = ocr(img)
        if not res:
            return ""
        # res: list of [box, text, score]
        texts = []
        for item in res:
            if len(item) >= 2:
                txt = (item[1] or "").strip()
                if txt:
                    texts.append(txt)
        return clamp_text(" | ".join(texts), 800)
    except Exception:
        return ""


def extract_cohere_text(response: Any) -> str:
    """
    Cohere SDK content shape can vary by version/object type.
    Collect all text parts defensively.
    """
    message = getattr(response, "message", None)
    content = getattr(message, "content", None)

    if isinstance(content, str):
        return content.strip()

    if not isinstance(content, list):
        return ""

    parts: List[str] = []
    for item in content:
        if isinstance(item, str):
            if item.strip():
                parts.append(item.strip())
            continue

        if isinstance(item, dict):
            txt = item.get("text")
            if isinstance(txt, str) and txt.strip():
                parts.append(txt.strip())
            continue

        txt = getattr(item, "text", None)
        if isinstance(txt, str) and txt.strip():
            parts.append(txt.strip())

    return "\n".join(parts).strip()


def parse_json_object_with_fallback(raw_text: str) -> Tuple[Dict[str, Any], bool]:
    """
    Try strict JSON first, then repair common issues:
    - markdown code fences
    - leading/trailing non-JSON text
    - trailing commas before } or ]
    """
    text = (raw_text or "").replace("\ufeff", "").strip()
    if not text:
        return {}, True

    candidates: List[str] = [text]

    no_fences = re.sub(r"^\s*```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    no_fences = re.sub(r"\s*```\s*$", "", no_fences).strip()
    if no_fences and no_fences != text:
        candidates.append(no_fences)

    src = no_fences if no_fences else text
    start = src.find("{")
    end = src.rfind("}")
    if start != -1 and end != -1 and end > start:
        obj_slice = src[start : end + 1]
        candidates.append(obj_slice)
        candidates.append(re.sub(r",(\s*[}\]])", r"\1", obj_slice))

    seen = set()
    for cand in candidates:
        c = cand.strip()
        if not c or c in seen:
            continue
        seen.add(c)
        try:
            parsed = json.loads(c)
            if isinstance(parsed, dict):
                return parsed, False
        except Exception:
            continue

    # Last-resort object so pipeline continues.
    return {
        "bullets": [],
        "summary": clamp_text(src, 1200),
        "confidence": "low",
        "safety_notes": "Model returned non-strict JSON; used fallback parser.",
    }, True


def normalize_model_output(parsed: Dict[str, Any]) -> Dict[str, Any]:
    bullets_raw = parsed.get("bullets", [])
    if isinstance(bullets_raw, str):
        bullets_raw = [bullets_raw]
    if not isinstance(bullets_raw, list):
        bullets_raw = []

    bullets = [clamp_text(str(b).strip(), 240) for b in bullets_raw if str(b).strip()]
    bullets = bullets[:10]

    summary = clamp_text(str(parsed.get("summary", "")).strip(), 1200)
    if not summary and bullets:
        summary = clamp_text(" ".join(bullets), 1200)

    confidence = str(parsed.get("confidence", "low")).strip().lower()
    if confidence not in {"high", "medium", "low"}:
        confidence = "low"

    safety_notes = clamp_text(str(parsed.get("safety_notes", "")).strip(), 400)

    return {
        "bullets": bullets,
        "summary": summary,
        "confidence": confidence,
        "safety_notes": safety_notes,
    }


# -----------------------------
# Data classes
# -----------------------------
@dataclass
class ImageContextPack:
    uid: str
    source_file: str
    page: int
    image_path: str
    context_text: str

@dataclass
class DistilledChunk:
    uid: str
    source_file: str
    page: int
    context_text: str
    ocr_text: str
    image_explanation: str
    confidence: str
    safety_notes: str
    final_chunk_text: str


# -----------------------------
# Extract images + nearby text (PDF)
# -----------------------------
def extract_image_contexts_from_pdf(
    pdf_path: Path,
    images_out_dir: Path,
    max_context_chars: int = MAX_CONTEXT_CHARS,
    near_dist: float = NEAR_DIST,
) -> List[ImageContextPack]:
    images_out_dir.mkdir(parents=True, exist_ok=True)
    packs: List[ImageContextPack] = []

    doc = fitz.open(pdf_path)

    for page_idx in range(len(doc)):
        page = doc[page_idx]

        # text blocks
        blocks = page.get_text("blocks")  # (x0, y0, x1, y1, "text", block_no, block_type)
        text_blocks: List[Tuple[fitz.Rect, str]] = []
        for b in blocks:
            r = fitz.Rect(b[0], b[1], b[2], b[3])
            txt = (b[4] if len(b) > 4 else "") or ""
            txt = txt.strip()
            if txt:
                text_blocks.append((r, txt))

        # image blocks (positions)
        d = page.get_text("dict")
        img_blocks = [blk for blk in d.get("blocks", []) if blk.get("type") == 1]

        for img_i, ib in enumerate(img_blocks):
            bbox = ib.get("bbox")
            if not bbox:
                continue

            img_rect = fitz.Rect(*bbox)
            img_center = rect_center(img_rect)

            # render clip
            img_name = f"{pdf_path.stem}_p{page_idx+1:03d}_img{img_i+1:02d}.png"
            img_path = images_out_dir / img_name
            ok = safe_render_image(page, img_rect, img_path, dpi=RENDER_DPI)
            if not ok:
                continue
            
            # collect nearby text
            scored = []
            for (tr, ttxt) in text_blocks:
                dist = l2(img_center, rect_center(tr))
                if dist <= near_dist:
                    scored.append((dist, ttxt, tr.y0))

            if not scored:
                # fallback nearest
                fallback = []
                for (tr, ttxt) in text_blocks:
                    dist = l2(img_center, rect_center(tr))
                    fallback.append((dist, ttxt, tr.y0))
                scored = sorted(fallback, key=lambda x: x[0])[:FALLBACK_NEAREST_BLOCKS]
            else:
                scored = sorted(scored, key=lambda x: x[0])

            # sort by vertical order for readability
            scored_sorted = sorted(scored, key=lambda x: x[2])
            context = "\n".join([t for _, t, _ in scored_sorted])
            context = clamp_text(context, max_context_chars)

            uid = stable_id(str(pdf_path), str(page_idx + 1), img_name)

            packs.append(
                ImageContextPack(
                    uid=uid,
                    source_file=str(pdf_path),
                    page=page_idx + 1,
                    image_path=str(img_path),
                    context_text=context,
                )
            )

    doc.close()
    return packs


# -----------------------------
# Cohere Vision call (JSON output)
# -----------------------------
def cohere_explain_image_json(
    co: cohere.ClientV2,
    image_path: Path,
    context_text: str,
    ocr_text: str,
) -> Dict[str, Any]:
    data_url = image_to_data_url(image_path)

    # Prompting strategy ضد الهلوس:
    # - قيّد: "لا تخمن" + "اربط بالتекст/الـOCR" + "لو مش متأكد قول غير واضح"
    # - اطلب confidence + safety_notes
    system = (
        "You are a careful medical-document assistant. "
        "Describe ONLY what is supported by the image and the provided text. "
        "Do NOT infer diagnosis or medical claims beyond evidence. "
        "If uncertain, state uncertainty explicitly."
    )

    user_text = (
        "Generate a JSON object with these exact keys:\n"
        "- bullets: array of 5-10 short bullet points describing visible elements.\n"
        "- summary: 2-4 sentences grounded in context.\n"
        "- confidence: one of [high, medium, low].\n"
        "- safety_notes: short note about any uncertainty or missing info.\n\n"
        f"CONTEXT:\n{context_text}\n\n"
        f"OCR (optional, may be empty):\n{ocr_text}\n"
    )

    # Cohere image input format in messages content (image_url + text). :contentReference[oaicite:4]{index=4}
    messages = [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        },
    ]

    # Structured Outputs JSON mode. :contentReference[oaicite:5]{index=5}
    res = co.chat(
        model=COHERE_MODEL,
        messages=messages,
        max_tokens=MAX_TOKENS,
        temperature=0.0,
        response_format={"type": "json_object"},
    )

    raw_txt = extract_cohere_text(res)
    parsed, _used_fallback = parse_json_object_with_fallback(raw_txt)
    return normalize_model_output(parsed)


def build_final_chunk(context_text: str, ocr_text: str, parsed: Dict[str, Any]) -> Tuple[str, str, str, str]:
    bullets = parsed.get("bullets", [])
    summary = parsed.get("summary", "")
    confidence = parsed.get("confidence", "low")
    safety_notes = parsed.get("safety_notes", "")

    bullets_txt = "\n".join([f"- {b}" for b in bullets if isinstance(b, str)])
    final = (
        "CONTEXT:\n"
        f"{context_text}\n\n"
        "OCR:\n"
        f"{ocr_text}\n\n"
        "IMAGE_EXPLANATION:\n"
        f"{bullets_txt}\n\n"
        f"SUMMARY:\n{summary}\n\n"
        f"CONFIDENCE: {confidence}\n"
        f"SAFETY_NOTES: {safety_notes}\n"
    )
    return final, bullets_txt, confidence, safety_notes


# -----------------------------
# Main distill folder
# -----------------------------
def distill_folder(input_folder: Path, output_folder: Path):
    output_folder.mkdir(parents=True, exist_ok=True)
    images_out_dir = output_folder / "extracted_images"
    out_path = output_folder / "distilled_chunks.jsonl"

    pdfs = [p for p in input_folder.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS]
    if not pdfs:
        raise RuntimeError(f"No PDFs found in {input_folder}")

    load_dotenv()
    api_key = (os.getenv("COHERE_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("COHERE_API_KEY not found. Put it in .env or environment variables.")

    co = cohere.ClientV2(api_key=api_key)

    total = 0
    with out_path.open("w", encoding="utf-8") as f:
        for pdf in tqdm(pdfs, desc="PDFs"):
            packs = extract_image_contexts_from_pdf(pdf, images_out_dir)

            for pack in tqdm(packs, desc=f"Images in {pdf.name}", leave=False):
                img_path = Path(pack.image_path)

                try:
                    ocr_text = try_ocr_text(img_path)
                    parsed = cohere_explain_image_json(co, img_path, pack.context_text, ocr_text)
                except Exception as e:
                    ocr_text = ""
                    parsed = {
                        "bullets": [],
                        "summary": "",
                        "confidence": "low",
                        "safety_notes": clamp_text(f"Cohere call failed: {type(e).__name__}: {e}", 400),
                    }
                    print(f"[WARN] Failed for {img_path.name} (page {pack.page}): {type(e).__name__}")

                final_text, _bullets_txt, confidence, safety_notes = build_final_chunk(
                    pack.context_text, ocr_text, parsed
                )

                rec = DistilledChunk(
                    uid=pack.uid,
                    source_file=pack.source_file,
                    page=pack.page,
                    context_text=pack.context_text,
                    ocr_text=ocr_text,
                    image_explanation=json.dumps(parsed, ensure_ascii=False),
                    confidence=confidence,
                    safety_notes=safety_notes,
                    final_chunk_text=final_text,
                )

                f.write(json.dumps(asdict(rec), ensure_ascii=False) + "\n")
                total += 1

    print(f"Saved JSONL: {out_path}")
    print(f"Extracted images kept at: {images_out_dir}")
    print(f"Total distilled chunks: {total}")


if __name__ == "__main__":
    INPUT = Path(r"C:\Users\Legion\OneDrive\سطح المكتب\Car--issues22-main\Car--issues\Car--issues\rag data\Mercedes-Benz-TN-T1-1977-1995-Factory-Repair-Manual-EN-DE")
    OUTPUT = Path(r"D:\AMIT\AOU PROJECT\AOU Graduation Project\AOU-Graduation-Project\BioIntellect\AI\fintune\distilled_output")

    distill_folder(INPUT, OUTPUT)
