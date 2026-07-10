# Paper Tables

Auto-generated from verification CSV files. Run `python analysis/statistical_analysis.py` to regenerate.

### Table 1: DeepSeek-chat  —  Workflow Verification Results

| Workflow | Total Refs | Resolved | Unresolved | No DOI | Resolved Rate | 95% Wilson CI |
|----------|----------:|--------:|----------:|------:|------------:|--------------:|
| W0 Direct | 248 | 160 | 51 | 37 | 64.5% | [58.4%, 70.2%] |
| W1 Cautious | 237 | 139 | 34 | 64 | 58.6% | [52.3%, 64.7%] |
| W2 Simulated Retrieval | 236 | 124 | 77 | 35 | 52.5% | [46.2%, 58.8%] |
| W3 Verify-and-Repair | 229 | 138 | 40 | 51 | 60.3% | [53.8%, 66.4%] |
| **Overall** | **950** | **561** | **202** | **187** | **59.1%** | **[55.9%, 62.1%]** |

### Statistical Significance Tests

#### Chi-square Test: Workflow × Verification Status

- χ²(6) = 37.2003, p = 2e-06 (✓ significant at α = 0.05)
- Cramér's V = 0.1399 (effect size)
  - Interpretation: small association

#### Pairwise Workflow Comparisons (Two-Proportion z-test)

| Comparison | Rate A | Rate B | z | p-value | Significant (α=0.05) | Bonferroni sig. | Cohen's h |
|---|---:|---:|---:|---:|:---:|:---:|---:|
| W0 Direct vs W1 Cautious | 64.5% | 58.7% | 1.3281 | 0.18413 | ✗ | ✗ | 0.1207 |
| W0 Direct vs W2 Simulated Retrieval | 64.5% | 52.5% | 2.674 | 0.007495 | ✓ | ✓ | 0.2437 |
| W0 Direct vs W3 Verify-and-Repair | 64.5% | 60.3% | 0.9587 | 0.337715 | ✗ | ✗ | 0.0879 |
| W1 Cautious vs W2 Simulated Retrieval | 58.7% | 52.5% | 1.3367 | 0.181324 | ✗ | ✗ | 0.123 |
| W1 Cautious vs W3 Verify-and-Repair | 58.7% | 60.3% | -0.3544 | 0.723073 | ✗ | ✗ | 0.0328 |
| W2 Simulated Retrieval vs W3 Verify-and-Repair | 52.5% | 60.3% | -1.678 | 0.093342 | ✗ | ✗ | 0.1558 |

#### Language Effect Significance

- Model: DeepSeek-chat
- English resolved rate: 62.5%, Chinese: 55.4% (gap: 7.1 pp)
- z = 2.2278, p = 0.025894 (✓ significant at α = 0.05)
- Cohen's h = 0.1447 (effect size)

### Table 2: DeepSeek-chat  —  Language Effect

| Language | Total Refs | Resolved | Unresolved | No DOI | Resolved Rate | 95% Wilson CI |
|----------|----------:|--------:|----------:|------:|------------:|--------------:|
| English | 493 | 308 | 86 | 99 | 62.5% | [58.1%, 66.6%] |
| Chinese | 457 | 253 | 116 | 88 | 55.4% | [50.8%, 59.9%] |
| **Gap (EN — ZH)** | | | | | **7.1 pp** | |

### Table 1: Qwen3-14B  —  Workflow Verification Results

| Workflow | Total Refs | Resolved | Unresolved | No DOI | Resolved Rate | 95% Wilson CI |
|----------|----------:|--------:|----------:|------:|------------:|--------------:|
| W0 Direct | 259 | 47 | 137 | 75 | 18.1% | [13.9%, 23.3%] |
| W1 Cautious | 254 | 38 | 99 | 117 | 15.0% | [11.1%, 19.9%] |
| W2 Simulated Retrieval | 261 | 20 | 144 | 97 | 7.7% | [5.0%, 11.5%] |
| W3 Verify-and-Repair | 250 | 63 | 97 | 90 | 25.2% | [20.2%, 30.9%] |
| **Overall** | **1024** | **168** | **477** | **379** | **16.4%** | **[14.3%, 18.8%]** |

