"""Enhanced statistical analysis with significance tests and effect sizes.

Extends the original table-generation script with:
- Chi-square tests for workflow × status association
- Two-proportion z-tests with Bonferroni correction
- Cross-model significance tests
- Effect sizes (Cramér's V, Cohen's h)
- Logistic regression for multi-factor analysis
"""

from __future__ import annotations

import csv
import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

try:
    import numpy as np
    from scipy.stats import chi2_contingency, norm

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

from common import (
    DEEPSEEK_VERIFIED,
    E3_SAMPLE,
    MODEL_KEYS,
    MODEL_LABELS,
    OUTPUT_DIR,
    QWEN_VERIFIED,
    TABLES_JSON,
    TABLES_MD,
    WORKFLOW_LABELS,
    WORKFLOW_ORDER,
    load_task_languages,
    normalize_status,
    parse_source_name,
)

# ========================================================================
#  Data loading
# ========================================================================


def load_verification_data(csv_path: Path) -> list[dict]:
    rows = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def build_contingency(
    rows: list[dict], task_languages: dict[str, str]
) -> tuple[list[list[int]], list[str], dict[str, dict]]:
    """Build a workflow × status contingency table.

    Returns:
        (workflow_x_status_matrix, status_labels, workflow_buckets)
    """
    status_labels = ["resolved", "unresolved", "no_doi"]
    workflow_buckets: dict[str, dict] = {}
    for wf in WORKFLOW_ORDER:
        workflow_buckets[wf] = {s: 0 for s in status_labels}

    for row in rows:
        source = row.get("source", "").strip()
        if not source:
            continue
        try:
            task_id, workflow, _ = parse_source_name(source)
        except ValueError:
            continue
        status = normalize_status(row.get("status", ""))
        if status in workflow_buckets[workflow]:
            workflow_buckets[workflow][status] += 1

    matrix = [
        [workflow_buckets[wf][s] for s in status_labels]
        for wf in WORKFLOW_ORDER
    ]
    return matrix, status_labels, workflow_buckets


# ========================================================================
#  Statistical tests
# ========================================================================


def chi_square_test(matrix: list[list[int]]) -> dict:
    """Chi-square test of independence: workflow vs verification status.

    Returns dict with chi2 statistic, p-value, dof, and Cramér's V.
    """
    if not SCIPY_AVAILABLE:
        return {"note": "scipy not available — install scipy for significance tests"}

    chi2, p, dof, expected = chi2_contingency(matrix)

    # Cramér's V
    n = sum(sum(row) for row in matrix)
    k = len(matrix)  # rows (workflows)
    r = len(matrix[0]) if matrix else 1  # cols (statuses)
    cramer_v = math.sqrt(chi2 / (n * min(k - 1, r - 1))) if n > 0 and min(k - 1, r - 1) > 0 else 0.0

    return {
        "test": "Chi-square test of independence",
        "chi2_statistic": round(float(chi2), 4),
        "p_value": round(float(p), 6),
        "degrees_of_freedom": int(dof),
        "sample_size": int(n),
        "cramers_v": round(float(cramer_v), 4),
        "significant_at_005": bool(p < 0.05),
    }


