# Data Lineage

This document traces the flow of data from raw inputs through processing steps to final outputs.

## Flow Diagram

```
                    ┌─────────────────┐
                    │  task_seed.csv   │
                    │  (30 questions)  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ build_prompts.py│
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   prompts.csv   │
                    │   (240 prompts) │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐       ┌───────────────────┐
                    │ Model API Calls │──────►│  Raw .txt outputs │
                    │ (DeepSeek/Qwen) │       │  (not bundled)    │
                    └────────┬────────┘       └───────────────────┘
                             │
                    ┌────────▼────────┐
                    │  extract refs   │
                    │  (verify_citations.py --extract)
                    └────────┬────────┘
                             │
             ┌───────────────┼───────────────┐
             │               │               │
    ┌────────▼───────┐ ┌────▼────────┐ ┌────▼────────┐
    │extracted_refs_ │ │extracted_refs│ │extracted_refs│
    │ deepseek.csv   │ │ _qwen.csv   │ │ _chatgpt.csv │
    │ (bundled as    │ │ (bundled)   │ │ (future)     │
    │ verified_refs_ │ │             │ │              │
    │ merged.csv)    │ │             │ │              │
    └────────┬───────┘ └────┬────────┘ └────┬────────┘
             │              │               │
    ┌────────▼───────┐ ┌────▼────────┐      │
    │ verify refs    │ │ verify refs │      │
    │(--online)      │ │(--online)   │      │
    └────────┬───────┘ └────┬────────┘      │
             │              │               │
    ┌────────▼───────┐ ┌────▼────────┐      │
    │verified_refs_  │ │verified_refs│      │
    │ merged.csv     │ │ _qwen.csv   │      │
    │(DeepSeek)      │ │ (Qwen3)     │      │
    └────────┬───────┘ └────┬────────┘      │
             │              │               │
             └──────┬───────┘               │
                    │                       │
           ┌────────▼────────┐              │
           │  summarizer &   │              │
           │  stats analysis │              │
           │  ┌──────────────┴──────────────┘
           │  │
           │  │  summarize_results.py  ───► summary_metrics.[md|json]
           │  │                               SVG bar chart
           │  │
           │  │  statistical_analysis.py ──► paper_tables.[md|json]
           │  │                               + significance tests
           │  │
           │  │  sensitivity_analysis.py ──► sensitivity_analysis.[md|json]
           │  │
           │  │  visualizations.py ───────► forest plot, heatmap,
           │  │                               session scatter, stacked bar
           │  │
           │  │  validate_integrity.py ───► data integrity report
           │  │
           │  └──────────────────────────────────────────
           │
           │         Manuscript
           │         paper_submission.md
           │         paper_submission.tex
           │
           ▼
    ┌─────────────────┐
    │  Final outputs  │
    └─────────────────┘
```

## File Dependencies

| File | Depends on | Generated by |
|------|-----------|-------------|
| `data/prompts.csv` | `data/task_seed.csv` | `code/build_prompts.py` |
| Raw `.txt` outputs | `data/prompts.csv` + API calls | External API (not bundled) |
| `results/extracted_refs_qwen.csv` | Raw `.txt` outputs | `code/verify_citations.py extract` |
| `results/verified_refs_merged.csv` | Raw `.txt` outputs + API | `code/verify_citations.py verify` (DeepSeek) |
| `results/verified_refs_qwen.csv` | `results/extracted_refs_qwen.csv` + API | `code/verify_citations.py verify` (Qwen3) |
| `analysis/summary_metrics.md` | Verification CSVs | `analysis/summarize_results.py` |
| `analysis/summary_metrics.json` | Verification CSVs | `analysis/summarize_results.py` |
| `analysis/generated/paper_tables.md` | Verification CSVs | `analysis/statistical_analysis.py` |
| `analysis/generated/paper_tables.json` | Verification CSVs | `analysis/statistical_analysis.py` |
| `analysis/generated/sensitivity_analysis.md` | Verification CSVs | `analysis/sensitivity_analysis.py` |
| `analysis/generated/sensitivity_analysis.json` | Verification CSVs | `analysis/sensitivity_analysis.py` |
| `docs/figures/*.svg` | Verification CSVs | `analysis/summarize_results.py` / `analysis/visualizations.py` |

## Data Quality Checks

The `analysis/validate_integrity.py` script performs:
- Consistent task IDs across all CSV files
- Correct workflow names
- Per-session citation counts within expected bounds
- Cross-file consistency between extraction and verification tables
- Total reference count matches manuscript claims
