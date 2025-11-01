import os, json, base64, pymupdf, datetime
from typing import Optional, Dict, Any, List
import pymupdf
from pathlib import Path

from groq import Groq
from dotenv import load_dotenv

load_dotenv()


def run_document_processing_engine(
    pdf_path: str,
    model: str = "meta-llama/llama-4-maverick-17b-128e-instruct",
    zoom: float = 0.5,
    max_pages: int = 5,
    image_output_root: str = "data/images",
    log_dir: str = "logs",
):
    """
    Document Processing Engine
    - Converts PDF to image(s)
    - Sends each image page to the LLM for structured JSON analysis
    - Saves images under data/images/<file_name>/
    - Logs results to logs/<timestamp>_<file_name>.json
    """

    # --- setup ---
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    os.makedirs(log_dir, exist_ok=True)

    file_name = os.path.splitext(os.path.basename(pdf_path))[0]
    image_dir = os.path.join(image_output_root, file_name)
    os.makedirs(image_dir, exist_ok=True)

    # --- clear existing images if rerun ---
    for f in os.listdir(image_dir):
        os.remove(os.path.join(image_dir, f))

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(log_dir, f"{timestamp}_{file_name}.json")

    # --- PDF → images ---
    doc = pymupdf.open(pdf_path)
    zoom_matrix = pymupdf.Matrix(zoom, zoom)

    image_files = []
    for i, page in enumerate(doc):
        if i >= max_pages:
            break
        pix = page.get_pixmap(matrix=zoom_matrix)
        img_path = os.path.join(image_dir, f"page_{i+1}.png")
        pix.save(img_path)
        image_files.append(img_path)

    # --- System prompt ---
    system_prompt = """
    You are a document analysis engine designed to process and evaluate documents for quality, structure, and compliance.
    Perform:
    - Content extraction (text, metadata, structure)
    - Format validation (spacing, fonts, indentation)
    - Quality assessment (completeness, accuracy)
    - Risk scoring (based on consistency, accuracy, authenticity)

    Output must be valid JSON:
    {
      "content_summary": "...",
      "metadata": {...},
      "format_issues": [...],
      "quality_issues": [...],
      "risk_score": number,
      "recommendations": [...]
    }
    """

    # --- Run inference for each image ---
    all_results = []
    for img_path in image_files:
        with open(img_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        chat_completion = client.chat.completions.create(
            model=model,
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_data}"},
                        }
                    ],
                },
            ],
        )

        result_text = chat_completion.choices[0].message.content
        try:
            result_json = json.loads(result_text)
        except Exception:
            result_json = {"error": "Invalid JSON returned", "raw_output": result_text}

        all_results.append(
            {
                "page": len(all_results) + 1,
                "image_path": img_path,
                "analysis": result_json,
            }
        )

    # --- Save run log ---
    run_log = {
        "file": pdf_path,
        "file_name": file_name,
        "timestamp": timestamp,
        "image_dir": image_dir,
        "num_pages_processed": len(all_results),
        "results": all_results,
    }

    with open(log_path, "w") as f:
        json.dump(run_log, f, indent=2)

    print(f"Run completed. Log saved to: {log_path}")
    print(f"Images saved to: {image_dir}")

    return run_log


def format_validation_system_prompt(
    template_spec: Optional[Dict[str, Any]] = None,
) -> str:
    """Prompt that ensures the model lists all issues clearly."""
    tmpl = json.dumps(template_spec or {}, ensure_ascii=False)
    return f"""
You are a Document Format Validation Engine. You will analyze **each PAGE IMAGE** and return a detailed JSON report.

Perform these tasks:
- **Formatting checks:** List all detected formatting issues (e.g. double spacing, irregular fonts, inconsistent indentation, misaligned paragraphs, inconsistent margins, etc.). Be exhaustive.
- **Content validation:** List spelling mistakes, incorrect headers, missing or misplaced sections.
- **Structure analysis:** Describe section order, missing sections, or duplicated sections.
- **Template matching:** Compare against the given template (if provided). Mention missing or extra parts.

Template (may be empty): {tmpl}

Return STRICT JSON (no text outside JSON). Example output format:

{{
  "formatting_checks": {{
    "issues": ["string", "string", "string"], 
    "severity": "low | medium | high"
  }},
  "content_validation": {{
    "issues": ["string", "string"],
    "missing_sections": ["string"]
  }},
  "structure_analysis": {{
    "issues": ["string"],
    "completeness": "ok | partial | missing"
  }},
  "template_match": {{
    "match": true | false,
    "missing_items": ["string"],
    "extra_items": ["string"]
  }},
  "risk_score": 0–100,
  "recommendations": ["string", "string"]
}}
""".strip()


def encode_image_to_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def format_validation_system(
    image_folder: str,
    model: str = "meta-llama/llama-4-maverick-17b-128e-instruct",
    template_spec: Optional[Dict[str, Any]] = None,
    log_dir: str = "logs",
    save_log: bool = True,
) -> Dict[str, Any]:
    """Simplified validator that lists all formatting issues and aggregates risk scores."""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    os.makedirs(log_dir, exist_ok=True)

    images = sorted(
        [
            os.path.join(image_folder, f)
            for f in os.listdir(image_folder)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
        ]
    )

    sys_prompt = format_validation_system_prompt(template_spec)
    page_results = []

    for idx, img_path in enumerate(images, start=1):
        print(f"🔍 Validating page {idx}: {img_path}")
        try:
            img_b64 = encode_image_to_b64(img_path)
            resp = client.chat.completions.create(
                model=model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_b64}"
                                },
                            }
                        ],
                    },
                ],
            )
            parsed = json.loads(resp.choices[0].message.content)
            page_results.append(parsed)
        except Exception as e:
            page_results.append({"error": str(e)})

    valid_scores = [p.get("risk_score", 0) for p in page_results if isinstance(p, dict)]
    avg_risk = int(sum(valid_scores) / len(valid_scores)) if valid_scores else 0

    output = {
        "folder": image_folder,
        "summary": {
            "average_risk_score": avg_risk,
            "pages_analyzed": len(page_results),
        },
        "pages": page_results,
    }

    if save_log:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(
            log_dir, f"format_validation_{ts}_{Path(image_folder).name}.json"
        )
        with open(log_path, "w") as f:
            json.dump(output, f, indent=2)
        print(f"✅ Log saved at: {log_path}")

    return output


