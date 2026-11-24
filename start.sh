#!/usr/bin/env bash
# Установка и запуск одним кликом (macOS/Linux): ./start.sh
cd "$(dirname "$0")" || exit 1
PY=python3; command -v python3 >/dev/null || PY=python
exec "$PY" tools/setup.py --open
