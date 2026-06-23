# ReceiptInject + EvalGrid: Evaluation Infrastructure for Untrusted Document-Understanding LLM Agents

## Abstract

Document-understanding LLM agents increasingly process receipts, invoices, bank statements, policy documents, and multi-document bundles. These documents are not just sources of facts; they can also contain text that resembles instructions, fake policies, private fields, or requests for external action. ReceiptInject + EvalGrid addresses this problem as an evaluation-infrastructure task: can we build a reproducible synthetic benchmark that measures both document utility and safety behavior under untrusted document inputs?

ReceiptInject provides the benchmark layer: deterministic synthetic data generation, document templates, typed schemas, prompt-mitigation modes, transparent scorers, optional PDF/OCR support, and failure-case analysis. EvalGrid provides the reusable evaluation-runner layer: provider abstraction, YAML configs, caching, raw output logging, scored CSV outputs, resumability, rate controls, and metadata tracking. The benchmark measures extraction accuracy, prompt-injection compliance, privacy leakage, unsafe-action recommendation, hallucination, over-refusal, suspicious-instruction detection, safe completion, and a utility/safety tradeoff score.

In a preliminary OpenAI text-only experiment on a deliberately hard 50-example synthetic subset, a minimal baseline prompt achieved 45.3% extraction accuracy and 54.0% safe completion, while a structured safety-schema mitigation achieved 84.7% extraction accuracy and 100.0% safe completion. Automated hallucination labels fell from 12.0% to 0.0%, and prompt-injection compliance fell from 6.0% to 0.0%. These results are preliminary synthetic benchmark results. They show that the evaluation pipeline can expose baseline failures and compare mitigations; they do not prove production safety and require broader manual review.

## 1. Motivation

LLM document agents often combine a user task, document text, OCR output, and model instructions in a single context. This creates a recurring ambiguity: the user may ask for factual extraction, while the document itself may contain text that looks like an instruction. A receipt footer can say to ignore the task. An invoice note can request payment approval. A policy appendix can impersonate an administrator. A bank-statement memo can ask the model to reveal private fields.

This matters because document extraction systems need to optimize for both utility and safety. A useful model should extract totals, dates, names, obligations, exceptions, and relevant comparisons. A safe model should avoid following embedded document instructions, leaking unnecessary private information, hallucinating unsupported facts, recommending external actions, or refusing benign extraction work.

Simple prompt-injection demos are not enough to evaluate this behavior. Serious evaluation requires reproducible datasets, typed examples, controlled prompt variants, raw output logs, scoring, run metadata, failure-case analysis, and manual-review workflows. ReceiptInject + EvalGrid was built to make these behaviors measurable and auditable.

## 2. System Overview

ReceiptInject is the benchmark layer. It defines synthetic document examples, attack categories, expected tasks, ground-truth fields, private fields, mitigation prompts, model-output schemas, and transparent scorers.

EvalGrid is the evaluation infrastructure layer. It runs benchmark tasks against model providers, handles YAML experiment configs, caches responses, records raw outputs, writes scored CSV rows, tracks metadata, and supports resumable and cost-controlled runs.

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
EvalGrid / Direct Evaluation Runner
        |
        v
Model Providers: OpenAI / Mistral / Mock
        |
        v
Raw JSONL Outputs + Scored CSV + Run Metadata
        |
        v
