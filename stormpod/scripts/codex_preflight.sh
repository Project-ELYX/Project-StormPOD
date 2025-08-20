# scripts/codex_preflight.sh
#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ! -d "$ROOT/.venv" ]]; then
  echo "[codex] First-time bootstrap..."
  sudo -n true || { echo "Run once: sudo bash scripts/setup_stormpod.sh"; exit 1; }
fi
source "$ROOT/.venv/bin/activate"
pip install -r "$ROOT/requirements.txt" >/dev/null
export PYTHONPATH="$ROOT:$PYTHONPATH"
echo "[codex] Env ready."
