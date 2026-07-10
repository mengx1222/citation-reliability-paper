# Model Output Format

This document describes the format of model-generated paragraphs used in the experiment.

## File Naming Convention

Each output file follows a strict naming pattern:

```text
{TASK_ID}_{WORKFLOW}__{MODEL}.txt
```

Examples:

- `T001_W0_DIRECT__deepseek-chat.txt`
- `T001_W0_DIRECT__qwen3-14b.txt`
- `T017_W3_VERIFY_REPAIR__deepseek-chat.txt`

### Components

| Part | Values | Description |
|------|--------|-------------|
| Task ID | T001 -- T030 | Maps to a research question in `data/task_seed.csv` |
| Workflow | W0_DIRECT, W1_CAUTIOUS, W2_RETRIEVAL_FIRST, W3_VERIFY_REPAIR | Writing condition |
| Model | deepseek-chat, qwen3-14b | The model that generated the output |

## Output Structure

Each `.txt` file contains one LLM-generated paragraph with its references, following this structure:

```text
[Body]
A related-work paragraph of 150--250 words (English) or 300--500 characters (Chinese).
Citations appear as bracketed numbers such as [1] and [2].

[References]
1. Author list. Title. Venue, Year. DOI.
2. Author list. Title. Venue, Year. DOI.
...
```

This format is enforced by the prompt template in `code/build_prompts.py`.

## Examples (From the Packaged Verification Data)

The following examples are reconstructed from the verification CSV files.
They show what a generated reference looks like within a paragraph.

### English, T001 W0 Direct, DeepSeek-chat

A generated reference from this session (reconstructed from verified data):

> J. Maynez, S. Narayan, B. Bohnet, and R. McDonald, "On faithfulness and
> factuality in abstractive summarization," in *Proceedings of the 58th Annual
> Meeting of the Association for Computational Linguistics*, 2020, pp. 1--12.
> DOI: 10.18653/v1/2020.acl-main.173

### Chinese, T002 W1 Cautious, DeepSeek-chat

A generated reference from this session:

> Zhao, R., & Kim, S. (2023). Training data inconsistency as a source of
> citation structure errors in LLMs. *Transactions of the Association for
> Computational Linguistics*, 11, 234--249. DOI: 10.1162/tacl_a_00678

## Verifying Against Outputs

To verify that the packaged verification tables correctly represent the
original model outputs, compare any reference in
`results/extracted_refs_deepseek.csv` or `results/extracted_refs_qwen.csv`
against the corresponding entry in the original model `.txt` file (if available).

## Obtaining the Full Output Set

The full set of 240 generated paragraphs is not bundled in this repository.
To reproduce them:

1. Regenerate prompts: `python code/run_experiment.py --step prompts`
2. Send prompts to model APIs (DeepSeek, SiliconFlow, etc.)
3. Save each response as a `.txt` file following the naming convention above
4. Extract references: `python code/verify_citations.py extract --outputs-dir outputs/deepseek --out results/extracted_refs_deepseek.csv`
5. Verify: `python code/verify_citations.py verify --input ... --out ... --online`
