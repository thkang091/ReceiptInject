# EvalGrid 300-Example Cross-Model Summary

Preliminary synthetic benchmark results. These rows come from local real-provider runs over `data/examples_300.jsonl`. Automated scorer limitations and synthetic-template limitations still apply.

| model | mitigation | rows | errors | extraction_accuracy | safe_completion_rate | prompt_injection_compliance | privacy_leakage | unsafe_action_rate | hallucination | over_refusal | suspicious_instruction_detection |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gemini-3.1-flash-lite | baseline_minimal | 300 | 0 | 0.493 | 0.313 | 0.197 | 0.030 | 0.003 | 0.327 | 0.000 | 0.837 |
| gemini-3.1-flash-lite | combined_safety_schema | 300 | 0 | 0.908 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| gpt-4o-mini | baseline_minimal | 300 | 0 | 0.595 | 0.740 | 0.040 | 0.000 | 0.017 | 0.087 | 0.000 | 0.537 |
| gpt-4o-mini | combined_safety_schema | 300 | 0 | 0.905 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.587 |
| mistral-large-latest | baseline_minimal | 300 | 0 | 0.404 | 0.250 | 0.387 | 0.047 | 0.000 | 0.403 | 0.000 | 0.810 |
| mistral-large-latest | combined_safety_schema | 300 | 0 | 0.906 | 0.997 | 0.000 | 0.000 | 0.000 | 0.003 | 0.000 | 0.983 |

Notes:
- Mock outputs are not included in this summary.
- All six 300-example real-provider runs completed with 0 error rows.
- These results should not be described as proof of production safety.
