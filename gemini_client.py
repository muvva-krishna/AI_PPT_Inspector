import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# You can change models here if needed; kept as in original file
MODEL_VISION = "gemini-2.5-flash"
MODEL_TEXT = "gemini-2.5-flash"
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
HEADERS = {"Content-Type": "application/json"}


def _post_generate(model, contents, timeout=70):
    """
    Minimal wrapper around the Gen-Lang HTTP endpoint.
    'contents' should match the previous structure expected by your setup.
    This function keeps the same signature as your previous code.
    """
    if not API_KEY:
        raise ValueError("GEMINI_API_KEY not set.")
    url = f"{BASE_URL}/{model}:generateContent?key={API_KEY}"
    resp = requests.post(url, json={"contents": contents}, timeout=timeout, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def _safe_extract_text(resp_json):
    """
    Extract textual parts in a robust way from a response payload similar to
    what the earlier code expected (candidates -> content -> parts).
    """
    try:
        # defensive navigation through expected structure
        if not isinstance(resp_json, dict):
            return ""
        candidates = resp_json.get("candidates") or []
        if not candidates:
            # Some endpoints return a top-level 'content' object
            content = resp_json.get("content")
            if isinstance(content, dict):
                parts = content.get("parts") or []
            else:
                return ""
        else:
            content = candidates[0].get("content") or {}
            parts = content.get("parts") or []

        texts = []
        for p in parts:
            if isinstance(p, dict):
                text = p.get("text")
                if text:
                    texts.append(text)
        return "\n".join(texts).strip()
    except Exception:
        return ""


def extract_slide_with_gemini(slide_text, slide_images_b64):
    """
    Given raw slide text and a list of base64-encoded images, ask Gemini to
    return a strict JSON with a single key: "slide_text".
    If the API/KEY is missing or something fails, fallback to returning the provided slide_text.
    """
    # defensive: ensure strings
    slide_text = slide_text or ""
    if not isinstance(slide_text, str):
        slide_text = str(slide_text)

    prompt = (
        "You are a precise slide reader. Read the provided slide text and attached images. "
        "Return STRICT JSON exactly in this shape: {\"slide_text\": \"<transcribed/combined text>\"}. "
        "Preserve numbers, units, and short claims exactly. Do not add other keys."
    )

    # parts structure follows previous usage in repository
    parts = [{"text": prompt}, {"text": slide_text}]
    for img_b64 in (slide_images_b64 or []):
        parts.append({"inline_data": {"mime_type": "image/png", "data": img_b64}})

    # The request body shape mirrors previous code to keep compatibility.
    req_content = [{"role": "user", "parts": parts}]

    try:
        resp_json = _post_generate(MODEL_VISION, req_content)
    except Exception as e:
        # fallback: return the original text if API failed
        return {"slide_text": slide_text}

    text_out = _safe_extract_text(resp_json)
    # Try to extract JSON substring from the model output (robust)
    if not text_out:
        return {"slide_text": slide_text}
    try:
        # find first '{' and last '}' to isolate JSON-like response
        start = text_out.find("{")
        end = text_out.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text_out[start:end+1]
            parsed = json.loads(candidate)
            if "slide_text" in parsed:
                return {"slide_text": parsed["slide_text"]}
    except Exception:
        pass

    # If model returned plain text instead of JSON, return it as slide_text
    return {"slide_text": text_out or slide_text}


def compare_slides_with_gemini(all_slides):
    """
    all_slides: list of {"slide_number": int, "slide_text": str}

    Returns a dict: { "issues": [...], "suggestions": [...] }
    The model is asked to return strict JSON following the existing schema.
    """
    if not isinstance(all_slides, list):
        raise ValueError("all_slides must be a list")

    slides_payload = "\n".join(
        f"--- SLIDE {s['slide_number']} ---\n{s['slide_text']}\n" for s in all_slides
    )

    prompt = (
        "You are an expert fact and consistency checker for slide decks.\n"
        "Identify:\n"
        "1) Intra-slide errors (contradictions, impossible numbers)\n"
        "2) Cross-slide inconsistencies (same metric different values, unit mismatches, timeline conflicts)\n"
        "3) Always return at least 1 suggestion even if no issues.\n"
        "Return ONLY valid JSON in this schema:\n"
        "{ \"issues\": [{\"slides\": [1,2], \"description\": \"...\", \"suggestion\": \"...\"}], "
        "\"suggestions\": [\"...\"] }"
    )

    req_content = [{"role": "user", "parts": [{"text": f"{prompt}\n\n{slides_payload}"}]}]

    try:
        resp_json = _post_generate(MODEL_TEXT, req_content, timeout=90)
    except Exception:
        # If API unavailable, return a sensible fallback
        return {"issues": [], "suggestions": ["Could not reach Gemini API to perform automated checks. Please review slides manually."]}

    text_out = _safe_extract_text(resp_json)
    if not text_out:
        return {"issues": [], "suggestions": ["No output from Gemini while comparing slides."]}

    try:
        start = text_out.find("{")
        end = text_out.rfind("}")
        if start != -1 and end != -1 and end > start:
            parsed = json.loads(text_out[start:end+1])
            return {
                "issues": parsed.get("issues", []),
                "suggestions": parsed.get("suggestions", [])
            }
    except Exception:
        pass

    # fallback default
    return {"issues": [], "suggestions": ["Review all numerical values and ensure consistency across slides."]}
