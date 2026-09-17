#!/bin/bash
# [ame] fixed: cd to project root so pyproject.toml is findable
cd "$(dirname "$0")/.."
if [ ! -d "venv" ]; then
  echo "Setting up environment..."
  echo "api_key=placeholder" >.env
  python3 -m venv venv
  source venv/bin/activate
  pip install -e .
else
  source venv/bin/activate
fi
kagent