def get_image_folder_from_filename(filename: str) -> str:
    """Convert a .pdf filename into its image folder path."""
    stem = Path(filename).stem
    folder_path = Path("data/images") / stem
    return str(folder_path)


def analyze_image(
    pdf_path: str,
    model: str = "meta-llama/llama-4-maverick-17b-128e-instruct",
    zoom: float = 0.5,
    max_pages: int = 5,
    template_spec: Optional[Dict[str, Any]] = None,
    image_output_root: str = "data/images",
    log_dir: str = "logs",
    save_combined_log: bool = True,
) -> Dict[str, Any]:
    """
    Comprehensive image analysis function that combines:
    1. Document processing engine (content extraction)
    2. Format validation system (formatting checks)

    Args:
        pdf_path: Path to PDF file to analyze
        model: Groq model to use
        zoom: Zoom factor for PDF to image conversion
        max_pages: Maximum number of pages to process
        template_spec: Optional template specification for validation
        image_output_root: Root directory for image output
        log_dir: Directory for log files
        save_combined_log: Whether to save combined results to log file

    Returns:
        Dictionary containing combined results from both functions:
        {
            "run_document_processing_engine": {...},
            "format_validation_system": {...},
            "metadata": {...}
        }
    """

    print("=" * 80)
    print("🚀 Starting Comprehensive Document Analysis")
    print("=" * 80)

    # Step 1: Run document processing engine
    print("\n📊 Step 1/2: Running Document Processing Engine...")
    print("-" * 80)

    processing_result = run_document_processing_engine(
        pdf_path=pdf_path,
        model=model,
        zoom=zoom,
        max_pages=max_pages,
        image_output_root=image_output_root,
        log_dir=log_dir,
    )

    # Step 2: Get image folder and run format validation
    print("\n🔍 Step 2/2: Running Format Validation System...")
    print("-" * 80)

    image_folder = get_image_folder_from_filename(pdf_path)

    validation_result = format_validation_system(
        image_folder=image_folder,
        model=model,
        template_spec=template_spec,
        log_dir=log_dir,
        save_log=False,  # We'll save combined log instead
    )

    # Combine results
    combined_result = {
        "run_document_processing_engine": processing_result,
        "format_validation_system": validation_result,
        "metadata": {
            "pdf_path": pdf_path,
            "analysis_timestamp": datetime.datetime.now().isoformat(),
            "model_used": model,
            "zoom_factor": zoom,
            "max_pages_processed": max_pages,
            "image_folder": image_folder,
            "pipeline_version": "1.0.0",
        },
    }

    # Save combined log if requested
    if save_combined_log:
        # send to audit_logs/
        audit_log_path = Path("audit_logs")
        audit_log_path.mkdir(exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = Path(pdf_path).stem
        audit_log_file = audit_log_path / f"audit_log_{timestamp}_{file_name}.json"
        with open(audit_log_file, "w") as f:
            json.dump(combined_result, f, indent=2)

        print("\n" + "=" * 80)
        print(f"✅ Combined analysis log saved to: {combined_log_path}")
        print("=" * 80)

    # Print summary
    print("\n" + "=" * 80)
    print("📋 ANALYSIS SUMMARY")
    print("=" * 80)

    # Summary from document processing
    doc_processing = combined_result["run_document_processing_engine"]
    print(f"\n📄 Document Processing:")
    print(f"   Pages processed: {doc_processing['num_pages_processed']}")
    print(f"   Images saved to: {doc_processing['image_dir']}")

    # Summary from format validation
    format_validation = combined_result["format_validation_system"]
    summary = format_validation.get("summary", {})
    print(f"\n🔍 Format Validation:")
    print(f"   Pages analyzed: {summary.get('pages_analyzed', 0)}")
    print(f"   Average risk score: {summary.get('average_risk_score', 0)}/100")

    # List issues from first page as example
    if format_validation.get("pages"):
        first_page = format_validation["pages"][0]
        if "formatting_checks" in first_page:
            issues = first_page["formatting_checks"].get("issues", [])
            if issues:
                print(f"\n⚠️  Formatting Issues Found (Page 1):")
                for issue in issues[:3]:  # Show first 3 issues
                    print(f"   - {issue}")
                if len(issues) > 3:
                    print(f"   ... and {len(issues) - 3} more issues")

    print("=" * 80 + "\n")

    return combined_result


if __name__ == "__main__":
    file_name = "Swiss_Home_Purchase_Agreement_Scanned_Noise_forparticipants.pdf"

    # Use the comprehensive analyze_image function
    result = analyze_image(
        pdf_path=f"data/{file_name}", max_pages=3, save_combined_log=True
    )

    # Print the combined result structure (keys only)
    print("\n📦 Combined Result Structure:")
    print(json.dumps({k: "..." for k in result.keys()}, indent=2))

    # Access specific results
    print("\n📊 Document Processing Result:")
    print(
        f"   Pages: {result['run_document_processing_engine']['num_pages_processed']}"
    )

    print("\n🔍 Format Validation Result:")
    print(
        f"   Risk Score: {result['format_validation_system']['summary']['average_risk_score']}/100"
    )
