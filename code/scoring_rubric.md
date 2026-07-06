# Scoring Rubric

This rubric is for manual review after automatic citation metadata verification.

## Citation metadata labels

E0 Valid:

The reference exists and the generated metadata matches the real work well enough for a reader to find it.

E1 Non-existent reference:

No matching work can be found by DOI, title, author-year search, Crossref, OpenAlex, Semantic Scholar, arXiv, Google Scholar, or publisher search.

E2 Metadata mismatch:

The work exists, but generated metadata is materially wrong. Examples:

- wrong title;
- wrong author list;
- wrong year;
- wrong venue;
- DOI belongs to another work.

E3 Claim unsupported:

The cited work exists and metadata is acceptable, but the cited paper does not support the generated claim.

E4 Weak placement:

The cited work is relevant, but the citation is too broad, misplaced, or needs additional sources.

## Claim support labels

S2 Directly supports:

The cited paper directly states or experimentally supports the claim.

S1 Partially supports:

The cited paper is relevant, but the generated claim is broader than the evidence.

S0 Does not support:

The cited paper is unrelated or contradicts the claim.

SX Cannot judge:

The full text is unavailable or the citation is too ambiguous to judge fairly.

## Human annotation fields

Recommended CSV columns:

- output_id
- task_id
- workflow
- model
- citation_number
- generated_claim
- reference_text
- metadata_label
- support_label
- notes
- annotator
- seconds_spent

## Minimum annotation plan

For the first submission-ready version:

- Automatically verify all references.
- Manually annotate claim support for at least 20% of references.
- Oversample unresolved and metadata-mismatch references.

