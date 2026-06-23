# ReceiptInject: Scalable Evaluation Infrastructure for Document-Understanding LLM Agents

## 1. Motivation

Document-understanding LLM agents increasingly process receipts, invoices, bank statements, policy memos, and scanned PDFs. These documents are not trusted instruction sources: a footer, internal note, OCR artifact, or policy appendix can contain text that looks like a command to the model. ReceiptInject studies this problem as evaluation infrastructure rather than as a one-off prompt-injection example.

## 2. Research Question

Can document-understanding LLM agents extract useful structured information from untrusted documents without following embedded instructions, leaking private fields, hallucinating facts, over-refusing benign tasks, or recommending unsafe external actions?

## 3. System

ReceiptInject is an end-to-end synthetic benchmark and experiment runner. It includes typed schemas, deterministic dataset generation, realistic document templates, PDF/PNG rendering, optional Mistral OCR, prompt mitigation modes, a multi-model client interface, resumable evaluation runs, raw JSONL logging, scored CSV outputs, aggregate summaries, figures, and failure-case reports.

The project is intentionally systems-heavy: the same pipeline supports mock validation, text-only real-model evaluation, OCR-derived evaluation, and final artifact generation for review.

## 4. Preliminary Results

Mock runs validate the pipeline but are not research evidence. The repository supports preliminary real Mistral text evaluation and a small OCR pilot when a local `.env` key is available. In the current local artifact snapshot, `results/final/final_results.csv` contains no real Mistral rows, so no empirical model-performance claim is made here. Final artifacts correctly state when real rows are absent.

## 5. Why This Fits ML Systems & Performance

ReceiptInject is a scalable evaluation infrastructure project. It combines deterministic synthetic data generation, a document rendering pipeline, OCR integration, multi-model abstraction, config-driven experiments, cost-controlled real-model runs, resumable execution, raw output logging, reproducible scoring, aggregate analysis, and failure-case export.

These are ML systems concerns: making model behavior measurable across providers, prompts, document formats, OCR modes, and failure taxonomies. The benchmark also exposes practical reliability questions such as schema validity, extraction utility, safety failures, OCR effects, provider variance, and run reproducibility.

## 6. Limitations

ReceiptInject uses synthetic documents and visible embedded instructions. It does not cover hidden text, steganography, all real OCR artifacts, production deployment conditions, or all domain-specific document formats. The current scorers are transparent but simple, so manual inspection is needed before drawing conclusions from any real-model run.

## 7. Future Work

Next steps include human annotation, richer OCR layouts, larger synthetic datasets, real-world-inspired but privacy-preserving templates, additional model providers, semantic scoring, latency/cost tracking, and controlled tool-using document-agent simulations.
