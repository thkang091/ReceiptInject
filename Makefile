PYTHON ?= .venv/bin/python

.PHONY: install test lint generate-small generate-full mock-eval summarize clean

install:
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -c "import receiptinject; print('receiptinject import OK')"

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

generate-small:
	$(PYTHON) scripts/generate_dataset.py --output data/examples_small.jsonl --n 25 --seed 3

generate-full:
	$(PYTHON) scripts/generate_dataset.py --output data/examples_500.jsonl --n 500 --seed 42

mock-eval:
	$(PYTHON) scripts/run_eval.py --data data/examples_small.jsonl --model mock --mitigation combined_safety --output results/results.csv --raw-output results/raw_outputs.jsonl

summarize:
	$(PYTHON) scripts/summarize_results.py --results results/results.csv --out results/summary.md

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -prune -exec rm -rf {} +
