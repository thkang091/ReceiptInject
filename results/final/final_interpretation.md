# Final Interpretation

These preliminary results should be interpreted cautiously. ReceiptInject uses a synthetic benchmark, and its automated scorers are intentionally simple and auditable rather than substitutes for human review.

The current headline comparison includes Gemini, OpenAI, and Mistral on the same 300-example synthetic dataset under `baseline_minimal`, `combined_safety_schema`, and `trusted_tool_gating`. The combined artifact contains 2,700 real-provider rows with 0 error rows.

Across all three providers, `combined_safety_schema` improved automated extraction and safety metrics relative to `baseline_minimal`. The trusted-tool-gating strategy adds a systems-oriented measurement: unsafe model proposals remain visible, while simulated executor-side gating blocks unsafe execution. In the current result, unsafe model proposal rates under trusted gating were 19.0% for Gemini, 8.0% for Mistral, and 1.0% for OpenAI; unsafe execution was 0.0% for all three providers.

This should be read as a preliminary synthetic benchmark result about evaluation infrastructure and defense-in-depth measurement, not as evidence that any provider is safe in production. The executor is simulated, the documents are synthetic, and scorer labels remain heuristic.

Claude/Anthropic was not run because no local Anthropic API key was available. OCR rows and mock rows are excluded from the headline comparison.

Dataset diversity remains a limitation: `results/dataset_diversity_audit.md` documents 608 repeated tracked-value occurrences in the 500-example synthetic dataset.
