"""Visualizations for the citation reliability study.

Generates:
1. Forest plot: resolved rate + 95% CI per workflow, both models
2. Language × Workflow heatmap
3. Per-session resolved rate scatter plot
"""

from __future__ import annotations
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from common import (
    MODEL_COLORS,
    MODEL_LABELS,
    MODEL_KEYS,
    OUTPUT_DIR,
    TABLES_JSON,
    WORKFLOW_LABELS,
    WORKFLOW_ORDER,
)

FIGS_DIR = Path(__file__).resolve().parents[1] / "docs" / "figures"
FIGS_DIR.mkdir(parents=True, exist_ok=True)


def load_data() -> dict:
    with TABLES_JSON.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    # Remap from 'deepseek'/'qwen3-14b' to short display keys
    return {
        "deepseek-chat": raw["deepseek"],
        "qwen3-14b": raw["qwen3-14b"],
    }


# ── 1. Forest plot ──────────────────────────────────────────────────────


def forest_plot(data: dict) -> str:
    """Resolved rate with Wilson CI per workflow, both models side by side."""
    fig, ax = plt.subplots(figsize=(10, 6))

    models = MODEL_KEYS
    n_workflows = len(WORKFLOW_ORDER)

    for m_idx, model in enumerate(models):
        stats = data[model]
        y_positions = []
        rates = []
        ci_los = []
        ci_his = []

        for w_idx, wf in enumerate(WORKFLOW_ORDER):
            w = stats["workflow"][wf]
            rates.append(w["resolved_rate"])
            ci_los.append(w["ci_lo"])
            ci_his.append(w["ci_hi"])
            # Offset the two models vertically within each workflow group
            y = w_idx * 2 + (0.5 if m_idx == 0 else -0.5)
            y_positions.append(y)

        color = MODEL_COLORS[model]
        label = MODEL_LABELS[model]

        for i in range(n_workflows):
            ax.plot(
                [ci_los[i], ci_his[i]],
                [y_positions[i], y_positions[i]],
                color=color,
                linewidth=2,
                marker="_",
                markersize=8,
            )
        ax.scatter(rates, y_positions, color=color, s=80, zorder=5, label=label)

    # Y-axis labels
    wf_centers = [w * 2 for w in range(n_workflows)]
    ax.set_yticks(wf_centers)
    ax.set_yticklabels([WORKFLOW_LABELS[wf] for wf in WORKFLOW_ORDER])
    ax.set_xlabel("Resolved Rate (%)")
    ax.set_title("Citation Resolved Rate by Workflow with 95% Wilson CI")
    ax.legend(loc="lower right")
    ax.grid(axis="x", alpha=0.3)
    ax.set_xlim(-5, 105)
    ax.axvline(0, color="gray", linewidth=0.5)

    plt.tight_layout()
    path = FIGS_DIR / "forest-plot-by-workflow.svg"
    fig.savefig(path, format="svg", bbox_inches="tight")
    plt.close(fig)
    print(f"  Wrote {path}")
    return str(path)


# ── 2. Language × Workflow heatmap ─────────────────────────────────────


def language_workflow_heatmap(data: dict) -> str:
    """Heatmap showing resolved rate for each workflow × language combination."""
    from common import load_task_languages

    task_languages = load_task_languages()

    # Build per-workflow-per-language resolved rates from source data
    import csv

    from common import DEEPSEEK_VERIFIED, QWEN_VERIFIED, normalize_status, parse_source_name

    def _compute_grid(csv_path: Path) -> np.ndarray:
        counts: dict = {}
        for wf in WORKFLOW_ORDER:
            counts[wf] = {"en": {"total": 0, "resolved": 0}, "zh": {"total": 0, "resolved": 0}}
        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                source = row.get("source", "").strip()
                if not source:
                    continue
                try:
                    task_id, workflow, _ = parse_source_name(source)
                except ValueError:
                    continue
                status = normalize_status(row.get("status", ""))
                lang = task_languages.get(task_id, "en")
                if workflow in counts and lang in counts[workflow]:
                    counts[workflow][lang]["total"] += 1
                    if status == "resolved":
                        counts[workflow][lang]["resolved"] += 1
        grid = np.zeros((len(WORKFLOW_ORDER), 2))
        for i, wf in enumerate(WORKFLOW_ORDER):
            for j, lang in enumerate(["en", "zh"]):
                c = counts[wf][lang]
                grid[i, j] = c["resolved"] / c["total"] * 100 if c["total"] > 0 else 0.0
        return grid

    fig, axes = plt.subplots(1, 2, figsize=(10, 5), sharey=True)

    for idx, (ax, model) in enumerate(zip(axes, MODEL_KEYS)):
        csv_path = DEEPSEEK_VERIFIED if model == "deepseek-chat" else QWEN_VERIFIED
        grid = _compute_grid(csv_path)

        im = ax.imshow(grid, cmap="RdYlGn", aspect="auto", vmin=0, vmax=100)

        ax.set_xticks(range(2))
        ax.set_xticklabels(["English", "Chinese"])
        ax.set_yticks(range(len(WORKFLOW_ORDER)))
        ax.set_yticklabels([WORKFLOW_LABELS[wf] for wf in WORKFLOW_ORDER])
        ax.set_title(MODEL_LABELS[model])

        # Annotate cells
        for i in range(len(WORKFLOW_ORDER)):
            for j in range(2):
                val = grid[i, j]
                ax.text(
                    j, i, f"{val:.1f}%",
                    ha="center", va="center",
                    color="white" if val < 60 else "black",
                    fontsize=11, fontweight="bold",
                )

    fig.colorbar(im, ax=axes, label="Resolved Rate (%)", shrink=0.6)
    fig.suptitle("Resolved Rate by Workflow and Language", fontsize=14)
    plt.tight_layout()
    path = FIGS_DIR / "language-workflow-heatmap.svg"
    fig.savefig(path, format="svg", bbox_inches="tight")
    plt.close(fig)
    print(f"  Wrote {path}")
    return str(path)


