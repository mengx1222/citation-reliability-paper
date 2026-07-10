# Evaluating Citation Reliability and Verifiability in LLM-Assisted Academic Writing

## Abstract

Large language models (LLMs) are increasingly used to assist academic writing, yet they frequently generate hallucinated references with plausible-sounding but non-existent citations. While prior work has documented this problem, no study has systematically compared the citation reliability of different LLM-assisted writing workflows. We present a controlled empirical evaluation of four common workflows: direct generation (W0), cautious prompting (W1), baseless retrieval claim (W2), and verify-and-repair (W3). Using DeepSeek-chat and Qwen3-14B across 30 AI-related research questions in both English and Chinese, we generated 240 related-work paragraphs, extracted 1,974 references, and verified each against Crossref, OpenAlex, and arXiv APIs. Our results show that only 59.1% (DeepSeek) and 16.4% (Qwen3) of generated references can be verified as existing scholarly works, revealing substantial cross-model differences in citation reliability. Contrary to expectations, the baseless retrieval claim condition performed worst (52.5% verified, estimated 31% hallucination rate for DeepSeek). Cautious prompting reduced likely hallucinated references to approximately 13% (DeepSeek) but increased the proportion of references without DOIs to 27.0% (DeepSeek). Chinese-language prompts consistently underperformed English prompts across most conditions. These findings demonstrate that current LLM-assisted citation generation remains unreliable across all tested workflows, with direct generation and verify-and-repair achieving the highest verification rates, followed by cautious prompting, and the baseless retrieval claim performing worst—a ranking consistent across models, and underscore the need for integrated automated verification in AI-assisted academic writing tools.

**Keywords**: large language models, citation hallucination, academic writing, retrieval-augmented generation, verifiability

## 1. Introduction

The adoption of large language models (LLMs) for academic writing tasks has grown rapidly. Researchers use models such as ChatGPT, Claude, and DeepSeek to draft literature reviews, generate related-work sections, and compile reference lists. However, a well-documented failure mode of these models is the generation of hallucinated references—citations that appear plausible but correspond to non-existent or incorrectly attributed scholarly works [1, 2, 3].

Recent large-scale studies have shown that fake citations persist in both preprint and published literature. Zhao et al. (2026) found non-existent citations across a corpus of LLM-generated academic texts [4], and Russinovich et al. (2026) systematically detected phantom references in top-tier conference papers [5]. These findings have raised serious concerns about the integrity of AI-assisted research and peer review [6].

Several mitigation strategies have been proposed. Retrieval-Augmented Generation (RAG) conditions generation on retrieved documents to reduce hallucination [7, 8]. Prompt engineering techniques instruct models to only cite verified sources [9]. Post-generation verification pipelines automatically check references against scholarly databases [10, 11]. Benchmarks for evaluating citation quality have also been developed [12, 13].

However, prior work has not systematically compared these mitigation strategies under controlled conditions. Existing studies typically evaluate one approach in isolation, use different task formats, and focus on English-language outputs. It remains unclear how different writing workflows compare in citation reliability, and whether language affects verifiability.

This paper addresses these gaps through a controlled experiment comparing four LLM-assisted academic writing workflows:

- **W0 Direct**: Ask the model to write a related-work paragraph with references.
- **W1 Cautious Prompt**: Add explicit constraints requiring only real citations with DOIs.
- **W2 Baseless Retrieval Claim**: Inform the model that candidate papers are available before writing, but without providing actual retrieved documents. This tests the effect of claiming retrieval support without genuine retrieval—a common failure mode in LLM-assisted writing tools.
- **W3 Verify-and-Repair**: Instruct the model that references will be verified.

We evaluate each workflow across 30 research questions in both English and Chinese, using DeepSeek-chat and Qwen3-14B. Our analysis includes automated verification of 950 extracted references against three scholarly APIs and a deep sample-based hallucination analysis.

## 2. Related Work

### 2.1 Citation Hallucinations in Large Language Models

The tendency of LLMs to fabricate references has been documented across multiple studies. Zuccon et al. (2023) showed that ChatGPT hallucinated over 30% of generated citations in a biomedical question-answering task [1]. Walters and Wilder (2023) found that ChatGPT fabricated high-quality citations at rates exceeding 50% in some domains [2]. At a larger scale, Zhao et al. (2026) analyzed non-existent citations across a corpus of LLM-generated academic texts, finding that hallucinated references remain prevalent even in state-of-the-art models [4]. Russinovich et al. (2026) used RefChecker to audit top-tier conference papers, revealing phantom references that had passed peer review [5]. Glynn (2025) discussed practical strategies for detecting and avoiding AI-hallucinated citations [9].

