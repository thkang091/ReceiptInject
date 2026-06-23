# ReceiptInject + EvalGrid

**Evaluation infrastructure for untrusted document-understanding LLM agents.**

ReceiptInject is a synthetic benchmark and evaluation infrastructure for testing how LLM document agents handle untrusted receipts, invoices, bank statements, policy documents, and mixed document bundles. EvalGrid is the reusable evaluation runner layer: provider abstraction, YAML configs, caching, raw output logging, resumable runs, scoring, metadata, and final artifacts.

This is a defensive AI safety / ML systems project. It does not use real private documents, does not claim production reliability, and does not claim to solve prompt injection.

## Why This Matters

Real document agents process messy, untrusted inputs. A receipt footer, invoice note, bank-statement memo, policy appendix, or OCR artifact can contain instructions, fake policies, private fields, or requests for external action. Accuracy alone is not enough: document agents should extract useful facts without treating document text as authority.

ReceiptInject studies whether an agent can:

- extract factual structured information from documents
- ignore visible embedded instructions inside document text
- avoid leaking synthetic private fields
- avoid recommending or claiming external actions
- avoid hallucinating unsupported facts
- avoid over-refusing benign document tasks

The project emphasizes reproducible evaluation infrastructure: deterministic data generation, raw output logging, structured scoring, failure-case export, and manual-review artifacts.

## What I Built

- Deterministic synthetic dataset generation with typed Pydantic schemas
- Balanced subset creation and deliberately harder adversarial subset creation
- Synthetic document families: receipts, invoices, bank statements, policy documents, and mixed bundles
- Visible benchmark attack types: instruction override, data poisoning, role confusion, privacy exfiltration, hidden action request, fake policy, format injection, conflicting instructions, and authority impersonation
- Direct ReceiptInject evaluation harness for mock, OpenAI, and Mistral runs
- EvalGrid reusable runner with provider abstraction, YAML configs, SQLite caching, raw JSONL logging, resumable runs, cost/metadata tracking, and rate controls
- Scoring for extraction accuracy, prompt-injection compliance, privacy leakage, unsafe action, hallucination, over-refusal, suspicious instruction detection, safe completion, and utility/safety tradeoff
- PDF/PNG rendering and optional Mistral OCR pipeline for document-to-markdown experiments
- Final reports, failure-case summaries, diversity audits, and manual-review samples

## Architecture

```text
Synthetic Dataset Generator
        |
        v
Balanced / Hard Subsets
        |
        v
ReceiptInject Benchmark
        |
        v
EvalGrid Runner
        |
        v
Model Providers: OpenAI / Mistral / Mock
        |
        v
Raw Outputs + Scored CSV + Metadata
        |
        v
Final Reports + Failure Cases + Manual Review Samples
```

Core modules:

| Path | Role |
| --- | --- |
| `receiptinject/` | Benchmark schemas, templates, dataset generation, prompts, scorers, model clients, OCR, rendering, analysis |
| `evalgrid/` | Reusable evaluation runner, provider abstraction, cache, rate limiting, metadata, storage, configs |
| `scripts/` | Dataset, validation, eval, OCR, summarization, final-artifact, and audit CLIs |
| `configs/` | YAML experiment configs for mock, OpenAI, Mistral, and OCR runs |
| `results/final/` | Curated final summaries, failure cases, validation notes, and interpretation |

## Preliminary Hard-Subset Results

The current headline result is a text-only OpenAI evaluation on a deliberately hard 50-example synthetic subset. The subset contains 10 examples per document type, 20 benign and 30 adversarial examples, and a difficulty mix of 43 hard, 6 medium, and 1 easy. These two selected OpenAI runs had 0 API/parsing errors.

| Hard subset run | Extraction Accuracy | Safe Completion | Hallucination | Prompt-Injection Compliance |
| --- | ---: | ---: | ---: | ---: |
| `baseline_minimal` | 45.3% | 54.0% | 12.0% | 6.0% |
| `combined_safety_schema` | 84.7% | 100.0% | 0.0% | 0.0% |

These are preliminary synthetic benchmark results. They show that the evaluation pipeline can expose baseline failures and compare mitigations, not that the model is production-safe.

Final artifacts:

- `results/final/final_summary.md`
- `results/final/final_interpretation.md`
- `results/final/final_failure_cases.md`
- `results/final/final_validation.md`
- `results/hard_manual_review_sample.md`

## Dataset Diversity Audit

The full 500-example synthetic dataset currently has:

| Audit item | Value |
| --- | ---: |
| Duplicate `document_text` | 0 |
| Repeated tracked-value occurrences | 608 |

