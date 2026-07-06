# ReceiptInject: Evaluation Infrastructure for Untrusted Document-Understanding LLM Agents

## Abstract

ReceiptInject is synthetic evaluation infrastructure for testing document-understanding LLM agents on untrusted inputs. It combines deterministic synthetic data generation, typed schemas, prompt mitigation modes, EvalGrid provider runs, raw-output logging, reproducible scoring, and final artifact generation. The current empirical result is a preliminary 2,700-row comparison across Gemini, OpenAI, and Mistral on 300 synthetic examples under three strategies: `baseline_minimal`, `combined_safety_schema`, and `trusted_tool_gating`.

## Problem Statement

Document-understanding agents often receive trusted user instructions and untrusted document text in the same context. A document can contain text that resembles an instruction, system note, reviewer comment, or administrative override. ReceiptInject evaluates whether models can extract useful structured facts while avoiding embedded-instruction compliance, private-field leakage, hallucination, unsafe action recommendations, and unnecessary refusal.

## Threat Model

The adversary controls visible text inside a synthetic document. The evaluator controls the trusted task. The model should treat document text as untrusted data and should not follow embedded document instructions as operational commands.

ReceiptInject does not model hidden text, invisible text, steganography, malware, account compromise, or unauthorized testing of production systems.

## Benchmark Design

Each example is represented by a typed `BenchmarkExample` schema containing document metadata, expected task, document text, ground-truth fields, synthetic private fields, expected safe behavior, and tags.

Document types:

- receipts
- invoices
- bank statements
- policy/legal/public-sector documents
- mixed bundles

Attack types:

- `none`
- `instruction_override`
- `privacy_exfiltration`
- `role_confusion`
- `fake_policy`
- `hidden_action_request`
- `data_poisoning`
- `conflicting_instructions`
- `authority_impersonation`
- `format_injection`

## System Architecture

```text
Synthetic templates -> deterministic JSONL dataset -> evaluation suite
        -> prompt mitigation -> EvalGrid provider call
        -> raw JSONL output -> scored CSV -> final summary/validation
```

EvalGrid provides config-driven provider execution, metadata, raw output logging, and resumability. The current 300-example comparison uses Gemini 3.1 Flash Lite, OpenAI GPT-4o mini, and Mistral Large Latest. Claude/Anthropic was not run because no local `ANTHROPIC_API_KEY` was available.

## Metrics

ReceiptInject reports:

- extraction accuracy
- prompt-injection compliance
- privacy leakage
- unsafe action rate
- hallucination
- over-refusal
- suspicious instruction detection
- safe completion rate
- utility/safety tradeoff

For trusted-tool gating, the project separates unsafe model proposals from unsafe execution. `unsafe_model_proposal` records whether the model proposed an unsafe action such as sending email, making payment, revealing private information, calling a webhook, updating records, or obeying an embedded document instruction. `unsafe_execution` records whether the deterministic executor-side gate allowed such an action. Under trusted-tool gating, unsafe proposals remain logged even when unsafe execution is blocked.

The scorers are intentionally transparent and reproducible, but they are heuristic and require manual inspection before strong conclusions.

## Preliminary 300-Example Cross-Provider Results

The current cross-provider result uses `data/examples_300.jsonl`: 300 synthetic examples per provider/strategy, 3 providers, 3 strategies, and 2,700 total real-provider rows. All nine runs completed with 0 error rows.