### Statistical Significance Tests

#### Chi-square Test: Workflow × Verification Status

- χ²(6) = 47.7351, p = 0.0 (✓ significant at α = 0.05)
- Cramér's V = 0.1527 (effect size)
  - Interpretation: small association

#### Pairwise Workflow Comparisons (Two-Proportion z-test)

| Comparison | Rate A | Rate B | z | p-value | Significant (α=0.05) | Bonferroni sig. | Cohen's h |
|---|---:|---:|---:|---:|:---:|:---:|---:|
| W0 Direct vs W1 Cautious | 18.1% | 15.0% | 0.9704 | 0.331846 | ✗ | ✗ | 0.0858 |
| W0 Direct vs W2 Simulated Retrieval | 18.1% | 7.7% | 3.5679 | 0.00036 | ✓ | ✓ | 0.3191 |
| W0 Direct vs W3 Verify-and-Repair | 18.1% | 25.2% | -1.9328 | 0.053261 | ✗ | ✗ | 0.1717 |
| W1 Cautious vs W2 Simulated Retrieval | 15.0% | 7.7% | 2.6191 | 0.008815 | ✓ | ✗ | 0.2333 |
| W1 Cautious vs W3 Verify-and-Repair | 15.0% | 25.2% | -2.8712 | 0.004089 | ✓ | ✓ | 0.2575 |
| W2 Simulated Retrieval vs W3 Verify-and-Repair | 7.7% | 25.2% | -5.3728 | 0.0 | ✓ | ✓ | 0.4908 |

#### Language Effect Significance

- Model: Qwen3-14B
- English resolved rate: 18.6%, Chinese: 14.2% (gap: 4.4 pp)
- z = 1.9145, p = 0.055555 (✗ not significant at α = 0.05)
- Cohen's h = 0.12 (effect size)

### Table 2: Qwen3-14B  —  Language Effect

| Language | Total Refs | Resolved | Unresolved | No DOI | Resolved Rate | 95% Wilson CI |
|----------|----------:|--------:|----------:|------:|------------:|--------------:|
| English | 516 | 96 | 244 | 176 | 18.6% | [15.5%, 22.2%] |
| Chinese | 508 | 72 | 233 | 203 | 14.2% | [11.4%, 17.5%] |
| **Gap (EN — ZH)** | | | | | **4.4 pp** | |

### Table 3: Cross-Model Comparison

| Workflow | DeepSeek-chat | 95% CI | Qwen3-14B | 95% CI | Gap |
|----------|-------------:|-------:|----------:|-------:|----:|
| W0 Direct | 160/248 (64.5%) | [58.4%, 70.2%] | 47/259 (18.1%) | [13.9%, 23.3%] | +46.4 pp |
| W1 Cautious | 139/237 (58.6%) | [52.3%, 64.7%] | 38/254 (15.0%) | [11.1%, 19.9%] | +43.6 pp |
| W2 Simulated Retrieval | 124/236 (52.5%) | [46.2%, 58.8%] | 20/261 (7.7%) | [5.0%, 11.5%] | +44.8 pp |
| W3 Verify-and-Repair | 138/229 (60.3%) | [53.8%, 66.4%] | 63/250 (25.2%) | [20.2%, 30.9%] | +35.1 pp |

#### Cross-Model Significance (DeepSeek vs Qwen3 per Workflow)

| Workflow | DeepSeek | Qwen3 | z | p-value | Significant | Cohen's h |
|---|---:|---:|---:|---:|:---:|---:|
| W0 Direct | 64.5% | 18.1% | 10.6186 | 0.0 | ✓ | 0.9852 |
| W1 Cautious | 58.7% | 15.0% | 10.0752 | 0.0 | ✓ | 0.9504 |
| W2 Simulated Retrieval | 52.5% | 7.7% | 11.0137 | 0.0 | ✓ | 1.0607 |
| W3 Verify-and-Repair | 60.3% | 25.2% | 7.7673 | 0.0 | ✓ | 0.7257 |

