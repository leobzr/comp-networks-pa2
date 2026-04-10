#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip
python -m pip install -r "$ROOT_DIR/tcp_des/requirements.txt"
python -m pip install -r "$ROOT_DIR/requirements-person2.txt"

echo "Running merged test suite..."
PYTHONPATH="$ROOT_DIR" pytest -q

echo
echo "Running Person 1 demo (tcp_des)..."
(
    cd "$ROOT_DIR/tcp_des"
    PYTHONPATH="$ROOT_DIR:$ROOT_DIR/tcp_des" python demo_dummy_tcp.py
)

echo
echo "Running Person 2 integration sweep..."
PYTHONPATH="$ROOT_DIR" python -m TCP_logic.run_integration
