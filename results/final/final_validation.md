# Final Validation

## Current Headline Runs

Current headline artifact: `results/evalgrid_2700_all_results.csv`  
Summary artifact: `results/evalgrid_2700_summary.md`  
Dataset: `data/examples_300.jsonl`

| run_id | model | mitigation | dataset | rows | errors |
| --- | --- | --- | --- | ---: | ---: |
| `evalgrid_gemini_300_baseline_minimal` | `gemini-3.1-flash-lite` | `baseline_minimal` | `data/examples_300.jsonl` | 300 | 0 |
| `evalgrid_gemini_300_safety_schema` | `gemini-3.1-flash-lite` | `combined_safety_schema` | `data/examples_300.jsonl` | 300 | 0 |
| `evalgrid_gemini_300_trusted_gating` | `gemini-3.1-flash-lite` | `trusted_tool_gating` | `data/examples_300.jsonl` | 300 | 0 |
| `evalgrid_openai_300_baseline_minimal` | `gpt-4o-mini` | `baseline_minimal` | `data/examples_300.jsonl` | 300 | 0 |
| `evalgrid_openai_300_safety_schema` | `gpt-4o-mini` | `combined_safety_schema` | `data/examples_300.jsonl` | 300 | 0 |
| `evalgrid_openai_300_trusted_gating` | `gpt-4o-mini` | `trusted_tool_gating` | `data/examples_300.jsonl` | 300 | 0 |
| `evalgrid_mistral_300_baseline_minimal` | `mistral-large-latest` | `baseline_minimal` | `data/examples_300.jsonl` | 300 | 0 |
| `evalgrid_mistral_300_safety_schema` | `mistral-large-latest` | `combined_safety_schema` | `data/examples_300.jsonl` | 300 | 0 |
| `evalgrid_mistral_300_trusted_gating` | `mistral-large-latest` | `trusted_tool_gating` | `data/examples_300.jsonl` | 300 | 0 |

Total selected headline result rows: 2,700.  
Total selected headline error rows: 0.

## Legacy Hard-Subset Artifacts

The older hard-subset files under `results/final/final_results.csv` and related summaries cover 200 rows from OpenAI + Mistral on `data/hard_test_subset_50.jsonl`. They are retained as early validation artifacts, not as the current headline result.

## Scope

The current headline comparison is text-only and includes Gemini, OpenAI, and Mistral on the same 300-example synthetic dataset and three strategies. Claude/Anthropic was not run because no local `ANTHROPIC_API_KEY` was available. OCR rows and mock rows are excluded from the headline comparison.

`trusted_tool_gating` is a simulated executor-side strategy. It records unsafe model proposals separately from unsafe execution. It does not execute real external actions and does not prove production tool safety.

## Validation Checklist

| Check | Status |
| --- | --- |
| Current headline centered on 2,700-row artifact | PASS |
| Three providers included: Gemini, OpenAI, Mistral | PASS |
| Three strategies included: baseline, safety/schema, trusted gating | PASS |
| Headline rows have zero errors | PASS |
| Mock rows excluded from final evidence | PASS |
| OCR rows excluded from headline comparison | PASS |
| Claude/Anthropic absence stated clearly | PASS |
| Dataset diversity caveat retained | PASS |
| `pytest` | PASS: 171 passed |
| `ruff check .` | PASS |
| `python scripts/validate_dataset.py --data data/examples_300.jsonl` | PASS |

## Dataset Diversity Caveat

`results/dataset_diversity_audit.md` reports 0 duplicate `document_text` rows and 608 repeated tracked-value occurrences across the 500-example dataset. This remains a known synthetic-template limitation.

## Manual Review

Manual review is still needed before drawing strong claims from individual examples. Automated scorers are useful for reproducible comparisons but can over-label formatting differences, paraphrases, schema choices, or model-specific structured-output behavior.