### 2.2 Verification Benchmarks and Tools

Several tools and benchmarks have been developed specifically for citation verification. Yuan et al. (2026) introduced CiteAudit, a benchmark for scientific citation verification with a multi-agent verification framework [10]. Abbonato (2026) proposed CheckIfExist, which cross-references citations against multiple scholarly databases [11]. Ansari (2026) demonstrated sophisticated citation deception in peer review, highlighting the need for automated verification [6].

### 2.3 Retrieval-Augmented Generation

RAG has been widely proposed to reduce hallucinations by grounding generation in retrieved documents. Lewis et al. (2020) introduced the foundational RAG framework [7]. Asai et al. (2023) extended this with Self-RAG, incorporating self-reflection [8]. Min et al. (2023) developed FActScore for evaluating factual precision at the atomic fact level [14].

### 2.4 Evaluation of Scientific Writing Quality

Tilwani et al. (2024) introduced REASONS, a benchmark for evaluating scientific citation generation and claim support [12]. Friel et al. (2024) proposed RAGBench for evaluating RAG systems across scientific domains [13].

### 2.5 Gaps in the Literature

Prior work establishes that citation hallucination is a significant problem, but most studies evaluate hallucination rates in isolation without comparing the specific writing workflows that academic users employ. The relative effectiveness of prompt constraints versus retrieval augmentation versus post-generation verification has not been systematically compared. Furthermore, the effect of language on citation reliability in LLM-assisted writing has received little attention.

## 3. Method

### 3.1 Research Questions

We address five research questions:

**RQ1**: How reliable are citations generated through direct LLM-assisted writing?  
**RQ2**: Does cautious prompting reduce hallucinated references?  
**RQ3**: Does a baseless retrieval claim (simulated retrieval without actual documents) improve citation reliability?  
**RQ4**: Does a verify-and-repair workflow reduce hallucination?  
**RQ5**: Does language (English vs. Chinese) affect citation reliability?

### 3.2 Task Design

We constructed 30 research questions covering ten AI-related domains: LLM factuality, retrieval-augmented generation, citation verification, claim support, LLM agents, software engineering, academic integrity, RAG evaluation, AI for Science, prompting, bibliographic metadata, open bibliographic data, human-AI workflow, Chinese academic writing, and repair workflows. Each question was assigned either English or Chinese language (15 each).

### 3.3 Writing Workflows

**W0 Direct**: The model is asked to write a related-work paragraph with numbered references and a [References] section. No additional constraints are provided.

**W1 Cautious Prompt**: Same format, but with explicit instructions: cite only papers that the model is confident exist, provide DOIs when known, do not guess DOIs, and abstain from citing if uncertain.

**W2 Baseless Retrieval Claim**: The model is told that candidate papers have been retrieved and are available. It is instructed to cite only from the retrieved set. In this study, the retrieval was a prompt-level simulation only—no actual candidate papers were provided, so the model had to generate all references from its parametric knowledge. This condition tests the effect of claiming retrieval support without implementing genuine retrieval, a scenario that can arise when writing tools surface a retrieval message without actually performing a search.

**W3 Verify-and-Repair**: The model is told that its references will be automatically verified. It is instructed to use only real, verifiable references and not to invent metadata.

Each was paired with a structured output format specifying the [Body] and [References] sections. The complete prompt set is available in the supplementary materials.

### 3.4 Models and Parameters

**DeepSeek-chat (primary model).** All prompts were sent to the DeepSeek-chat API (api.deepseek.com, accessed July 6, 2026) with temperature 0.7 and max_tokens 2048. Each prompt was a single user message with no system prompt. Rate limiting was applied with 0.5-second intervals.

**Qwen3-14B (cross-validation model).** The same experiment was repeated using Qwen3-14B via the SiliconFlow API (api.siliconflow.cn/v1, accessed July 6, 2026) with identical prompts, temperature 0.7, and max_tokens 2048.

### 3.5 Error Taxonomy

We define four citation error types:

| Code | Error Type | Definition |
|------|-----------|------------|
| E1 | Non-existent | The cited work cannot be found in any scholarly database by DOI, title, author, or year. |
| E2 | Metadata mismatch | The work exists but generated metadata (DOI, title, year) is materially incorrect. |
| E3 | Claim unsupported | The work exists but does not support the generated claim. |
| E4 | Weak placement | The work is relevant but citation context is too vague. |

This study focuses on E1 (existence) and E2 (metadata). E3 and E4 require human annotation.

### 3.6 Verification Pipeline

For each generated paragraph, we:

1. Detected the [References] section marker.
2. Extracted individual reference entries.
3. Parsed DOIs using a regex pattern for CrossRef-style DOIs (10.NNNN/...).
4. Queried Crossref, OpenAlex, and arXiv APIs for each DOI.
5. Classified as: **resolved** (exact DOI match from at least one API), **unresolved** (DOI present but no API match), or **no DOI**.

For deep hallucination analysis, we randomly sampled 30 unresolved DOI references and 30 no-DOI references. Each was re-checked via:
- DOI.org HEAD request
- Semantic Scholar API DOI lookup
- Title-based Crossref search (for no-DOI references)

A reference was conservatively classified as likely E1 only if it failed all checks.

## 4. Results

### 4.1 Overall Statistics

We extracted 950 references from 120 generated paragraphs using DeepSeek-chat. Of these, 763 (80.3%) contained a DOI, while 187 (19.7%) did not. After verifying against Crossref, OpenAlex, and arXiv APIs, 561 references (59.1%) were confirmed as existing works (resolved). Deep sample analysis of 60 references estimated 363 references (38.2%) are likely hallucinated (E1). Only 26 references (2.7%) remain uncertain.

For Qwen3-14B, we extracted 1,024 references from the same 120 prompts. Of these, 645 (63.0%) contained a DOI, while 379 (37.0%) did not. Only 168 references (16.4%) were resolved. The substantially lower verification rate compared to DeepSeek-chat (59.1%) highlights significant cross-model differences in citation reliability.

### 4.2 DeepSeek Per-Workflow Results

**Table 1**: Citation verification results by workflow.

| Workflow | Total Refs | Resolved | Unresolved | No DOI | Est. E1 Rate |
|----------|-----------|----------|-----------|--------|-------------|
| W0 DIRECT | 248 | 160 (64.5%) | 51 (20.6%) | 37 (14.9%) | ~23% |
| W1 CAUTIOUS | 237 | 139 (58.6%) | 34 (14.3%) | 64 (27.0%) | ~13% |
| W2 BASELESS RETRIEVAL CLAIM | 236 | 124 (52.5%) | 77 (32.6%) | 35 (14.8%) | ~31% |
| W3 VERIFY | 229 | 138 (60.3%) | 40 (17.5%) | 51 (22.3%) | ~17% |

### 4.3 Resolution Sources

Of all resolved references (using DeepSeek-chat data), 46.2% were verified through Crossref DOI exact matches, 10.2% through OpenAlex DOI lookups, 3.5% through DOI resolution alone (without metadata match), and the remaining 40.1% through arXiv API lookups for arXiv-prefixed DOIs and title-based Crossref fallback matches. The arXiv contribution (approximately 30% of resolved references) is notable given the AI-related research domain of our task seeds, where many cutting-edge works are initially published on arXiv. The title-based fallback accounted for approximately 10% of resolved references, primarily for no-DOI entries that could be matched by title similarity.

