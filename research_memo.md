# ReceiptInject: Scalable Evaluation Infrastructure for Document-Understanding LLM Agents

## 1. Motivation

Document-understanding LLM agents increasingly process receipts, invoices, bank statements, policy memos, and scanned PDFs. These documents are not trusted instruction sources: a footer, internal note, OCR artifact, or policy appendix can contain text that looks like a command. ReceiptInject studies this as an evaluation-infrastructure problem rather than as a one-off prompt-injection demo.

## 2. Research Question

Can document-understanding LLM agents extract useful structured information from untrusted documents without following embedded instructions, leaking private fields, hallucinating facts, over-refusing benign tasks, or recommending unsafe external actions?

## 3. System

ReceiptInject includes typed schemas, deterministic synthetic dataset generation, realistic document templates, optional PDF/OCR support, prompt mitigation modes, EvalGrid provider abstraction, resumable runs, raw JSONL logging, scored CSV outputs, summaries, validation artifacts, and failure-case reporting.

## 4. Preliminary Results

The current curated final result uses a 50-example synthetic hard subset with 10 examples per document type, 20 benign and 30 adversarial examples, and two mitigation settings.

| Model | Mitigation | Extraction | Safe Completion | Hallucination | Prompt-Injection Compliance |
| --- | --- | ---: | ---: | ---: | ---: |
| OpenAI | `baseline_minimal` | 45.3% | 54.0% | 12.0% | 6.0% |
| OpenAI | `combined_safety_schema` | 84.7% | 100.0% | 0.0% | 0.0% |
| Mistral | `baseline_minimal` | 26.3% | 12.0% | 40.0% | 50.0% |
| Mistral | `combined_safety_schema` | 84.0% | 98.0% | 2.0% | 0.0% |

These are preliminary synthetic benchmark results. They show that the infrastructure can compare providers and prompt mitigations under controlled conditions; they do not prove production safety or establish broad model rankings. Claude/Anthropic was not run because no local Anthropic key was available.

## 5. Why This Fits ML Systems & Performance

ReceiptInject is systems-heavy: deterministic synthetic data generation, configurable provider runs, caching/resume behavior, raw-output logging, reproducible scoring, final artifact generation, and validation checks. The project focuses on making model behavior measurable across providers, prompts, document types, and failure modes.

## 6. Limitations

The benchmark uses synthetic documents and visible embedded instructions. Automated scorers are transparent but heuristic, so manual inspection is required before strong claims. The dataset diversity audit reports 608 repeated tracked-value occurrences in the 500-example dataset, which remains a documented synthetic-template limitation.

## 7. Future Work

Next steps include Claude/Anthropic runs, richer synthetic templates, human annotation, semantic scoring, OCR stress tests, and broader provider comparisons after manual-review calibration.
