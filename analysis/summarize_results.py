from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS_CSV = ROOT / "data" / "task_seed.csv"
DEEPSEEK_CSV = ROOT / "results" / "verified_refs_merged.csv"
QWEN_CSV = ROOT / "results" / "verified_refs_qwen.csv"
SUMMARY_MD = ROOT / "analysis" / "summary_metrics.md"
SUMMARY_JSON = ROOT / "analysis" / "summary_metrics.json"
SVG_OUT = ROOT / "docs" / "figures" / "resolved-rate-by-workflow.svg"

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
    "deepseek-chat": DEEPSEEK_CSV,
    "qwen3-14b": QWEN_CSV,
}

MODEL_LABELS = {
    "deepseek-chat": "DeepSeek-chat",
    "qwen3-14b": "Qwen3-14B",
}

MODEL_COLORS = {
    "deepseek-chat": "#1f77b4",
    "qwen3-14b": "#f28e2b",
}

SOURCE_RE = re.compile(
    r"^(?P<task_id>T\d+)_(?P<workflow>W\d+_[A-Z_]+)__"
    r"(?P<model>[^.]+)\.txt$",
    re.IGNORECASE,
)


def pct(numerator: int, denominator: int) -> float:
    return (numerator / denominator * 100.0) if denominator else 0.0


def load_task_languages() -> dict[str, str]:
    task_languages: dict[str, str] = {}
    with TASKS_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            task_languages[row["task_id"]] = row["language"]
    return task_languages


def empty_counter() -> dict[str, int]:
    return {"total": 0, "resolved": 0, "unresolved": 0, "no_doi": 0}


def normalize_status(raw_status: str) -> str:
    status = (raw_status or "").strip().lower()
    if status in {"resolved", "unresolved", "no_doi"}:
        return status
    return "unresolved"


def parse_source_name(source_name: str) -> tuple[str, str, str]:
    match = SOURCE_RE.match(source_name.strip())
    if not match:
        raise ValueError(f"Unrecognized source naming pattern: {source_name}")
    return (
        match.group("task_id"),
        match.group("workflow").upper(),
        match.group("model").lower(),
    )


def add_status(bucket: dict[str, int], status: str) -> None:
    bucket["total"] += 1
    if status not in {"resolved", "unresolved", "no_doi"}:
        status = "unresolved"
    bucket[status] += 1


def collect_summary() -> dict[str, object]:
    task_languages = load_task_languages()
    summary: dict[str, object] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "models": {},
    }

    for model_key, csv_path in MODEL_FILES.items():
        workflow_stats: dict[str, dict[str, int]] = {
            workflow: empty_counter() for workflow in WORKFLOW_ORDER
        }
        language_stats: dict[str, dict[str, int]] = {
            "en": empty_counter(),
            "zh": empty_counter(),
        }
        overall = empty_counter()

        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                source_name = row.get("source", "")
                status = normalize_status(row.get("status", ""))
                task_id, workflow, _source_model = parse_source_name(source_name)
                language = task_languages[task_id]

                add_status(overall, status)
                add_status(workflow_stats[workflow], status)
                add_status(language_stats[language], status)

        summary["models"][model_key] = {
            "overall": with_rates(overall),
            "workflow": {k: with_rates(v) for k, v in workflow_stats.items()},
            "language": {k: with_rates(v) for k, v in language_stats.items()},
        }

    return summary


def with_rates(counter: dict[str, int]) -> dict[str, float | int]:
    total = counter["total"]
    resolved = counter["resolved"]
    unresolved = counter["unresolved"]
    no_doi = counter["no_doi"]
    return {
        "total": total,
        "resolved": resolved,
        "unresolved": unresolved,
        "no_doi": no_doi,
        "resolved_rate": round(pct(resolved, total), 1),
        "unresolved_rate": round(pct(unresolved, total), 1),
        "no_doi_rate": round(pct(no_doi, total), 1),
    }


