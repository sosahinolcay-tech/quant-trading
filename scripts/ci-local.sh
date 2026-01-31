#!/usr/bin/env bash
set -euo pipefail

python -m pip install --upgrade pip setuptools wheel
pip install -r requirements-ci.txt

echo "Running black..."
black --check --diff qt tests tools

echo "Running flake8..."
flake8 qt tests --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 qt tests --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

echo "Running mypy..."
mypy qt --ignore-missing-imports --no-error-summary || true

echo "Running pytest..."
pytest tests/unit tests/integration --cov=qt --cov-report=term-missing -v --tb=short --strict-markers