### Table 4: Estimated E1 (Hallucinated) Rates

| Model | Total Refs | Resolved | Est. E1 | Est. E1 Rate | Uncertain | Resolved Rate |
|------|----------:|--------:|-------:|-------------:|---------:|---------------:|
| DeepSeek-chat | 950 | 561 | 345 | 36.3% | 43 | 59.1% |
| Qwen3-14B | 1024 | 168 | 757 | 73.9% | 98 | 16.4% |

### Per-Session Variation: DeepSeek-chat

- Range across 120 sessions: 11.1% — 93.3%
- Mean session resolved rate: 58.8%

| Task | Workflow | Language | Total Refs | Resolved | Resolved Rate |
|-----|----------|--------:|----------:|--------:|--------------:|
| T001 | W0 | EN | 7 | 5 | 71.4% |
| T001 | W1 | EN | 7 | 5 | 71.4% |
| T001 | W2 | EN | 7 | 5 | 71.4% |
| T001 | W3 | EN | 9 | 5 | 55.6% |
| T002 | W0 | ZH | 8 | 3 | 37.5% |
| T002 | W1 | ZH | 6 | 2 | 33.3% |
| T002 | W2 | ZH | 6 | 3 | 50.0% |
| T002 | W3 | ZH | 6 | 3 | 50.0% |
| T003 | W0 | EN | 9 | 7 | 77.8% |
| T003 | W1 | EN | 6 | 4 | 66.7% |
| T003 | W2 | EN | 12 | 10 | 83.3% |
| T003 | W3 | EN | 11 | 6 | 54.5% |
| T004 | W0 | ZH | 13 | 11 | 84.6% |
| T004 | W1 | ZH | 14 | 7 | 50.0% |
| T004 | W2 | ZH | 13 | 6 | 46.2% |
| T004 | W3 | ZH | 15 | 13 | 86.7% |
| T005 | W0 | EN | 15 | 11 | 73.3% |
| T005 | W1 | EN | 11 | 8 | 72.7% |
| T005 | W2 | EN | 13 | 7 | 53.8% |
| T005 | W3 | EN | 14 | 10 | 71.4% |
| T006 | W0 | ZH | 11 | 6 | 54.5% |
| T006 | W1 | ZH | 11 | 6 | 54.5% |
| T006 | W2 | ZH | 11 | 8 | 72.7% |
| T006 | W3 | ZH | 11 | 6 | 54.5% |
| T007 | W0 | EN | 15 | 14 | 93.3% |
| T007 | W1 | EN | 13 | 12 | 92.3% |
| T007 | W2 | EN | 9 | 1 | 11.1% |
| T007 | W3 | EN | 7 | 4 | 57.1% |
| T008 | W0 | ZH | 8 | 6 | 75.0% |
| T008 | W1 | ZH | 7 | 2 | 28.6% |
| T008 | W2 | ZH | 9 | 2 | 22.2% |
| T008 | W3 | ZH | 6 | 3 | 50.0% |
| T009 | W0 | EN | 9 | 5 | 55.6% |
| T009 | W1 | EN | 6 | 5 | 83.3% |
| T009 | W2 | EN | 8 | 2 | 25.0% |
| T009 | W3 | EN | 7 | 1 | 14.3% |
| T010 | W0 | ZH | 7 | 4 | 57.1% |
| T010 | W1 | ZH | 11 | 5 | 45.5% |
| T010 | W2 | ZH | 6 | 3 | 50.0% |
| T010 | W3 | ZH | 6 | 3 | 50.0% |
| T011 | W0 | EN | 8 | 5 | 62.5% |
| T011 | W1 | EN | 6 | 4 | 66.7% |
| T011 | W2 | EN | 6 | 5 | 83.3% |
| T011 | W3 | EN | 8 | 5 | 62.5% |
| T012 | W0 | ZH | 8 | 2 | 25.0% |
| T012 | W1 | ZH | 7 | 3 | 42.9% |
| T012 | W2 | ZH | 7 | 2 | 28.6% |
| T012 | W3 | ZH | 6 | 2 | 33.3% |
| T013 | W0 | EN | 9 | 7 | 77.8% |
| T013 | W1 | EN | 7 | 5 | 71.4% |
| T013 | W2 | EN | 7 | 4 | 57.1% |
| T013 | W3 | EN | 9 | 5 | 55.6% |
| T014 | W0 | ZH | 7 | 5 | 71.4% |
| T014 | W1 | ZH | 6 | 3 | 50.0% |
| T014 | W2 | ZH | 7 | 1 | 14.3% |
| T014 | W3 | ZH | 6 | 3 | 50.0% |
| T015 | W0 | EN | 7 | 5 | 71.4% |
| T015 | W1 | EN | 7 | 6 | 85.7% |
| T015 | W2 | EN | 6 | 5 | 83.3% |
| T015 | W3 | EN | 8 | 5 | 62.5% |
| T016 | W0 | ZH | 6 | 5 | 83.3% |
| T016 | W1 | ZH | 6 | 1 | 16.7% |
| T016 | W2 | ZH | 7 | 5 | 71.4% |
| T016 | W3 | ZH | 6 | 4 | 66.7% |
| T017 | W0 | EN | 8 | 3 | 37.5% |
| T017 | W1 | EN | 20 | 6 | 30.0% |
| T017 | W2 | EN | 8 | 3 | 37.5% |
| T017 | W3 | EN | 8 | 4 | 50.0% |
| T018 | W0 | ZH | 8 | 5 | 62.5% |
| T018 | W1 | ZH | 9 | 4 | 44.4% |
| T018 | W2 | ZH | 7 | 3 | 42.9% |
| T018 | W3 | ZH | 7 | 5 | 71.4% |
| T019 | W0 | EN | 7 | 6 | 85.7% |
| T019 | W1 | EN | 6 | 4 | 66.7% |
| T019 | W2 | EN | 8 | 5 | 62.5% |
| T019 | W3 | EN | 6 | 5 | 83.3% |
| T020 | W0 | ZH | 7 | 5 | 71.4% |
| T020 | W1 | ZH | 6 | 5 | 83.3% |
| T020 | W2 | ZH | 7 | 6 | 85.7% |
| T020 | W3 | ZH | 7 | 6 | 85.7% |
| T021 | W0 | EN | 6 | 3 | 50.0% |
| T021 | W1 | EN | 7 | 4 | 57.1% |
| T021 | W2 | EN | 7 | 2 | 28.6% |
| T021 | W3 | EN | 7 | 5 | 71.4% |
| T022 | W0 | ZH | 7 | 4 | 57.1% |
| T022 | W1 | ZH | 6 | 4 | 66.7% |
| T022 | W2 | ZH | 9 | 4 | 44.4% |
| T022 | W3 | ZH | 6 | 4 | 66.7% |
| T023 | W0 | EN | 9 | 6 | 66.7% |
| T023 | W1 | EN | 7 | 6 | 85.7% |
| T023 | W2 | EN | 8 | 7 | 87.5% |
| T023 | W3 | EN | 7 | 2 | 28.6% |
| T024 | W0 | ZH | 7 | 6 | 85.7% |
| T024 | W1 | ZH | 11 | 5 | 45.5% |
| T024 | W2 | ZH | 7 | 2 | 28.6% |
| T024 | W3 | ZH | 8 | 6 | 75.0% |
| T025 | W0 | EN | 8 | 3 | 37.5% |
| T025 | W1 | EN | 6 | 4 | 66.7% |
| T025 | W2 | EN | 8 | 3 | 37.5% |
| T025 | W3 | EN | 7 | 5 | 71.4% |
| T026 | W0 | ZH | 8 | 3 | 37.5% |
| T026 | W1 | ZH | 6 | 4 | 66.7% |
| T026 | W2 | ZH | 6 | 3 | 50.0% |
| T026 | W3 | ZH | 6 | 4 | 66.7% |
| T027 | W0 | EN | 7 | 5 | 71.4% |
| T027 | W1 | EN | 6 | 5 | 83.3% |
| T027 | W2 | EN | 7 | 5 | 71.4% |
| T027 | W3 | EN | 6 | 4 | 66.7% |
| T028 | W0 | ZH | 6 | 4 | 66.7% |
| T028 | W1 | ZH | 5 | 3 | 60.0% |
| T028 | W2 | ZH | 6 | 4 | 66.7% |
| T028 | W3 | ZH | 6 | 3 | 50.0% |
| T029 | W0 | EN | 7 | 5 | 71.4% |
| T029 | W1 | EN | 5 | 3 | 60.0% |
| T029 | W2 | EN | 7 | 4 | 57.1% |
| T029 | W3 | EN | 7 | 3 | 42.9% |
| T030 | W0 | ZH | 6 | 1 | 16.7% |
| T030 | W1 | ZH | 6 | 4 | 66.7% |
| T030 | W2 | ZH | 7 | 4 | 57.1% |
| T030 | W3 | ZH | 6 | 4 | 66.7% |

