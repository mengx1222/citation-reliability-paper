# Analysis Utilities

This folder contains lightweight re-analysis code for the packaged verification results.

## Included

- [summarize_results.py](summarize_results.py)
  - reads the packaged verification CSV files
  - reconstructs per-model, per-workflow, and per-language counts
  - writes Markdown and JSON summaries
  - generates a small SVG figure for the README

## Run

```bash
python analysis/summarize_results.py
```

## Outputs

- [summary_metrics.md](summary_metrics.md)
- [summary_metrics.json](summary_metrics.json)
- [../docs/figures/resolved-rate-by-workflow.svg](../docs/figures/resolved-rate-by-workflow.svg)

The goal here is not a full statistical paper pipeline. It is a compact audit layer that helps a reviewer verify that the packaged CSV files support the headline workflow comparisons.
