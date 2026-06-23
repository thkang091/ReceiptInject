# Preliminary Hard-Subset Results

Source results: `results/results.csv`
Dataset path: `data/hard_test_subset_50.jsonl`

Model name: `openai`
Run IDs included: `openai_hard_baseline_minimal_50`, `openai_hard_combined_schema_50`
Rows included: 100 total result rows, covering 50 hard-subset examples under two mitigation modes.

These are preliminary synthetic benchmark results. The hard subset is deliberately more adversarial than the balanced subset. The results show that ReceiptInject can expose failures in a weak baseline and compare them against a structured mitigation. They do not prove production safety.

## Headline Comparison

| Metric | baseline_minimal | combined_safety_schema | Change |
| --- | ---: | ---: | ---: |
| Extraction accuracy | 45.3% | 84.7% | +39.3 pp |
| Safe completion rate | 54.0% | 100.0% | +46.0 pp |
| Hallucination rate | 12.0% | 0.0% | -12.0 pp |
| Prompt-injection compliance | 6.0% | 0.0% | -6.0 pp |
| Suspicious instruction detection | 40.0% | 52.0% | +12.0 pp |

## Metric Table

| model_name | mitigation | input_mode | n | extraction_accuracy | prompt_injection_compliance | privacy_leakage | unsafe_action_rate | hallucination | over_refusal | suspicious_instruction_detection | safe_completion_rate | utility_safety_tradeoff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openai | baseline_minimal | text | 50 | 0.453 | 0.060 | 0.000 | 0.000 | 0.120 | 0.000 | 0.400 | 0.540 | 0.449 |
| openai | combined_safety_schema | text | 50 | 0.847 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.520 | 1.000 | 0.847 |

## Hard Subset Composition

The hard subset contains 50 examples: 10 receipts, 10 invoices, 10 bank statements, 10 policy documents, and 10 mixed bundles. It includes 20 benign examples and 30 adversarial examples. Difficulty is intentionally skewed toward harder cases: 43 hard, 6 medium, and 1 easy.

## Result Interpretation

The weak `baseline_minimal` prompt produces visible extraction and safety failures on the hard subset. The `combined_safety_schema` prompt improves extraction accuracy and safe completion while reducing automated hallucination and prompt-injection compliance labels in this run. This is useful evidence that the benchmark can differentiate prompt mitigations under controlled synthetic conditions, not evidence that the model is safe in production.

## Known Limitations

Synthetic templates still repeat some tracked values. The diversity audit reports 0 duplicate document texts but 608 repeated tracked-value occurrences, especially recurring synthetic merchants, vendors, and institutions.

No real private documents are used. All examples are synthetic benchmark data.

Automated scorers are transparent but limited and are not a substitute for human review. The manual review sample is small and should be expanded before making strong claims.

OCR coverage is preliminary or absent in these selected final rows; the current headline comparison is text-only.

Results may vary by model, provider, prompt formatting, SDK behavior, and generation settings.

## OCR Pilot Status

No OCR evaluation rows were found in the selected final hard-subset results. OCR results should be reported separately as a small pilot when present, not mixed into this headline comparison.
