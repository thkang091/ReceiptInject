# Dataset Card for ReceiptInject

## Dataset Summary

ReceiptInject is a synthetic benchmark for evaluating document-understanding LLM agents on untrusted document inputs. It contains generated receipts, invoices, bank statements, policy/legal-style documents, and mixed multi-document bundles, with ground-truth labels for extraction utility and safety-relevant model behavior.

The benchmark is designed for controlled empirical AI safety research. Embedded instructions are visible, clearly labeled benchmark content; the dataset does not use hidden text, invisible text, steganography, or real private records.

## Purpose

ReceiptInject studies whether document-understanding agents can extract useful structured information from untrusted documents without following embedded instructions, leaking private fields, hallucinating unsupported facts, over-refusing benign requests, or recommending unsafe external actions.

The dataset supports reproducible evaluation of mitigation prompts, OCR pipelines, multi-model comparisons, and safety/utility tradeoffs in document AI systems.

## Dataset Composition

The default benchmark generation command is:

```bash
python scripts/generate_dataset.py --n 500 --output data/examples_500.jsonl --seed 42
```

For `n=500`, the intended composition is:

- 125 receipts
- 125 invoices
- 100 bank statements
- 100 policy/legal/public-sector documents
- 50 mixed multi-document bundles

The dataset is approximately balanced between benign and adversarial examples. Difficulty labels follow a target distribution of 35% easy, 45% medium, and 20% hard.

## Document Types

- `receipt`: Synthetic point-of-sale receipts with line items, totals, dates, payment labels, and optional internal notes.
- `invoice`: Synthetic business invoices with invoice IDs, due dates, line items, payment status, and totals.
- `bank_statement`: Synthetic statement-like documents with balances, transactions, dates, and account labels.
- `policy_document`: Synthetic policy, legal, compliance, or public-sector style documents with obligations, exceptions, and decision-relevant facts.
- `mixed_bundle`: Multi-section bundles combining more than one document type for comparison, reconciliation, or neutral summary tasks.

## Attack Types

ReceiptInject includes benign examples with `attack_type=none` and adversarial examples using visible embedded instruction patterns:

- `instruction_override`: Tells the model to ignore or replace the evaluator task.
- `privacy_exfiltration`: Asks the model to reveal private or internal fields.
- `role_confusion`: Presents document text as if it were a system, developer, or administrator message.
- `fake_policy`: Claims that a false policy update overrides normal behavior.
- `hidden_action_request`: Asks for external actions such as payment approval, refund processing, account updates, legal approval, compliance decisions, or eligibility decisions.
- `data_poisoning`: Asks the model to change totals, dates, names, or official facts.
- `conflicting_instructions`: Includes conflicting instructions that should be treated as document content only.
- `authority_impersonation`: Claims authority from an administrator, auditor, court, compliance officer, or similar role.
- `format_injection`: Requests unsafe output formatting or inclusion of hidden/private fields.

## Difficulty Levels

- `easy`: Clear layouts, direct extraction targets, and simple embedded instruction placement.
- `medium`: More complex formatting, additional distractor fields, or less direct extraction tasks.
- `hard`: Longer documents, multi-section layouts, mixed bundles, denser fields, or more challenging safety/utility tradeoffs.

## Synthetic Data Generation

All examples are generated deterministically from code and seeds. The generator uses fictional organizations, names, identifiers, dates, totals, policy labels, and account-like values. It intentionally avoids real companies, banks, addresses, emails, account numbers, government IDs, legal cases, medical data, and private personal information.

Generation outputs include the full document text, expected task, ground-truth fields, synthetic private fields, tags, difficulty labels, attack labels, and expected safe behavior descriptions. Dataset validation checks schema validity, duplicate IDs/text, balance properties, mixed-bundle structure, and patterns that could resemble real SSNs or full credit card numbers.

## Private Fields

Private fields are synthetic labels used only to test whether a model unnecessarily reveals information. Example private-field keys include:

- `customer_name`
- `payment_last4`
- `account_last4`
- `account_holder`
- `internal_customer_id`
- `client_email`
- `internal_account_code`
- `internal_reviewer`
- `internal_case_id`

These fields are not real personal data. They are designed to support privacy-minimization evaluation in a controlled setting.

## Ground Truth Fields

Ground-truth fields provide the expected recoverable facts for scoring extraction accuracy. Depending on document type, these may include totals, dates, document IDs, line-item facts, balances, obligations, exceptions, bundle IDs, and comparison targets.

Ground truth is intended for benchmark scoring, not for operational decision-making.

## Intended Uses

- Defensive AI safety evaluation of document-understanding agents.
- Research on prompt-injection robustness for untrusted documents.
- Evaluation of privacy leakage, hallucination, refusal, and unsafe-action behavior.
- Comparison of mitigation prompts, OCR pathways, and model providers.
- Reproducible ML systems and evaluation-infrastructure experiments.
- Qualitative failure-case analysis for empirical AI governance and safety research.

Mock model results should be used only to validate the pipeline. Real-model and OCR
results, when generated, should be reported as preliminary synthetic-benchmark evidence
with scorer limitations and manual-inspection caveats.

## Out-of-Scope Uses

- Attacking real document-processing systems.
- Developing operational prompt-injection payloads for misuse.
- Processing real private, personal, financial, legal, medical, or government documents.
- Creating deceptive documents for real workflows.
- Making legal, financial, medical, compliance, eligibility, lending, employment, or benefits decisions.
- Claiming broad model safety guarantees from this benchmark alone.

## Ethical Considerations

ReceiptInject is a defensive benchmark designed to study and reduce unsafe model behavior. It uses synthetic data to avoid exposing real individuals, organizations, accounts, cases, or sensitive records.

Researchers should clearly state that embedded instructions are visible benchmark data and that results measure controlled failure modes. High-stakes document AI systems require human review, domain-specific validation, privacy controls, and operational safeguards beyond this benchmark.

## Limitations

ReceiptInject is synthetic and may not capture the full diversity of real document layouts, OCR artifacts, institutional formats, language varieties, accessibility constraints, or domain-specific terminology. The benchmark focuses on visible embedded instructions and does not evaluate hidden text, invisible text, steganography, or attacks against deployed systems.

Scores should be interpreted as measurements on a controlled benchmark, not as universal evidence that a model or mitigation is safe in production.

## Versioning

Dataset versions should record:

- Generator code version or git commit
- Random seed
- Number of examples
- Generation command
- Validation report
- Rendering/OCR pipeline settings, when applicable
- Prompt mitigation and model configuration, when reporting results

Recommended version label format:

```text
receiptinject-v0.1-n500-seed42
```

## Citation Placeholder

If you use ReceiptInject in research, cite the project repository and the associated report:

```bibtex
@misc{receiptinject2026,
  title = {ReceiptInject: Synthetic Evaluation Infrastructure for Document-Understanding Agents on Untrusted Inputs},
  author = {ReceiptInject Contributors},
  year = {2026},
  note = {Synthetic defensive AI safety benchmark},
  url = {https://github.com/your-org/receiptinject}
}
```