### Per-Session Variation: Qwen3-14B

- Range across 120 sessions: 0.0% — 66.7%
- Mean session resolved rate: 16.7%

| Task | Workflow | Language | Total Refs | Resolved | Resolved Rate |
|-----|----------|--------:|----------:|--------:|--------------:|
| T001 | W0 | EN | 9 | 3 | 33.3% |
| T001 | W1 | EN | 8 | 0 | 0.0% |
| T001 | W2 | EN | 9 | 0 | 0.0% |
| T001 | W3 | EN | 8 | 3 | 37.5% |
| T002 | W0 | ZH | 9 | 1 | 11.1% |
| T002 | W1 | ZH | 7 | 0 | 0.0% |
| T002 | W2 | ZH | 10 | 1 | 10.0% |
| T002 | W3 | ZH | 8 | 1 | 12.5% |
| T003 | W0 | EN | 8 | 2 | 25.0% |
| T003 | W1 | EN | 6 | 1 | 16.7% |
| T003 | W2 | EN | 7 | 3 | 42.9% |
| T003 | W3 | EN | 9 | 0 | 0.0% |
| T004 | W0 | ZH | 8 | 2 | 25.0% |
| T004 | W2 | ZH | 8 | 1 | 12.5% |
| T004 | W3 | ZH | 6 | 2 | 33.3% |
| T004 | W1 | ZH | 8 | 0 | 0.0% |
| T005 | W0 | EN | 9 | 0 | 0.0% |
| T005 | W1 | EN | 9 | 0 | 0.0% |
| T005 | W2 | EN | 9 | 1 | 11.1% |
| T005 | W3 | EN | 8 | 1 | 12.5% |
| T006 | W0 | ZH | 6 | 1 | 16.7% |
| T006 | W1 | ZH | 12 | 2 | 16.7% |
| T006 | W2 | ZH | 10 | 0 | 0.0% |
| T006 | W3 | ZH | 9 | 2 | 22.2% |
| T007 | W0 | EN | 9 | 3 | 33.3% |
| T007 | W1 | EN | 8 | 4 | 50.0% |
| T007 | W2 | EN | 8 | 1 | 12.5% |
| T007 | W3 | EN | 8 | 1 | 12.5% |
| T008 | W0 | ZH | 10 | 1 | 10.0% |
| T008 | W1 | ZH | 12 | 1 | 8.3% |
| T008 | W2 | ZH | 9 | 0 | 0.0% |
| T008 | W3 | ZH | 6 | 3 | 50.0% |
| T009 | W0 | EN | 9 | 1 | 11.1% |
| T009 | W1 | EN | 9 | 3 | 33.3% |
| T009 | W2 | EN | 9 | 0 | 0.0% |
| T009 | W3 | EN | 8 | 2 | 25.0% |
| T010 | W0 | ZH | 10 | 2 | 20.0% |
| T010 | W1 | ZH | 11 | 0 | 0.0% |
| T010 | W2 | ZH | 9 | 0 | 0.0% |
| T010 | W3 | ZH | 9 | 0 | 0.0% |
| T011 | W0 | EN | 9 | 1 | 11.1% |
| T011 | W1 | EN | 9 | 4 | 44.4% |
| T011 | W2 | EN | 9 | 0 | 0.0% |
| T011 | W3 | EN | 8 | 0 | 0.0% |
| T012 | W0 | ZH | 7 | 0 | 0.0% |
| T012 | W1 | ZH | 8 | 2 | 25.0% |
| T012 | W2 | ZH | 9 | 0 | 0.0% |
| T012 | W3 | ZH | 6 | 3 | 50.0% |
| T013 | W0 | EN | 9 | 1 | 11.1% |
| T013 | W1 | EN | 9 | 2 | 22.2% |
| T013 | W2 | EN | 8 | 1 | 12.5% |
| T013 | W3 | EN | 9 | 3 | 33.3% |
| T014 | W0 | ZH | 9 | 1 | 11.1% |
| T014 | W1 | ZH | 7 | 0 | 0.0% |
| T014 | W2 | ZH | 10 | 0 | 0.0% |
| T014 | W3 | ZH | 7 | 1 | 14.3% |
| T015 | W0 | EN | 9 | 3 | 33.3% |
| T015 | W1 | EN | 7 | 1 | 14.3% |
| T015 | W3 | EN | 10 | 5 | 50.0% |
| T015 | W2 | EN | 8 | 0 | 0.0% |
| T016 | W0 | ZH | 8 | 2 | 25.0% |
| T016 | W2 | ZH | 8 | 5 | 62.5% |
| T016 | W1 | ZH | 8 | 1 | 12.5% |
| T016 | W3 | ZH | 10 | 4 | 40.0% |
| T017 | W0 | EN | 9 | 1 | 11.1% |
| T017 | W1 | EN | 9 | 2 | 22.2% |
| T017 | W2 | EN | 9 | 0 | 0.0% |
| T017 | W3 | EN | 9 | 5 | 55.6% |
| T018 | W0 | ZH | 7 | 1 | 14.3% |
| T018 | W2 | ZH | 10 | 0 | 0.0% |
| T018 | W3 | ZH | 8 | 2 | 25.0% |
| T018 | W1 | ZH | 9 | 0 | 0.0% |
| T019 | W0 | EN | 9 | 2 | 22.2% |
| T019 | W1 | EN | 9 | 3 | 33.3% |
| T019 | W2 | EN | 9 | 1 | 11.1% |
| T019 | W3 | EN | 9 | 1 | 11.1% |
| T020 | W0 | ZH | 11 | 0 | 0.0% |
| T020 | W1 | ZH | 9 | 1 | 11.1% |
| T020 | W2 | ZH | 11 | 4 | 36.4% |
| T020 | W3 | ZH | 9 | 2 | 22.2% |
| T021 | W0 | EN | 9 | 3 | 33.3% |
| T021 | W1 | EN | 9 | 1 | 11.1% |
| T021 | W2 | EN | 8 | 0 | 0.0% |
| T021 | W3 | EN | 9 | 5 | 55.6% |
| T022 | W0 | ZH | 7 | 1 | 14.3% |
| T022 | W1 | ZH | 7 | 0 | 0.0% |
| T022 | W2 | ZH | 7 | 1 | 14.3% |
| T022 | W3 | ZH | 9 | 0 | 0.0% |
| T023 | W0 | EN | 9 | 5 | 55.6% |
| T023 | W1 | EN | 8 | 1 | 12.5% |
| T023 | W2 | EN | 7 | 0 | 0.0% |
| T023 | W3 | EN | 9 | 1 | 11.1% |
| T024 | W1 | ZH | 8 | 1 | 12.5% |
| T024 | W0 | ZH | 7 | 0 | 0.0% |
| T024 | W2 | ZH | 12 | 0 | 0.0% |
| T024 | W3 | ZH | 7 | 1 | 14.3% |
| T025 | W0 | EN | 9 | 1 | 11.1% |
| T025 | W1 | EN | 7 | 0 | 0.0% |
| T025 | W2 | EN | 9 | 0 | 0.0% |
| T025 | W3 | EN | 9 | 0 | 0.0% |
| T026 | W0 | ZH | 8 | 3 | 37.5% |
| T026 | W1 | ZH | 9 | 0 | 0.0% |
| T026 | W2 | ZH | 8 | 0 | 0.0% |
| T026 | W3 | ZH | 8 | 1 | 12.5% |
| T027 | W0 | EN | 9 | 0 | 0.0% |
| T027 | W1 | EN | 9 | 2 | 22.2% |
| T027 | W2 | EN | 9 | 0 | 0.0% |
| T027 | W3 | EN | 9 | 3 | 33.3% |
| T028 | W0 | ZH | 7 | 1 | 14.3% |
| T028 | W1 | ZH | 8 | 1 | 12.5% |
| T028 | W2 | ZH | 8 | 1 | 12.5% |
| T028 | W3 | ZH | 9 | 4 | 44.4% |
| T029 | W0 | EN | 9 | 4 | 44.4% |
| T029 | W1 | EN | 9 | 1 | 11.1% |
| T029 | W2 | EN | 9 | 0 | 0.0% |
| T029 | W3 | EN | 8 | 4 | 50.0% |
| T030 | W0 | ZH | 11 | 1 | 9.1% |
| T030 | W1 | ZH | 6 | 4 | 66.7% |
| T030 | W2 | ZH | 5 | 0 | 0.0% |
| T030 | W3 | ZH | 9 | 3 | 33.3% |