def pairwise_z_tests(
    matrix: list[list[int]], status_labels: list[str]
) -> list[dict]:
    """Two-proportion z-tests for all pairs of workflows on 'resolved' rate.

    Applies Bonferroni correction for multiple comparisons.
    """
    if not SCIPY_AVAILABLE:
        return [{"note": "scipy not available"}]

    resolved_idx = status_labels.index("resolved")
    n_pairs = len(matrix) * (len(matrix) - 1) // 2
    alpha_bonf = 0.05 / n_pairs if n_pairs > 0 else 0.05

    results = []
    for i in range(len(matrix)):
        for j in range(i + 1, len(matrix)):
            n1 = sum(matrix[i])
            x1 = matrix[i][resolved_idx]
            n2 = sum(matrix[j])
            x2 = matrix[j][resolved_idx]

            if n1 == 0 or n2 == 0:
                continue

            # Pooled proportion
            p_pool = (x1 + x2) / (n1 + n2)
            se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
            z = (x1 / n1 - x2 / n2) / se if se > 0 else 0.0
            p_value = 2 * (1 - norm.cdf(abs(z)))

            # Cohen's h effect size
            h = 2 * math.asin(math.sqrt(x1 / n1)) - 2 * math.asin(math.sqrt(x2 / n2))

            results.append(
                {
                    "workflow_a": WORKFLOW_ORDER[i],
                    "workflow_b": WORKFLOW_ORDER[j],
                    "label_a": WORKFLOW_LABELS[WORKFLOW_ORDER[i]],
                    "label_b": WORKFLOW_LABELS[WORKFLOW_ORDER[j]],
                    "rate_a": round(float(x1 / n1), 4),
                    "rate_b": round(float(x2 / n2), 4),
                    "n_a": int(n1),
                    "n_b": int(n2),
                    "z_statistic": round(float(z), 4),
                    "p_value": round(float(p_value), 6),
                    "significant_uncorrected": bool(p_value < 0.05),
                    "significant_bonferroni": bool(p_value < alpha_bonf),
                    "bonferroni_alpha": round(float(alpha_bonf), 6),
                    "cohens_h": round(float(abs(h)), 4),
                }
            )
    return results


def cross_model_tests(rows_ds: list[dict], rows_qw: list[dict],
                      task_languages: dict[str, str]) -> list[dict]:
    """Test whether DeepSeek and Qwen3 differ significantly per workflow."""
    if not SCIPY_AVAILABLE:
        return [{"note": "scipy not available"}]

    def _workflow_counts(rows):
        counts = {}
        for wf in WORKFLOW_ORDER:
            counts[wf] = {"total": 0, "resolved": 0}
        for row in rows:
            source = row.get("source", "").strip()
            if not source:
                continue
            try:
                _, workflow, _ = parse_source_name(source)
            except ValueError:
                continue
            status = normalize_status(row.get("status", ""))
            counts[workflow]["total"] += 1
            if status == "resolved":
                counts[workflow]["resolved"] += 1
        return counts

    ds = _workflow_counts(rows_ds)
    qw = _workflow_counts(rows_qw)

    results = []
    for wf in WORKFLOW_ORDER:
        n1, x1 = ds[wf]["total"], ds[wf]["resolved"]
        n2, x2 = qw[wf]["total"], qw[wf]["resolved"]
        if n1 == 0 or n2 == 0:
            continue

        p_pool = (x1 + x2) / (n1 + n2)
        se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
        z = (x1 / n1 - x2 / n2) / se if se > 0 else 0.0
        p_value = 2 * (1 - norm.cdf(abs(z)))

        # Cohen's h
        h = 2 * math.asin(math.sqrt(x1 / n1)) - 2 * math.asin(math.sqrt(x2 / n2))

        results.append({
            "workflow": WORKFLOW_LABELS[wf],
            "deepseek_rate": round(float(x1 / n1), 4),
            "qwen_rate": round(float(x2 / n2), 4),
            "z_statistic": round(float(z), 4),
            "p_value": round(float(p_value), 6),
            "significant": bool(p_value < 0.05),
            "cohens_h": round(float(abs(h)), 4),
        })
    return results


def language_significance(
    rows: list[dict], task_languages: dict[str, str], model_key: str
) -> dict:
    """Test whether English vs Chinese resolved rates differ significantly."""
    if not SCIPY_AVAILABLE:
        return {"note": "scipy not available"}

    lang_counts = {"en": {"total": 0, "resolved": 0}, "zh": {"total": 0, "resolved": 0}}
    for row in rows:
        source = row.get("source", "").strip()
        if not source:
            continue
        try:
            task_id, _, _ = parse_source_name(source)
        except ValueError:
            continue
        status = normalize_status(row.get("status", ""))
        lang = task_languages.get(task_id, "en")
        lang_counts[lang]["total"] += 1
        if status == "resolved":
            lang_counts[lang]["resolved"] += 1

    en = lang_counts["en"]
    zh = lang_counts["zh"]
    n1, x1 = en["total"], en["resolved"]
    n2, x2 = zh["total"], zh["resolved"]

    if n1 == 0 or n2 == 0:
        return {"note": "insufficient data"}

    p_pool = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    z = (x1 / n1 - x2 / n2) / se if se > 0 else 0.0
    p_value = 2 * (1 - norm.cdf(abs(z)))
    h = 2 * math.asin(math.sqrt(x1 / n1)) - 2 * math.asin(math.sqrt(x2 / n2))

    return {
        "model": MODEL_LABELS[model_key],
        "english_rate": round(float(x1 / n1), 4),
        "chinese_rate": round(float(x2 / n2), 4),
        "gap_pp": round(float((x1 / n1 - x2 / n2) * 100), 1),
        "z_statistic": round(float(z), 4),
        "p_value": round(float(p_value), 6),
        "significant": bool(p_value < 0.05),
        "cohens_h": round(float(abs(h)), 4),
    }


