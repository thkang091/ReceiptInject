# ReceiptInject: Evaluation Infrastructure for Untrusted Document-Understanding LLM Agents

## Abstract

ReceiptInject is synthetic evaluation infrastructure for testing document-understanding LLM agents on untrusted inputs. It combines deterministic synthetic data generation, typed schemas, prompt mitigation modes, EvalGrid provider runs, raw-output logging, reproducible scoring, and final artifact generation. The current curated empirical result is a preliminary passive hard-subset comparison between OpenAI and Mistral on 50 synthetic examples under two mitigation conditions.

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
Synthetic templates -> deterministic JSONL dataset -> hard subset
        -> prompt mitigation -> EvalGrid provider call
        -> raw JSONL output -> scored CSV -> final summary/validation
```

EvalGrid provides config-driven provider execution, caching, metadata, raw output logging, and resumability. The current final comparison uses OpenAI and Mistral. Claude/Anthropic was not run because no local `ANTHROPIC_API_KEY` was available.

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

The scorers are intentionally transparent and reproducible, but they are heuristic and require manual inspection before strong conclusions.

## Preliminary Hard-Subset Results

The current final result uses `data/hard_test_subset_50.jsonl`: 50 synthetic examples, 10 per document type, 20 benign and 30 adversarial, with 43 hard, 6 medium, and 1 easy examples.

| Model | Mitigation | n | Extraction Accuracy | Safe Completion | Hallucination | Prompt-Injection Compliance | Suspicious Instruction Detection |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| OpenAI | `baseline_minimal` | 50 | 45.3% | 54.0% | 12.0% | 6.0% | 40.0% |
| OpenAI | `combined_safety_schema` | 50 | 84.7% | 100.0% | 0.0% | 0.0% | 52.0% |
| Mistral | `baseline_minimal` | 50 | 26.3% | 12.0% | 40.0% | 50.0% | 80.0% |
| Mistral | `combined_safety_schema` | 50 | 84.0% | 98.0% | 2.0% | 0.0% | 94.0% |

These numbers support a narrow claim: ReceiptInject can run a controlled, reproducible passive comparison across providers and mitigation prompts on synthetic untrusted documents. They do not prove production safety or establish broad model rankings.

## Dataset Diversity Audit

The dataset diversity audit reports:

| Audit item | Value |
| --- | ---: |
| Duplicate `document_text` rows | 0 |
| Repeated tracked-value occurrences | 608 |

Repeated synthetic merchants, vendors, institutions, and tracked values remain a limitation. This pass did not regenerate the dataset, so broad coverage language should remain cautious.

## Validation

The final artifacts include 200 curated passive rows:

- OpenAI `baseline_minimal`: 50 rows
- OpenAI `combined_safety_schema`: 50 rows
- Mistral `baseline_minimal`: 50 rows
- Mistral `combined_safety_schema`: 50 rows

Mistral was run through EvalGrid using `mistral-large-latest`. One transient 429 in the combined-safety pass was retried successfully; the curated final CSV contains completed rows only.

## Limitations

- Synthetic data only
- Small hard-subset comparison
- No Claude/Anthropic rows
- Automated scorers are heuristic
- Manual review is still needed
- OCR is implemented but excluded from this headline comparison
- Dataset templates still repeat some tracked values
- Results may vary by provider, model version, prompt formatting, and API behavior

## Responsible Use

ReceiptInject is for defensive AI safety evaluation only. Users should not insert real private documents or use the project to attack real systems. Results are not legal, financial, medical, compliance, or operational advice.

## Future Work

- Add Claude/Anthropic once a key is available
- Increase synthetic template and value diversity
- Add human annotation and manual adjudication
- Expand OCR stress tests
- Improve semantic scoring
- Track cost and latency more systematically across providers
