"""Rule-based skin image analysis (visual, educational only)."""

from PIL import Image, ImageStat, ImageFilter
import io


def _dominant_stats(image):
    """Return brightness, contrast estimate and red prominence."""
    gray = image.convert("L")
    stat = ImageStat.Stat(gray)
    brightness = stat.mean[0]
    contrast = stat.stddev[0]

    rgb = image.convert("RGB")
    r, g, b = rgb.split()
    rs = ImageStat.Stat(r)
    gs = ImageStat.Stat(g)
    bs = ImageStat.Stat(b)
    red_prominence = rs.mean[0] - (gs.mean[0] + bs.mean[0]) / 2.0
    return brightness, contrast, red_prominence


def _quality_report(image):
    """Estimate technical image usability; this is not clinical confidence."""
    width, height = image.size
    gray = image.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edge_contrast = ImageStat.Stat(edges).mean[0]
    stat = ImageStat.Stat(gray)
    brightness = stat.mean[0]
    checks = {
        "image_detected": True,
        "resolution": width >= 300 and height >= 300,
        "lighting": 45 <= brightness <= 220,
        "clarity": edge_contrast >= 8,
        "face_visibility": None,
    }
    score = 100
    if not checks["resolution"]:
        score -= 30
    if not checks["lighting"]:
        score -= 20
    if not checks["clarity"]:
        score -= 25
    # No face-recognition dependency is used; the user can select regions manually.
    quality_note = "Face visibility is not automatically verified; use the manual area map."
    if brightness < 70:
        quality_note = "Slight shadow detected."
    elif brightness > 205:
        quality_note = "Image may be overexposed."
    return {
        "score": max(25, min(98, score)),
        "width": width,
        "height": height,
        "checks": checks,
        "note": quality_note,
        "usable": score >= 55 and checks["resolution"] and checks["lighting"] and checks["clarity"],
    }


def analyze_skin_image(file_storage):
    """Analyze an uploaded face/skin image.

    Returns dict with concerns list, severity, explanation, routines, dermatologist note.
    """
    try:
        file_storage.stream.seek(0)
        image = Image.open(io.BytesIO(file_storage.read())).convert("RGB")
        image.thumbnail((800, 800))
    except Exception as exc:
        return {"error": f"Invalid or unreadable image file: {exc}"}

    brightness, contrast, red_prominence = _dominant_stats(image)
    width, height = image.size
    area = width * height
    pixel_count = area
    quality = _quality_report(image)
    if pixel_count < 150 * 150:
        return {
            "error": "Image quality is insufficient for a useful visual assessment. Please upload a clearer, well-lit image.",
            "quality": quality,
        }
    if not quality["usable"]:
        return {
            "error": "Image quality is insufficient for a useful visual assessment. Please upload a clearer, well-lit image.",
            "quality": quality,
        }

    # HEIC/format check
    if image.mode in ("RGBA", "P") and pixel_count < 200 * 200:
        pass

    concerns = []

    # Redness / irritation detection based on red prominence
    if red_prominence > 18:
        severity = "Moderate" if red_prominence > 30 else "Mild"
        concerns.append({
            "key": "redness",
            "concern": "Redness / Irritation",
            "severity": severity,
            "why_noticed": "The uploaded image contains areas that appear visibly more red than surrounding tones.",
            "explanation": (
                "The image shows elevated red-tone prominence, which can be associated with "
                "redness or irritation. This is a visual heuristic, not a diagnosis."
            ),
        })

    # Oiliness guess: higher brightness + low color variance in skin tone
    if brightness > 150 and contrast < 45 and red_prominence < 10:
        concerns.append({
            "key": "oiliness",
            "concern": "Oiliness (possible)",
            "severity": "Mild",
            "why_noticed": "Bright, low-contrast areas can appear more reflective or oily in this image.",
            "explanation": (
                "Bright, low-contrast skin texture can be associated with an oily appearance. "
                "This is a general heuristic only."
            ),
        })

    # Dryness guess
    if brightness < 90 and contrast > 55:
        concerns.append({
            "key": "dryness",
            "concern": "Dryness (possible)",
            "severity": "Mild",
            "why_noticed": "Some areas show lower brightness with stronger visible texture contrast.",
            "explanation": (
                "Low brightness with high texture contrast can be associated with dry skin. "
                "This is a general heuristic, not a diagnosis."
            ),
        })

    # If no specific concern, return a clean summary rather than empty
    if not concerns:
        concerns.append({
            "key": "none",
            "concern": "No obvious visible concern detected",
            "severity": "None detected",
            "why_noticed": "No strong visible signal was detected by these basic image statistics.",
            "explanation": (
                "Based on basic image statistics no strong redness, dryness, or oiliness signal "
                "was detected. This is not a medical diagnosis."
            ),
        })

    worst_severity = "Unknown"
    order = {"None detected": 0, "Mild": 1, "Moderate": 2, "Severe": 3}
    for c in concerns:
        if order.get(c["severity"], 0) > order.get(worst_severity, -1):
            worst_severity = c["severity"]

    area_observations = {}
    for area_name in ("Forehead", "Left cheek", "Right cheek", "Nose", "Chin"):
        area_observations[area_name] = [c["concern"] for c in concerns if c["key"] != "none"] or ["No obvious visible concern detected"]
    return {
        "concerns": concerns,
        "quality": quality,
        "area_observations": area_observations,
        "visible_summary": "The image shows " + ", ".join(c["concern"].lower() for c in concerns) + ".",
        "overall_severity": worst_severity,
        "brightness": round(brightness, 1),
        "red_prominence": round(red_prominence, 1),
        "morning_routine": [
            "Cleanse with a gentle, fragrance-free cleanser",
            "Apply a light non-comedogenic moisturizer",
            "Use SPF 30+ sunscreen (sun protection)",
        ],
        "evening_routine": [
            "Cleanse gently to remove the day's oil and dirt",
            "Apply a simple moisturizer",
            "Keep skin care simple; avoid harsh scrubs overnight",
        ],
        "dermatologist_note": (
            "If symptoms are persistent, painful, worsening, or causing concern, "
            "please see a dermatologist. We do not make medical diagnoses."
        ),
        "disclaimer": (
            "Dia Assist provides general educational wellness information and does not provide a definitive skin diagnosis."
        ),
    }