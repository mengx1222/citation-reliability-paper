"""Sensitivity analysis: how resolved rates change under different similarity thresholds.

This script re-verifies the resolved/unresolved classification for each
reference at multiple title similarity thresholds to test whether the
workflow ranking is robust to threshold choice.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

try:
    import numpy as np
    from scipy.stats import chi2_contingency

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

from common import (
    DEEPSEEK_VERIFIED,
    MODEL_LABELS,
    MODEL_KEYS,
    OUTPUT_DIR,
    QWEN_VERIFIED,
    SIMILARITY_THRESHOLD_DOI_MATCH,
    SIMILARITY_THRESHOLD_TITLE_MATCH,
    WORKFLOW_LABELS,
    WORKFLOW_ORDER,
    normalize_status,
    parse_source_name,
)

SENSITIVITY_JSON = OUTPUT_DIR / "sensitivity_analysis.json"
SENSITIVITY_MD = OUTPUT_DIR / "sensitivity_analysis.md"


def load_verification_data(csv_path: Path) -> list[dict]:
    rows = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def compute_resolved_rate_threshold(
    rows: list[dict], doi_threshold: float, title_threshold: float
) -> dict[str, float]:
    """Recompute resolved rate per workflow given custom thresholds.

    Simulates the logic in verify_citations.py:
    - A reference is 'resolved' if:
      - It has a DOI that resolves AND title_score >= doi_threshold, OR
      - It has no DOI but a title match with score >= title_threshold
    """
    from common import SOURCE_RE

    workflow_counts: dict[str, dict[str, int]] = {}
    for wf in WORKFLOW_ORDER:
        workflow_counts[wf] = {"total": 0, "resolved": 0}

    for row in rows:
        source = row.get("source", "").strip()
        if not source:
            continue
        m = SOURCE_RE.match(source.strip())
        if not m:
            continue
        workflow = m.group("workflow").upper()
        if workflow not in workflow_counts:
            continue

        doi = row.get("doi_in_text", "").strip()
        doi_resolves = row.get("doi_resolves", "").strip().lower() == "true"
        title_score_str = row.get("title_match_score", "").strip()
        title_score = float(title_score_str) if title_score_str else 0.0
        raw_status = row.get("status", "").strip().lower()
        metadata_source = row.get("metadata_match_source", "").strip()
        status = normalize_status(raw_status)

        workflow_counts[workflow]["total"] += 1

        # Determine if resolved under these thresholds
        if status == "no_doi":
            # No DOI → must rely on title match or fallback
            if title_score >= title_threshold:
                workflow_counts[workflow]["resolved"] += 1
            else:
                pass  # stay unresolved
        elif doi and doi_resolves and title_score >= doi_threshold:
            workflow_counts[workflow]["resolved"] += 1
        elif "title_strong" in metadata_source and title_score >= title_threshold:
            workflow_counts[workflow]["resolved"] += 1
        elif status == "resolved":
            workflow_counts[workflow]["resolved"] += 1
        else:
            pass  # unresolved

    rates = {}
    for wf in WORKFLOW_ORDER:
        c = workflow_counts[wf]
        rates[wf] = c["resolved"] / c["total"] * 100 if c["total"] > 0 else 0.0
    return rates


# ── Threshold grid ──────────────────────────────────────────────────────

DOI_THRESHOLDS = [0.50, 0.60, 0.70, 0.80, 0.90]
TITLE_THRESHOLDS = [0.70, 0.75, 0.82, 0.90, 0.95]


def run_sensitivity(model_key: str) -> dict:
    csv_path = DEEPSEEK_VERIFIED if model_key == "deepseek-chat" else QWEN_VERIFIED
    rows = load_verification_data(csv_path)

    results: dict[str, dict] = {}

    for dt in DOI_THRESHOLDS:
        for tt in TITLE_THRESHOLDS:
            key = f"doi={dt:.2f}_title={tt:.2f}"
            rates = compute_resolved_rate_threshold(rows, dt, tt)
            results[key] = {
                "doi_threshold": dt,
                "title_threshold": tt,
                "workflow_rates": {
                    wf: round(rates[wf], 1) for wf in WORKFLOW_ORDER
                },
                "ranking": _rank_workflows(rates),
            }

    # Baseline: current paper thresholds
    baseline_key = (
        f"doi={SIMILARITY_THRESHOLD_DOI_MATCH:.2f}_"
        f"title={SIMILARITY_THRESHOLD_TITLE_MATCH:.2f}"
    )

    # Check ranking stability: is the W0 > W3 > W1 > W2 pattern preserved?
    stability = _ranking_stability(results)

    return {
        "model": MODEL_LABELS[model_key],
        "baseline_thresholds": {
            "doi_threshold": SIMILARITY_THRESHOLD_DOI_MATCH,
            "title_threshold": SIMILARITY_THRESHOLD_TITLE_MATCH,
        },
        "baseline_key": baseline_key,
        "n_scenarios": len(results),
        "scenarios": results,
        "ranking_stability": stability,
    }


def _rank_workflows(rates: dict[str, float]) -> list[str]:
    """Rank workflows by resolved rate descending."""
    return sorted(rates, key=lambda wf: rates[wf], reverse=True)


def _ranking_stability(results: dict[str, dict]) -> dict:
    """Check how often each workflow appears at each rank position."""
    positions: dict[str, dict[int, int]] = {}
    for wf in WORKFLOW_ORDER:
        positions[wf] = {r: 0 for r in range(1, len(WORKFLOW_ORDER) + 1)}

    for scenario, data in results.items():
        ranking = data["ranking"]
        for rank, wf in enumerate(ranking, 1):
            positions[wf][rank] += 1

    n_scenarios = len(results)
    stability = {}
    for wf in WORKFLOW_ORDER:
        most_common_rank = max(positions[wf], key=positions[wf].get)
        stability[wf] = {
            "most_common_rank": most_common_rank,
            "frequency_at_rank": positions[wf][most_common_rank],
            "proportion": round(positions[wf][most_common_rank] / n_scenarios * 100, 1),
        }
    return stability


# ── Report ──────────────────────────────────────────────────────────────


def render_sensitivity_report(ds_result: dict, qw_result: dict) -> str:
    lines = []
    lines.append("# Sensitivity Analysis: Similarity Thresholds\n")

    for result in (ds_result, qw_result):
        lines.append(f"## {result['model']}\n")
        lines.append(
            f"Baseline thresholds: "
            f"DOI match = {result['baseline_thresholds']['doi_threshold']}, "
            f"Title match = {result['baseline_thresholds']['title_threshold']}\n"
        )
        lines.append(f"Tested {result['n_scenarios']} threshold combinations.\n")

        # Stability summary
        lines.append("### Ranking Stability\n")
        lines.append(
            "| Workflow | Most Common Rank | Frequency | Proportion |"
        )
        lines.append("|---|---:|---:|---:|")
        base_rank = _rank_workflows(
            result["scenarios"][result["baseline_key"]]["workflow_rates"]
        )
        for rank, wf in enumerate(base_rank, 1):
            stab = result["ranking_stability"][wf]
            lines.append(
                f"| {WORKFLOW_LABELS[wf]} | {stab['most_common_rank']} | "
                f"{stab['frequency_at_rank']}/{result['n_scenarios']} | "
                f"{stab['proportion']}% |"
            )

        # Table of all scenarios
        lines.append("\n### All Threshold Combinations\n")
        lines.append(
            "| DOI Thresh | Title Thresh | W0 | W1 | W2 | W3 | Ranking |"
        )
        lines.append("|---|---:|---:|---:|---:|---:|---:|")

        for key, scenario in result["scenarios"].items():
            wf_rates = scenario["workflow_rates"]
            ranking = scenario["ranking"]
            ranking_labels = " → ".join(WORKFLOW_LABELS[wf] for wf in ranking)
            lines.append(
                f"| {scenario['doi_threshold']} | {scenario['title_threshold']} | "
                f"{wf_rates['W0_DIRECT']}% | {wf_rates['W1_CAUTIOUS']}% | "
                f"{wf_rates['W2_RETRIEVAL_FIRST']}% | {wf_rates['W3_VERIFY_REPAIR']}% | "
                f"{ranking_labels} |"
            )
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Running sensitivity analysis...")
    ds_result = run_sensitivity("deepseek-chat")
    qw_result = run_sensitivity("qwen3-14b")

    # Summary
    combined = {
        "deepseek-chat": ds_result,
        "qwen3-14b": qw_result,
        "doi_thresholds_tested": DOI_THRESHOLDS,
        "title_thresholds_tested": TITLE_THRESHOLDS,
    }

    SENSITIVITY_JSON.write_text(json.dumps(combined, indent=2), encoding="utf-8")
    SENSITIVITY_MD.write_text(render_sensitivity_report(ds_result, qw_result), encoding="utf-8")

    print(f"Wrote {SENSITIVITY_JSON}")
    print(f"Wrote {SENSITIVITY_MD}")


if __name__ == "__main__":
    main()
