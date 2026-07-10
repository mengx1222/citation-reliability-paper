"""Shared constants, regular expressions, and utility functions for analysis scripts.

This module centralizes definitions used across multiple analysis scripts
to avoid duplication and ensure consistency.
"""

from __future__ import annotations

import re
from pathlib import Path


# ── Paths ────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[1]

TASKS_CSV = ROOT / "data" / "task_seed.csv"
PROMPTS_CSV = ROOT / "data" / "prompts.csv"

DEEPSEEK_VERIFIED = ROOT / "results" / "verified_refs_merged.csv"
QWEN_VERIFIED = ROOT / "results" / "verified_refs_qwen.csv"
DEEPSEEK_EXTRACTED = ROOT / "results" / "extracted_refs_deepseek.csv"
QWEN_EXTRACTED = ROOT / "results" / "extracted_refs_qwen.csv"
QWEN_COUNT = ROOT / "results" / "qwen_output_count.txt"
E3_SAMPLE = ROOT / "data" / "e3_annotation_sample.csv"

OUTPUT_DIR = ROOT / "analysis" / "generated"
TABLES_MD = OUTPUT_DIR / "paper_tables.md"
TABLES_JSON = OUTPUT_DIR / "paper_tables.json"
E3_CANDIDATES = OUTPUT_DIR / "e3_candidate_selectors.md"

SUMMARY_MD = ROOT / "analysis" / "summary_metrics.md"
SUMMARY_JSON = ROOT / "analysis" / "summary_metrics.json"
SVG_OUT = ROOT / "docs" / "figures" / "resolved-rate-by-workflow.svg"

# ── Workflow definitions ─────────────────────────────────────────────────

WORKFLOW_ORDER = (
    "W0_DIRECT",
    "W1_CAUTIOUS",
    "W2_RETRIEVAL_FIRST",
    "W3_VERIFY_REPAIR",
)

WORKFLOW_LABELS: dict[str, str] = {
    "W0_DIRECT": "W0 Direct",
    "W1_CAUTIOUS": "W1 Cautious",
    "W2_RETRIEVAL_FIRST": "W2 Simulated Retrieval",
    "W3_VERIFY_REPAIR": "W3 Verify-and-Repair",
}

# Short labels used for compact tables / figures
WORKFLOW_SHORT_LABELS: dict[str, str] = {
    "W0_DIRECT": "W0",
    "W1_CAUTIOUS": "W1",
    "W2_RETRIEVAL_FIRST": "W2",
    "W3_VERIFY_REPAIR": "W3",
}

# ── Model definitions ────────────────────────────────────────────────────

MODEL_FILES: dict[str, Path] = {
    "deepseek-chat": DEEPSEEK_VERIFIED,
    "qwen3-14b": QWEN_VERIFIED,
}

MODEL_LABELS: dict[str, str] = {
    "deepseek-chat": "DeepSeek-chat",
    "qwen3-14b": "Qwen3-14B",
}

MODEL_KEYS = ["deepseek-chat", "qwen3-14b"]

MODEL_COLORS: dict[str, str] = {
    "deepseek-chat": "#1f77b4",
    "qwen3-14b": "#f28e2b",
}

# ── Regular expressions ──────────────────────────────────────────────────

SOURCE_RE = re.compile(
    r"^(?P<task_id>T\d+)_(?P<workflow>W\d+_[A-Z_]+)__"
    r"(?P<model>[^.]+)\.txt$",
    re.IGNORECASE,
)

# ── Verification status mapping ──────────────────────────────────────────
# The verification pipeline produces fine-grained statuses.
# This map defines how they are collapsed for aggregate analysis.

VERIFICATION_STATUS_MAP: dict[str, str] = {
    # Positive: reference was matched to a real work
    "exists_metadata_plausible": "resolved",
    "exists_title_match_doi_unconfirmed": "resolved",
    # Negative: reference could not be matched
    "doi_points_to_different_work": "unresolved",
    "exists_but_bad_doi": "unresolved",
    "doi_resolves_metadata_unavailable": "unresolved",
    "unresolved": "unresolved",
    "not_checked": "unresolved",
    # Input sentinel (no DOI to check)
    "": "no_doi",
}


def normalize_status(raw_status: str) -> str:
    """Map a fine-grained verification status to one of {resolved, unresolved, no_doi}."""
    status = (raw_status or "").strip().lower()
    if status in {"resolved", "unresolved", "no_doi"}:
        return status
    return VERIFICATION_STATUS_MAP.get(status, "unresolved")


# ── Similarity thresholds ────────────────────────────────────────────────
# Used in verify_citations.py for title-matching decisions.

# Minimum title similarity score to consider a DOI-based match "plausible"
SIMILARITY_THRESHOLD_DOI_MATCH = 0.70
# Minimum title similarity score to accept a title-only fallback match
SIMILARITY_THRESHOLD_TITLE_MATCH = 0.82

# ── Utility functions ────────────────────────────────────────────────────


def parse_source_name(source_name: str) -> tuple[str, str, str]:
    """Parse a source filename into (task_id, workflow, model).

    Returns:
        (task_id, workflow, model)

    Raises:
        ValueError: if the filename does not match the expected pattern.
    """
    match = SOURCE_RE.match(source_name.strip())
    if not match:
        raise ValueError(
            f"Unrecognized source naming pattern: {source_name!r}. "
            f"Expected format e.g. 'T001_W0_DIRECT__deepseek-chat.txt'"
        )
    return (
        match.group("task_id"),
        match.group("workflow").upper(),
        match.group("model").lower(),
    )


def load_task_languages() -> dict[str, str]:
    """Load task_id -> language mapping from task_seed.csv."""
    import csv

    task_languages: dict[str, str] = {}
    with TASKS_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            task_languages[row["task_id"]] = row["language"]
    return task_languages


def verify_source_names(rows: list[dict]) -> set[str]:
    """Verify that all source filenames in rows can be parsed.

    Logs warnings for unparseable names. Returns the set of valid model names found.
    """
    import sys

    models_found: set[str] = set()
    for row in rows:
        source = row.get("source", "").strip()
        if not source:
            continue
        try:
            _, _, model = parse_source_name(source)
            models_found.add(model)
        except ValueError as exc:
            print(f"WARNING: {exc}", file=sys.stderr)
    return models_found
