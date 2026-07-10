from __future__ import annotations

import csv
import json
import math
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TASKS_CSV = ROOT / "data" / "task_seed.csv"
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

WORKFLOW_ORDER = [
    "W0_DIRECT",
    "W1_CAUTIOUS",
    "W2_RETRIEVAL_FIRST",
    "W3_VERIFY_REPAIR",
]

WORKFLOW_LABELS = {
    "W0_DIRECT": "W0 Direct",
    "W1_CAUTIOUS": "W1 Cautious",
    "W2_RETRIEVAL_FIRST": "W2 Simulated Retrieval",
    "W3_VERIFY_REPAIR": "W3 Verify-and-Repair",
}

MODEL_FILES = {
    "deepseek-chat": DEEPSEEK_VERIFIED,
    "qwen3-14b": QWEN_VERIFIED,
}

MODEL_LABELS = {
    "deepseek-chat": "DeepSeek-chat",
    "qwen3-14b": "Qwen3-14B",
}

MODEL_KEYS = ["deepseek-chat", "qwen3-14b"]

SOURCE_RE = re.compile(
    r"^(?P<task_id>T\d+)_(?P<workflow>W\d+_[A-Z_]+)__"
    r"(?P<model>[^.]+)\.txt$",
    re.IGNORECASE,
)


def load_task_languages() -> dict[str, str]:
    task_languages: dict[str, str] = {}
    with TASKS_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            task_languages[row["task_id"]] = row["language"]
    return task_languages


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


def parse_source_name(source_name: str) -> tuple[str, str, str]:
    match = SOURCE_RE.match(source_name.strip())
    if not match:
        raise ValueError(f"Unrecognized source naming pattern: {source_name}")
    return (
        match.group("task_id"),
        match.group("workflow").upper(),
        match.group("model").lower(),
    )


def normalize_status(raw_status: str) -> str:
    status = (raw_status or "").strip().lower()
    return status if status in {"resolved", "unresolved", "no_doi"} else "unresolved"


def load_verification_data(csv_path: Path) -> list[dict]:
    rows = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


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
        task_id, workflow, _ = parse_source_name(source)
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
        _, _, _ = parse_source_name(source)
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
    ds_total = comparison[0]["deepseek_n"]
    qw_total = comparison[0]["qwen_n"]
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

    lines.append(
        f"- Range across {len(sessions)} sessions: {min_v:.1f}% — {max_v:.1f}%"
    )
    lines.append(f"- Mean session resolved rate: {mean_v:.1f}%")
    lines.append("")

    lines.append(
        "| Task | Workflow | Language | Total Refs | Resolved | Resolved Rate |"
    )
    lines.append(
        "|-----|----------|--------:|----------:|--------:|--------------:|"
    )
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


def render_e3_candidate_guide(e3_sample_csv: Path) -> str:
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
                lines.append(
                    f"| {model} | {wf} | {lang} | 15 |"
                )
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
    lines.append("Required annotation fields:")
    lines.append(
        "- `workflow`, `language`, `pid`, `citation_number`, "
        "`verification_status`, `generated_claim`, "
        "`reference_text`, `support_label`, `notes`"
    )
    lines.append("")
    return "\n".join(lines)


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

    parts: list[str] = []

    parts.append("# Paper Tables")
    parts.append("")
    parts.append(
        "Auto-generated from verification CSV files. "
        "Run `python analysis/statistical_analysis.py` to regenerate."
    )
    parts.append("")

    parts.append(render_table1(ds_stats, "deepseek-chat"))
    parts.append(render_table2(ds_stats, "deepseek-chat"))
    parts.append(render_table1(qw_stats, "qwen3-14b"))
    parts.append(render_table2(qw_stats, "qwen3-14b"))
    parts.append(render_table3(comparison))
    parts.append(render_e1_table(ds_e1, qw_e1))
    parts.append(render_session_stats(ds_stats, "deepseek-chat"))
    parts.append(render_session_stats(qw_stats, "qwen3-14b"))
    parts.append(render_e3_candidate_guide(E3_SAMPLE))

    full_md = "\n".join(parts)
    TABLES_MD.write_text(full_md, encoding="utf-8")

    combined_json = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "deepseek": ds_stats,
        "qwen3-14b": qw_stats,
        "cross_model_comparison": comparison,
        "e1_estimates": {"deepseek-chat": ds_e1, "qwen3-14b": qw_e1},
    }
    TABLES_JSON.write_text(json.dumps(combined_json, indent=2), encoding="utf-8")

    print(f"Wrote {TABLES_MD}")
    print(f"Wrote {TABLES_JSON}")


if __name__ == "__main__":
    main()
