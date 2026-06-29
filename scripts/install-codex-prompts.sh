#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 "$ROOT/scripts/bootstrap_ai_berkshire.py" --no-claude --no-codex "$@"

echo "Installed Codex slash prompts via bootstrap_ai_berkshire.py"
