# Citation Reliability in LLM-Assisted Academic Writing

## Experiment Summary

This workspace contains a complete empirical study evaluating citation reliability in LLM-assisted academic writing.

- Model: DeepSeek-chat
- Task: 30 research questions × 4 workflows × 2 languages = 120 paragraphs
- Extracted references: 950
- Verified against: Crossref, OpenAlex, arXiv APIs

## Key Results

- Verified genuine: 561/950 (59.1%)
- Estimated hallucinated (E1): ~363/950 (38.2%)
- Best workflow: W1 Cautious Prompt (E1 ~13%)
- Worst workflow: W2 Retrieval-first (E1 ~31%)
- Language gap: English 62.4% vs Chinese 55.5% resolved

## Output Files

| File | Description |
|------|-------------|
| outputs/paper_submission_english.md | Full English submission-ready paper with appendices |
| outputs/cover_letter.md | Submission cover letter |
| outputs/paper_draft_v4.md | Bilingual paper draft |
| outputs/citation_reliability_paper_startup.md | Paper startup document with experimental setup |
| outputs/experiment_progress_report.md | Progress summary |

## Work Files

| File | Description |
|------|-------------|
| work/paper-citation-reliability/data/prompts.csv | 120 experiment prompts |
| work/paper-citation-reliability/data/model_outputs/ | 120 DeepSeek-chat output files |
| work/paper-citation-reliability/data/task_seed.csv | 30 research questions |
| work/paper-citation-reliability/experiments/ | Verification results, protocols, analysis |
| work/paper-citation-reliability/literature/ | Source references and evidence tables |

## How to Reproduce

1. Run scripts/build_prompts.py to generate prompts
2. Send prompts to DeepSeek (or other model) API
3. Run reference extraction on output files
4. Run API verification pipeline
5. Statistical analysis from merged results

## Publication Status

Manuscript in preparation for submission.
Target: Applied Intelligence / arXiv preprint.
