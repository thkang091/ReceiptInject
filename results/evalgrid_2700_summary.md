# EvalGrid 2,700-Row Cross-Model Summary

Preliminary synthetic benchmark results from real-provider runs over `data/examples_300.jsonl`: 3 providers x 3 strategies x 300 examples. Automated scorer limitations and synthetic-template limitations apply.

| model | mitigation | rows | errors | extraction | safe_completion | injection | hallucination | unsafe_model_proposal | unsafe_execution | blocked_actions | allowed_actions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gemini-3.1-flash-lite | baseline_minimal | 300 | 0 | 0.493 | 0.313 | 0.197 | 0.327 | 0.000 | 0.000 | 0.000 | 0.000 |
| gemini-3.1-flash-lite | combined_safety_schema | 300 | 0 | 0.908 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| gemini-3.1-flash-lite | trusted_tool_gating | 300 | 0 | 0.908 | 1.000 | 0.000 | 0.000 | 0.190 | 0.000 | 0.190 | 0.310 |
| gpt-4o-mini | baseline_minimal | 300 | 0 | 0.595 | 0.740 | 0.040 | 0.087 | 0.000 | 0.000 | 0.000 | 0.000 |
| gpt-4o-mini | combined_safety_schema | 300 | 0 | 0.905 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| gpt-4o-mini | trusted_tool_gating | 300 | 0 | 0.898 | 0.990 | 0.000 | 0.000 | 0.010 | 0.000 | 0.010 | 0.000 |
| mistral-large-latest | baseline_minimal | 300 | 0 | 0.404 | 0.250 | 0.387 | 0.403 | 0.000 | 0.000 | 0.000 | 0.000 |
| mistral-large-latest | combined_safety_schema | 300 | 0 | 0.906 | 0.997 | 0.000 | 0.003 | 0.000 | 0.000 | 0.000 | 0.000 |
| mistral-large-latest | trusted_tool_gating | 300 | 0 | 0.906 | 1.000 | 0.000 | 0.000 | 0.080 | 0.000 | 0.080 | 0.793 |

Notes:
- Mock outputs are not included.
- Full trusted-tool-gating results are included here only because the three real-provider 300-example runs completed.
- `unsafe_model_proposal` and `unsafe_execution` are only meaningful for `trusted_tool_gating`; baseline and safety/schema rows default to false/0.
- These results do not prove production safety.
