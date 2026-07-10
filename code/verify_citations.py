"""Extract and verify scholarly references from LLM-generated academic paragraphs.

Features:
- Reference extraction from [References] / [参考文献] sections
- Multi-source API verification (Crossref, OpenAlex, arXiv)
- Exponential backoff retry for API calls
- Local JSON caching to avoid redundant queries
- Configurable similarity thresholds
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


# ── Configuration ───────────────────────────────────────────────────────

# Default similarity thresholds (can be overridden via env vars)
SIMILARITY_THRESHOLD_DOI_MATCH = float(
    os.environ.get("SIMILARITY_THRESHOLD_DOI_MATCH", "0.70")
)
SIMILARITY_THRESHOLD_TITLE_MATCH = float(
    os.environ.get("SIMILARITY_THRESHOLD_TITLE_MATCH", "0.82")
)

# API request settings
REQUEST_TIMEOUT = int(os.environ.get("API_TIMEOUT", "20"))
RATE_LIMIT_SECONDS = float(os.environ.get("API_RATE_LIMIT", "0.1"))
MAX_RETRIES = int(os.environ.get("API_MAX_RETRIES", "3"))
CACHE_DIR = Path(os.environ.get("CACHE_DIR", "cache/api_responses"))

# User-Agent for API requests
API_USER_AGENT = os.environ.get(
    "API_USER_AGENT",
    "citation-reliability-study/0.2 (https://github.com/example/citation-reliability-paper)",
)

# ── Regex patterns ──────────────────────────────────────────────────────

DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)
REF_LINE_RE = re.compile(
    r"^\s*(?:\[(?P<bracket>\d+)\]|(?P<num>\d+)[.)])\s*(?P<body>.+?)\s*$"
)


# ── Data structures ─────────────────────────────────────────────────────


@dataclass
class ExtractedReference:
    source_file: str
    citation_number: str
    reference_text: str
    doi_in_text: str


@dataclass
class CacheEntry:
    url: str
    data: dict[str, Any] | None
    timestamp: float


# ── Text utilities ──────────────────────────────────────────────────────


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def normalize_title(text: str) -> str:
    text = text.lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = DOI_RE.sub(" ", text)
    text = re.sub(r"[^a-z0-9一-鿿 ]+", " ", text)
    return normalize_space(text)


def similarity(a: str, b: str) -> float:
    a_norm = normalize_title(a)
    b_norm = normalize_title(b)
    if not a_norm or not b_norm:
        return 0.0
    return SequenceMatcher(None, a_norm, b_norm).ratio()


def guess_title(reference: str) -> str:
    """Extract a likely title from a reference text string."""
    ref = DOI_RE.sub("", reference)
    quoted = re.findall(r'"([^"]{12,})"', ref)
    if quoted:
        return max(quoted, key=len)

    after_year = re.search(
        r"(?:\(\d{4}[a-z]?\)|\b\d{4}[a-z]?\b)\.?\s*(?P<title>[^.]{12,180})\.", ref
    )
    if after_year:
        title = normalize_space(after_year.group("title"))
        if title:
            return title

    parts = [normalize_space(p) for p in re.split(r"\.\s+", ref) if normalize_space(p)]
    if len(parts) >= 3:
        return parts[1]
    if len(parts) >= 2:
        return parts[-1]
    return ref


# ── Reference extraction ────────────────────────────────────────────────


def extract_references(text: str, source_file: str) -> list[ExtractedReference]:
    marker_match = re.search(
        r"\[(?:References|参考文献)\]|References|参考文献", text, re.IGNORECASE
    )
    if marker_match:
        ref_text = text[marker_match.end() :]
    else:
        ref_text = text

    references: list[ExtractedReference] = []
    current_number = ""
    current_parts: list[str] = []

    def flush() -> None:
        nonlocal current_number, current_parts
        if not current_parts:
            return
        ref = normalize_space(" ".join(current_parts))
        doi_match = DOI_RE.search(ref)
        references.append(
            ExtractedReference(
                source_file=source_file,
                citation_number=current_number,
                reference_text=ref,
                doi_in_text=doi_match.group(0).rstrip(".,;") if doi_match else "",
            )
        )
        current_number = ""
        current_parts = []

    for raw_line in ref_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = REF_LINE_RE.match(line)
        if match:
            flush()
            current_number = match.group("bracket") or match.group("num") or ""
            current_parts = [match.group("body")]
        elif current_parts:
            current_parts.append(line)

    flush()
    return references


# ── Caching ─────────────────────────────────────────────────────────────


def _cache_path(url: str) -> Path:
    safe_name = re.sub(r"[^a-zA-Z0-9]", "_", url)
    # Keep paths under length limit
    if len(safe_name) > 200:
        safe_name = safe_name[:200]
    return CACHE_DIR / f"{safe_name}.json"


def _cached_get(url: str, timeout: int = 20) -> dict[str, Any]:
    """Wrapper around http_json with disk caching and retry."""
    cache_file = _cache_path(url)
    if cache_file.exists():
        try:
            entry = json.loads(cache_file.read_text(encoding="utf-8"))
            # Cache entries are valid for 7 days
            if time.time() - entry.get("timestamp", 0) < 7 * 86400:
                if entry.get("data") is not None:
                    return entry["data"]
        except (json.JSONDecodeError, KeyError):
            pass  # Stale or corrupt cache, re-fetch

    data = _http_json_with_retry(url, timeout=timeout)

    # Cache the result (even None for transient errors)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(
        json.dumps({"url": url, "data": data, "timestamp": time.time()}),
        encoding="utf-8",
    )
    return data


def _http_json_with_retry(url: str, timeout: int = 20) -> dict[str, Any] | None:
    """Fetch JSON from URL with exponential backoff retry."""
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={"Accept": "application/json", "User-Agent": API_USER_AGENT},
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, OSError) as e:
            last_error = e
            if attempt < MAX_RETRIES:
                wait = 0.5 * (2 ** (attempt - 1))  # 0.5, 1.0, 2.0 seconds
                print(
                    f"  API retry {attempt}/{MAX_RETRIES} for {url[:80]}... "
                    f"waiting {wait:.1f}s after {type(e).__name__}",
                    file=sys.stderr,
                )
                time.sleep(wait)
    return None


def http_json(url: str, timeout: int = 20) -> dict[str, Any]:
    """Public entry point: fetch JSON with caching and retry."""
    return _cached_get(url, timeout=timeout)


# ── API verification endpoints ──────────────────────────────────────────


def crossref_by_doi(doi: str) -> dict[str, Any] | None:
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
    try:
        data = http_json(url)
        item = data.get("message")
        if not item:
            return None
        returned_doi = str(item.get("DOI", "")).lower()
        return item if returned_doi == doi.lower() else None
    except Exception:
        return None


def crossref_by_title(title: str) -> dict[str, Any] | None:
    params = urllib.parse.urlencode({"query.title": title, "rows": 3})
    url = f"https://api.crossref.org/works?{params}"
    try:
        data = http_json(url)
        items = data.get("message", {}).get("items", [])
        if not items:
            return None
        return max(items, key=lambda item: similarity(title, " ".join(item.get("title", []))))
    except Exception:
        return None


def openalex_by_doi(doi: str) -> dict[str, Any] | None:
    doi_url = "https://doi.org/" + doi.lower()
    params = urllib.parse.urlencode({"filter": f"doi:{doi_url}"})
    url = f"https://api.openalex.org/works?{params}"
    try:
        data = http_json(url)
        results = data.get("results", [])
        if not results:
            return None
        item = results[0]
        returned_doi = str(item.get("doi", "")).lower()
        return item if returned_doi == doi_url else None
    except Exception:
        return None


def arxiv_by_doi(doi: str) -> dict[str, Any] | None:
    prefix = "10.48550/arxiv."
    doi_lower = doi.lower()
    if not doi_lower.startswith(prefix):
        return None

    arxiv_id = doi_lower.removeprefix(prefix)
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"id_list": arxiv_id})
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": API_USER_AGENT},
        )
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            root = ET.fromstring(resp.read())
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entry = root.find("atom:entry", ns)
        if entry is None:
            return None
        title = entry.findtext("atom:title", default="", namespaces=ns)
        published = entry.findtext("atom:published", default="", namespaces=ns)
        entry_id = entry.findtext("atom:id", default="", namespaces=ns)
        return {
            "title": normalize_space(title),
            "publication_year": published[:4],
            "id": entry_id,
            "doi": doi,
        }
    except Exception:
        return None


def doi_resolves(doi: str) -> bool:
    url = "https://doi.org/" + urllib.parse.quote(doi, safe="/.")
    req = urllib.request.Request(
        url,
        method="HEAD",
        headers={"User-Agent": API_USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return 200 <= resp.status < 400
    except Exception:
        return False


# ── Metadata helpers ────────────────────────────────────────────────────


def item_title(item: dict[str, Any] | None, source: str) -> str:
    if not item:
        return ""
    if source == "crossref":
        titles = item.get("title") or []
        return titles[0] if titles else ""
    if source == "openalex":
        return item.get("title") or ""
    if source == "arxiv":
        return item.get("title") or ""
    return ""


def item_year(item: dict[str, Any] | None, source: str) -> str:
    if not item:
        return ""
    if source == "crossref":
        for key in ("published-print", "published-online", "issued"):
            parts = item.get(key, {}).get("date-parts")
            if parts and parts[0]:
                return str(parts[0][0])
    if source == "openalex":
        year = item.get("publication_year")
        return str(year) if year else ""
    if source == "arxiv":
        year = item.get("publication_year")
        return str(year) if year else ""
    return ""


# ── Verification logic ──────────────────────────────────────────────────


def verify_reference(reference: ExtractedReference, online: bool) -> dict[str, str]:
    guessed_title = guess_title(reference.reference_text)
    doi = reference.doi_in_text

    crossref_doi_item = None
    openalex_doi_item = None
    arxiv_doi_item = None
    crossref_title_item = None
    doi_is_resolvable = False

    if online:
        if doi:
            doi_is_resolvable = doi_resolves(doi)
            time.sleep(RATE_LIMIT_SECONDS)
            crossref_doi_item = crossref_by_doi(doi)
            time.sleep(RATE_LIMIT_SECONDS)
            openalex_doi_item = openalex_by_doi(doi)
            time.sleep(RATE_LIMIT_SECONDS)
            arxiv_doi_item = arxiv_by_doi(doi)
            time.sleep(RATE_LIMIT_SECONDS)

        if crossref_doi_item is None and openalex_doi_item is None and arxiv_doi_item is None:
            crossref_title_item = crossref_by_title(guessed_title)
            time.sleep(RATE_LIMIT_SECONDS)

    doi_item = crossref_doi_item or openalex_doi_item or arxiv_doi_item
    doi_item_source = ""
    if crossref_doi_item:
        doi_item_source = "crossref"
    elif openalex_doi_item:
        doi_item_source = "openalex"
    elif arxiv_doi_item:
        doi_item_source = "arxiv"

    title_item = crossref_title_item

    crossref_title = item_title(crossref_doi_item or crossref_title_item, "crossref")
    openalex_title = item_title(openalex_doi_item, "openalex")
    arxiv_title = item_title(arxiv_doi_item, "arxiv")
    best_title = item_title(doi_item, doi_item_source)
    if not best_title:
        best_title = item_title(title_item, "crossref")
    title_score = similarity(guessed_title, best_title) if best_title else 0.0

    if not online:
        status = "not_checked"
        error_type = ""
        match_source = ""
    elif doi_item:
        match_source = f"doi_exact_{doi_item_source}"
        if title_score >= SIMILARITY_THRESHOLD_DOI_MATCH:
            status = "exists_metadata_plausible"
            error_type = ""
        else:
            status = "doi_points_to_different_work"
            error_type = "E2"
    elif title_item and title_score >= SIMILARITY_THRESHOLD_TITLE_MATCH:
        match_source = "title_strong"
        if doi and not doi_is_resolvable:
            status = "exists_but_bad_doi"
            error_type = "E2"
        elif doi and doi_is_resolvable:
            status = "exists_title_match_doi_unconfirmed"
            error_type = ""
        else:
            status = "exists_metadata_plausible"
            error_type = ""
    else:
        match_source = "doi_resolves_only" if doi_is_resolvable else ""
        status = "doi_resolves_metadata_unavailable" if doi_is_resolvable else "unresolved"
        error_type = "" if doi_is_resolvable else "E1"

    return {
        "source_file": reference.source_file,
        "citation_number": reference.citation_number,
        "reference_text": reference.reference_text,
        "doi_in_text": doi,
        "guessed_title": guessed_title,
        "crossref_title": crossref_title,
        "crossref_year": item_year(crossref_doi_item or crossref_title_item, "crossref"),
        "crossref_doi": (
            (crossref_doi_item or crossref_title_item or {}).get("DOI", "")
            if (crossref_doi_item or crossref_title_item)
            else ""
        ),
        "openalex_title": openalex_title,
        "openalex_year": item_year(openalex_doi_item, "openalex"),
        "openalex_id": (openalex_doi_item or {}).get("id", "") if openalex_doi_item else "",
        "arxiv_title": arxiv_title,
        "arxiv_year": item_year(arxiv_doi_item, "arxiv"),
        "arxiv_id": (arxiv_doi_item or {}).get("id", "") if arxiv_doi_item else "",
        "doi_resolves": str(doi_is_resolvable).lower(),
        "metadata_match_source": match_source,
        "title_match_score": f"{title_score:.3f}",
        "verification_status": status,
        "error_type": error_type,
    }


# ── Commands ────────────────────────────────────────────────────────────


def command_extract(args: argparse.Namespace) -> None:
    outputs_dir = Path(args.outputs_dir)
    rows: list[dict[str, str]] = []
    for path in sorted(outputs_dir.glob("*.txt")):
        text = path.read_text(encoding="utf-8", errors="replace")
        refs = extract_references(text, path.name)
        for ref in refs:
            rows.append(
                {
                    "source_file": ref.source_file,
                    "citation_number": ref.citation_number,
                    "reference_text": ref.reference_text,
                    "doi_in_text": ref.doi_in_text,
                }
            )

    write_csv(Path(args.out), rows)
    print(f"Extracted {len(rows)} references to {args.out}")


def command_verify(args: argparse.Namespace) -> None:
    with Path(args.input).open("r", encoding="utf-8-sig", newline="") as f:
        input_rows = list(csv.DictReader(f))

    if not input_rows:
        print("WARNING: input file is empty or has no data rows", file=sys.stderr)
        return

    rows = []
    for idx, row in enumerate(input_rows):
        ref = ExtractedReference(
            source_file=row.get("source_file", ""),
            citation_number=row.get("citation_number", ""),
            reference_text=row.get("reference_text", ""),
            doi_in_text=row.get("doi_in_text", ""),
        )
        result = verify_reference(ref, online=args.online)
        rows.append(result)

        if (idx + 1) % 50 == 0:
            print(f"  Verified {idx + 1}/{len(input_rows)} references...")

    write_csv(Path(args.out), rows)
    print(f"Verified {len(rows)} references to {args.out} (online={args.online})")


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def command_clear_cache(args: argparse.Namespace) -> None:
    """Clear the API response cache."""
    if CACHE_DIR.exists():
        import shutil
        shutil.rmtree(CACHE_DIR)
        print(f"Cleared cache directory: {CACHE_DIR}")
    else:
        print(f"Cache directory does not exist: {CACHE_DIR}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract and verify scholarly references from LLM-generated text.",
        epilog=(
            "Configuration via environment variables:\n"
            "  SIMILARITY_THRESHOLD_DOI_MATCH  (default: 0.70)\n"
            "  SIMILARITY_THRESHOLD_TITLE_MATCH (default: 0.82)\n"
            "  API_TIMEOUT                     (default: 20)\n"
            "  API_RATE_LIMIT                  (default: 0.1)\n"
            "  API_MAX_RETRIES                 (default: 3)\n"
            "  API_USER_AGENT                  (default: citation-reliability-study/0.2)\n"
            "  CACHE_DIR                       (default: cache/api_responses)\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(required=True)

    extract = sub.add_parser("extract", help="Extract numbered references from .txt model outputs.")
    extract.add_argument("--outputs-dir", required=True)
    extract.add_argument("--out", required=True)
    extract.set_defaults(func=command_extract)

    verify = sub.add_parser("verify", help="Verify extracted references against scholarly APIs.")
    verify.add_argument("--input", required=True)
    verify.add_argument("--out", required=True)
    verify.add_argument(
        "--online", action="store_true",
        help="Query Crossref/OpenAlex/arXiv APIs. Omit for local parsing only."
    )
    verify.set_defaults(func=command_verify)

    cache_cmd = sub.add_parser("clear-cache", help="Clear the API response cache.")
    cache_cmd.set_defaults(func=command_clear_cache)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