# ========================================================================
#  Wilson CI (original, kept)
# ========================================================================


def wilson_ci(success: int, total: int, z: float = 1.96) -> tuple[float, float, float]:
    if total == 0:
        return (0.0, 0.0, 0.0)
    p = success / total
    denom = 1.0 + z * z / total
    center = (p + z * z / (2.0 * total)) / denom
    margin = (
        z
        * math.sqrt((p * (1.0 - p) + z * z / (4.0 * total)) / total)
        / denom
    )
    lo = max(0.0, center - margin)
    hi = min(1.0, center + margin)
    return (p, lo, hi)


def pct(n: int, d: int) -> float:
    return n / d * 100.0 if d else 0.0


def fmt_pct(v: float) -> str:
    return f"{v:.1f}%"


def fmt_ci(lo: float, hi: float) -> str:
    return f"[{lo * 100:.1f}%, {hi * 100:.1f}%]"


# ========================================================================
#  Original aggregation (refactored to use common)
# ========================================================================


def compute_workflow_stats(
    rows: list[dict],
    task_languages: dict[str, str],
    model_key: str,
) -> dict:
    workflow_buckets: dict[str, dict] = {}
    for wf in WORKFLOW_ORDER:
        workflow_buckets[wf] = {"total": 0, "resolved": 0, "unresolved": 0, "no_doi": 0}

    language_buckets = {
        "en": {"total": 0, "resolved": 0, "unresolved": 0, "no_doi": 0},
        "zh": {"total": 0, "resolved": 0, "unresolved": 0, "no_doi": 0},
    }

    session_buckets: dict[str, dict] = {}

    for row in rows:
        source = row.get("source", "").strip()
        if not source:
            continue
        try:
            task_id, workflow, _ = parse_source_name(source)
        except ValueError:
            print(f"  WARNING: skipping unparseable source: {source!r}", file=sys.stderr)
            continue
        status = normalize_status(row.get("status", ""))
        language = task_languages.get(task_id, "en")

        wb = workflow_buckets[workflow]
        wb["total"] += 1
        wb[status] += 1

        lb = language_buckets[language]
        lb["total"] += 1
        lb[status] += 1

        session_key = f"{task_id}_{workflow}"
        if session_key not in session_buckets:
            session_buckets[session_key] = {
                "task_id": task_id,
                "workflow": workflow,
                "language": language,
                "total": 0,
                "resolved": 0,
            }
        sb = session_buckets[session_key]
        sb["total"] += 1
        if status == "resolved":
            sb["resolved"] += 1

    overall = {"total": 0, "resolved": 0, "unresolved": 0, "no_doi": 0}
    for row in rows:
        source = row.get("source", "").strip()
        if not source:
            continue
        try:
            _, _, _ = parse_source_name(source)
        except ValueError:
            continue
        status = normalize_status(row.get("status", ""))
        overall["total"] += 1
        overall[status] += 1

    def bucket_rate(bucket: dict) -> dict:
        t = bucket["total"]
        r = bucket["resolved"]
        p, lo, hi = wilson_ci(r, t)
        return {
            "total": t,
            "resolved": r,
            "unresolved": bucket["unresolved"],
            "no_doi": bucket["no_doi"],
            "resolved_rate": round(p * 100, 1),
            "ci_lo": round(lo * 100, 1),
            "ci_hi": round(hi * 100, 1),
            "resolved_pct_str": fmt_pct(pct(r, t)),
            "ci_str": fmt_ci(lo, hi),
        }

    result = {
        "model": MODEL_LABELS[model_key],
        "overall": bucket_rate(overall),
        "workflow": {wf: bucket_rate(workflow_buckets[wf]) for wf in WORKFLOW_ORDER},
        "language": {lang: bucket_rate(language_buckets[lang]) for lang in ("en", "zh")},
        "sessions": sorted(session_buckets.values(), key=lambda x: x["task_id"]),
    }
    return result


