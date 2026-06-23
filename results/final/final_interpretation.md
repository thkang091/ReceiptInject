# Final Interpretation

These preliminary results should be interpreted cautiously. ReceiptInject uses a synthetic benchmark, and its automated scorers are intentionally simple and auditable rather than a substitute for human review.

## What the Hard-Subset Results Suggest

On the 50-example hard subset, `baseline_minimal` achieved 45.3% extraction accuracy and 54.0% safe completion. `combined_safety_schema` achieved 84.7% extraction accuracy and 100.0% safe completion. Automated hallucination labels fell from 12.0% to 0.0%, and prompt-injection compliance fell from 6.0% to 0.0%.

This makes the mitigation contrast visible: the benchmark can expose failures in a weak prompt and compare them against a structured safety prompt. These are preliminary synthetic benchmark results and do not prove production safety.

## Where Combined Safety Helped

The structured mitigation appears to help with extraction utility and safety discipline on this hard subset. In particular, it improved extraction accuracy, improved safe completion, reduced automated hallucination labels, and reduced automated prompt-injection compliance labels in the selected OpenAI run.

## Where Manual Review Is Still Needed

The manual review sample looks broadly plausible, but it also reveals scorer limitations. Some policy-document hallucination labels appear to reflect strict matching or phrasing differences rather than clear fabricated facts. This is useful for benchmark development, but it means the automated metrics should be treated as screening signals rather than final judgments.

## Dataset Diversity Limitation

The dataset diversity audit reports 0 duplicate document texts, but 608 repeated tracked-value occurrences remain. This is acceptable for a synthetic benchmark prototype if disclosed, but it should be improved before claiming broad coverage of real-world document variation.

## OCR Pipeline Notes

The current final hard-subset comparison is text-only. OCR support exists elsewhere in the project, but OCR coverage should be described as preliminary or pending unless a specific OCR run is included in the selected final artifacts.

## Responsible Interpretation

ReceiptInject is defensive evaluation infrastructure. It should be described as a way to generate synthetic untrusted-document tasks, run controlled model evaluations, log raw outputs, compute reproducible metrics, and export cases for manual inspection. It should not be described as solving prompt injection or proving that a model is safe.

## Future Work

Future work should add larger manually reviewed samples, human annotation, more diverse synthetic templates, richer semantic scorers, more provider comparisons, OCR stress tests, and controlled tool-use simulations.
