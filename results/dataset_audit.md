# ReceiptInject Dataset Audit

Dataset: `data/examples_300.jsonl`
Status: **PASS**
Total examples: 300
Errors: 0
Warnings: 0

## Counts

### Document Types
| Value | Count |
| --- | ---: |
| `bank_statement` | 75 |
| `invoice` | 75 |
| `policy_document` | 75 |
| `receipt` | 75 |

### Attack Types
| Value | Count |
| --- | ---: |
| `authority_impersonation` | 16 |
| `conflicting_instructions` | 16 |
| `data_poisoning` | 17 |
| `fake_policy` | 17 |
| `format_injection` | 16 |
| `hidden_action_request` | 17 |
| `instruction_override` | 17 |
| `none` | 150 |
| `privacy_exfiltration` | 17 |
| `role_confusion` | 17 |

### Difficulty
| Value | Count |
| --- | ---: |
| `easy` | 105 |
| `hard` | 60 |
| `medium` | 135 |

## Findings

No audit findings.

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
