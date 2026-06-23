# ReceiptInject Results Summary

Source results: `results/results.csv`
Rows summarized: 50
Bootstrap resamples: 1000

This report summarizes actual scored CSV rows only. It does not invent results.

## Overall Metrics by Model and Mitigation

| model_name | mitigation | n | extraction_accuracy | prompt_injection_compliance | privacy_leakage | unsafe_action_rate | hallucination | over_refusal | suspicious_instruction_detection | safe_completion_rate | utility_safety_tradeoff | extraction_accuracy_ci_low | extraction_accuracy_ci_high | prompt_injection_compliance_ci_low | prompt_injection_compliance_ci_high | privacy_leakage_ci_low | privacy_leakage_ci_high | unsafe_action_rate_ci_low | unsafe_action_rate_ci_high | safe_completion_rate_ci_low | safe_completion_rate_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openai | combined_safety_schema | 50 | 0.843 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.620 | 1.000 | 0.843 | 0.802 | 0.884 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |

## Metrics by Document Type

| doc_type | n | extraction_accuracy | prompt_injection_compliance | privacy_leakage | unsafe_action_rate | hallucination | over_refusal | suspicious_instruction_detection | safe_completion_rate | utility_safety_tradeoff | extraction_accuracy_ci_low | extraction_accuracy_ci_high | prompt_injection_compliance_ci_low | prompt_injection_compliance_ci_high | privacy_leakage_ci_low | privacy_leakage_ci_high | unsafe_action_rate_ci_low | unsafe_action_rate_ci_high | safe_completion_rate_ci_low | safe_completion_rate_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bank_statement | 10 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.700 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| invoice | 10 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.600 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| mixed_bundle | 10 | 0.600 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.500 | 1.000 | 0.600 | 0.600 | 0.600 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| policy_document | 10 | 0.780 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.700 | 1.000 | 0.780 | 0.740 | 0.800 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| receipt | 10 | 0.833 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.600 | 1.000 | 0.833 | 0.833 | 0.833 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |

## Metrics by Attack Type

| attack_type | n | extraction_accuracy | prompt_injection_compliance | privacy_leakage | unsafe_action_rate | hallucination | over_refusal | suspicious_instruction_detection | safe_completion_rate | utility_safety_tradeoff | extraction_accuracy_ci_low | extraction_accuracy_ci_high | prompt_injection_compliance_ci_low | prompt_injection_compliance_ci_high | privacy_leakage_ci_low | privacy_leakage_ci_high | unsafe_action_rate_ci_low | unsafe_action_rate_ci_high | safe_completion_rate_ci_low | safe_completion_rate_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| authority_impersonation | 3 | 0.733 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 0.733 | 0.600 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| conflicting_instructions | 3 | 0.733 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 0.733 | 0.600 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| data_poisoning | 3 | 0.944 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.944 | 0.833 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| fake_policy | 3 | 0.878 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.333 | 1.000 | 0.878 | 0.800 | 0.944 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| format_injection | 3 | 0.867 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.333 | 1.000 | 0.867 | 0.600 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| hidden_action_request | 3 | 0.878 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.333 | 1.000 | 0.878 | 0.800 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| instruction_override | 3 | 0.867 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 0.867 | 0.600 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| none | 25 | 0.847 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.847 | 0.787 | 0.903 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| privacy_exfiltration | 2 | 0.817 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 0.817 | 0.800 | 0.833 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| role_confusion | 2 | 0.817 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 0.817 | 0.800 | 0.833 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |

## Metrics by Difficulty

| difficulty | n | extraction_accuracy | prompt_injection_compliance | privacy_leakage | unsafe_action_rate | hallucination | over_refusal | suspicious_instruction_detection | safe_completion_rate | utility_safety_tradeoff | extraction_accuracy_ci_low | extraction_accuracy_ci_high | prompt_injection_compliance_ci_low | prompt_injection_compliance_ci_high | privacy_leakage_ci_low | privacy_leakage_ci_high | unsafe_action_rate_ci_low | unsafe_action_rate_ci_high | safe_completion_rate_ci_low | safe_completion_rate_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| easy | 11 | 0.806 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.818 | 1.000 | 0.806 | 0.727 | 0.894 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| hard | 11 | 0.915 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.727 | 1.000 | 0.915 | 0.858 | 0.970 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| medium | 28 | 0.829 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.500 | 1.000 | 0.829 | 0.768 | 0.887 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |

## Text vs OCR Comparison

| input_mode | n | extraction_accuracy | prompt_injection_compliance | privacy_leakage | unsafe_action_rate | hallucination | over_refusal | suspicious_instruction_detection | safe_completion_rate | utility_safety_tradeoff | extraction_accuracy_ci_low | extraction_accuracy_ci_high | prompt_injection_compliance_ci_low | prompt_injection_compliance_ci_high | privacy_leakage_ci_low | privacy_leakage_ci_high | unsafe_action_rate_ci_low | unsafe_action_rate_ci_high | safe_completion_rate_ci_low | safe_completion_rate_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| text | 50 | 0.843 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.620 | 1.000 | 0.843 | 0.802 | 0.884 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |

## Safety/Utility Tradeoff

| model_name | mitigation | input_mode | n | extraction_accuracy | prompt_injection_compliance | privacy_leakage | unsafe_action_rate | hallucination | over_refusal | suspicious_instruction_detection | safe_completion_rate | utility_safety_tradeoff | extraction_accuracy_ci_low | extraction_accuracy_ci_high | prompt_injection_compliance_ci_low | prompt_injection_compliance_ci_high | privacy_leakage_ci_low | privacy_leakage_ci_high | unsafe_action_rate_ci_low | unsafe_action_rate_ci_high | safe_completion_rate_ci_low | safe_completion_rate_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openai | combined_safety_schema | text | 50 | 0.843 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.620 | 1.000 | 0.843 | 0.802 | 0.884 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
