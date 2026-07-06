# Claim Audit

Audited files: `README.md`, `docs/ReceiptInject_Report.md`, `paper/ReceiptInject_Report.md`, `research_memo.md`, and `results/final/*` summary files.

## Findings

| Claim surface | Status | Backing artifact | Action |
| --- | --- | --- | --- |
| 2,700-row cross-provider result: Gemini, OpenAI, Mistral x baseline/safety/trusted-gating x 300 examples | Backed | `results/evalgrid_2700_all_results.csv`, `results/evalgrid_2700_summary.md` | Current headline |
| 0 error rows across the 2,700-row headline artifact | Backed | `results/evalgrid_2700_all_results.csv` | Kept |
| Gemini baseline/safety/trusted-gating rows | Backed | `results/evalgrid_gemini_300_*_results.csv` and metadata files | Kept |
| OpenAI baseline/safety/trusted-gating rows | Backed | `results/evalgrid_openai_300_*_results.csv` and metadata files | Kept |
| Mistral baseline/safety/trusted-gating rows | Backed | `results/evalgrid_mistral_300_*_results.csv` and metadata files | Kept |
| Trusted-tool gating separates unsafe model proposals from unsafe execution | Backed by implementation and result columns | `receiptinject/tool_policy.py`, `receiptinject/eval_harness.py`, `results/evalgrid_2700_all_results.csv` | Kept with simulated-executor caveat |
| OpenAI/Mistral 50-example hard-subset result | Backed as legacy validation | `results/final/final_results.csv` | Marked legacy, not current headline |
| Claude/Anthropic comparison | Not backed | No Anthropic key; no Claude rows | Not claimed |
| Mock results as research evidence | Not backed | Mock mode is pipeline validation only | Not claimed |
| Broad real-world safety / production reliability | Not backed | Synthetic data and heuristic scorers | Explicitly caveated |
| Broad dataset coverage despite repeated synthetic values | Caveated | `results/dataset_diversity_audit.md` | Caveat retained |

## Decision

The public headline is now the 2,700-row synthetic real-provider comparison across Gemini, OpenAI, and Mistral. The older 50-example hard-subset artifacts are retained as legacy validation material. Claude/Anthropic is explicitly absent. The benchmark supports a preliminary, synthetic, automated-scoring claim about evaluation infrastructure and mitigation comparison; it does not prove production safety.
