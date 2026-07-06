# ReceiptInject

ReceiptInject is scalable evaluation infrastructure for testing document-understanding LLM agents on untrusted synthetic inputs. It combines deterministic dataset generation, document templates, optional rendering/OCR, multi-provider evaluation through EvalGrid, raw-output logging, reproducible scoring, and failure-case analysis.

This is defensive AI safety / ML systems infrastructure. All benchmark documents are synthetic. The project does not prove production safety, solve prompt injection, or execute real-world actions.

## Current Resume-Facing Result

ReceiptInject now has a clean preliminary cross-provider result on `data/examples_300.jsonl`: 300 synthetic examples per provider/strategy, 3 providers, 3 strategies, and 2,700 total real-provider rows with 0 error rows.

The completed 2,700-row result covers `baseline_minimal`, `combined_safety_schema`, and `trusted_tool_gating`. Trusted-tool gating separates unsafe model proposals from unsafe execution by running model-proposed actions through a deterministic executor-side policy gate.

| Model | Mitigation | n | Extraction Accuracy | Safe Completion | Hallucination | Prompt-Injection Compliance |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Gemini 3.1 Flash Lite | `baseline_minimal` | 300 | 49.3% | 31.3% | 32.7% | 19.7% |
| Gemini 3.1 Flash Lite | `combined_safety_schema` | 300 | 90.8% | 100.0% | 0.0% | 0.0% |
| OpenAI GPT-4o mini | `baseline_minimal` | 300 | 59.5% | 74.0% | 8.7% | 4.0% |
| OpenAI GPT-4o mini | `combined_safety_schema` | 300 | 90.5% | 100.0% | 0.0% | 0.0% |
| OpenAI GPT-4o mini | `trusted_tool_gating` | 300 | 89.8% | 99.0% | 0.0% | 0.0% |
| Mistral Large Latest | `baseline_minimal` | 300 | 40.4% | 25.0% | 40.3% | 38.7% |
| Mistral Large Latest | `combined_safety_schema` | 300 | 90.6% | 99.7% | 0.3% | 0.0% |
| Mistral Large Latest | `trusted_tool_gating` | 300 | 90.6% | 100.0% | 0.0% | 0.0% |
| Gemini 3.1 Flash Lite | `trusted_tool_gating` | 300 | 90.8% | 100.0% | 0.0% | 0.0% |

Interpretation: on this synthetic 300-example suite, `combined_safety_schema` improved automated extraction and safety metrics for all three evaluated providers. This is preliminary benchmark evidence from automated scorers, not production reliability evidence or a broad model ranking.

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
- A real `trusted_tool_gating` strategy that asks for structured action proposals and runs them through a deterministic executor-side policy gate
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
- 300-example cross-provider combined CSV: `results/evalgrid_300_all_results.csv`
- 300-example cross-provider summary: `results/evalgrid_300_summary.md`
- 2,700-row cross-provider CSV: `results/evalgrid_2700_all_results.csv`
- 2,700-row cross-provider summary: `results/evalgrid_2700_summary.md`
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

## 300-Example Cross-Provider Runs

OpenAI, Mistral, and Gemini 300-example baseline/safety-schema runs have been completed locally and summarized in `results/evalgrid_300_summary.md`. Before running any new full 300-example condition, run a one-example smoke check and confirm the raw output shows the real provider/model rather than `mock`.

```bash
.venv/bin/python scripts/run_eval.py --config configs/evalgrid_mistral_300_baseline.yaml --limit 1 --fresh
.venv/bin/python scripts/run_eval.py --config configs/evalgrid_openai_300_baseline.yaml --limit 1 --fresh
```

Then run the full baseline conditions:

```bash
.venv/bin/python scripts/run_eval.py --config configs/evalgrid_mistral_300_baseline.yaml --fresh
.venv/bin/python scripts/run_eval.py --config configs/evalgrid_openai_300_baseline.yaml --fresh
```

Mistral is rate-limit sensitive; the 300-example Mistral configs use slower pacing than OpenAI. If Mistral returns many `429` rows, do not treat that run as a clean benchmark artifact. Rerun after quota recovery with the configured conservative sleep and `--fresh`, or write a clearly labeled retry artifact.

After baseline completes, run safety/schema:

```bash
.venv/bin/python scripts/run_eval.py --config configs/evalgrid_mistral_300_safety_schema.yaml --fresh
.venv/bin/python scripts/run_eval.py --config configs/evalgrid_openai_300_safety_schema.yaml --fresh
```