def render_markdown(summary: dict[str, object]) -> str:
    models = summary["models"]
    lines: list[str] = []
    lines.append("# Summary Metrics")
    lines.append("")
    lines.append(
        "Auto-generated from the packaged verification CSV files by "
        "`analysis/summarize_results.py`."
    )
    lines.append("")
    lines.append("## Overall By Model")
    lines.append("")
    lines.append("| Model | Total Refs | Resolved | Unresolved | No DOI | Resolved Rate |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for model_key in MODEL_FILES:
        overall = models[model_key]["overall"]
        lines.append(
            "| {model} | {total} | {resolved} | {unresolved} | {no_doi} | {rate:.1f}% |".format(
                model=MODEL_LABELS[model_key],
                total=overall["total"],
                resolved=overall["resolved"],
                unresolved=overall["unresolved"],
                no_doi=overall["no_doi"],
                rate=overall["resolved_rate"],
            )
        )

    lines.append("")
    lines.append("## By Workflow")
    lines.append("")
    lines.append("| Model | Workflow | Total Refs | Resolved | Unresolved | No DOI | Resolved Rate |")
    lines.append("|---|---|---:|---:|---:|---:|---:|")
    for model_key in MODEL_FILES:
        workflow_stats = models[model_key]["workflow"]
        for workflow in WORKFLOW_ORDER:
            stats = workflow_stats[workflow]
            lines.append(
                "| {model} | {workflow} | {total} | {resolved} | {unresolved} | {no_doi} | {rate:.1f}% |".format(
                    model=MODEL_LABELS[model_key],
                    workflow=WORKFLOW_LABELS[workflow],
                    total=stats["total"],
                    resolved=stats["resolved"],
                    unresolved=stats["unresolved"],
                    no_doi=stats["no_doi"],
                    rate=stats["resolved_rate"],
                )
            )

    lines.append("")
    lines.append("## By Language")
    lines.append("")
    lines.append("| Model | Language | Total Refs | Resolved | Unresolved | No DOI | Resolved Rate |")
    lines.append("|---|---|---:|---:|---:|---:|---:|")
    for model_key in MODEL_FILES:
        language_stats = models[model_key]["language"]
        for language in ("en", "zh"):
            stats = language_stats[language]
            label = "English" if language == "en" else "Chinese"
            lines.append(
                "| {model} | {language} | {total} | {resolved} | {unresolved} | {no_doi} | {rate:.1f}% |".format(
                    model=MODEL_LABELS[model_key],
                    language=label,
                    total=stats["total"],
                    resolved=stats["resolved"],
                    unresolved=stats["unresolved"],
                    no_doi=stats["no_doi"],
                    rate=stats["resolved_rate"],
                )
            )

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- These numbers summarize the packaged CSV tables, not the full manuscript argument.")
    lines.append("- `resolved` means a reference linked to some scholarly metadata source.")
    lines.append("- `resolved` does not guarantee perfect metadata alignment or claim support.")
    return "\n".join(lines) + "\n"


def generate_svg(summary: dict[str, object]) -> str:
    models = summary["models"]
    rates = {
        model_key: [
            models[model_key]["workflow"][workflow]["resolved_rate"]
            for workflow in WORKFLOW_ORDER
        ]
        for model_key in MODEL_FILES
    }

    width = 860
    height = 420
    left = 80
    right = 30
    top = 50
    bottom = 85
    chart_width = width - left - right
    chart_height = height - top - bottom
    max_rate = 100.0
    group_width = chart_width / len(WORKFLOW_ORDER)
    bar_width = 42
    intra_gap = 16

    def y_from_rate(rate: float) -> float:
        return top + chart_height - (rate / max_rate) * chart_height

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">'
    )
    parts.append("<title id=\"title\">Resolved citation rate by workflow</title>")
    parts.append(
        "<desc id=\"desc\">Grouped bar chart comparing DeepSeek-chat and Qwen3-14B "
        "across four workflows.</desc>"
    )
    parts.append(f'<rect width="{width}" height="{height}" fill="#ffffff"/>')
    parts.append(
        '<text x="80" y="28" font-family="Arial, sans-serif" font-size="20" '
        'font-weight="700" fill="#111827">Resolved Rate by Workflow</text>'
    )
    parts.append(
        '<text x="80" y="46" font-family="Arial, sans-serif" font-size="12" '
        'fill="#4b5563">Packaged verification tables only</text>'
    )

    for tick in range(0, 101, 20):
        y = y_from_rate(float(tick))
        parts.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" '
            'stroke="#e5e7eb" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{left - 10}" y="{y + 4:.1f}" text-anchor="end" '
            'font-family="Arial, sans-serif" font-size="11" fill="#6b7280">'
            f"{tick}%</text>"
        )

    parts.append(
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + chart_height}" '
        'stroke="#111827" stroke-width="1.5"/>'
    )
    parts.append(
        f'<line x1="{left}" y1="{top + chart_height}" x2="{width - right}" '
        f'y2="{top + chart_height}" stroke="#111827" stroke-width="1.5"/>'
    )

    legend_x = width - 250
    legend_y = 24
    for index, model_key in enumerate(MODEL_FILES):
        y = legend_y + index * 18
        color = MODEL_COLORS[model_key]
        label = MODEL_LABELS[model_key]
        parts.append(
            f'<rect x="{legend_x}" y="{y - 10}" width="12" height="12" fill="{color}" rx="2"/>'
        )
        parts.append(
            f'<text x="{legend_x + 18}" y="{y}" font-family="Arial, sans-serif" '
            f'font-size="12" fill="#374151">{label}</text>'
        )

    for i, workflow in enumerate(WORKFLOW_ORDER):
        group_x = left + i * group_width
        group_center = group_x + group_width / 2
        start_x = group_center - (bar_width * 2 + intra_gap) / 2

        for j, model_key in enumerate(MODEL_FILES):
            rate = rates[model_key][i]
            bar_x = start_x + j * (bar_width + intra_gap)
            bar_y = y_from_rate(rate)
            bar_h = top + chart_height - bar_y
            color = MODEL_COLORS[model_key]
            parts.append(
                f'<rect x="{bar_x:.1f}" y="{bar_y:.1f}" width="{bar_width}" height="{bar_h:.1f}" '
                f'fill="{color}" rx="4"/>'
            )
            parts.append(
                f'<text x="{bar_x + bar_width / 2:.1f}" y="{bar_y - 8:.1f}" text-anchor="middle" '
                'font-family="Arial, sans-serif" font-size="11" fill="#111827">'
                f"{rate:.1f}%</text>"
            )

        parts.append(
            f'<text x="{group_center:.1f}" y="{height - 42}" text-anchor="middle" '
            'font-family="Arial, sans-serif" font-size="12" font-weight="700" fill="#111827">'
            f"W{i}</text>"
        )
        parts.append(
            f'<text x="{group_center:.1f}" y="{height - 26}" text-anchor="middle" '
            'font-family="Arial, sans-serif" font-size="11" fill="#4b5563">'
            f"{WORKFLOW_LABELS[workflow].split(' ', 1)[1]}</text>"
        )

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def write_outputs(summary: dict[str, object]) -> None:
    SUMMARY_MD.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    SVG_OUT.parent.mkdir(parents=True, exist_ok=True)

    SUMMARY_MD.write_text(render_markdown(summary), encoding="utf-8")
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    SVG_OUT.write_text(generate_svg(summary), encoding="utf-8")


def main() -> None:
    summary = collect_summary()
    write_outputs(summary)
    print(f"Wrote {SUMMARY_MD}")
    print(f"Wrote {SUMMARY_JSON}")
    print(f"Wrote {SVG_OUT}")


if __name__ == "__main__":
    main()
