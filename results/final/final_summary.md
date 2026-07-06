# Preliminary 2,700-Row Cross-Provider Results

Current headline artifact: `results/evalgrid_2700_all_results.csv`  
Summary artifact: `results/evalgrid_2700_summary.md`  
Dataset: `data/examples_300.jsonl`

These are preliminary real-provider results on a 300-example synthetic benchmark suite. The comparison includes Gemini, OpenAI, and Mistral on the same dataset under three strategies: `baseline_minimal`, `combined_safety_schema`, and `trusted_tool_gating`.

The older 50-example hard-subset files under `results/final/final_results.csv` are retained as legacy/early validation artifacts. They are no longer the public headline result.

## Headline Table

| Model | Mitigation | n | Errors | Extraction Accuracy | Safe Completion | Hallucination | Prompt-Injection Compliance | Unsafe Model Proposal | Unsafe Execution |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Gemini 3.1 Flash Lite | `baseline_minimal` | 300 | 0 | 49.3% | 31.3% | 32.7% | 19.7% | 0.0% | 0.0% |
| Gemini 3.1 Flash Lite | `combined_safety_schema` | 300 | 0 | 90.8% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Gemini 3.1 Flash Lite | `trusted_tool_gating` | 300 | 0 | 90.8% | 100.0% | 0.0% | 0.0% | 19.0% | 0.0% |
| OpenAI GPT-4o mini | `baseline_minimal` | 300 | 0 | 59.5% | 74.0% | 8.7% | 4.0% | 0.0% | 0.0% |
| OpenAI GPT-4o mini | `combined_safety_schema` | 300 | 0 | 90.5% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| OpenAI GPT-4o mini | `trusted_tool_gating` | 300 | 0 | 89.8% | 99.0% | 0.0% | 0.0% | 1.0% | 0.0% |
| Mistral Large Latest | `baseline_minimal` | 300 | 0 | 40.4% | 25.0% | 40.3% | 38.7% | 0.0% | 0.0% |
| Mistral Large Latest | `combined_safety_schema` | 300 | 0 | 90.6% | 99.7% | 0.3% | 0.0% | 0.0% | 0.0% |
| Mistral Large Latest | `trusted_tool_gating` | 300 | 0 | 90.6% | 100.0% | 0.0% | 0.0% | 8.0% | 0.0% |

## Interpretation

On this synthetic 300-example suite, `combined_safety_schema` improved automated extraction and safety metrics relative to `baseline_minimal` for all three evaluated providers.

The trusted-tool-gating result supports a more systems-oriented claim: the benchmark can distinguish unsafe model proposals from unsafe simulated execution. Under `trusted_tool_gating`, unsafe model proposal rates were nonzero for Gemini, OpenAI, and Mistral, while unsafe execution remained 0.0% because the deterministic gate blocked unsafe proposed actions.

This does not prove production safety, does not establish broad model rankings, and should not be treated as legal, financial, compliance, or operational advice. Automated scorer labels are heuristic and require manual review.

## Scope Notes

- Gemini rows: 900 real-provider rows across three strategies.
- OpenAI rows: 900 real-provider rows across three strategies.
- Mistral rows: 900 real-provider rows across three strategies.
- Claude/Anthropic: not run in this pass.
- OCR: not included in this headline comparison.
- Mock results: pipeline validation only, not research evidence.
- Raw outputs are local artifacts; summary CSVs and metadata substantiate the public result.

## Dataset Diversity Caveat

`results/dataset_diversity_audit.md` reports 0 duplicate `document_text` rows but 608 repeated tracked-value occurrences across the 500-example dataset. This remains a synthetic-template limitation, so broad coverage language should stay cautious.
