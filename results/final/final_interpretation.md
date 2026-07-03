# Final Interpretation

These preliminary results should be interpreted cautiously. ReceiptInject uses a synthetic benchmark, and its automated scorers are intentionally simple and auditable rather than substitutes for human review.

The current curated passive comparison includes OpenAI and Mistral on the same 50-example hard subset under `baseline_minimal` and `combined_safety_schema`. Both providers improved under the structured safety prompt by automated metrics, but these numbers should be treated as small-sample synthetic evidence about the evaluation pipeline and prompt comparison, not production reliability evidence.

Claude/Anthropic was not run because no local Anthropic API key was available. OCR rows and mock rows are excluded from the headline comparison.

Dataset diversity remains a limitation: `results/dataset_diversity_audit.md` documents 608 repeated tracked-value occurrences in the 500-example synthetic dataset.
