# Final Validation

## Included Runs

| run_id | model | mitigation | dataset | rows | errors |
| --- | --- | --- | --- | ---: | ---: |
| `openai_hard_baseline_minimal_50` | `openai` | `baseline_minimal` | `data/hard_test_subset_50.jsonl` | 50 | 0 |
| `openai_hard_combined_schema_50` | `openai` | `combined_safety_schema` | `data/hard_test_subset_50.jsonl` | 50 | 0 |
| `mistral_hard_baseline_minimal_50` | `mistral-large-latest` | `baseline_minimal` | `data/hard_test_subset_50.jsonl` | 50 | 0 |
| `mistral_hard_combined_schema_50` | `mistral-large-latest` | `combined_safety_schema` | `data/hard_test_subset_50.jsonl` | 50 | 0 |

Total selected result rows: 200.

## Scope

The final artifacts center `data/hard_test_subset_50.jsonl`. The hard subset contains 50 examples, with 10 examples from each document type: bank statement, invoice, mixed bundle, policy document, and receipt.

The selected comparison is text-only and includes OpenAI + Mistral on the same examples and the same two passive mitigation modes. Claude/Anthropic was not run because no local `ANTHROPIC_API_KEY` was available.

## Mistral Run Notes

Mistral was run through EvalGrid using `mistral-large-latest`.

- Baseline EvalGrid run: 50 completed, 0 failed.
- Combined-safety EvalGrid run: 49 completed, 1 transient 429 failure, then 1 resumed completion.
- Curated final CSV: 100 completed Mistral rows, 0 errors.

The transient failed 429 row is not included in the curated completed-row final CSV. The raw EvalGrid outputs and per-run summaries remain under `results/final/`.

## Validation Checklist

| Check | Status |
| --- | --- |
| Final results centered on hard subset | PASS |
| Included run rows present | PASS |
| Curated final rows have zero errors | PASS |
| OpenAI and Mistral use same hard subset | PASS |
| Claude/Anthropic absence stated clearly | PASS |
| Mock rows excluded from final evidence | PASS |
| OCR rows excluded from headline comparison | PASS |
| Dataset diversity caveat retained | PASS |
| `pytest` | PASS: 148 passed |
| `ruff check .` | PASS |

## Dataset Diversity Caveat

`results/dataset_diversity_audit.md` reports 0 duplicate `document_text` rows and 608 repeated tracked-value occurrences across the 500-example dataset. The dataset was not regenerated in this pass, so this remains a known synthetic-template limitation.

## Manual Review

Manual review is still needed before drawing strong claims from individual examples. Automated scorers are useful for reproducible comparisons but can over-label formatting differences, paraphrases, or schema choices.