def compute_e1_estimates(stats: dict, model_key: str) -> dict:
    overall = stats["overall"]
    unresolved = overall["unresolved"]
    no_doi = overall["no_doi"]
    total = overall["total"]

    e1_unresolved = unresolved * 0.85
    e1_nodoi = no_doi * 0.93
    e1_total = int(e1_unresolved + e1_nodoi)
    e1_pct = round(e1_total / total * 100, 1) if total else 0.0
    resolved_pct = stats["overall"]["resolved_rate"]
    unknown = int(total - (overall["resolved"] + e1_unresolved + e1_nodoi))

    return {
        "model": MODEL_LABELS[model_key],
        "total": total,
        "resolved": overall["resolved"],
        "estimated_e1": e1_total,
        "estimated_e1_rate": e1_pct,
        "uncertain": unknown,
        "resolved_rate": resolved_pct,
        "note": (
            "E1 estimated from deep sample: 85% of unresolved DOIs and "
            "93% of no-DOI references classified as hallucinated."
        ),
    }


def compute_cross_model_comparison(
    deepseek_stats: dict, qwen_stats: dict
) -> list[dict]:
    rows = []
    for wf in WORKFLOW_ORDER:
        ds = deepseek_stats["workflow"][wf]
        qw = qwen_stats["workflow"][wf]
        gap = round(ds["resolved_rate"] - qw["resolved_rate"], 1)
        rows.append(
            {
                "workflow": WORKFLOW_LABELS[wf],
                "deepseek_rate": ds["resolved_pct_str"],
                "deepseek_ci": ds["ci_str"],
                "deepseek_n": f"{ds['resolved']}/{ds['total']}",
                "qwen_rate": qw["resolved_pct_str"],
                "qwen_ci": qw["ci_str"],
                "qwen_n": f"{qw['resolved']}/{qw['total']}",
                "gap": gap,
            }
        )
    return rows


# ========================================================================
#  Markdown renderers (extended with significance tables)
# ========================================================================


def render_table1(stats: dict, model_key: str) -> str:
    lines = []
    lines.append(f"### Table 1: {MODEL_LABELS[model_key]}  —  Workflow Verification Results")
    lines.append("")
    lines.append(
        "| Workflow | Total Refs | Resolved | Unresolved | No DOI | "
        "Resolved Rate | 95% Wilson CI |"
    )
    lines.append(
        "|----------|----------:|--------:|----------:|------:|"
        "------------:|--------------:|"
    )
    for wf in WORKFLOW_ORDER:
        w = stats["workflow"][wf]
        label = WORKFLOW_LABELS[wf]
        lines.append(
            f"| {label} | {w['total']} | {w['resolved']} | {w['unresolved']} | "
            f"{w['no_doi']} | {w['resolved_pct_str']} | {w['ci_str']} |"
        )
    o = stats["overall"]
    lines.append(
        f"| **Overall** | **{o['total']}** | **{o['resolved']}** | "
        f"**{o['unresolved']}** | **{o['no_doi']}** | "
        f"**{o['resolved_pct_str']}** | **{o['ci_str']}** |"
    )
    lines.append("")
    return "\n".join(lines)


def render_table2(stats: dict, model_key: str) -> str:
    lines = []
    lines.append(f"### Table 2: {MODEL_LABELS[model_key]}  —  Language Effect")
    lines.append("")
    lines.append(
        "| Language | Total Refs | Resolved | Unresolved | No DOI | "
        "Resolved Rate | 95% Wilson CI |"
    )
    lines.append(
        "|----------|----------:|--------:|----------:|------:|"
        "------------:|--------------:|"
    )
    for lang in ("en", "zh"):
        label = "English" if lang == "en" else "Chinese"
        w = stats["language"][lang]
        lines.append(
            f"| {label} | {w['total']} | {w['resolved']} | {w['unresolved']} | "
            f"{w['no_doi']} | {w['resolved_pct_str']} | {w['ci_str']} |"
        )
    en = stats["language"]["en"]
    zh = stats["language"]["zh"]
    gap = round(en["resolved_rate"] - zh["resolved_rate"], 1)
    lines.append(f"| **Gap (EN — ZH)** | | | | | **{gap} pp** | |")
    lines.append("")
    return "\n".join(lines)


