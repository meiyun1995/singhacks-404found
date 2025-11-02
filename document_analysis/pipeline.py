"""
Document Analysis Pipeline
Integrates image analysis, reverse search, and synthetic image detection
"""

import os
import json
import base64
import pymupdf
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Import the individual analysis modules
from groq import Groq
from image_analysis import analyze_image
from reverse_search import reverse_image_search_gcv, assess_image_authenticity
from synthetic_image_detection import detect_deepfake
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def analyze_document_image(
    image_path: str,
    deepfake_threshold: float = 0.8,
    perform_reverse_search: bool = True,
) -> Dict[str, Any]:
    """
    Comprehensive document image analysis pipeline.

    Performs:
    1. Image analysis (text extraction, metadata, quality checks)
    2. Reverse image search (to find similar images online)
    3. Synthetic image detection (deepfake detection)

    Args:
        image_path: Path to the image file
        deepfake_threshold: Confidence threshold for real/fake classification (default: 0.8)
        perform_reverse_search: Whether to perform reverse image search (default: True)
        max_reverse_results: Maximum number of reverse search results (default: 5)

    Returns:
        Comprehensive JSON analysis including all three components
    """

    # Initialize result structure
    result = {
        "metadata": {
            "image_path": image_path,
            "analysis_timestamp": datetime.now().isoformat(),
            "pipeline_version": "1.0.0",
        },
        "image_analysis": {},
        "reverse_search": {},
        "synthetic_detection": {},
        "summary": {},
        "risk_assessment": {},
    }

    try:
        # STEP 1: Image Analysis
        print("📊 Step 1/3: Analyzing image...")
        image_analysis_result = analyze_image(image_path)
        result["image_analysis"] = image_analysis_result

        # STEP 2: Reverse Image Search
        if perform_reverse_search:
            print("🔍 Step 2/3: Performing reverse image search...")
            try:
                result = reverse_image_search_gcv(image_path)
                reverse_search_result = assess_image_authenticity(result)
                result["reverse_search"] = reverse_search_result
            except Exception as e:
                result["reverse_search"] = {
                    "status": "error",
                    "error": str(e),
                    "message": "Reverse search failed",
                }
        else:
            result["reverse_search"] = {
                "status": "skipped",
                "message": "Reverse search disabled",
            }

        # STEP 3: Synthetic Image Detection
        print("🤖 Step 3/3: Detecting synthetic/deepfake content...")
        verdict, confidence, deepfake_results = detect_deepfake(
            image_path, threshold=deepfake_threshold
        )

        result["synthetic_detection"] = {
            "verdict": verdict,
            "confidence": confidence,
            "threshold_used": deepfake_threshold,
            "all_predictions": deepfake_results,
            "is_synthetic": verdict == "FAKE",
        }

        # STEP 4: Generate Summary and Risk Assessment
        print("📋 Generating summary and risk assessment...")
        result["summary"] = _generate_summary(result)
        result["risk_assessment"] = _assess_risk(result)

        # Mark overall status as success
        result["status"] = "success"

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        result["error_type"] = type(e).__name__

    return result


