import os, time, requests, re, io, json, hashlib
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
from dotenv import load_dotenv

from groq import Groq
from collections import defaultdict
from datetime import datetime
from difflib import unified_diff
from urllib.parse import urljoin


load_dotenv()


if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY not found. Please set it in your .env or env vars.")

if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env or env vars.")

if not os.getenv("GOOGLE_CX"):
    raise ValueError("GOOGLE_CX not found. Please set it in your .env or env vars.")

if not os.getenv("GOOGLE_SEARCH_ENDPOINT"):
    raise ValueError("GOOGLE_SEARCH_ENDPOINT not found. Please set it in your .env or env vars.")

llm_client = Groq()
LLM_MODEL = "llama-3.3-70b-versatile"
KEYWORDS = [
    r"\bhigh[- ]risk countr(y|ies)\b",
    r"\bhigh[- ]risk jurisdiction(s)?\b",
    r"\bcountry risk\b",
    r"\bgeograph(ic(al)?)? risk\b",
    r"\bFATF\b",
    r"\bFATF[- ]identified\b",
    r"\bFATF (list|listing)\b",
    r"\benhanced due diligence\b",
    r"\bEDD\b",
    r"\bcustomer due diligence\b",
    r"\bCDD\b",
    r"\brisk[- ]based approach\b",
    r"\brisk assessment\b",
    r"\bsanction(ed|s)? countr(y|ies)\b",
    r"\bsanction(s)?\b",
    r"\bnon[- ]cooperative jurisdiction(s)?\b",
    r"\bproliferation financing\b",
    r"\bforeign jurisdiction(s)?\b",
    r"\bjurisdiction(s)? of concern\b",
    r"\bheightened risk\b"
]
KW_RE = re.compile("|".join(KEYWORDS), re.I)


SUMMARIZE_SYS = (
    "You are a compliance analyst. Given a PDF or HTML page and a user query, "
    "summarize MAS regulatory guidance precisely in one sentence with concrete details that analysts can use "
    "to detect, assess, or mitigate risks from high-risk countries or jurisdictions. "
    "Focus on enhanced due diligence (EDD), sanctions, and KYC/AML country-risk obligations."
)

PIPELINE_VERSION = "1.0.0"
AUDIT_LOG_FILE = "audit_logs/regulation_audit_log.jsonl"
AUDIT_DIFF_FILE = "regulation_audit_diff.log"


def google_cse_search(query: str, max_results: int = 10, sleep: float = 0.2, max_retries: int = 3):
    results = []
    start = 1
    while len(results) < max_results:
        remaining = max_results - len(results)
        num = min(10, remaining)
        params = {"key": os.getenv("GOOGLE_API_KEY"), "cx": os.getenv("GOOGLE_CX"), "q": query, "start": start, "num": num}

        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.get(os.getenv("GOOGLE_SEARCH_ENDPOINT"), params=params, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("items", []) or []
                    results.extend(items[:num])
                    next_pages = (data.get("queries") or {}).get("nextPage") or []
                    if not items or not next_pages:
                        return results[:max_results]
                    start = next_pages[0].get("startIndex", start + 10)
                    break
                else:
                    print(f"[{attempt}/{max_retries}] HTTP {resp.status_code}: {resp.text[:120]}")
            except Exception as e:
                print(f"[{attempt}/{max_retries}] Error: {e}")
            if attempt < max_retries:
                time.sleep(1.5 * attempt)
            else:
                print(f"[!] Failed after {max_retries} retries at start={start}.")
        time.sleep(sleep)
    return results[:max_results]


UA_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    )
}
PDF_LINK_RE = re.compile(r'href=["\']([^"\']+\.pdf(?:\?[^\s"\']*)?)["\']', re.I)
SRC_PDF_RE  = re.compile(r'(?:src|data)=["\']([^"\']+\.pdf(?:\?[^\s"\']*)?)["\']', re.I)
JS_PDF_RE   = re.compile(r'["\'](https?://[^"\']+\.pdf(?:\?[^\s"\']*)?)["\']', re.I)

def _looks_like_pdf(bin_bytes: bytes) -> bool:
    return bin_bytes.startswith(b"%PDF-")

def _content_disposition_filename(resp):
    cd = resp.headers.get("Content-Disposition", "")
    m = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', cd, re.I)
    return m.group(1) if m else None

def _find_pdf_candidates(html, base_url):
    cands = []
    for pat in (PDF_LINK_RE, SRC_PDF_RE, JS_PDF_RE):
        for u in pat.findall(html or ""):
            cands.append(urljoin(base_url, u))
    seen, out = set(), []
    for u in cands:
        if u not in seen:
            seen.add(u); out.append(u)
    return out

def _fetch(url, session, timeout=60):
    return session.get(url, headers=UA_HEADERS, timeout=timeout, stream=True, allow_redirects=True)