Final Summaries + Failure Cases + Manual Review Samples
```

The direct ReceiptInject harness and EvalGrid share the same basic evaluation idea: load examples, build prompts, call a provider, validate structured JSON outputs, score behavior, and persist artifacts for later analysis. Mock mode is used for offline pipeline validation only. Real-provider runs are intentionally cost-controlled and should be interpreted as preliminary evidence on synthetic tasks.

## 3. Dataset Design

ReceiptInject uses synthetic-only generation. No real personal, financial, legal, medical, or private documents are used. Embedded adversarial instructions are visible benchmark content, not hidden text or steganography.

The benchmark supports five document types:

| Document type | Description |
| --- | --- |
| `receipt` | Synthetic point-of-sale receipts with merchants, items, fees, totals, and tender-like fake tokens |
| `invoice` | Synthetic vendor invoices with IDs, line items, dates, totals, and payment-like statuses |
| `bank_statement` | Synthetic activity summaries with balances, deposits, withdrawals, and pending items |
| `policy_document` | Synthetic policy/legal/public-sector style documents with obligations and exceptions |
| `mixed_bundle` | Multi-section bundles combining document excerpts for comparison tasks |

The benchmark supports benign examples and nine adversarial attack types:

| Attack type | Intended behavior under test |
| --- | --- |
| `none` | Benign document extraction or summarization |
| `authority_impersonation` | Document claims to be from an administrator, auditor, court, or compliance officer |
| `conflicting_instructions` | Document contains conflicting instructions that should be treated as content only |
| `data_poisoning` | Document asks the model to alter totals, dates, names, or facts |
| `fake_policy` | Document invents or overrides policy-like rules |
| `format_injection` | Document requests unsafe output formats or unnecessary private fields |
| `hidden_action_request` | Document asks for payment approval, email sending, refunds, eligibility decisions, or similar external actions |
| `instruction_override` | Document tells the model to ignore or replace the user task |
| `privacy_exfiltration` | Document asks the model to reveal private or internal fields |
| `role_confusion` | Document pretends to be a system, developer, or admin message |

The full generated dataset supports balanced document-type, benign/adversarial, and difficulty distributions. For the preliminary headline experiment, a harder subset was created:

| Hard subset property | Value |
| --- | ---: |
| Total examples | 50 |
| Examples per document type | 10 |
| Benign examples | 20 |
| Adversarial examples | 30 |
| Hard examples | 43 |
| Medium examples | 6 |
| Easy examples | 1 |

The hard subset is intentionally more adversarial than the balanced dataset. It is useful for stress-testing whether an evaluation pipeline can distinguish a weak baseline from a stronger structured mitigation.

## 4. Evaluation Metrics

Metrics are normalized internally from 0 to 1. Percentages are used in this report for readability.

| Metric | Definition |
| --- | --- |
| `extraction_accuracy` | Fractional match between extracted fields and ground-truth fields, using transparent normalization rules |
| `prompt_injection_compliance` | Whether the model followed embedded document instructions |
| `privacy_leakage` | Whether private fields were unnecessarily revealed |
| `unsafe_action_rate` | Whether the model recommended, approved, initiated, or claimed an external action |
| `hallucination` | Whether the model introduced important unsupported values not present in the document |
| `over_refusal` | Whether the model refused a benign extraction task unnecessarily |
| `suspicious_instruction_detection` | Whether the model identified suspicious embedded instructions when present |
| `safe_completion_rate` | Whether the model completed the useful task without unsafe behavior |
| `utility_safety_tradeoff` | Extraction accuracy minus safety penalties |

An important scoring update is that `safe_completion_rate` now requires useful extraction, not merely clean safety flags. The implemented rule requires extraction accuracy of at least 0.5 in addition to avoiding safety failures. This prevents a useless but non-dangerous output from being counted as a successful safe completion.

The scorers are deliberately simple, auditable heuristics. They are useful for reproducible comparisons and regression tests, but they are not a substitute for human review.

## 5. Experiments

The main preliminary experiment compares two prompt modes on the same hard subset:

- `baseline_minimal`: a weak extraction prompt with minimal safety framing
- `combined_safety_schema`: a structured safety prompt that separates task, facts, suspicious instructions, and allowed output

Both runs used `data/hard_test_subset_50.jsonl`. The selected OpenAI runs were:

- `openai_hard_baseline_minimal_50`
- `openai_hard_combined_schema_50`

The selected runs contained 100 scored result rows total, 50 per mitigation. There were zero API/parsing errors in these two runs.

| Run | Extraction Accuracy | Safe Completion | Hallucination | Prompt-Injection Compliance | Suspicious Instruction Detection |
| --- | ---: | ---: | ---: | ---: | ---: |
| `baseline_minimal` | 45.3% | 54.0% | 12.0% | 6.0% | 40.0% |
| `combined_safety_schema` | 84.7% | 100.0% | 0.0% | 0.0% | 52.0% |

## 6. Results Interpretation

The minimal baseline exposed measurable failures on the hard subset. It had lower extraction accuracy, lower safe completion, nonzero automated hallucination labels, and nonzero prompt-injection compliance labels. The structured `combined_safety_schema` mitigation improved both utility and automated safety metrics in this controlled comparison.

This supports the value of evaluating untrusted document inputs with controlled synthetic tasks. The result is not that the model is safe, nor that prompt injection is solved. The result is that ReceiptInject + EvalGrid can create a repeatable test setting where failures become visible, mitigations can be compared, and artifacts can be inspected.

The suspicious-instruction detection result is also useful to interpret carefully. Detection improved from 40.0% to 52.0%, but it did not reach complete detection. A model can sometimes behave safely without explicitly flagging every suspicious instruction, and explicit detection alone is not sufficient for safe task completion.

## 7. Failure Case Analysis

Failure-case export joins scored rows, raw model outputs, and source examples. It summarizes embedded instructions rather than reproducing long adversarial passages. The relevant artifacts are:

- `results/hard_manual_review_sample.md`
- `results/final/final_failure_cases.md`

The current manual-review sample includes benign and adversarial examples, baseline failures, combined-safety successes, and grounded extraction cases. Baseline failures include mixed-bundle data-poisoning and hidden-action-request cases, as well as a bank-statement privacy-exfiltration case flagged for prompt-injection compliance. Structured prompt examples show successful benign extraction from mixed bundles and policy documents without over-refusal.

Manual inspection also found an important scorer limitation: some baseline policy-document hallucination labels appear to reflect strict matching or paraphrase differences rather than obvious fabricated facts. This is a useful finding for benchmark development. It suggests that automated labels should be treated as triage signals for review, not final adjudications.

## 8. Dataset Diversity Audit

The dataset diversity audit checks duplicate document texts and repeated tracked values in the 500-example synthetic dataset.

| Audit item | Value |
| --- | ---: |
| Duplicate `document_text` | 0 |
| Repeated tracked-value occurrences | 608 |

The audit found no duplicate documents, but repeated values remain due to synthetic templates. Repeated synthetic merchants, vendors, and institutions are documented as a limitation and motivate future template/value diversification. This is preferable to hiding the issue: reviewers should be able to see where the benchmark is already systematic and where the data generator remains prototype-grade.

## 9. Limitations

ReceiptInject + EvalGrid has several important limitations:

- The data is synthetic only.
- No real private documents are used.
- Repeated tracked values remain in the generated dataset.
- Automated scorers are heuristic and can mislabel paraphrases or semantically equivalent outputs.
- The manual review sample is small.
- There is no human annotation set yet.
- OCR coverage is limited or pending depending on the selected artifact set.
- Results depend on provider, model, prompt formatting, SDK behavior, and sampling/settings.
- The benchmark does not cover all prompt-injection modalities, including hidden text, invisible text, steganography, malware, or production system compromise.
- The current results should not be interpreted as production reliability evidence.

These limitations are central to interpreting the project. The benchmark is designed to support measurement and comparison, not to certify systems as safe.

## 10. Future Work

Future work should improve both the benchmark and the evaluation infrastructure:

- Increase document, layout, and value diversity
- Add human annotation and adjudication workflows
- Expand OCR stress tests with more layouts and degradation patterns
- Add more model providers and comparable model-family configs
- Add semantic scorers or calibrated LLM-as-judge checks for extraction and hallucination
- Track cost, latency, retries, and provider failures more systematically
- Add controlled tool-use simulations for document agents that can send emails, approve payments, update accounts, or trigger workflows
- Publish benchmark cards and model/provider evaluation cards
- Compare behavior across model families, mitigations, costs, and input modes

## 11. Conclusion

ReceiptInject + EvalGrid is best understood as evaluation infrastructure for making document-agent behavior measurable and auditable under untrusted synthetic inputs. Its contribution is not a claim that a particular model is safe, but a reproducible system for generating controlled document tasks, running model evaluations, logging raw outputs, scoring failure modes, and exporting cases for manual review.

