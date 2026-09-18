#!/bin/bash
# [ame] fixed: cd to project root so pyproject.toml is findable
cd "$(dirname "$0")/.."
if [ ! -d "venv" ]; then
  read -sp "Enter your api key: " api_key
  echo ""
  echo "api_key=${api_key}" >./.env
  echo "Setting up environment..."
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -e .
else
  source .venv/bin/activate
fi

kagent
