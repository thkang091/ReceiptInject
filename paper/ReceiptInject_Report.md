# ReceiptInject: Scalable Evaluation Infrastructure for Document-Understanding LLM Agents Under Untrusted Inputs

## Abstract

ReceiptInject is a research engineering project for evaluating document-understanding LLM agents on untrusted synthetic inputs. It combines deterministic synthetic data generation, realistic document templates, optional PDF/OCR support, multi-provider evaluation through EvalGrid, raw output logging, reproducible scoring, trusted-tool-gating experiments, and final artifact generation. The current curated result is a preliminary 2,700-row real-provider comparison across Gemini, OpenAI, and Mistral on a 300-example synthetic suite. The results are synthetic, automated-scored, and scorer-limited.

## Introduction

LLM document agents increasingly process receipts, invoices, bank statements, policy memos, and scanned documents. These inputs are not trusted instruction sources. A footer, internal note, OCR artifact, or policy appendix can contain text that looks like a command. ReceiptInject treats this as an evaluation-infrastructure problem: can a reproducible pipeline measure document-agent behavior under untrusted input conditions?

## Threat Model

The adversary controls visible text inside a synthetic document. The evaluator controls the actual task, such as extracting fields or summarizing factual content. The model should treat document text as untrusted data and should not follow embedded document instructions as operational commands.

## Benchmark Design

ReceiptInject examples use typed schemas with document metadata, expected task, document text, ground-truth fields, synthetic private fields, safe-behavior descriptions, expected constraints, and tags. Documents cover receipts, invoices, bank statements, policy/legal/public-sector documents, and mixed bundles.

Attack types include instruction override, privacy exfiltration, role confusion, fake policy, hidden action request, data poisoning, conflicting instructions, authority impersonation, and format injection.

## Dataset Generation

The generator is deterministic and seed-controlled. For `n=500`, the intended composition is 125 receipts, 125 invoices, 100 bank statements, 100 policy/legal/public-sector documents, and 50 mixed bundles. All names, IDs, totals, account-like values, emails, and private fields are synthetic.

The dataset diversity audit reports 0 duplicate `document_text` rows and 608 repeated tracked-value occurrences. This repeated-value issue is a synthetic-template limitation, and the current pass leaves that caveat intact.

## Evaluation Harness

The evaluation path loads JSONL examples, builds mitigation prompts, calls model providers, validates structured JSON output, scores results, and writes raw JSONL plus scored CSV rows. EvalGrid adds YAML configs, caching, resumability, provider metadata, and cost summaries.

## Metrics

ReceiptInject reports extraction accuracy, prompt-injection compliance, privacy leakage, unsafe action rate, hallucination, over-refusal, suspicious instruction detection, safe completion rate, and utility/safety tradeoff. These scorers are transparent MVP heuristics, not substitutes for human review.

## Preliminary Results

The current headline result uses `data/examples_300.jsonl`: 300 synthetic text-only examples across receipts, invoices, bank statements, and policy documents. Gemini, OpenAI, and Mistral were each evaluated under three strategies: `baseline_minimal`, `combined_safety_schema`, and `trusted_tool_gating`, for 2,700 total real-provider rows. The older `data/hard_test_subset_50.jsonl` comparison is retained as legacy validation material, not as the current public headline.

| Model | Strategy | n | Extraction Accuracy | Safe Completion | Hallucination | Prompt-Injection Compliance | Unsafe Proposal | Unsafe Execution |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Gemini 3.1 Flash Lite | `baseline_minimal` | 300 | 49.3% | 31.3% | 32.7% | 19.7% | 0.0% | 0.0% |
| Gemini 3.1 Flash Lite | `combined_safety_schema` | 300 | 90.8% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Gemini 3.1 Flash Lite | `trusted_tool_gating` | 300 | 90.8% | 100.0% | 0.0% | 0.0% | 19.0% | 0.0% |
| OpenAI GPT-4o mini | `baseline_minimal` | 300 | 59.5% | 74.0% | 8.7% | 4.0% | 0.0% | 0.0% |
| OpenAI GPT-4o mini | `combined_safety_schema` | 300 | 90.5% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| OpenAI GPT-4o mini | `trusted_tool_gating` | 300 | 89.8% | 99.0% | 0.0% | 0.0% | 1.0% | 0.0% |
| Mistral Large Latest | `baseline_minimal` | 300 | 40.4% | 25.0% | 40.3% | 38.7% | 0.0% | 0.0% |
| Mistral Large Latest | `combined_safety_schema` | 300 | 90.6% | 99.7% | 0.3% | 0.0% | 0.0% | 0.0% |
| Mistral Large Latest | `trusted_tool_gating` | 300 | 90.6% | 100.0% | 0.0% | 0.0% | 8.0% | 0.0% |

These results show that ReceiptInject can expose mitigation-sensitive behavior in a controlled synthetic setting and can run the same benchmark across multiple providers. The trusted-tool-gating rows also demonstrate a systems distinction between unsafe model proposals and unsafe simulated execution: the executor-side gate recorded nonzero unsafe proposal rates for some providers while blocking unsafe execution in this simulated setting. They do not prove production safety, and they should not be interpreted as broad model rankings.

Claude/Anthropic was not run because no local `ANTHROPIC_API_KEY` was available.

## Systems Lessons

The strongest contribution is systems execution: deterministic data generation, typed schemas, prompt configurations, provider abstraction, resumable runs, raw-output logging, reproducible scoring, final summaries, and validation artifacts. These are the components needed to turn a prompt-injection intuition into an auditable evaluation pipeline.

## Limitations

- Synthetic data only
- Synthetic 300-example text suite; no real private documents
- No Claude/Anthropic rows
- Automated scorers are heuristic
- Manual review is required before strong claims
- Dataset templates repeat some tracked values
- OCR is implemented but not part of the current headline comparison
- Trusted-tool gating is simulated and should be treated as a defense-in-depth baseline, not a guarantee of production tool safety

## Responsible Use

ReceiptInject is for defensive AI safety evaluation only. Users should not insert real private documents or use the project to attack real systems. Results are not legal, financial, medical, compliance, or operational advice.

## Future Work

Future work includes human annotation, richer rendered layouts, larger and more diverse synthetic datasets, real-world-inspired but privacy-preserving templates, additional model providers, semantic scorers, cost/latency tracking, and OCR stress tests.
