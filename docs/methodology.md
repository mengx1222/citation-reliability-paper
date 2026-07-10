# Methodology Notes

This note explains what the repository is actually measuring, what the packaged CSV files mean, and where the current evidence boundary sits.

## 1. Research Question

The project studies citation reliability in LLM-assisted academic writing by asking:

- how often generated references correspond to real scholarly works
- how workflow design changes citation reliability
- whether the same workflow pattern appears across two tested models
- whether prompt language changes verification outcomes

## 2. Experimental Design

### Task grid

- 30 research questions
- 4 workflows
- 2 languages
- 2 models

This yields 240 generated paragraphs in the manuscript framing.

### Workflow definitions

- `W0_DIRECT`
  - Directly asks the model to write a related-work paragraph with numbered references.
- `W1_CAUTIOUS`
  - Adds uncertainty-aware instructions such as "cite only papers you are confident really exist."
- `W2_RETRIEVAL_FIRST`
  - Simulates a retrieval-first setting by telling the model to rely on a candidate source list.
- `W3_VERIFY_REPAIR`
  - Tells the model that citations will later be checked and therefore should be real and verifiable.

Important caveat: `W2_RETRIEVAL_FIRST` is a **prompt-level simulated retrieval condition**, not a fully implemented production RAG system.

## 3. Verification Pipeline

The core pipeline lives in [code/verify_citations.py](../code/verify_citations.py).

### Stage A: extraction

The script:

1. locates a `[References]` or `[参考文献]` section
2. parses numbered reference entries
3. extracts DOI-like strings with regex

### Stage B: metadata verification

For each extracted reference, the script attempts:

1. Crossref DOI exact lookup
2. OpenAlex DOI lookup
3. arXiv metadata recovery for `10.48550/arXiv.*`
4. DOI resolution check
5. title-based Crossref fallback when DOI lookup fails

## 4. Meaning Of Packaged Status Labels

The current packaged CSV files use simple status labels:

- `resolved`
  - the reference could be linked to some real scholarly metadata source
- `unresolved`
  - the automated pipeline could not confidently recover a matching work
- `no_doi`
  - no DOI was available in the extracted reference text

These labels are useful, but they are **not equivalent to full semantic correctness**.

## 5. Important Interpretation Boundary

A reference can still be problematic even if it resolves.

Examples:

- the DOI may point to a different paper than the generated title implies
- the title may be approximately similar while the author list or venue is wrong
- the cited paper may exist but not support the generated claim

That is why the manuscript also discusses stricter error notions such as:

- non-existent references
- metadata mismatch
- unsupported claims
- weak citation placement

The repository includes a starter annotation sample in [data/e3_annotation_sample.csv](../data/e3_annotation_sample.csv) and a rubric in [code/scoring_rubric.md](../code/scoring_rubric.md) for this richer evaluation layer.

## 6. What The Current Repo Is Strongest At

This repo is strongest as:

- a compact empirical study of citation reliability under different prompting workflows
- a reusable citation verification script for future experiments
- a re-analysis package for the supplied verification tables

It is currently weaker as:

- a one-command benchmark runner
- a fully archived raw-output dataset
- a complete end-to-end claim-support benchmark

## 7. Recommended Reading Order

1. [README.md](../README.md)
2. [paper_submission.md](../paper_submission.md)
3. [analysis/summary_metrics.md](../analysis/summary_metrics.md)
4. [code/verify_citations.py](../code/verify_citations.py)
5. [code/scoring_rubric.md](../code/scoring_rubric.md)
