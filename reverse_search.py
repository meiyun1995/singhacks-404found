import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Tell Google client libs where to find your credentials
cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not cred_path or not os.path.exists(cred_path):
    raise FileNotFoundError("Missing or invalid GOOGLE_APPLICATION_CREDENTIALS path in .env")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path

from google.cloud import vision

def reverse_image_search_gcv(image_path_or_url: str):
    client = vision.ImageAnnotatorClient()

    if image_path_or_url.startswith(("http://", "https://")):
        image = vision.Image()
        image.source.image_uri = image_path_or_url
    else:
        with open(image_path_or_url, "rb") as f:
            image = vision.Image(content=f.read())

    resp = client.web_detection(image=image)
    if resp.error.message:
        raise RuntimeError(resp.error.message)

    web = resp.web_detection
    result = {
        "pages_with_matching_images": [p.url for p in web.pages_with_matching_images],
        "full_matching_images": [i.url for i in web.full_matching_images],
        "partial_matching_images": [i.url for i in web.partial_matching_images],
        "visually_similar_images": [i.url for i in web.visually_similar_images],
        "best_guess_labels": [l.label for l in web.best_guess_labels],
        "web_entities": [{"desc": e.description, "score": e.score} for e in web.web_entities],
    }
    return result

def assess_image_authenticity(result: dict) -> dict:
    """
    Assess authenticity of an image using Google Vision Web Detection results.

    Input: result (dict) from reverse_image_search_gcv()
    Output: structured forensic judgment
    """
    pages = result.get("pages_with_matching_images", [])
    full = result.get("full_matching_images", [])
    partial = result.get("partial_matching_images", [])
    similar = result.get("visually_similar_images", [])
    web_entities = result.get("web_entities", [])

    # Direct evidence of duplication
    if pages or full or partial:
        evidence_links = pages + full + partial
        confidence = min(1.0, 0.8 + 0.05 * len(evidence_links))
        return {
            "authenticity_verdict": "Possibly Stolen or Reused",
            "confidence": round(confidence, 2),
            "evidence_links": evidence_links,
            "reason": "Exact or partial duplicates were found online."
        }

    # No exact match but some visually similar ones
    elif similar:
        confidence = 0.6
        return {
            "authenticity_verdict": "⚠️ No exact matches, but visually similar images found",
            "confidence": confidence,
            "evidence_links": similar,
            "reason": "Visually similar images exist online, though not identical."
        }

    # No signals found — likely authentic / private
    else:
        confidence = 0.95
        return {
            "authenticity_verdict": "Likely Authentic / Not found online",
            "confidence": confidence,
            "evidence_links": [],
            "reason": "No online matches or duplicates detected."
        }


result = reverse_image_search_gcv("1761982583131.jpg")
print(assess_image_authenticity(result))