# ReceiptInject

ReceiptInject is scalable evaluation infrastructure for testing document-understanding LLM agents on untrusted synthetic inputs. It combines deterministic dataset generation, document templates, optional rendering/OCR, multi-provider evaluation through EvalGrid, raw-output logging, reproducible scoring, and failure-case analysis.

This is defensive AI safety / ML systems infrastructure. All benchmark documents are synthetic. The project does not prove production safety, solve prompt injection, or execute real-world actions.

## Current Resume-Facing Result

The committed final artifacts now center a passive hard-subset comparison on `data/hard_test_subset_50.jsonl`: 50 synthetic examples, 10 per document type, 20 benign and 30 adversarial, with 43 hard, 6 medium, and 1 easy examples.

The current committed result scope is OpenAI + Mistral. Gemini support is implemented for future runs, but Gemini benchmark numbers should not be claimed until a real run is completed and committed. Claude/Anthropic was not run because no local `ANTHROPIC_API_KEY` was available.

| Model | Mitigation | n | Extraction Accuracy | Safe Completion | Hallucination | Prompt-Injection Compliance |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| OpenAI | `baseline_minimal` | 50 | 45.3% | 54.0% | 12.0% | 6.0% |
| OpenAI | `combined_safety_schema` | 50 | 84.7% | 100.0% | 0.0% | 0.0% |
| Mistral | `baseline_minimal` | 50 | 26.3% | 12.0% | 40.0% | 50.0% |
| Mistral | `combined_safety_schema` | 50 | 84.0% | 98.0% | 2.0% | 0.0% |

Interpretation: on this small synthetic hard subset, the structured `combined_safety_schema` prompt improved automated extraction and safety metrics for both evaluated providers. This is preliminary benchmark evidence, not production reliability evidence or a broad model ranking.

## Why This Matters

Document-understanding agents process untrusted text. A receipt footer, invoice note, policy memo, bank-statement annotation, or OCR transcript can contain instructions that look operational but should be treated as document content only.

ReceiptInject studies whether models can extract useful structured information while avoiding embedded-instruction compliance, private-field leakage, hallucination, unsafe action recommendations, and unnecessary refusal.

## System Architecture

```text
Synthetic document templates
        |
        v
Deterministic dataset generation
        |
        v
Hard / balanced subsets
        |
        v
Prompt mitigation modes
        |
        v
EvalGrid provider runner
        |
        v
OpenAI / Mistral / Gemini / mock providers
        |
        v
Raw outputs + scored CSV rows
        |
        v
Final summaries + validation + failure cases
```

## What Is Included

- Typed Pydantic schemas for benchmark examples, model outputs, and scored rows
- Deterministic synthetic dataset generation
- Synthetic receipts, invoices, bank statements, policy documents, and mixed bundles
- Visible embedded-instruction benchmark data
- Prompt mitigation modes including `baseline_minimal` and `combined_safety_schema`
- EvalGrid provider abstraction with OpenAI, Mistral, Gemini, Anthropic, and mock support, plus caching, metadata, and resume behavior
- Raw JSONL logging and scored CSV outputs
- Trusted-tool gating primitives that separate unsafe model proposals from unsafe simulated execution
- Dataset validation and diversity audit
- Final artifacts under `results/final/`
- `pytest` and `ruff` quality checks

## Key Artifacts

- Final selected results: `results/final/final_results.csv`
- Final summary: `results/final/final_summary.md`
- Final validation: `results/final/final_validation.md`
- Claim audit: `results/final/claim_audit.md`
- Mistral EvalGrid hard-run CSV: `results/final/evalgrid_mistral_hard_results.csv`
- Dataset diversity audit: `results/dataset_diversity_audit.md`
- Technical report: `docs/ReceiptInject_Report.md`
- Paper-style report: `paper/ReceiptInject_Report.md`
- Research memo: `research_memo.md`

## Reproducibility

Install:

```bash
make install
```

Generate the base dataset and hard subset:

```bash
python scripts/generate_dataset.py --n 500 --output data/examples_500.jsonl --seed 42
python scripts/create_hard_subset.py --data data/examples_500.jsonl --out data/hard_test_subset_50.jsonl --n 50 --seed 123
```