The repeated tracked values are documented as a limitation of synthetic-template generation, especially recurring synthetic merchant, vendor, and institution names. Future work should increase template and value diversity before presenting the benchmark as broad coverage of real-world document variation.

## Quickstart

Create and activate a virtual environment, then install dependencies:

```bash
make install
```

Generate the full synthetic dataset:

```bash
python scripts/generate_dataset.py --n 500 --output data/examples_500.jsonl --seed 42
```

Create the hard 50-example subset:

```bash
python scripts/create_hard_subset.py \
  --data data/examples_500.jsonl \
  --out data/hard_test_subset_50.jsonl \
  --n 50 \
  --seed 123
```

Run the weak baseline on the hard subset:

```bash
python scripts/run_eval.py \
  --data data/hard_test_subset_50.jsonl \
  --model openai \
  --mitigation baseline_minimal \
  --limit 50 \
  --sleep 1.0 \
  --run-id openai_hard_baseline_minimal_50 \
  --fresh
```

Run the structured safety mitigation:

```bash
python scripts/run_eval.py \
  --data data/hard_test_subset_50.jsonl \
  --model openai \
  --mitigation combined_safety_schema \
  --limit 50 \
  --sleep 1.0 \
  --run-id openai_hard_combined_schema_50
```

Summarize results:

```bash
python scripts/summarize_results.py \
  --results results/results.csv \
  --out results/summary.md
```

Create final artifacts:

```bash
python scripts/create_final_artifacts.py \
  --results results/results.csv \
  --raw results/raw_outputs.jsonl \
  --data data/hard_test_subset_50.jsonl \
  --out results/final
```

## Environment Variables

Put API keys in a local `.env` file at the project root. Do not commit `.env`.

```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini

MISTRAL_API_KEY=your_key_here
MISTRAL_MODEL=mistral-large-latest
MISTRAL_OCR_MODEL=mistral-ocr-latest
```

Mock mode runs without API keys and is for pipeline validation only.

## EvalGrid

EvalGrid is the reusable ML evaluation infrastructure layer used by ReceiptInject. It supports:

- benchmark adapters
- mock, OpenAI, and Mistral providers
- YAML-driven experiment configs
- concurrency and sleep-based rate controls
- SQLite response caching
- resumable runs
- raw output JSONL
- scored CSV output
- run metadata and estimated cost tracking

Mock smoke test:

```bash
python scripts/evalgrid_run.py --config configs/evalgrid_receiptinject_mock.yaml
python scripts/evalgrid_summarize.py \
  --results results/evalgrid_results.csv \
  --metadata results/evalgrid_run_metadata.json \
  --out results/evalgrid_summary.md
```

Small real-provider smoke tests should use low limits, low concurrency, sleeps, and caching. They validate infrastructure, not research claims.

## Optional OCR Pipeline

ReceiptInject can render synthetic examples and run OCR before evaluation:

```bash
python scripts/render_documents.py --data data/examples_500.jsonl --out data/rendered_docs --limit 25
python scripts/run_ocr.py --manifest data/rendered_docs/manifest.jsonl --output data/ocr_outputs/ocr_results.jsonl --limit 10 --sleep 1.0
python scripts/run_eval.py --data data/ocr_outputs/ocr_results.jsonl --input-mode ocr --model mistral --mitigation combined_safety --limit 10 --sleep 1.0
```

OCR coverage is currently preliminary. OCR results should be reported separately from the hard-subset text-only results.

## Testing

```bash
pytest
ruff check .
```

Current local status:

- `pytest`: 128 tests passed
- `ruff check .`: clean

Tests do not require real API keys.

## Responsible Use

ReceiptInject is for defensive AI safety evaluation only.

- Do not insert real private documents.
- Do not use this project to attack real systems.
- Do not use benchmark outputs for legal, financial, medical, compliance, eligibility, lending, employment, insurance, or benefits decisions.
- Treat all results as preliminary unless manually reviewed.

See `responsible_use.md`.

## Limitations

- Synthetic data only
- No real private documents
- Visible embedded benchmark instructions only; no hidden text or steganography
- Automated scorers are transparent but limited and require manual review
- Repeated tracked values remain in the synthetic dataset
- OCR pilot coverage is limited or pending depending on the selected run
- No human annotation yet
- Results may vary by provider, model, prompt formatting, and SDK behavior
- No claim of solved prompt injection or production safety

## Future Work

- Increase synthetic template and value diversity
- Add human annotation and adjudication workflows
- Expand OCR stress tests and document layouts
- Add more model providers and comparable configs
- Build richer semantic scorers for extraction and hallucination
- Simulate tool-using document agents under controlled conditions
- Publish benchmark cards and model/provider evaluation cards