# ── 3. Per-session scatter plot ─────────────────────────────────────────


def session_scatter(data: dict) -> str:
    """Scatter plot of resolved rate per session (task × workflow)."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)

    for idx, (ax, model) in enumerate(zip(axes, MODEL_KEYS)):
        stats = data[model]
        sessions = stats["sessions"]

        # Color by language
        colors = ["#2196F3" if s["language"] == "en" else "#FF5722" for s in sessions]
        rates = [s["resolved"] / s["total"] * 100 if s["total"] > 0 else 0 for s in sessions]

        x_positions = range(len(sessions))
        ax.scatter(x_positions, rates, c=colors, s=60, alpha=0.8, edgecolors="black", linewidth=0.5)
        ax.axhline(stats["overall"]["resolved_rate"], color="gray", linestyle="--", alpha=0.7, label="Overall mean")

        ax.set_xticks(x_positions)
        ax.set_xticklabels([s["task_id"] for s in sessions], rotation=90, fontsize=7)
        ax.set_ylabel("Resolved Rate (%)")
        ax.set_title(MODEL_LABELS[model])
        ax.legend(fontsize=9)
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle("Per-Session Citation Resolved Rate", fontsize=14)
    plt.tight_layout()
    path = FIGS_DIR / "session-scatter.svg"
    fig.savefig(path, format="svg", bbox_inches="tight")
    plt.close(fig)
    print(f"  Wrote {path}")
    return str(path)


# ── 4. Resolution source stacked bar ────────────────────────────────────


def resolution_source_stacked(data: dict) -> str:
    """Stacked bar chart showing how references were resolved per workflow.

    Reads the detailed verification status from the JSON for one model.
    """
    import csv

    from common import DEEPSEEK_VERIFIED, QWEN_VERIFIED, parse_source_name

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)

    status_categories = [
        "crossref_doi",
        "openalex_doi",
        "arxiv_doi",
        "title_fallback",
        "doi_only",
        "unresolved",
        "no_doi",
    ]
    category_colors = {
        "crossref_doi": "#2ecc71",
        "openalex_doi": "#3498db",
        "arxiv_doi": "#9b59b6",
        "title_fallback": "#f39c12",
        "doi_only": "#1abc9c",
        "unresolved": "#e74c3c",
        "no_doi": "#95a5a6",
    }

    def _count_sources(csv_path: Path) -> dict:
        counts = {wf: {cat: 0 for cat in status_categories} for wf in WORKFLOW_ORDER}
        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                source = row.get("source", "").strip()
                if not source:
                    continue
                try:
                    _, workflow, _ = parse_source_name(source)
                except ValueError:
                    continue
                doi = row.get("doi_in_text", "").strip()
                meta = row.get("metadata_match_source", "").strip()
                status = row.get("status", "").strip().lower()
                doi_resolves = row.get("doi_resolves", "").strip().lower() == "true"

                if status == "no_doi" or not doi:
                    counts[workflow]["no_doi"] += 1
                elif "unresolved" in status:
                    counts[workflow]["unresolved"] += 1
                elif "crossref" in meta:
                    counts[workflow]["crossref_doi"] += 1
                elif "openalex" in meta:
                    counts[workflow]["openalex_doi"] += 1
                elif "arxiv" in meta:
                    counts[workflow]["arxiv_doi"] += 1
                elif "title" in meta:
                    counts[workflow]["title_fallback"] += 1
                elif doi_resolves:
                    counts[workflow]["doi_only"] += 1
                else:
                    counts[workflow]["unresolved"] += 1
        return counts

    for idx, (ax, model) in enumerate(zip(axes, MODEL_KEYS)):
        csv_path = DEEPSEEK_VERIFIED if model == "deepseek-chat" else QWEN_VERIFIED
        counts = _count_sources(csv_path)

        bottom = np.zeros(len(WORKFLOW_ORDER))
        for cat in status_categories:
            values = [counts[wf][cat] for wf in WORKFLOW_ORDER]
            ax.bar(
                range(len(WORKFLOW_ORDER)), values, bottom=bottom,
                label=cat, color=category_colors[cat], width=0.6,
            )
            bottom += np.array(values)

        ax.set_xticks(range(len(WORKFLOW_ORDER)))
        ax.set_xticklabels([f"W{i}" for i in range(len(WORKFLOW_ORDER))])
        ax.set_title(MODEL_LABELS[model])
        ax.set_ylabel("Number of References")

    axes[0].legend(loc="upper right", fontsize=8)
    fig.suptitle("Resolution Source by Workflow", fontsize=14)
    plt.tight_layout()
    path = FIGS_DIR / "resolution-source-stacked.svg"
    fig.savefig(path, format="svg", bbox_inches="tight")
    plt.close(fig)
    print(f"  Wrote {path}")
    return str(path)


# ── Main ────────────────────────────────────────────────────────────────


def main() -> None:
    data = load_data()

    print("Generating visualizations...")
    forest_plot(data)
    language_workflow_heatmap(data)
    session_scatter(data)
    resolution_source_stacked(data)
    print("All visualizations generated in docs/figures/")


if __name__ == "__main__":
    main()
