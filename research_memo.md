# ReceiptInject: Scalable Evaluation Infrastructure for Document-Understanding LLM Agents

## 1. Motivation

Document-understanding LLM agents increasingly process receipts, invoices, bank statements, policy memos, and scanned PDFs. These documents are not trusted instruction sources: a footer, internal note, OCR artifact, or policy appendix can contain text that looks like a command. ReceiptInject studies this as an evaluation-infrastructure problem rather than as a one-off prompt-injection demo.

## 2. Research Question

Can document-understanding LLM agents extract useful structured information from untrusted documents without following embedded instructions, leaking private fields, hallucinating facts, over-refusing benign tasks, or recommending unsafe external actions?

## 3. System

ReceiptInject includes typed schemas, deterministic synthetic dataset generation, realistic document templates, optional PDF/OCR support, prompt mitigation modes, EvalGrid provider abstraction, resumable runs, raw JSONL logging, scored CSV outputs, summaries, validation artifacts, and failure-case reporting.

## 4. Preliminary Results

The current curated final result uses a 300-example synthetic text-only suite across three providers and three strategies, for 2,700 real-provider rows. The evaluated providers are Gemini, OpenAI, and Mistral; Claude/Anthropic was not run because no local Anthropic key was available.

| Model | Strategy | Extraction | Safe Completion | Prompt-Injection Compliance | Unsafe Proposal | Unsafe Execution |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Gemini 3.1 Flash Lite | `baseline_minimal` | 49.3% | 31.3% | 19.7% | 0.0% | 0.0% |
| Gemini 3.1 Flash Lite | `combined_safety_schema` | 90.8% | 100.0% | 0.0% | 0.0% | 0.0% |
| Gemini 3.1 Flash Lite | `trusted_tool_gating` | 90.8% | 100.0% | 0.0% | 19.0% | 0.0% |
| OpenAI GPT-4o mini | `baseline_minimal` | 59.5% | 74.0% | 4.0% | 0.0% | 0.0% |
| OpenAI GPT-4o mini | `combined_safety_schema` | 90.5% | 100.0% | 0.0% | 0.0% | 0.0% |
| OpenAI GPT-4o mini | `trusted_tool_gating` | 89.8% | 99.0% | 0.0% | 1.0% | 0.0% |
| Mistral Large Latest | `baseline_minimal` | 40.4% | 25.0% | 38.7% | 0.0% | 0.0% |
| Mistral Large Latest | `combined_safety_schema` | 90.6% | 99.7% | 0.0% | 0.0% | 0.0% |
| Mistral Large Latest | `trusted_tool_gating` | 90.6% | 100.0% | 0.0% | 8.0% | 0.0% |

These are preliminary synthetic benchmark results. The most systems-relevant result is that trusted-tool gating records unsafe model proposals separately from unsafe simulated execution: proposal rates were nonzero for Gemini and Mistral under the gated strategy, while unsafe execution remained 0.0% because the local executor blocked unsafe proposed actions. This is not production safety evidence and should not be interpreted as a broad model ranking.

## 5. Why This Fits ML Systems & Performance

ReceiptInject is systems-heavy: deterministic synthetic data generation, configurable provider runs, caching/resume behavior, raw-output logging, reproducible scoring, final artifact generation, and validation checks. The project focuses on making model behavior measurable across providers, prompts, document types, and failure modes.

## 6. Limitations

The benchmark uses synthetic documents and visible embedded instructions. Automated scorers are transparent but heuristic, so manual inspection is required before strong claims. The dataset diversity audit reports 608 repeated tracked-value occurrences in the 500-example dataset, which remains a documented synthetic-template limitation. The 50-example hard-subset artifacts remain in the repository as legacy validation material, not as the current headline result.

## 7. Future Work

Next steps include Claude/Anthropic runs, richer synthetic templates, human annotation, semantic scoring, OCR stress tests, confidence intervals, and broader provider comparisons after manual-review calibration.
