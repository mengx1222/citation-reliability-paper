# Reproduction Guide

This document separates what can be reproduced **immediately from packaged artifacts** from what requires **new model generations**.

## 1. Reproduce The Packaged Analysis

This is the fastest way to audit the current repository state.

### Inputs already included

- [data/task_seed.csv](data/task_seed.csv)
- [data/prompts.csv](data/prompts.csv)
- [results/verified_refs_merged.csv](results/verified_refs_merged.csv)
- [results/verified_refs_qwen.csv](results/verified_refs_qwen.csv)
- [results/extracted_refs_qwen.csv](results/extracted_refs_qwen.csv)

### Command

```bash
python analysis/summarize_results.py
```

### Outputs regenerated

- [analysis/summary_metrics.md](analysis/summary_metrics.md)
- [analysis/summary_metrics.json](analysis/summary_metrics.json)
- [docs/figures/resolved-rate-by-workflow.svg](docs/figures/resolved-rate-by-workflow.svg)

This path lets a reviewer verify that the packaged CSV files are internally consistent with the summarized workflow and language tables.

## 2. Rebuild The Prompt Set

The prompt generation step is fully reproducible from the repo.

### Command

```bash
python code/build_prompts.py
```

### Expected artifact

- [data/prompts.csv](data/prompts.csv)

The script expands 30 task seeds across four workflows.

## 3. Re-run Reference Extraction On Raw Model Outputs

If you have the raw `.txt` generations from a model run, you can re-run extraction locally.

### Recommended folder convention

```text
outputs/
├── deepseek/
└── qwen/
```

Each file should follow the existing naming style:

```text
T001_W0_DIRECT__deepseek-chat.txt
T001_W0_DIRECT__qwen3-14b.txt
```

### Command

```bash
python code/verify_citations.py extract --outputs-dir outputs/qwen --out results/extracted_refs_qwen.csv
```

You can use the same pattern for any other model output directory.

## 4. Re-run Metadata Verification

Once you have an extracted reference table, you can re-run the API-backed verification stage.

### Command

```bash
python code/verify_citations.py verify --input results/extracted_refs_qwen.csv --out results/verified_refs_qwen.csv --online
```

### What this stage checks

1. DOI exact match via Crossref
2. DOI lookup via OpenAlex
3. arXiv metadata recovery for `10.48550/arXiv.*`
4. DOI resolution check
5. Title-based fallback matching when DOI-based verification fails

## 5. What Is Not Yet Fully Reproducible From This Repo Alone

The following steps are **not** fully bundled today:

- sending all prompts to each external model provider
- storing the full 240 raw generations in the repo
- rerunning the exact historical API calls with the same provider state, access policy, and model snapshot
- regenerating every manuscript table from a single orchestrated pipeline

That means the current repository is strongest as a **re-analysis and verification package**, not yet as a fully self-contained benchmark runner.

## 6. Reviewer Checklist

If you are reviewing the repo for research credibility, the quickest path is:

1. Read [docs/methodology.md](docs/methodology.md)
2. Run `python analysis/summarize_results.py`
3. Compare [analysis/summary_metrics.md](analysis/summary_metrics.md) with the claims in [paper_submission.md](paper_submission.md)
4. Inspect several rows in the verification CSV files for obvious metadata mismatches
5. Check [data/e3_annotation_sample.csv](data/e3_annotation_sample.csv) to understand the claim-support extension path
