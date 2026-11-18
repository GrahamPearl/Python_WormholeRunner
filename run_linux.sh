#!/usr/bin/env bash
# Wormhole Runner launcher for Linux (and macOS). Needs Python 3.10+ with venv support
# (Debian/Ubuntu: sudo apt install python3-venv).
cd "$(dirname "$0")" || exit 1
if [ ! -d .venv ]; then
    python3 -m venv .venv || { echo "Could not create a virtual environment (install python3-venv)."; exit 1; }
fi
# shellcheck disable=SC1091
. .venv/bin/activate
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
exec python main.py "$@"