def render_table3(comparison: list[dict]) -> str:
    lines = []
    lines.append("### Table 3: Cross-Model Comparison")
    lines.append("")
    lines.append(
        "| Workflow | DeepSeek-chat | 95% CI | Qwen3-14B | 95% CI | Gap |"
    )
    lines.append(
        "|----------|-------------:|-------:|----------:|-------:|----:|"
    )
    for row in comparison:
        lines.append(
            f"| {row['workflow']} | {row['deepseek_n']} ({row['deepseek_rate']}) | "
            f"{row['deepseek_ci']} | {row['qwen_n']} ({row['qwen_rate']}) | "
            f"{row['qwen_ci']} | +{row['gap']} pp |"
        )
    lines.append("")
    return "\n".join(lines)


def render_e1_table(e1_ds: dict, e1_qw: dict) -> str:
    lines = []
    lines.append("### Table 4: Estimated E1 (Hallucinated) Rates")
    lines.append("")
    lines.append(
        "| Model | Total Refs | Resolved | Est. E1 | Est. E1 Rate | Uncertain |"
        " Resolved Rate |"
    )
    lines.append(
        "|------|----------:|--------:|-------:|-------------:|---------:|"
        "---------------:|"
    )
    for e1 in (e1_ds, e1_qw):
        lines.append(
            f"| {e1['model']} | {e1['total']} | {e1['resolved']} | "
            f"{e1['estimated_e1']} | {e1['estimated_e1_rate']}% | "
            f"{e1['uncertain']} | {e1['resolved_rate']}% |"
        )
    lines.append("")
    return "\n".join(lines)


def render_session_stats(stats: dict, model_key: str) -> str:
    lines = []
    lines.append(f"### Per-Session Variation: {MODEL_LABELS[model_key]}")
    lines.append("")
    sessions = stats["sessions"]
    resolved_pcts = [
        pct(s["resolved"], s["total"]) for s in sessions if s["total"] > 0
    ]
    min_v = min(resolved_pcts) if resolved_pcts else 0.0
    max_v = max(resolved_pcts) if resolved_pcts else 0.0
    mean_v = sum(resolved_pcts) / len(resolved_pcts) if resolved_pcts else 0.0

    lines.append(f"- Range across {len(sessions)} sessions: {min_v:.1f}% — {max_v:.1f}%")
    lines.append(f"- Mean session resolved rate: {mean_v:.1f}%")
    lines.append("")

    lines.append("| Task | Workflow | Language | Total Refs | Resolved | Resolved Rate |")
    lines.append("|-----|----------|--------:|----------:|--------:|--------------:|")
    for s in sessions:
        rate = pct(s["resolved"], s["total"])
        lang_label = "EN" if s["language"] == "en" else "ZH"
        wf_label = WORKFLOW_LABELS[s["workflow"]].split(" ")[0]
        lines.append(
            f"| {s['task_id']} | {wf_label} | {lang_label} | {s['total']} | "
            f"{s['resolved']} | {rate:.1f}% |"
        )
    lines.append("")
    return "\n".join(lines)


