# Final Validation

## Included Runs

| Run ID | Model | Mitigation | Dataset | Rows | Errors |
| --- | --- | --- | --- | ---: | ---: |
| `openai_hard_baseline_minimal_50` | `openai` | `baseline_minimal` | `data/hard_test_subset_50.jsonl` | 50 | 0 |
| `openai_hard_combined_schema_50` | `openai` | `combined_safety_schema` | `data/hard_test_subset_50.jsonl` | 50 | 0 |

Total selected result rows: 100.

## Dataset Used

The final artifacts center `data/hard_test_subset_50.jsonl`, not the older balanced-set-only results. The hard subset contains 50 examples, with 10 examples from each document type: bank statement, invoice, mixed bundle, policy document, and receipt.

The subset intentionally contains 20 benign and 30 adversarial examples. Difficulty is intentionally skewed toward hard examples: 43 hard, 6 medium, and 1 easy. Because of this intentional skew, the generic balanced-dataset validator's difficulty-balance warning is not treated as a final-artifact failure for this subset.

## Excluded Runs

High-error or earlier exploratory Mistral runs are not included in the selected final hard-subset comparison. Older balanced-set runs may remain useful for development history, but they are not the headline result in `final_summary.md`.

## Validation Checks

| Check | Status |
| --- | --- |
| Final results centered on hard subset | PASS |
| Included run rows present | PASS |
| Per-row API/evaluation errors in selected runs | PASS: 0 errors |
| Duplicate document_text in full dataset diversity audit | PASS: 0 duplicates |
| Repeated tracked values disclosed | PASS: 608 repeated tracked-value occurrences documented |
| `pytest` | PASS: 128 passed |
| `ruff check .` | PASS |
| Real private data used | PASS: no real private data used; benchmark data is synthetic |

## Manual Review Status

`results/hard_manual_review_sample.md` exists and includes examples from both mitigation modes, benign and adversarial documents, baseline failures, and successful extraction cases. Manual review is still needed before making strong claims because automated scorers can over-label paraphrases or formatting differences as failures.