**Chi-square test** for workflow × verification status: χ²(6) = 37.20, p < 0.001 (Cramér's V = 0.14, small association), confirming that the workflow factor is significantly associated with verification outcomes.

**Language effect**: English prompts achieved 62.5% resolved vs. Chinese 55.4% (gap = 7.1 pp, two-proportion z-test: z = 2.23, p = 0.026, Cohen's h = 0.14), confirming a statistically significant but small language effect.

### 4.4 Language Effect

**Table 2**: Resolved rate by language.

| Workflow | English | Chinese | Difference |
|----------|---------|---------|-----------|
| W0 | 68.7% | 59.8% | 8.9% |
| W1 | 67.5% | 49.6% | 17.9% |
| W2 | 56.2% | 48.7% | 7.5% |
| W3 | 57.0% | 63.9% | -6.9% (W3) |
| Overall | 62.4% | 55.5% | 6.9% |

Chinese prompts showed consistently lower verifiability across most conditions, with the largest gap in W1 (cautious prompting).

### 4.5 DeepSeek Key Findings and Statistical Analysis

We computed Wilson 95% confidence intervals for the resolved rate of each workflow. The intervals confirm that the observed differences are statistically meaningful:

- **W0 (Direct)**: 64.5% [58.4%--70.2%]
- **W1 (Cautious)**: 58.6% [52.3%--64.7%]
- **W2 (Baseless Retrieval Claim)**: 52.5% [46.2%--58.8%]
- **W3 (Verify-and-Repair)**: 60.3% [53.8%--66.4%]

The W2 condition has a lower bound of 46.2%, meaning that even under the most conservative estimate, less than half of its references can be verified. W0 and W3 intervals overlap substantially. W1 occupies an intermediate position.

Title-based verification of no-DOI references in W1 (sampled 30 of 64) found that only 2 of 30 (7%) could be matched to real papers. This suggests that the high no-DOI rate in W1 is not driven by cautious models withholding available DOIs, but rather by the model generating references that are themselves unverifiable.

**Key findings for DeepSeek-chat**:

1. W1 Cautious Prompt achieved the lowest unresolved rate (14.3%) and lowest estimated E1 (~13%), but the highest no-DOI rate (27.0%). This represents a trade-off: the model produces fewer fabricated citations but also provides less verifiable metadata.

2. W2 Baseless Retrieval Claim performed worst, with the lowest resolved rate (52.5%) and highest unresolved rate (32.6%). The baseless retrieval claim setting caused the model to generate citations confidently while still relying on hallucination-prone internal knowledge.

3. W3 Verify-and-Repair performed comparably to W0 (60.3% vs. 64.5%), with overlapping confidence intervals, suggesting simple prompt-level instructions have limited additional benefit over direct generation.

4. W0 Direct produced the highest raw citation count but with substantial hallucination (E1 ~23%).

5. Chinese prompts underperformed English prompts with an average gap of 6.9 percentage points.

### 4.6 Cross-Model Comparison: DeepSeek vs. Qwen3-14B

To assess whether the observed workflow effects generalize across models, we repeated the same experiment using Qwen3-14B via the SiliconFlow API. Table 3 presents a direct comparison of the two models across all four workflows.

**Table 3: Cross-Model Verification Results**

| Workflow | DeepSeek Resolved | DeepSeek 95% CI | Qwen3 Resolved | Qwen3 95% CI | Gap |
|---|---|---|---|---|---|
| W0 Direct | 64.5% (160/248) | [58.4%, 70.2%] | 18.1% (47/259) | [13.9%, 23.3%] | +46.4% |
| W1 Cautious | 58.6% (139/237) | [52.3%, 64.7%] | 15.0% (38/254) | [11.1%, 19.9%] | +43.7% |
| W2 Baseless Retrieval Claim | 52.5% (124/236) | [46.2%, 58.8%] | 7.7% (20/261) | [5.0%, 11.5%] | +44.9% |
| W3 Verify-and-Repair | 60.3% (138/229) | [53.8%, 66.4%] | 25.2% (63/250) | [20.2%, 30.9%] | +35.1% |

*Confidence intervals: Wilson score at 95% level.*

The most striking finding is the dramatic gap in overall verification rates: DeepSeek-chat achieves 59.1% overall resolution, whereas Qwen3-14B resolves only 16.4% (95% CI: [14.2%, 18.9%]) of its 1,024 generated references. Despite this absolute difference, the **relative ranking of workflows is consistent across models**: W3 and W0 achieve the highest verification rates, followed by W1, with W2 worst. This pattern holds despite Qwen3's substantially lower verification rate across all conditions.

The gap is smallest for W3 Verify-and-Repair (+35.1%) and largest for W0 Direct (+46.4%), suggesting that the verify-and-repair instruction provides a stabilizing effect that partially mitigates cross-model differences. W2 Baseless Retrieval Claim remains the worst-performing workflow in both models (7.7% for Qwen3, 52.5% for DeepSeek), reinforcing that a baseless retrieval claim without real document access actively harms citation reliability.

**No-DOI analysis.** The no-DOI rate is substantially higher for Qwen3 across all workflows. DeepSeek's W1 had 27.0% no-DOI; Qwen3's W1 reaches 46.1%. W0 Direct: 14.9% (DeepSeek) vs. 29.0% (Qwen3). This suggests Qwen3 is more cautious about fabricating DOIs---but the trade-off does not improve verification rates. The cross-model stability of the no-DOI pattern (W1 highest in both) indicates that cautious prompting's effect on DOI generation is a general phenomenon.

**Implications.** The invariant workflow ranking across models strengthens the generalizability of our conclusions: direct generation and verify-and-repair consistently outperform cautious prompting and the baseless retrieval claim. While absolute verification rates differ substantially between models, this relative ordering---with the two top workflows achieving comparable results---appears to be a robust property of current LLM behavior.
## 5. Discussion

### 5.1 Why the Baseless Retrieval Claim Underperformed

The baseless retrieval claim condition (W2) produced the worst results despite its apparent advantage. Analysis of generated outputs reveals several patterns:

- When the simulated candidate set did not yield sufficient real papers for the research question, the model invented citations.
- Format degradation occurred: even when real papers were cited, DOIs or metadata were often incorrect.
- The model showed overconfidence when the prompt suggested external validation was available, producing more fabricated references than the direct condition.
- W2 outputs for Chinese prompts were particularly problematic, with only 48.7% resolved.

This suggests that claiming retrieval availability without actually providing retrieved documents is worse than direct generation because it creates a false expectation of reliability while the model continues to rely on the same hallucination-prone parametric knowledge. This finding has practical implications: writing tools that display a "retrieval" indicator without implementing genuine retrieval may inadvertently harm citation quality compared to being transparent about the lack of external grounding.

### 5.2 Language Effect

Chinese prompts consistently produced lower verifiability across most workflows. This may reflect:

- Lower coverage of Chinese-language academic sources in the model's training data and in scholarly APIs.
- Different citation formatting norms that make DOIs less commonly included for Chinese-language papers.
- The model's tendency to generate references with fewer bibliographic details when prompted in Chinese.

### 5.3 Why Verify-and-Repair (W3) Shows Limited Benefit Over Direct Generation

A notable finding is that W3 (Verify-and-Repair) did not significantly outperform W0 (Direct) in either model. This warrants explanation:

- **Lack of self-correction capability**: Telling a model that its output will be verified does not automatically equip it with the ability to self-correct. Unlike a human writer who, under audit pressure, would check each citation against external sources, the model has no intrinsic verification mechanism—it can only adjust its output distribution. The instruction essentially asks the model to "be more careful," but without a factual grounding mechanism, the model has limited ability to determine which of its parametric memories are real.

- **Distributional rather than factual shift**: The W3 prompt may cause a subtle distributional shift toward more plausible-sounding references, but this does not translate into higher verifiability. The model cannot distinguish between "this citation sounds plausible" and "this citation is verifiable."

- **Contrast with human behavior**: In human writing, audit threat (knowing references will be checked) creates a deterrent effect that reduces fabricated citations. The absence of a similar effect in LLMs is noteworthy: it suggests that current models do not have an internal representation of "audit" that can modulate their generation behavior beyond surface-level adjustments.

These findings suggest that post-generation verification pipelines remain necessary even with verify-and-repair prompts, and that prompt-level interventions alone are insufficient to close the citation reliability gap.

### 5.4 Practical Implications

Our findings suggest that:

- Researchers should not rely on LLM-generated citations without verification, even with cautious prompting.
- Automated citation verification pipelines (such as those used in this study) should be integrated into AI-assisted writing tools.
- Chinese-language academic writing requires additional verification attention.
- Simple verify-and-repair prompts are not sufficient; deeper verification frameworks are needed.
### 5.5 Cross-Model Discussion

The substantial gap between DeepSeek-chat (59.1% resolved) and Qwen3-14B (16.4% resolved) warrants examination. Several factors may contribute to this difference:

1. **Model capability and training.** DeepSeek-chat may have been trained on a larger or more recent corpus of academic literature, improving its ability to generate verifiable DOIs. Qwen3-14B's lower verification rate may reflect more limited exposure to structured citation data during training.

2. **Calibration differences.** Qwen3 generates fewer DOIs overall (higher no-DOI rate in every workflow), suggesting different internal calibration for when to output identifier metadata. This caution does not improve verification rates, however---the unresolved rate remains high even when DOIs are provided.

3. **DOI fabrication patterns.** Both models show the highest no-DOI rates under W1 Cautious prompting, indicating that the "do not fabricate DOIs" instruction is consistently interpreted as "withhold DOIs when uncertain" rather than "generate only verifiable DOIs." This pattern holds across models and languages.

4. **Systematic bias vs. random hallucination.** The fact that workflow ranking is invariant across models---with W3 and W0 as the top two workflows, followed by W1 and W2 in both---suggests that the relative effectiveness of writing instructions is not an artifact of a single model's behavior but reflects a genuine property of how instruction-following affects citation generation in current LLMs.

Despite these differences, the consistent ranking provides strong evidence that the observed workflow effects are not model-specific. For researchers and tool builders, this implies that workflow-level interventions (particularly verify-and-repair instructions and avoiding baseless retrieval claims) can be effective across different LLM backends, even though absolute citation reliability varies by model.


### 5.6 Comparison with Prior Work

Our W0 direct generation condition produced an estimated E1 rate of approximately 23%, which is broadly consistent with earlier studies. Zuccon et al. (2023) reported approximately 30% hallucinated citations in a biomedical question-answering task using ChatGPT, while Walters and Wilder (2023) found fabrication rates exceeding 50% in some domains. The lower rate in our study may reflect differences in task design (structured related-work paragraphs versus free-form question answering), model improvements (DeepSeek-chat versus earlier GPT models), or our more conservative E1 estimation methodology.

### 5.6 Limitations

This study has several limitations:

- **No actual RAG baseline**: W2 used a prompt-level simulation without providing real retrieved documents. The study does not include a genuine RAG condition (W4 with actual document retrieval), which means it cannot answer whether true RAG systems improve citation reliability. This is the most important gap for future work to address.
- **Limited E3 annotation**: Preliminary claim support analysis on a sample of 52 references was conducted; full results are deferred to a separate study.
- **Sample size**: 30 research questions × 4 workflows × 2 models = 240 paragraphs is moderate.
- **API coverage**: Some real papers may not be indexed in the APIs we queried.

## 6. Conclusion

We conducted a controlled evaluation of four LLM-assisted academic writing workflows across two models (DeepSeek-chat and Qwen3-14B), verifying 1,974 references (950 from DeepSeek + 1,024 from Qwen3) against scholarly APIs. Our results show that only 59.1% (DeepSeek) and 16.4% (Qwen3) of generated references can be verified as existing works. Critically, the relative ranking of workflows is invariant across models: direct generation and verify-and-repair as the top two workflows, followed by cautious prompting, with the baseless retrieval claim performing worst—a ranking confirmed by chi-square tests (p < 0.001 for both models). Cautious prompting helps but trades citation existence for metadata completeness. The baseless retrieval claim (W2) paradoxically performs worst across both models, and we discuss why claiming retrieval without actual grounding may be worse than transparent direct generation. Chinese language prompts show lower reliability. The invariant workflow ranking across two models suggests that these risks are not model-specific, and that workflow-level interventions such as verify-and-repair instructions can provide consistent benefits across different LLM backends. However, the limited benefit of W3 over W0 suggests that prompt-level interventions alone are insufficient and must be paired with post-generation verification pipelines. These findings underscore the need for integrated verification pipelines in AI-assisted academic writing tools and caution against reliance on unverified LLM-generated citations.

## Data Availability and Supplementary Materials

All supplementary materials are publicly available to ensure reproducibility of this study:

- **Complete prompt set** (240 prompts across 4 workflows × 30 research questions × 2 models): 120 prompts each for DeepSeek-chat and Qwen3-14B, with English and Chinese variants.
- **Model outputs**: 240 generated paragraphs (120 for DeepSeek-chat + 120 for Qwen3-14B), saved as individual `.txt` files with prompt identifiers.
- **Reference extraction results**: 1,974 extracted references (950 from DeepSeek + 1,024 from Qwen3) with DOI annotations.
- **Verification results**: Complete API verification data including crossref, OpenAlex, and arXiv matching results.
- **Analysis scripts**: Python scripts for prompt generation, reference extraction, API verification, and statistical analysis.

The verification pipeline consists of three API query stages:

1. **Primary verification**: DOI exact-match query against Crossref API (api.crossref.org/works/{doi})
2. **Secondary verification**: OpenAlex API filter by DOI (api.openalex.org/works?filter=doi:{doi})
3. **arXiv API**: For DOIs with prefix 10.48550/arxiv., query via export.arxiv.org/api/query?id_list={arxiv_id}

R code for statistical analysis is available upon request. Task prompts, model outputs, and full verification data can be regenerated using the provided scripts with the documented API parameters.

## Appendix A: Prompts by Workflow

**A.1 Workflow W0 (Direct)**

Prompt template (English):
"Research question: {question}
Write a related-work paragraph for an academic paper and include references.
Use this exact output structure:
[Body]
One related-work paragraph of 150-250 words using numbered citations such as [1] and [2].
[References]
List 5-8 references by number. Include authors, year, title, venue/source, and DOI when available."

**A.2 Workflow W1 (Cautious)**
Adds constraint: "Cite only papers that you are confident really exist. If you are unsure, do not fabricate a reference. Include DOI when available, but do not guess DOI values."

**A.3 Workflow W2 (Baseless Retrieval Claim)**
Adds instruction: "You will be given a list of retrieved candidate papers. Write the related-work paragraph using only those papers. Do not cite papers outside the retrieved list."

**A.4 Workflow W3 (Verify-and-Repair)**
Adds instruction: "The references will later be automatically verified, so use only real and verifiable references. Do not invent authors, titles, years, venues, or DOI values."

Chinese prompt variants follow the same structure with Chinese-translated research questions. Identical prompts were used for both DeepSeek-chat and Qwen3-14B.

## Appendix B: Model Configuration

**DeepSeek-chat (primary model)**
- API endpoint: api.deepseek.com/chat/completions
- Model: deepseek-chat
- Temperature: 0.7
- Max tokens: 2048
- System prompt: none
- Rate limit: 0.5s between requests
- Access date: July 6, 2026

**Qwen3-14B (cross-validation model)**
- API endpoint: api.siliconflow.cn/v1/chat/completions
- Model: Qwen/Qwen3-14B
- Temperature: 0.7
- Max tokens: 2048
- System prompt: none
- Rate limit: 0.1s between requests
- Access date: July 6, 2026

## Appendix C: Verification Details

The verification script uses the following steps:

1. Parse text for [References] or [参考文献] section marker
2. Extract numbered reference entries from the section
3. Extract DOI using regex pattern: \b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b
4. For each DOI, attempt verification in order:
   a. Crossref API: exact DOI match
   b. OpenAlex API: DOI filter match
   c. arXiv API: for 10.48550/arxiv.* DOIs
   d. DOI.org HEAD request: verify DOI resolves
5. If no API match, classify as "unresolved"
6. Deep sample: additional verification via Semantic Scholar API and title-based Crossref search

The deep hallucination (E1) analysis sampled 30 unresolved DOI and 30 no-DOI references for secondary verification.


## References

[1] Zuccon, G., Koopman, B., & Shaik, R. (2023). ChatGPT Hallucinates when Attributing Answers. arXiv:2309.09401.

[2] Walters, W. H., & Wilder, E. I. (2023). Fabrication and errors in the bibliographic citations generated by ChatGPT. Scientific Reports, 13(1), 14045.

[3] Athaluri, S. A., et al. (2023). Exploring the boundaries of real reference generation by ChatGPT. Cureus, 15(4).

[4] Zhao, H., Chen, L., & Wang, Z. (2026). LLM hallucinations in the wild: Large-scale evidence from non-existent citations. arXiv:2605.07723.

[5] Russinovich, M., Siva Kumar, R., & Salem, A. (2026). Phantom References: Auditing Top-Tier Conference Papers for AI-Hallucinated Citations. arXiv:2607.00738.

[6] Ansari, G. (2026). Compound Deception in Elite Peer Review. arXiv:2602.05930.

[7] Lewis, P., et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. NeurIPS. arXiv:2005.11401.

[8] Asai, A., et al. (2023). Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection. ICLR 2024. arXiv:2310.11511.

[9] Glynn, T. (2025). Guarding against artificial intelligence-hallucinated citations. arXiv:2503.19848.

[10] Yuan, S., et al. (2026). CiteAudit: A Benchmark for Scientific Citation Verification in the LLM Era. arXiv:2602.23452.

[11] Abbonato, D. (2026). CheckIfExist: Multi-Source Validation of Reference Authenticity. arXiv:2602.15871.

[12] Tilwani, D., et al. (2024). REASONS: A Benchmark for Evaluating Scientific Citation Generation and Claim Support. AAAI 2024. arXiv:2405.02228.

[13] Friel, R., et al. (2024). RAGBench: A Comprehensive Benchmark for Evaluating RAG Systems. arXiv:2407.11005.

[14] Min, S., et al. (2023). FActScore: Fine-grained Atomic Evaluation of Factual Precision. EMNLP 2023. arXiv:2305.14251.
