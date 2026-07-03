# Claim Audit

Audited files: `README.md`, `docs/ReceiptInject_Report.md`, `paper/ReceiptInject_Report.md`, and `research_memo.md`.

## Findings

| Claim surface | Status | Backing artifact | Action |
| --- | --- | --- | --- |
| OpenAI passive hard-subset numbers: 45.3% to 84.7% extraction, 54.0% to 100.0% safe completion, 12.0% to 0.0% hallucination, 6.0% to 0.0% prompt-injection compliance | Backed | `results/final/final_results.csv` before and after this pass | Kept |
| Mistral 5-row EvalGrid smoke test | Backed only as smoke validation | `results/evalgrid_mistral_summary.md` | Not used as research evidence |
| Mistral passive hard-subset 50-example baseline and combined-safety runs | Backed after this pass | `results/final/evalgrid_mistral_hard_results.csv`, `results/final/final_results.csv` | Added to final scope |
| Claude/Anthropic comparison | Not backed | No Anthropic key; no Claude rows | Not claimed |
| Agentic GPT+Mistral 100-task claims in README/docs | Not part of committed `results/final` passive artifact set | Local untracked agentic artifacts may exist, but they are outside this resume-facing final scope | Removed from public passive README/report surfaces |
| Broad dataset coverage despite repeated synthetic values | Caveated | `results/dataset_diversity_audit.md` | Caveat retained |

## Decision

The resume-facing passive comparison is now OpenAI + Mistral only. Claude is explicitly absent. Agentic cross-model claims should not be used in resume-facing public docs unless their data artifacts are separately committed and validated.