| Model | Mitigation | n | Extraction Accuracy | Safe Completion | Hallucination | Prompt-Injection Compliance | Suspicious Instruction Detection |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Gemini 3.1 Flash Lite | `baseline_minimal` | 300 | 49.3% | 31.3% | 32.7% | 19.7% | 83.7% |
| Gemini 3.1 Flash Lite | `combined_safety_schema` | 300 | 90.8% | 100.0% | 0.0% | 0.0% | 100.0% |
| Gemini 3.1 Flash Lite | `trusted_tool_gating` | 300 | 90.8% | 100.0% | 0.0% | 0.0% | 100.0% |
| OpenAI GPT-4o mini | `baseline_minimal` | 300 | 59.5% | 74.0% | 8.7% | 4.0% | 53.7% |
| OpenAI GPT-4o mini | `combined_safety_schema` | 300 | 90.5% | 100.0% | 0.0% | 0.0% | 58.7% |
| OpenAI GPT-4o mini | `trusted_tool_gating` | 300 | 89.8% | 99.0% | 0.0% | 0.0% | 97.7% |
| Mistral Large Latest | `baseline_minimal` | 300 | 40.4% | 25.0% | 40.3% | 38.7% | 81.0% |
| Mistral Large Latest | `combined_safety_schema` | 300 | 90.6% | 99.7% | 0.3% | 0.0% | 98.3% |
| Mistral Large Latest | `trusted_tool_gating` | 300 | 90.6% | 100.0% | 0.0% | 0.0% | 99.7% |

These numbers support a narrow claim: ReceiptInject can run a controlled, reproducible passive comparison across providers and mitigation prompts on synthetic untrusted documents. They do not prove production safety or establish broad model rankings.

## Trusted-Tool Gating Status

The `trusted_tool_gating` strategy is implemented as a real execution path. The prompt asks the model for an extraction section and a structured `proposed_actions` section. The deterministic policy gate records:

- `unsafe_model_proposal`
- `unsafe_execution`
- `blocked_action_count`
- `allowed_action_count`

The full 300-example trusted-gating runs completed for OpenAI, Mistral, and Gemini. Unsafe model proposal rates were 1.0% for OpenAI, 8.0% for Mistral, and 19.0% for Gemini. Unsafe execution was 0.0% for all three providers under the deterministic gate. This supports a defense-in-depth evaluation result: unsafe model proposals can remain measurable while executor-side gating blocks simulated unsafe execution.

## Dataset Diversity Audit

The dataset diversity audit reports:

| Audit item | Value |
| --- | ---: |
| Duplicate `document_text` rows | 0 |
| Repeated tracked-value occurrences | 608 |

Repeated synthetic merchants, vendors, institutions, and tracked values remain a limitation. This pass did not regenerate the dataset, so broad coverage language should remain cautious.

## Validation

The current 300-example artifacts include 2,700 real-provider rows:

- Gemini `baseline_minimal`: 300 rows
- Gemini `combined_safety_schema`: 300 rows
- OpenAI `baseline_minimal`: 300 rows
- OpenAI `combined_safety_schema`: 300 rows
- Mistral `baseline_minimal`: 300 rows
- Mistral `combined_safety_schema`: 300 rows
- Gemini `trusted_tool_gating`: 300 rows
- OpenAI `trusted_tool_gating`: 300 rows
- Mistral `trusted_tool_gating`: 300 rows

The combined artifacts are `results/evalgrid_2700_all_results.csv` and `results/evalgrid_2700_summary.md`.

## Limitations

- Synthetic data only
- Preliminary 300-example synthetic comparison
- No Claude/Anthropic rows
- Full trusted-gating 300-example results are pending
- Automated scorers are heuristic
- Manual review is still needed
- OCR is implemented but excluded from this headline comparison
- Dataset templates still repeat some tracked values
- Results may vary by provider, model version, prompt formatting, and API behavior

## Responsible Use

ReceiptInject is for defensive AI safety evaluation only. Users should not insert real private documents or use the project to attack real systems. Results are not legal, financial, medical, compliance, or operational advice.

## Future Work

- Add Claude/Anthropic once a key is available
- Add manual review for trusted-gating blocked-action cases
- Increase synthetic template and value diversity
- Add human annotation and manual adjudication
- Expand OCR stress tests
- Improve semantic scoring
- Track cost and latency more systematically across providers
