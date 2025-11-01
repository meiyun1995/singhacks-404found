from transformers import pipeline
from typing import Dict, List, Tuple

# Initialize the model pipeline once (outside the function for efficiency)
deepfake_detector = pipeline(
    "image-classification", model="prithivMLmods/deepfake-detector-model-v1"
)


def detect_deepfake(
    image_path: str, threshold: float = 0.8
) -> Tuple[str, float, List[Dict[str, float]]]:
    """
    Detect if an image is a deepfake using a pre-trained model.

    Args:
        image_path: Path to the image file to analyze
        threshold: Confidence threshold for REAL classification (default: 0.8)
                  If REAL score >= threshold, classify as REAL, otherwise FAKE

    Returns:
        Tuple containing:
        - verdict: "REAL" or "FAKE"
        - confidence: Score of the verdict (0.0 to 1.0)
        - results: Full list of predictions with labels and confidence scores
    """
    results = deepfake_detector(image_path)

    # Find the REAL score
    real_score = 0.0
    for prediction in results:
        if prediction["label"].upper() == "REAL":
            real_score = prediction["score"]
            break

    # Apply threshold check
    if real_score >= threshold:
        verdict = "REAL"
        confidence = real_score
    else:
        verdict = "FAKE"
        confidence = 1.0 - real_score  # Fake confidence is inverse of real

    return verdict, confidence, results


# Example usage
if __name__ == "__main__":
    image_path = "/Users/chuameiyun/Documents/singhacks-404found/Screenshot 2025-11-01 at 5.22.37 PM.png"

    # Test with default threshold (0.8)
    verdict, confidence, results = detect_deepfake(image_path)

    print(f"\n🔍 Deepfake Detection Results for: {image_path}")
    print("=" * 60)
    print(f"\nAll Predictions:")
    for prediction in results:
        label = prediction["label"]
        score = prediction["score"]
        percentage = score * 100
        print(f"   {label}: {percentage:.2f}%")

    print(f"\n📊 Verdict (threshold: 0.8):")
    print(f"   Classification: {verdict}")
    print(f"   Confidence: {confidence:.2%}")

    if verdict == "FAKE":
        print("\n⚠️  WARNING: This image is likely a DEEPFAKE!")
    else:
        print("\n✅ This image appears to be REAL.")