def extract_from_pdf(url: str, timeout=60, window=2, max_hops=4):
    try:
        session = requests.Session()
        resp = _fetch(url, session, timeout=timeout)
        content_type = (resp.headers.get("Content-Type") or "").lower()
        content = resp.content

        if "pdf" in content_type or _looks_like_pdf(content):
            final_bin = content; final_url = resp.url
        else:
            fname = _content_disposition_filename(resp)
            if ("application/octet-stream" in content_type) and fname and fname.lower().endswith(".pdf"):
                final_bin = content; final_url = resp.url
            else:
                html, final_bin, final_url = resp.text, None, resp.url
                hops = 0
                while hops < max_hops:
                    candidates = _find_pdf_candidates(html, final_url)
                    if not candidates:
                        break
                    for cand in candidates[:5]:
                        r2 = _fetch(cand, session, timeout=timeout)
                        ct2 = (r2.headers.get("Content-Type") or "").lower()
                        b2 = r2.content
                        fname2 = _content_disposition_filename(r2)
                        if "pdf" in ct2 or _looks_like_pdf(b2) or (
                            "application/octet-stream" in ct2 and fname2 and fname2.lower().endswith(".pdf")
                        ):
                            final_bin = b2; final_url = r2.url; break
                        if "text/html" in ct2:
                            html = r2.text; final_url = r2.url
                    if final_bin: break
                    hops += 1
                if final_bin is None:
                    raise ValueError(f"Still not a PDF after hunting: {content_type}")

        hits = []
        for page_num, layout in enumerate(extract_pages(io.BytesIO(final_bin)), start=1):
            lines = []
            for el in layout:
                if isinstance(el, LTTextContainer):
                    for tline in el.get_text().splitlines():
                        tl = " ".join(tline.split())
                        if tl: lines.append(tl)
            page_text = "\n".join(lines)
            for i, line in enumerate(lines):
                if KW_RE.search(line):
                    s = max(0, i - window); e = min(len(lines), i + window + 1)
                    snippet = " ".join(lines[s:e])
                    hits.append({
                        "doc_url": final_url,
                        "doc_title": final_url.split("/")[-1],
                        "type": "pdf",
                        "page": page_num,
                        "section_path": None,
                        "quote": line,
                        "regulation": snippet,
                        "page_text": page_text
                    })
        return hits if hits else [{"doc_url": final_url, "note": "PDF fetched but no keyword hits"}]
    except Exception as e:
        return [{"doc_url": url, "error": str(e)}]


def extract_from_html(url: str, timeout=30):
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for t in soup(["script", "style", "noscript"]): t.extract()
    sections, current_path = [], []
    def norm_text(x): return re.sub(r"\s+", " ", x).strip()
    for node in soup.find_all(["h1","h2","h3","h4","h5","h6","p","li"]):
        tag = node.name.lower(); txt = norm_text(node.get_text(" "))
        if not txt: continue
        if tag.startswith("h"):
            level = int(tag[1]); current_path = [t for (t,lvl) in current_path if lvl < level]; current_path.append((txt, level))
        elif KW_RE.search(txt):
            sections.append({
                "doc_url": url,
                "doc_title": soup.title.get_text(strip=True) if soup.title else "",
                "type": "html",
                "section_path": " > ".join([t for t,_ in current_path]) or None,
                "quote": txt,
                "regulation": None,
                "page_text": txt
            })
    return sections


def enrich_cse_item(item: dict):
    url = item.get("link") or item.get("url")
    if not url: return []
    is_pdf = (item.get("mime") == "application/pdf") or url.lower().endswith(".pdf")
    try:
        return extract_from_pdf(url) if is_pdf else extract_from_html(url)
    except Exception as e:
        return [{"doc_url": url, "error": str(e)}]

def extract_clauses_from_cse_items(items):
    all_hits = []
    for it in items:
        hits = enrich_cse_item(it)
        all_hits.extend(hits)
    seen, dedup = set(), []
    for h in all_hits:
        k = (h.get("doc_url"), h.get("page"), h.get("quote"))
        if k not in seen:
            seen.add(k); dedup.append(h)
    return dedup


