# Citation Reliability in LLM-Assisted Academic Writing

An empirical research repository for auditing how often LLM-generated academic citations can be verified against open scholarly metadata sources.

## Why This Repo Exists

LLM-assisted writing tools can produce fluent related-work paragraphs while quietly fabricating citations, mixing metadata across real papers, or omitting enough fields to make references hard to verify. This project studies that failure mode as a **workflow reliability** problem rather than a single-model anecdote.

Instead of asking only "does model X hallucinate?", this repo compares four writing workflows, two languages, and two models under a shared verification pipeline.

## At A Glance

- **30 research questions**
- **4 writing workflows**
- **2 languages**: English and Chinese
- **2 models**: DeepSeek-chat and Qwen3-14B
- **240 generated paragraphs**
- **1,974 extracted references**
- **Verification sources**: Crossref, OpenAlex, arXiv

### Main Findings

- DeepSeek-chat resolved **59.1%** of generated references in the packaged verification table.
- Qwen3-14B resolved **16.4%** of generated references in the packaged verification table.
- Across the two tested models, **W0 Direct** and **W3 Verify-and-Repair** emerged as the top two workflows overall.
- **W2 Simulated Retrieval** was the weakest workflow in both tested models.
- Chinese prompts showed lower verification rates than English prompts in most conditions.

![Resolved Rate by Workflow](docs/figures/resolved-rate-by-workflow.svg)

## What Is Included

This version of the repository packages the parts that support **inspection, audit, and downstream analysis**:

- The manuscript in Markdown and LaTeX:
  - [paper_submission.md](paper_submission.md)
  - [paper_submission.tex](paper_submission.tex)
- Experimental task seeds and generated prompts:
  - [data/task_seed.csv](data/task_seed.csv)
  - [data/prompts.csv](data/prompts.csv)
- Verification results:
  - [results/verified_refs_merged.csv](results/verified_refs_merged.csv) for DeepSeek-chat
  - [results/verified_refs_qwen.csv](results/verified_refs_qwen.csv) for Qwen3-14B
  - [results/extracted_refs_qwen.csv](results/extracted_refs_qwen.csv) for extracted Qwen references
- Manual annotation starter sample:
  - [data/e3_annotation_sample.csv](data/e3_annotation_sample.csv)
- Re-analysis utilities added in this repo:
  - [analysis/summarize_results.py](analysis/summarize_results.py)
  - [analysis/statistical_analysis.py](analysis/statistical_analysis.py)
  - [analysis/summary_metrics.md](analysis/summary_metrics.md)
  - [analysis/rebuild_extracted.py](analysis/rebuild_extracted.py)
- Reconstructed extraction table for DeepSeek:
  - [results/extracted_refs_deepseek.csv](results/extracted_refs_deepseek.csv)
- Auto-generated paper tables with Wilson CIs:
  - [analysis/generated/paper_tables.md](analysis/generated/paper_tables.md)

## Repository Guide

```text
.
├── analysis/
│   ├── README.md
│   ├── summarize_results.py
│   ├── statistical_analysis.py
│   ├── rebuild_extracted.py
│   ├── summary_metrics.json
│   ├── summary_metrics.md
│   └── generated/
│       ├── paper_tables.md
│       └── paper_tables.json
├── code/
│   ├── build_prompts.py
│   ├── scoring_rubric.md
│   └── verify_citations.py
├── data/
│   ├── e3_annotation_sample.csv
│   ├── prompts.csv
│   └── task_seed.csv
├── docs/
│   ├── figures/
│   │   └── resolved-rate-by-workflow.svg
│   └── methodology.md
├── results/
│   ├── extracted_refs_deepseek.csv
│   ├── extracted_refs_qwen.csv
│   ├── qwen_output_count.txt
│   ├── verified_refs_merged.csv
│   └── verified_refs_qwen.csv
├── REPRODUCE.md
├── paper_submission.md
└── paper_submission.tex
```

## Quick Start

If you want to understand the project quickly without rerunning model APIs:

1. Read the project framing in [docs/methodology.md](docs/methodology.md).
2. Inspect the manuscript in [paper_submission.md](paper_submission.md).
3. Regenerate the packaged summary tables and figure:

```bash
python analysis/summarize_results.py
```

4. Open [analysis/summary_metrics.md](analysis/summary_metrics.md) for a compact metrics view.

## Reproduction Scope

This repo currently supports two useful levels of reproduction:

1. **Audit the packaged results** using the included CSV files and summary script.
2. **Rerun the verification pipeline** on your own model outputs using [code/verify_citations.py](code/verify_citations.py).

The repo does **not** yet bundle a full provider-specific generation client for recreating all 240 model outputs from scratch. That step depends on external API credentials and model access. See [REPRODUCE.md](REPRODUCE.md) for the exact boundary between what is included now and what must be supplied by the reproducer.

## Method Notes

- The packaged result tables use coarse statuses such as `resolved`, `unresolved`, and `no_doi`.
- The manuscript discusses stricter error categories including existence errors, metadata mismatch, and claim-support issues.
- For that reason, treat the CSV verification tables as the **first-pass evidence layer**, not the full epistemic judgment of citation quality.

More detail: [docs/methodology.md](docs/methodology.md)

## Suggested Positioning

If you are browsing this repo for research or hiring evaluation, the strongest interpretation is:

> A small but complete empirical framework for measuring citation reliability in LLM-assisted academic writing, with prompts, verification data, manuscript artifacts, and a reusable verification script.

### License

This repository is shared under [CC BY 4.0](LICENSE). The manuscript, experimental data, and analysis scripts are open for use with attribution. Model-generated content and third-party dependencies carry their own licenses.


## Chinese Summary

这个仓库更适合被理解为一个“**大模型学术引用可靠性评估与自动核验框架**”，而不只是论文附件。

- 它的核心贡献是把“引用幻觉”问题做成了可比较的工作流实验。
- 当前仓库已经包含论文、prompt、核验结果、标注样本和复盘脚本。
- 当前版本更偏“可审计、可复盘”，还不是完整的一键式全流程复现仓库。

如果你想继续把它打磨成更强的开源项目，建议下一步优先补原始模型输出、完整统计脚本和一个真实检索 baseline。