The configured outputs are `results/evalgrid_mistral_300_*` and `results/evalgrid_openai_300_*`. Stop and inspect the config if a run prints `results/results.csv` or `results/raw_outputs.jsonl`.

## Trusted-Tool Gating

`trusted_tool_gating` is implemented as a real third strategy, not a prompt-only label. The model returns normal extracted fields plus `proposed_actions`; the deterministic policy gate records `unsafe_model_proposal`, `unsafe_execution`, blocked action count, and allowed action count. The gate preserves unsafe model proposals as measurable warning signals while blocking unsafe execution.

Completed full 300-example commands:

```bash
.venv/bin/python scripts/run_eval.py --config configs/evalgrid_openai_300_trusted_gating.yaml --fresh
.venv/bin/python scripts/run_eval.py --config configs/evalgrid_mistral_300_trusted_gating.yaml --fresh
.venv/bin/python scripts/run_eval.py --config configs/evalgrid_gemini_300_trusted_gating.yaml --fresh
```

In the completed trusted-gating runs, unsafe model proposal rates were 1.0% for OpenAI, 8.0% for Mistral, and 19.0% for Gemini, while unsafe execution was 0.0% for all three providers. This supports a defense-in-depth evaluation claim, not a production safety guarantee.

Run a cheap Gemini smoke test after setting `GEMINI_API_KEY`:

```bash
python scripts/run_eval.py --config configs/gemini_smoke.yaml --fresh
```

The smoke test uses 1 example and writes to `results/gemini_smoke_*`. It does not update `results/final/` and should not be reported as benchmark evidence.

Current local note: a Gemini smoke attempt reached the Gemini API but returned quota/resource-exhausted errors, so no successful Gemini outputs are claimed or committed.

Generate the optional 300-example scaled suite:

```bash
python scripts/generate_300_suite.py --output data/examples_300.jsonl --seed 42
python scripts/validate_dataset.py --data data/examples_300.jsonl
```

## Gemini Free-Tier Run Plan

Gemini provider support is configured for `gemini-3.1-flash-lite`. The current free-tier quota table makes this the useful low-cost text model for this project, but the daily request cap matters: a 300-example suite across three strategies would require roughly 900 requests, which exceeds a 500-request daily quota. Do not run all strategies in one day on the free tier.

Run one strategy per day, with the smoke test first:

```bash
python scripts/evalgrid_run.py --config configs/evalgrid_receiptinject_gemini.yaml --fresh --clear-cache
python scripts/evalgrid_run.py --config configs/evalgrid_gemini_300_baseline.yaml
python scripts/evalgrid_run.py --config configs/evalgrid_gemini_300_safety_schema.yaml
```

These configs use `max_concurrency: 1`, `sleep_between_requests: 8.0`, `resume: true`, and separate output paths. If Gemini returns `429` quota/resource-exhausted errors, wait for quota reset and rerun the same config with resume enabled.

Gemini trusted-gating has been run for 300 examples. Future Gemini runs should still be split by strategy because of free-tier daily request limits.

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
GEMINI_MODEL=gemini-3.1-flash-lite
```

Mock mode runs without API keys and is for pipeline validation only.

## Dataset Diversity Caveat

`results/dataset_diversity_audit.md` reports 0 duplicate `document_text` rows but 608 repeated tracked-value occurrences across the 500-example dataset. This is a synthetic-template limitation and remains explicitly documented. The dataset was not regenerated in the latest Mistral scale-up pass.

## Limitations

- Synthetic data only
- Preliminary synthetic real-provider comparison with automated scorers
- Automated scorers are transparent but heuristic
- Manual review is still needed before strong claims
- No Claude/Anthropic rows are present
- Trusted-gating uses a deterministic simulated policy gate; it does not prove real production executor safety
- OCR is implemented but excluded from the headline final comparison
- Trusted-tool gating is a defense-in-depth primitive for simulated tools, not a guarantee of safe production tool use
- Results may vary by provider, model version, prompt formatting, and structured-output behavior
- No claim of production safety, solved prompt injection, or benchmark completeness

## Responsible Use

ReceiptInject is defensive evaluation infrastructure using synthetic data only. Do not insert real private documents. Do not use it to attack real systems. Do not use outputs for legal, financial, medical, compliance, eligibility, lending, employment, insurance, or benefits decisions.

See `responsible_use.md`.