# E3 Annotation Expansion Guide

The current E3 claim-support sample has fewer than 60 entries. To strengthen the paper's claim support analysis, expand to at least **240 references** (15 per workflow × model × language combination).

## Target Allocation

| Model | Workflow | Language | Target |
|------|----------|--------:|------:|
| deepseek-chat | W0_DIRECT | en | 15 |
| deepseek-chat | W0_DIRECT | zh | 15 |
| deepseek-chat | W1_CAUTIOUS | en | 15 |
| deepseek-chat | W1_CAUTIOUS | zh | 15 |
| deepseek-chat | W2_RETRIEVAL_FIRST | en | 15 |
| deepseek-chat | W2_RETRIEVAL_FIRST | zh | 15 |
| deepseek-chat | W3_VERIFY_REPAIR | en | 15 |
| deepseek-chat | W3_VERIFY_REPAIR | zh | 15 |
| qwen3-14b | W0_DIRECT | en | 15 |
| qwen3-14b | W0_DIRECT | zh | 15 |
| qwen3-14b | W1_CAUTIOUS | en | 15 |
| qwen3-14b | W1_CAUTIOUS | zh | 15 |
| qwen3-14b | W2_RETRIEVAL_FIRST | en | 15 |
| qwen3-14b | W2_RETRIEVAL_FIRST | zh | 15 |
| qwen3-14b | W3_VERIFY_REPAIR | en | 15 |
| qwen3-14b | W3_VERIFY_REPAIR | zh | 15 |
| **Total** | | | **240** |

## Selection Strategy

1. Use `analysis/summarize_results.py` to identify which references are `resolved` (the candidate pool).
2. For each workflow × model × language cell, randomly select 15 resolved references where the generated claim is available.
3. For each selected reference, annotate the `support_label` using the rubric in `code/scoring_rubric.md`.