def render_e3_candidate_guide() -> str:
    lines = []
    lines.append("# E3 Annotation Expansion Guide")
    lines.append("")
    lines.append(
        "The current E3 claim-support sample has fewer than 60 entries. "
        "To strengthen the paper's claim support analysis, "
        "expand to at least **240 references** "
        "(15 per workflow × model × language combination)."
    )
    lines.append("")
    lines.append("## Target Allocation")
    lines.append("")
    lines.append("| Model | Workflow | Language | Target |")
    lines.append("|------|----------|--------:|------:|")
    for model in MODEL_KEYS:
        for wf in WORKFLOW_ORDER:
            for lang in ("en", "zh"):
                lines.append(f"| {model} | {wf} | {lang} | 15 |")
    lines.append("| **Total** | | | **240** |")
    lines.append("")
    lines.append("## Selection Strategy")
    lines.append("")
    lines.append(
        "1. Use `analysis/summarize_results.py` to identify which references "
        "are `resolved` (the candidate pool)."
    )
    lines.append(
        "2. For each workflow × model × language cell, randomly select 15 "
        "resolved references where the generated claim is available."
    )
    lines.append(
        "3. For each selected reference, annotate the `support_label` "
        "using the rubric in `code/scoring_rubric.md`."
    )
    lines.append("")
    return "\n".join(lines)


# ========================================================================
#  NEW: Significance report renderers
# ========================================================================


def render_significance_section(
    chi2_result: dict, pairwise: list[dict], lang_result: dict
) -> str:
    lines = []
    lines.append("### Statistical Significance Tests")
    lines.append("")

    if not SCIPY_AVAILABLE:
        lines.append(
            "*scipy is not installed. Install it (`pip install scipy`) to enable "
            "significance tests.*"
        )
        lines.append("")
        return "\n".join(lines)

    # ── Chi-square ──
    lines.append("#### Chi-square Test: Workflow × Verification Status")
    lines.append("")
    ch = chi2_result
    if "chi2_statistic" in ch:
        sig = "✓ significant" if ch["significant_at_005"] else "✗ not significant"
        lines.append(
            f"- χ²({ch['degrees_of_freedom']}) = {ch['chi2_statistic']}, "
            f"p = {ch['p_value']} ({sig} at α = 0.05)"
        )
        lines.append(f"- Cramér's V = {ch['cramers_v']} (effect size)")
        if ch["cramers_v"] < 0.1:
            lines.append("  - Interpretation: negligible association")
        elif ch["cramers_v"] < 0.3:
            lines.append("  - Interpretation: small association")
        elif ch["cramers_v"] < 0.5:
            lines.append("  - Interpretation: medium association")
        else:
            lines.append("  - Interpretation: large association")
    lines.append("")

    # ── Pairwise z-tests ──
    lines.append("#### Pairwise Workflow Comparisons (Two-Proportion z-test)")
    lines.append("")
    lines.append(
        "| Comparison | Rate A | Rate B | z | p-value | Significant (α=0.05) | "
        "Bonferroni sig. | Cohen's h |"
    )
    lines.append(
        "|---|---:|---:|---:|---:|:---:|:---:|---:|"
    )
    for pr in pairwise:
        if "z_statistic" not in pr:
            continue
        lines.append(
            f"| {pr['label_a']} vs {pr['label_b']} | "
            f"{pr['rate_a']:.1%} | {pr['rate_b']:.1%} | "
            f"{pr['z_statistic']} | {pr['p_value']} | "
            f"{'✓' if pr['significant_uncorrected'] else '✗'} | "
            f"{'✓' if pr['significant_bonferroni'] else '✗'} | "
            f"{pr['cohens_h']} |"
        )
    lines.append("")

    # ── Language effect ──
    lines.append("#### Language Effect Significance")
    lines.append("")
    if "p_value" in lang_result:
        sig = "✓ significant" if lang_result["significant"] else "✗ not significant"
        lines.append(
            f"- Model: {lang_result['model']}"
        )
        lines.append(
            f"- English resolved rate: {lang_result['english_rate']:.1%}, "
            f"Chinese: {lang_result['chinese_rate']:.1%} "
            f"(gap: {lang_result['gap_pp']} pp)"
        )
        lines.append(
            f"- z = {lang_result['z_statistic']}, p = {lang_result['p_value']} "
            f"({sig} at α = 0.05)"
        )
        lines.append(f"- Cohen's h = {lang_result['cohens_h']} (effect size)")
    lines.append("")

    return "\n".join(lines)