def _generate_summary(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a concise summary of all findings"""

    summary = {"key_findings": [], "flags": [], "confidence_scores": {}}

    # Synthetic detection summary
    synthetic = analysis_result.get("synthetic_detection", {})
    if synthetic.get("is_synthetic"):
        summary["flags"].append(
            f"🚨 SYNTHETIC IMAGE DETECTED (confidence: {synthetic.get('confidence', 0):.2%})"
        )
        summary["key_findings"].append(
            "Image appears to be AI-generated or manipulated"
        )
    else:
        summary["key_findings"].append("Image appears to be authentic/real")

    summary["confidence_scores"]["authenticity"] = synthetic.get("confidence", 0)

    # Reverse search summary
    reverse = analysis_result.get("reverse_search", {})
    if reverse.get("status") == "success":
        num_matches = len(reverse.get("results", []))
        if num_matches > 0:
            summary["flags"].append(f"ℹ️ Found {num_matches} similar images online")
            summary["key_findings"].append(
                f"Image has {num_matches} similar matches on the internet"
            )

    # Image analysis summary
    img_analysis = analysis_result.get("image_analysis", {})
    if img_analysis.get("extracted_text"):
        summary["key_findings"].append(
            f"Contains text: {len(img_analysis.get('extracted_text', []))} segments"
        )

    if img_analysis.get("metadata"):
        summary["key_findings"].append("Metadata available for verification")

    return summary


def _assess_risk(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """Assess overall risk level based on all findings"""

    risk_factors = []
    risk_score = 0.0

    # Check synthetic detection
    synthetic = analysis_result.get("synthetic_detection", {})
    if synthetic.get("is_synthetic"):
        risk_factors.append(
            {
                "factor": "Synthetic/Deepfake Image",
                "severity": "HIGH",
                "confidence": synthetic.get("confidence", 0),
                "weight": 0.6,
            }
        )
        risk_score += 0.6

    # Check reverse search results
    reverse = analysis_result.get("reverse_search", {})
    if reverse.get("status") == "success":
        num_matches = len(reverse.get("results", []))
        if num_matches > 10:
            risk_factors.append(
                {
                    "factor": "Widely distributed image",
                    "severity": "MEDIUM",
                    "detail": f"{num_matches} matches found",
                    "weight": 0.2,
                }
            )
            risk_score += 0.2
        elif num_matches > 0:
            risk_factors.append(
                {
                    "factor": "Image found online",
                    "severity": "LOW",
                    "detail": f"{num_matches} matches found",
                    "weight": 0.1,
                }
            )
            risk_score += 0.1

    # Check metadata anomalies
    img_analysis = analysis_result.get("image_analysis", {})
    metadata = img_analysis.get("metadata", {})
    if not metadata or len(metadata) < 3:
        risk_factors.append(
            {
                "factor": "Limited metadata",
                "severity": "LOW",
                "detail": "Missing EXIF data may indicate editing",
                "weight": 0.1,
            }
        )
        risk_score += 0.1

    # Determine overall risk level
    if risk_score >= 0.7:
        risk_level = "HIGH"
    elif risk_score >= 0.4:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "overall_risk_level": risk_level,
        "risk_score": min(risk_score, 1.0),  # Cap at 1.0
        "risk_factors": risk_factors,
        "recommendation": _get_recommendation(risk_level, risk_factors),
    }


def _get_recommendation(risk_level: str, risk_factors: list) -> str:
    """Generate recommendation based on risk level"""

    if risk_level == "HIGH":
        return "⛔ REJECT - Document requires manual review and verification. High risk of fraud or manipulation detected."
    elif risk_level == "MEDIUM":
        return "⚠️ REVIEW - Additional verification recommended. Escalate to compliance team for manual review."
    else:
        return "✅ ACCEPT - Document appears legitimate. Proceed with standard verification procedures."


def analyze_and_export_to_llm(
    image_path: str, output_file: Optional[str] = None, **kwargs
) -> Dict[str, Any]:
    """
    Analyze image and prepare JSON output for LLM consumption.

    Args:
        image_path: Path to image file
        output_file: Optional path to save JSON output (default: auto-generated)
        **kwargs: Additional arguments passed to analyze_document_image()

    Returns:
        Analysis result ready for LLM
    """

    # Perform comprehensive analysis
    result = analyze_document_image(image_path, **kwargs)

    # Add LLM-specific formatting
    llm_payload = {
        "analysis_result": result,
        "llm_prompt_context": _generate_llm_context(result),
        "structured_data": _extract_structured_data(result),
    }

    # Save to file if requested
    if output_file:
        output_path = Path(output_file)
    else:
        # Auto-generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_name = Path(image_path).stem
        output_path = Path(f"analysis_{image_name}_{timestamp}.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(llm_payload, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Analysis complete! JSON saved to: {output_path}")

    return llm_payload


def _generate_llm_context(result: Dict[str, Any]) -> str:
    """Generate context text for LLM prompt"""

    summary = result.get("summary", {})
    risk = result.get("risk_assessment", {})

    context = f"""Document Image Analysis Results:

Risk Level: {risk.get('overall_risk_level', 'UNKNOWN')}
Risk Score: {risk.get('risk_score', 0):.2%}

Key Findings:
"""

    for finding in summary.get("key_findings", []):
        context += f"- {finding}\n"

    if summary.get("flags"):
        context += "\nFlags:\n"
        for flag in summary["flags"]:
            context += f"- {flag}\n"

    context += f"\nRecommendation: {risk.get('recommendation', 'N/A')}"

    return context


def _extract_structured_data(result: Dict[str, Any]) -> Dict[str, Any]:
    """Extract key structured data for LLM consumption"""

    return {
        "is_synthetic": result.get("synthetic_detection", {}).get(
            "is_synthetic", False
        ),
        "authenticity_confidence": result.get("synthetic_detection", {}).get(
            "confidence", 0
        ),
        "risk_level": result.get("risk_assessment", {}).get(
            "overall_risk_level", "UNKNOWN"
        ),
        "risk_score": result.get("risk_assessment", {}).get("risk_score", 0),
        "has_online_matches": len(result.get("reverse_search", {}).get("results", []))
        > 0,
        "num_online_matches": len(result.get("reverse_search", {}).get("results", [])),
        "extracted_text": result.get("image_analysis", {}).get("extracted_text", []),
        "has_metadata": bool(result.get("image_analysis", {}).get("metadata")),
    }


def document_analysis_reporter(image_path: str):
    """Send the prepared analysis to Groq LLM for further processing"""
    llm_ready_output = analyze_and_export_to_llm(
        image_path=image_path, deepfake_threshold=0.8, perform_reverse_search=True
    )
    system_prompt = f"""
    You are a document forensics expert. Analyze the following document analysis results and provide a detailed report highlighting any risks, anomalies, or recommendations.
    Ensure that ALL anomalies are stated clearly in the report.
    {llm_ready_output}
    """
    # send to groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    groq_response = client.chat.completions.create(
        model="meta-llama/llama-4-maverick-17b-128e-instruct",
        messages=[{"role": "user", "content": system_prompt}],
    )
    groq_response = groq_response.choices[0].message.content
    # save to report folder
    report_folder = Path("reports")
    report_folder.mkdir(exist_ok=True)
    report_path = report_folder / f"report_{Path(image_path).stem}.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(groq_response)

    return groq_response


# Example usage
if __name__ == "__main__":
    images = []
    document_path = "data/Loan Contract_3 to 26(part 2).pdf"
    file_name, _ = os.path.splitext(document_path)

    zoom_matrix = pymupdf.Matrix(0.5, 0.5)
    doc = pymupdf.open(document_path)
    
    for idx, page in enumerate(doc):
        pix = page.get_pixmap(matrix = zoom_matrix)
        image_path = f"{file_name}_{idx}.png"
        pix.save(image_path)
        images.append(image_path)

    # # Example 1: Analyze with all features
    # image_path = "/Users/chuameiyun/Documents/singhacks-404found/data/Swiss_Home_Purchase_Agreement_Scanned_Noise_forparticipants.png"

    for image_path in images:
        print("🚀 Starting comprehensive document analysis...")
        print("=" * 60)

        # Perform analysis and export for LLM
        report = document_analysis_reporter(image_path)
        # Display summary
        print("\n" + "=" * 60)
        print("📊 ANALYSIS SUMMARY")
        print("=" * 60)
        print(report)

# TODO: add another agent to stitch and summarize the report for all the pages into 1 report