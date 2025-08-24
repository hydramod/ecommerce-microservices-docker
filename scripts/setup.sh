#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

PY=${PYTHON:-python3}
VENV_DIR="${VENV_DIR:-.venv}"

echo ">>> Creating venv at $VENV_DIR (if missing)"
[ -d "$VENV_DIR" ] || $PY -m venv "$VENV_DIR"

# Find pip for POSIX or Windows Git Bash
if [ -x "$VENV_DIR/bin/pip" ]; then
  PIP="$VENV_DIR/bin/pip"
elif [ -x "$VENV_DIR/Scripts/pip.exe" ]; then
  PIP="$VENV_DIR/Scripts/pip.exe"
elif [ -x "$VENV_DIR/Scripts/pip" ]; then
  PIP="$VENV_DIR/Scripts/pip"
else
  echo "ERROR: Could not find pip inside $VENV_DIR (looked in bin/ and Scripts/)"
  exit 1
fi

echo ">>> Installing dev tools"
"$PIP" install -U pip
"$PIP" install -r requirements-dev.txt

echo ">>> Installing editable service packages"
SERVICES=(auth catalog order cart payment shipping notifications)
for s in "${SERVICES[@]}"; do
  if [ -f "services/$s/pyproject.toml" ]; then
    echo "  - services/$s"
    "$PIP" install -e "services/$s"
  fi
done

echo
echo "Setup complete."
echo "Activate your venv with:"
echo "  source $VENV_DIR/bin/activate         # Linux/macOS/Git Bash (if present)"
echo "  or: .\\$VENV_DIR\\Scripts\\Activate.ps1  # Windows PowerShell"