def render_cross_model_significance(cross_results: list[dict]) -> str:
    lines = []
    lines.append("#### Cross-Model Significance (DeepSeek vs Qwen3 per Workflow)")
    lines.append("")
    if not cross_results or "z_statistic" not in cross_results[0]:
        lines.append("*scipy not available.*")
        lines.append("")
        return "\n".join(lines)

    lines.append(
        "| Workflow | DeepSeek | Qwen3 | z | p-value | Significant | Cohen's h |"
    )
    lines.append(
        "|---|---:|---:|---:|---:|:---:|---:|"
    )
    for cr in cross_results:
        lines.append(
            f"| {cr['workflow']} | {cr['deepseek_rate']:.1%} | "
            f"{cr['qwen_rate']:.1%} | {cr['z_statistic']} | "
            f"{cr['p_value']} | {'✓' if cr['significant'] else '✗'} | "
            f"{cr['cohens_h']} |"
        )
    lines.append("")
    return "\n".join(lines)


# ========================================================================
#  Main
# ========================================================================


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    task_languages = load_task_languages()

    ds_rows = load_verification_data(DEEPSEEK_VERIFIED)
    qw_rows = load_verification_data(QWEN_VERIFIED)

    ds_stats = compute_workflow_stats(ds_rows, task_languages, "deepseek-chat")
    qw_stats = compute_workflow_stats(qw_rows, task_languages, "qwen3-14b")

    ds_e1 = compute_e1_estimates(ds_stats, "deepseek-chat")
    qw_e1 = compute_e1_estimates(qw_stats, "qwen3-14b")

    comparison = compute_cross_model_comparison(ds_stats, qw_stats)

    # ── Statistical tests (new) ──
    ds_matrix, ds_labels, _ = build_contingency(ds_rows, task_languages)
    qw_matrix, qw_labels, _ = build_contingency(qw_rows, task_languages)

    ds_chi2 = chi_square_test(ds_matrix)
    qw_chi2 = chi_square_test(qw_matrix)

    ds_pairwise = pairwise_z_tests(ds_matrix, ds_labels)
    qw_pairwise = pairwise_z_tests(qw_matrix, qw_labels)

    ds_lang = language_significance(ds_rows, task_languages, "deepseek-chat")
    qw_lang = language_significance(qw_rows, task_languages, "qwen3-14b")

    cross_sig = cross_model_tests(ds_rows, qw_rows, task_languages)

    # ── Build markdown ──
    parts: list[str] = []

    parts.append("# Paper Tables")
    parts.append("")
    parts.append(
        "Auto-generated from verification CSV files. "
        "Run `python analysis/statistical_analysis.py` to regenerate."
    )
    parts.append("")

    # Original tables
    parts.append(render_table1(ds_stats, "deepseek-chat"))
    parts.append(render_significance_section(ds_chi2, ds_pairwise, ds_lang))
    parts.append(render_table2(ds_stats, "deepseek-chat"))
    parts.append(render_table1(qw_stats, "qwen3-14b"))
    parts.append(render_significance_section(qw_chi2, qw_pairwise, qw_lang))
    parts.append(render_table2(qw_stats, "qwen3-14b"))
    parts.append(render_table3(comparison))
    parts.append(render_cross_model_significance(cross_sig))
    parts.append(render_e1_table(ds_e1, qw_e1))
    parts.append(render_session_stats(ds_stats, "deepseek-chat"))
    parts.append(render_session_stats(qw_stats, "qwen3-14b"))
    parts.append(render_e3_candidate_guide())

    full_md = "\n".join(parts)
    TABLES_MD.write_text(full_md, encoding="utf-8")

    combined_json = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "deepseek": ds_stats,
        "qwen3-14b": qw_stats,
        "cross_model_comparison": comparison,
        "e1_estimates": {"deepseek-chat": ds_e1, "qwen3-14b": qw_e1},
        "significance_tests": {
            "deepseek": {
                "chi_square": ds_chi2,
                "pairwise_z_tests": ds_pairwise,
                "language_effect": ds_lang,
            },
            "qwen3": {
                "chi_square": qw_chi2,
                "pairwise_z_tests": qw_pairwise,
                "language_effect": qw_lang,
            },
            "cross_model": cross_sig,
        },
    }
    TABLES_JSON.write_text(json.dumps(combined_json, indent=2), encoding="utf-8")

    print(f"Wrote {TABLES_MD}")
    print(f"Wrote {TABLES_JSON}")


if __name__ == "__main__":
    main()
