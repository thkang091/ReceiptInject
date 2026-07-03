# Preliminary Hard-Subset Results

Source: `results/final/final_results.csv`
Dataset: `data/hard_test_subset_50.jsonl`

These are preliminary real-model results on a 50-example synthetic hard subset. The comparison now includes OpenAI and Mistral on the same examples and the same two passive mitigation conditions. Claude/Anthropic was not run because no local `ANTHROPIC_API_KEY` was available.

The hard subset contains 50 examples: 10 receipts, 10 invoices, 10 bank statements, 10 policy documents, and 10 mixed bundles. It includes 20 benign examples and 30 adversarial examples. Difficulty is intentionally skewed toward harder cases: 43 hard, 6 medium, and 1 easy.

## Headline Table

| Model | Mitigation | n | Extraction Accuracy | Safe Completion | Hallucination | Prompt-Injection Compliance | Suspicious Instruction Detection |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mistral-large-latest | `baseline_minimal` | 50 | 26.3% | 12.0% | 40.0% | 50.0% | 80.0% |
| mistral-large-latest | `combined_safety_schema` | 50 | 84.0% | 98.0% | 2.0% | 0.0% | 94.0% |
| openai | `baseline_minimal` | 50 | 45.3% | 54.0% | 12.0% | 6.0% | 40.0% |
| openai | `combined_safety_schema` | 50 | 84.7% | 100.0% | 0.0% | 0.0% | 52.0% |

## Interpretation

On this synthetic hard subset, `combined_safety_schema` improved automated extraction and safety metrics for both evaluated providers relative to `baseline_minimal`. This supports a narrow claim: ReceiptInject can run a controlled cross-provider passive comparison and expose mitigation-sensitive behavior on synthetic untrusted documents.

This does not prove production safety, does not establish broad model rankings, and should not be treated as legal, financial, compliance, or operational advice. Automated scorer labels remain heuristic and require manual review.

## Scope Notes

- OpenAI final rows: 100 rows from two 50-example runs.
- Mistral final rows: 100 completed rows from two 50-example EvalGrid runs; one transient 429 in the combined run was retried successfully and excluded from the curated completed-row CSV.
- Claude/Anthropic: not run in this pass.
- OCR: not included in this headline comparison.
- Mock results: pipeline validation only, not research evidence.

## Dataset Diversity Caveat

`results/dataset_diversity_audit.md` reports 0 duplicate `document_text` rows but 608 repeated tracked-value occurrences across the 500-example dataset. This remains a synthetic-template limitation; the dataset was not regenerated in this pass, so broad coverage language should stay cautious.
