# Responsible Use

ReceiptInject is a defensive AI safety benchmark for studying document-understanding LLM agents on untrusted inputs. The benchmark is designed to measure and reduce unsafe model behavior, including prompt-injection compliance, privacy leakage, hallucination, unsafe action recommendations, and over-refusal.

All ReceiptInject benchmark data is synthetic. The project must not include real personal, financial, legal, medical, government, business-confidential, or otherwise private information.

## Required Use Boundaries

- Use ReceiptInject only for defensive research, evaluation, education, and safety engineering.
- Use only synthetic data generated for the benchmark.
- Do not insert real private documents into the dataset, rendering pipeline, OCR pipeline, evaluation harness, prompts, or reports.
- Do not include real account numbers, real emails, real addresses, real government IDs, real legal cases, real medical records, or real financial records.
- Keep embedded benchmark instructions visible and clearly labeled as document content.
- Do not use hidden text, invisible text, steganography, or deceptive rendering techniques.

## Prohibited Uses

- Do not use ReceiptInject to attack, probe, bypass, or compromise real systems.
- Do not use the benchmark to develop operational prompt-injection payloads for misuse.
- Do not test real production document-processing systems without authorization.
- Do not use generated adversarial examples as instructions for targeting deployed systems.
- Do not use ReceiptInject outputs to make real legal, financial, medical, compliance, eligibility, lending, employment, insurance, or benefits decisions.

## Interpretation of Results

ReceiptInject results are measurements on controlled synthetic examples. They are not legal, financial, medical, compliance, or operational advice.

Mock scores validate the evaluation pipeline; they are not evidence about real model safety. Real-model scores are preliminary measurements on a synthetic benchmark. OCR pilot scores are small-sample measurements and should not be treated as production document reliability evidence.

Benchmark scores do not prove that a model or document AI system is safe for production. They should be interpreted alongside human review, domain expertise, privacy review, security testing, monitoring, and broader evaluation on appropriate authorized data.

High-stakes document AI systems require human oversight. A model should not be allowed to approve payments, send emails, update accounts, issue refunds, make compliance decisions, determine eligibility, or take similar external actions without appropriate authorization and review.

## Research Intent

The benchmark exists to help researchers and engineers understand where document-understanding agents fail and how safety mitigations affect utility. Its purpose is to support safer systems, better evaluations, and clearer empirical evidence about model behavior on untrusted documents.

When publishing or sharing results, clearly state:

- The dataset is synthetic.
- Embedded instructions are visible benchmark content.
- The work is for defensive AI safety evaluation.
- Results measure controlled failure modes, not universal safety guarantees.
- No conclusions should be treated as professional advice or a substitute for human review.