def summarize_page_one_sentence(page_text: str, query: str) -> dict:
    prompt = (
        f"Query: {query}\n\n"
        f"Page text:\n{page_text[:12000]}\n\n"
        "Respond in JSON with keys: summary (1 sentence <= 40 words, no hallucination), "
        "section (string or null). If irrelevant, set summary='Not relevant to the query on this page.'"
    )
    resp = llm_client.chat.completions.create(
        model=LLM_MODEL,
        temperature=0.1,
        messages=[{"role": "system", "content": SUMMARIZE_SYS},
                  {"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    out = resp.choices[0].message.content
    try:
        data = json.loads(out)
        return {"summary": data.get("summary"), "section": data.get("section")}
    except Exception:
        return {"summary": "Summary unavailable.", "section": None}


SKIP_SECTIONS = {"TABLE OF CONTENTS", "CONCLUSION", "SUPERVISORY EXPECTATIONS", "FOREWORD"}

def summarize_hits_with_llm(hits: list, query: str, regulator="MAS") -> dict:
    # prefilter relevant pages
    filtered_hits = [h for h in hits if KW_RE.search((h.get("quote") or "") + " " + (h.get("regulation") or ""))]
    if not filtered_hits:
        return {regulator: [{"note": "No relevant content detected."}]}

    by_doc = defaultdict(list)
    for h in filtered_hits:
        by_doc[h["doc_url"]].append(h)

    results = []
    for doc_url, doc_hits in by_doc.items():
        best = max(doc_hits, key=lambda x: len(x.get("page_text", "")))
        page_text = best.get("page_text") or best.get("regulation", "")
        s = summarize_page_one_sentence(page_text, query)
        summary, section = s["summary"], s["section"]

        if not section:
            for line in page_text.splitlines()[:20]:
                L = line.strip()
                if L and len(L) <= 80 and L.isupper() and L not in SKIP_SECTIONS:
                    section = L; break

        if summary and not summary.startswith("Not relevant"):
            results.append({
                "doc_url": doc_url,
                "doc_title": best.get("doc_title"),
                "regulation": summary,
                "section": section
            })

    return {regulator: results or [{"note": "No relevant summaries returned."}]}

def run_pipeline_for_site(site: str, query: str, regulator: str, max_results=10):
    """
    Run the same pipeline for a specific regulator site.
    e.g. site='mas.gov.sg', regulator='MAS'
    """
    search_query = f"site:{site} {query}"
    items = google_cse_search(search_query, max_results=max_results)
    hits = extract_clauses_from_cse_items(items)
    result = summarize_hits_with_llm(hits, query, regulator=regulator)
    maybe_log_with_diff(regulator, query, result)   # <--- add this line
    return result


def run_all_regulators(query: str, max_results=10):
    """
    Run the pipeline for multiple regulators and combine results.
    """
    regulators = {
        "MAS": "mas.gov.sg",
        "FINMA": "finma.ch",
        "HKMA": "hkma.gov.hk"
    }

    final_output = {}
    for reg_name, site in regulators.items():
        print(f"\n=== Running for {reg_name} ({site}) ===")
        result = run_pipeline_for_site(site, query, reg_name, max_results)
        final_output.update(result)  # each is {"MAS": [...]}, {"FINMA": [...]}, etc.

    print("\n====== FINAL COMBINED RESULT ======")
    with open("reports/regulations.json", "w") as f:
        json.dump(final_output, f, indent = 2)

    return final_output


def _canon_result_for_reg(result: dict, regulator: str) -> str:
    """
    Return a canonical JSON string of the regulator's slice to ensure stable hashing & diff.
    """
    reg_slice = result.get(regulator, result)
    return json.dumps(reg_slice, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

def _hash_result(canon: str) -> str:
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()

def _load_audit_log(path: str = AUDIT_LOG_FILE) -> list[dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
    except FileNotFoundError:
        return []

def _latest_entry(entries: list[dict], regulator: str, query: str) -> dict | None:
    matches = [e for e in entries if e.get("regulator") == regulator and e.get("query") == query]
    if not matches:
        return None
    # newest first (ISO timestamps sort lexicographically)
    matches.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return matches[0]

def _write_audit_entry(regulator: str, query: str, result: dict, result_hash: str):
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": PIPELINE_VERSION,
        "regulator": regulator,
        "query": query,
        "keywords": KEYWORDS,
        "llm_model": LLM_MODEL,
        "result_hash": result_hash,
        "result": result,
    }
    with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record

def _write_diff(old_entry: dict, new_entry: dict, regulator: str):
    old_txt = _canon_result_for_reg(old_entry.get("result", {}), regulator)
    new_txt = _canon_result_for_reg(new_entry.get("result", {}), regulator)
    diff = unified_diff(
        old_txt.splitlines(),
        new_txt.splitlines(),
        fromfile=f'old_{regulator}_{old_entry.get("timestamp","")}',
        tofile=f'new_{regulator}_{new_entry.get("timestamp","")}',
        lineterm=""
    )
    diff_text = "\n".join(diff)
    if not diff_text.strip():
        return
    with open(AUDIT_DIFF_FILE, "a", encoding="utf-8") as f:
        f.write("\n" + "="*80 + "\n")
        f.write(diff_text + "\n")
    # also print to console for convenience
    print("\n=== DIFF WRITTEN ===\n" + diff_text)

def maybe_log_with_diff(regulator: str, query: str, result: dict):
    """
    - If no previous entry for (regulator, query): write baseline.
    - Else:
        - If results changed: write new entry + append unified diff.
        - If identical: do nothing (no noise).
    """
    entries = _load_audit_log()
    prev = _latest_entry(entries, regulator, query)

    canon = _canon_result_for_reg(result, regulator)
    new_hash = _hash_result(canon)

    if prev is None:
        # baseline
        new_entry = _write_audit_entry(regulator, query, result, new_hash)
        print(f"[audit] Baseline logged for {regulator} / {query}")
        return

    if new_hash == prev.get("result_hash"):
        print(f"[audit] No change for {regulator} / {query} (skipped logging).")
        return

    # changed → log + diff
    new_entry = _write_audit_entry(regulator, query, result, new_hash)
    _write_diff(prev, new_entry, regulator)
    print(f"[audit] Change detected → new version logged for {regulator} / {query}")



if __name__ == "__main__":
    run_all_regulators("high-risk jurisdictions AML", max_results=10)