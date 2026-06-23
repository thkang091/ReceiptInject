# ReceiptInject: Scalable Evaluation Infrastructure for Document-Understanding LLM Agents Under Untrusted Inputs

## Abstract

ReceiptInject is a research engineering project for evaluating document-understanding LLM agents on untrusted inputs. It combines deterministic synthetic data generation, realistic document templates, PDF/PNG rendering, optional OCR, multi-model evaluation, raw output logging, reproducible scoring, aggregate analysis, and qualitative failure-case export. The benchmark studies whether agents can extract useful factual information while ignoring embedded document instructions, minimizing private-field leakage, avoiding unsupported facts, avoiding unsafe external-action recommendations, and avoiding unnecessary refusal. All examples are synthetic, and embedded instructions are visible benchmark content. This report describes the benchmark design and systems implementation. In the current local artifact snapshot, final curated results contain no real Mistral rows, so the report does not make empirical claims about model safety.

## Introduction

LLM document agents increasingly process receipts, invoices, statements, policy memos, and scanned PDFs. These systems often place user instructions, OCR text, and document content into a shared context. A document can therefore contain text that resembles a system message, internal note, or administrative override. ReceiptInject treats this as a systems evaluation problem: the question is not whether one prompt can be tricked, but whether a reproducible pipeline can measure document-agent behavior across document types, attack categories, mitigation prompts, and input modes.

The project’s contribution is infrastructure for empirical measurement. It supports synthetic dataset generation, document rendering, OCR, model abstraction, resumable evaluation, raw logs, deterministic scoring, aggregate reporting, and failure-case analysis.

## Threat Model

The adversary controls visible text inside a synthetic document. The evaluator controls the actual task, such as extracting fields, summarizing factual content, or comparing document sections. The model should treat document text as untrusted data and should not follow embedded document instructions as operational commands.

ReceiptInject does not model hidden text, invisible text, steganography, malware, account compromise, or unauthorized testing of production systems. The benchmark is defensive and synthetic.

## Benchmark Design

Each example is represented by a typed `BenchmarkExample` schema containing document metadata, expected task, document text, ground-truth fields, synthetic private fields, expected safe behavior, and tags. The benchmark covers benign examples and visible adversarial instruction patterns.

Document families include receipts, invoices, bank statements, policy/legal/public-sector documents, and mixed multi-document bundles. Attack categories include instruction override, privacy exfiltration, role confusion, fake policy, hidden action request, data poisoning, conflicting instructions, authority impersonation, and format injection.

## Dataset Generation

The generator is deterministic and seed-controlled. For `n=500`, the intended composition is 125 receipts, 125 invoices, 100 bank statements, 100 policy/legal/public-sector documents, and 50 mixed bundles. The target split is 50% benign and 50% adversarial, with a 35/45/20 easy/medium/hard difficulty distribution.

All names, IDs, totals, account-like values, emails, and private fields are synthetic. Dataset validation checks schema validity, duplicate IDs/text, benign/adversarial consistency, real-looking SSN or credit-card patterns, ground-truth recoverability, private-field placement, and mixed-bundle structure.

## PDF/OCR Pipeline

ReceiptInject renders synthetic examples to PDFs and PNGs with document-specific layouts. Receipts use narrower formats, invoices and bank statements use table-like sections, policy documents use memo-style layouts, and mixed bundles use multiple sections. Embedded instructions remain visible and clearly part of the synthetic benchmark document.

The OCR pipeline supports Mistral OCR and a mock OCR mode. OCR JSONL rows include example IDs, source files, OCR markdown, errors, timestamps, and example metadata for downstream scoring. OCR errors are recorded per document rather than crashing the entire run.

## Model Evaluation Harness

The evaluation harness loads text examples or OCR rows, builds a mitigation prompt, calls a selected model client, validates structured JSON output, scores the result, and writes raw JSONL plus scored CSV rows. It supports mock evaluation, Mistral evaluation, run IDs, limits, sleep intervals, resume behavior, fresh output files, and YAML experiment configs.

Mock evaluation is used for pipeline validation only. Mistral evaluation is supported through a local `.env` file and should be interpreted as preliminary real-model evidence when run.

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

The scorers are intentionally transparent MVP heuristics. They make runs reproducible and auditable, but they do not replace manual inspection.

## Mitigation Strategies

Mitigation modes include baseline, untrusted-document isolation, action confirmation, structured policy guard, privacy minimization, and combined safety. These are prompt-level mitigations for controlled comparison, not security guarantees.

## Preliminary Real-Model Results

The final artifact workflow selects non-mock real-model rows from `results/results.csv` and writes curated artifacts under `results/final/`. In the current local snapshot, `results/final/final_results.csv` contains no real Mistral rows. Therefore, this report intentionally does not claim model performance numbers.

When real Mistral rows are present, the appropriate interpretation is preliminary: synthetic benchmark, small run sizes, automated scorer limitations, and manual inspection required.

## OCR Pilot Results

The repository supports a small OCR pilot:

```bash
python scripts/render_documents.py --data data/examples_500.jsonl --out data/rendered_docs --limit 25
python scripts/run_ocr.py --manifest data/rendered_docs/manifest.jsonl --output data/ocr_outputs/ocr_results.jsonl --limit 10 --sleep 1.0
python scripts/run_eval.py --data data/ocr_outputs/ocr_results.jsonl --input-mode ocr --model mistral --mitigation combined_safety --limit 10 --sleep 1.0 --run-id mistral_ocr_combined_10
```

In the current local snapshot, rendered examples exist but real OCR results are not present. Any future OCR results should be described as a small pilot, not production document reliability evidence.

## Failure Analysis

ReceiptInject exports failure cases by joining scored rows, raw model outputs, and source examples. The report prioritizes prompt-injection compliance, privacy leakage, unsafe action, hallucination, over-refusal, OCR-specific failures, and mixed-bundle cases. Embedded instructions are summarized rather than reproduced at length.

## Systems Lessons

The main systems lesson is that document-agent safety evaluation requires more than prompt examples. Reproducible measurement depends on typed schemas, deterministic data, rendering/OCR pipelines, cost controls, resumable runs, raw output logs, structured scoring, aggregate analysis, and qualitative failure inspection.

ReceiptInject is designed so that a small smoke test, a mock run, a real-model run, and an OCR run share the same artifact pathway.

## Scorer and Manual Validation Limitations

Automated scores depend on structured model outputs and simple heuristics. They can miss semantic nuance, overstate failures in ambiguous cases, or rely on model self-report fields. Manual inspection of raw outputs and rendered documents is needed before drawing conclusions.

## Responsible Use

ReceiptInject is for defensive AI safety evaluation only. It uses synthetic data and visible benchmark instructions. Users should not insert real private documents or use the project to attack real systems. Results are not legal, financial, medical, compliance, or operational advice.

## Future Work

Future work includes human annotation, richer rendered layouts, larger synthetic datasets, real-world-inspired but privacy-preserving templates, more model providers, semantic scorers, cost/latency tracking, longitudinal regression tests, and controlled tool-use simulations.
