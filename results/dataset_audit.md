# ReceiptInject Dataset Audit

Dataset: `data/hard_test_subset_50.jsonl`
Status: **FAIL**
Total examples: 50
Errors: 4
Warnings: 0

## Counts

### Document Types
| Value | Count |
| --- | ---: |
| `bank_statement` | 10 |
| `invoice` | 10 |
| `mixed_bundle` | 10 |
| `policy_document` | 10 |
| `receipt` | 10 |

### Attack Types
| Value | Count |
| --- | ---: |
| `authority_impersonation` | 4 |
| `conflicting_instructions` | 4 |
| `data_poisoning` | 4 |
| `fake_policy` | 3 |
| `format_injection` | 3 |
| `hidden_action_request` | 3 |
| `instruction_override` | 3 |
| `none` | 20 |
| `privacy_exfiltration` | 3 |
| `role_confusion` | 3 |

### Difficulty
| Value | Count |
| --- | ---: |
| `easy` | 1 |
| `hard` | 43 |
| `medium` | 6 |

## Findings

| Severity | Check | Example | Message |
| --- | --- | --- | --- |
| error | attack_type_balance | - | Benign/adversarial split is not close to 50/50. |
| error | difficulty_balance | - | Difficulty easy count is outside expected tolerance. |
| error | difficulty_balance | - | Difficulty medium count is outside expected tolerance. |
| error | difficulty_balance | - | Difficulty hard count is outside expected tolerance. |

## Audit Checks

- Pydantic schema validation
- No real-looking SSNs
- No real-looking full credit card numbers
- Non-empty document text
- No duplicate IDs
- No duplicate document text
- Reasonable attack type balance
- Reasonable difficulty balance
- Embedded instruction spans for adversarial examples
- Benign examples use attack_type `none`
- Private fields do not appear in document text unless explicitly tagged
- Ground truth values are recoverable from document text where appropriate
- Mixed bundles contain more than one document section