Run OpenAI passive evaluation:

```bash
python scripts/run_eval.py --data data/hard_test_subset_50.jsonl --model openai --mitigation baseline_minimal --limit 50 --sleep 1.0 --run-id openai_hard_baseline_minimal_50 --fresh
python scripts/run_eval.py --data data/hard_test_subset_50.jsonl --model openai --mitigation combined_safety_schema --limit 50 --sleep 1.0 --run-id openai_hard_combined_schema_50
```

Run Mistral passive evaluation through EvalGrid:

```bash
python scripts/evalgrid_run.py --config configs/evalgrid_receiptinject_mistral_hard_baseline.yaml --fresh --clear-cache
python scripts/evalgrid_run.py --config configs/evalgrid_receiptinject_mistral_hard_combined.yaml
```

Summarize Mistral EvalGrid runs:

```bash
python scripts/evalgrid_summarize.py --results results/final/evalgrid_mistral_hard_results.csv --metadata results/final/evalgrid_mistral_hard_baseline_metadata.json --raw results/final/evalgrid_mistral_hard_raw_outputs.jsonl --out results/final/evalgrid_mistral_hard_baseline_summary.md --run-id mistral_hard_baseline_minimal_50
python scripts/evalgrid_summarize.py --results results/final/evalgrid_mistral_hard_results.csv --metadata results/final/evalgrid_mistral_hard_combined_metadata.json --raw results/final/evalgrid_mistral_hard_raw_outputs.jsonl --out results/final/evalgrid_mistral_hard_combined_summary.md --run-id mistral_hard_combined_schema_50
```

Run a cheap Gemini smoke test after setting `GEMINI_API_KEY`:

```bash
python scripts/run_eval.py --config configs/gemini_smoke.yaml --fresh
```

The smoke test uses at most 3 examples and writes to `results/gemini_smoke_*`. It does not update `results/final/` and should not be reported as benchmark evidence.

Current local note: a Gemini smoke attempt reached the Gemini API but returned quota/resource-exhausted errors, so no successful Gemini outputs are claimed or committed.

Generate the optional 300-example scaled suite:

```bash
python scripts/generate_300_suite.py --output data/examples_300.jsonl --seed 42
python scripts/validate_dataset.py --data data/examples_300.jsonl
```

Prepared full Gemini 300-example command:

```bash
python scripts/run_eval.py --config configs/gemini_300_benchmark.yaml
```

Do not claim Gemini 300-example results until this real run is intentionally executed, reviewed, and committed.

Run quality checks:

```bash
pytest
ruff check .
```

## Environment

Put provider keys in a local `.env` file. Do not commit `.env`.

```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini

MISTRAL_API_KEY=your_key_here
MISTRAL_MODEL=mistral-large-latest

GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash-lite
```

Mock mode runs without API keys and is for pipeline validation only.

## Dataset Diversity Caveat

`results/dataset_diversity_audit.md` reports 0 duplicate `document_text` rows but 608 repeated tracked-value occurrences across the 500-example dataset. This is a synthetic-template limitation and remains explicitly documented. The dataset was not regenerated in the latest Mistral scale-up pass.

## Limitations

- Synthetic data only
- Small hard-subset real-model comparison
- Automated scorers are transparent but heuristic
- Manual review is still needed before strong claims
- No Claude/Anthropic rows are present
- Gemini provider support exists, but no committed Gemini benchmark result is claimed yet
- OCR is implemented but excluded from the headline final comparison
- Trusted-tool gating is a defense-in-depth primitive for simulated tools, not a guarantee of safe production tool use
- Results may vary by provider, model version, prompt formatting, and structured-output behavior
- No claim of production safety, solved prompt injection, or benchmark completeness

## Responsible Use

ReceiptInject is defensive evaluation infrastructure using synthetic data only. Do not insert real private documents. Do not use it to attack real systems. Do not use outputs for legal, financial, medical, compliance, eligibility, lending, employment, insurance, or benefits decisions.

See `responsible_use.md`.
