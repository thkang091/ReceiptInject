# ReceiptInject Dataset Diversity Audit

Dataset: `data/examples_500.jsonl`
Total examples: 500
Duplicate document_text count: 0

## Repeated Ground Truth Values

| Field | Repeated value | Count |
| --- | --- | ---: |
| institution | `Meridian Example Trust` | 44 |
| institution | `Blue Orchard Demo Bank` | 32 |
| institution | `Civic Ledger Sandbox` | 24 |
| invoice_total | `871.10` | 8 |
| invoice_total | `541.45` | 7 |
| invoice_total | `437.35` | 7 |
| invoice_total | `680.25` | 7 |
| invoice_total | `420.00` | 6 |
| invoice_total | `472.05` | 6 |
| invoice_total | `888.45` | 6 |
| invoice_total | `940.50` | 6 |
| invoice_total | `732.30` | 5 |
| invoice_total | `905.80` | 5 |
| merchant | `QUARTZ HARBOR MART` | 51 |
| merchant | `LUMA RIDGE MARKET` | 39 |
| merchant | `FENNEL BROOK GROCER` | 35 |
| receipt_total | `56.74` | 5 |
| receipt_total | `77.75` | 5 |
| receipt_total | `62.47` | 4 |
| receipt_total | `37.64` | 4 |
| receipt_total | `51.01` | 4 |
| receipt_total | `70.11` | 3 |
| receipt_total | `60.56` | 3 |
| receipt_total | `54.83` | 3 |
| receipt_total | `68.20` | 2 |
| receipt_total | `39.55` | 2 |
| total | `24.74` | 3 |
| total | `58.72` | 3 |
| total | `29.98` | 2 |
| total | `32.60` | 2 |
| total | `40.46` | 2 |
| total | `48.51` | 2 |
| total | `37.57` | 2 |
| total | `24.01` | 2 |
| total | `26.55` | 2 |
| total | `26.09` | 2 |
| vendor | `Northstar Fabrication Studio` | 48 |
| vendor | `Cedarline Prototype Works` | 40 |
| vendor | `Juniper Systems Bench` | 37 |

## Top Repeated Values by Document Type

### bank_statement

| Value | Count |
| --- | ---: |
| `institution: Meridian Example Trust` | 44 |
| `institution: Blue Orchard Demo Bank` | 32 |
| `institution: Civic Ledger Sandbox` | 24 |

### invoice

| Value | Count |
| --- | ---: |
| `vendor: Northstar Fabrication Studio` | 48 |
| `vendor: Cedarline Prototype Works` | 40 |
| `vendor: Juniper Systems Bench` | 37 |
| `invoice_total: 871.10` | 8 |
| `invoice_total: 541.45` | 7 |
| `invoice_total: 437.35` | 7 |
| `invoice_total: 680.25` | 7 |
| `invoice_total: 420.00` | 6 |
| `invoice_total: 472.05` | 6 |
| `invoice_total: 888.45` | 6 |

### mixed_bundle

| Value | Count |
| --- | ---: |
| `receipt_total: 56.74` | 5 |
| `receipt_total: 77.75` | 5 |
| `invoice_total: 278.30` | 4 |
| `invoice_total: 447.30` | 4 |
| `receipt_total: 62.47` | 4 |
| `invoice_total: 396.60` | 4 |
| `receipt_total: 37.64` | 4 |
| `invoice_total: 236.05` | 4 |
| `receipt_total: 51.01` | 4 |
| `invoice_total: 168.45` | 3 |

### policy_document

_No repeated tracked values._

### receipt

| Value | Count |
| --- | ---: |
| `merchant: QUARTZ HARBOR MART` | 51 |
| `merchant: LUMA RIDGE MARKET` | 39 |
| `merchant: FENNEL BROOK GROCER` | 35 |
| `total: 24.74` | 3 |
| `total: 58.72` | 3 |
| `total: 29.98` | 2 |
| `total: 32.60` | 2 |
| `total: 40.46` | 2 |
| `total: 48.51` | 2 |
| `total: 37.57` | 2 |
