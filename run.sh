#!/usr/bin/env bash
set -euo pipefail
SIM_URL="${1:?usage: ./run.sh <SIM_URL>}"
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
exec python3 -m controller run "$SIM_URL" --state-dir "${CONTROLLER_STATE:-$HERE/controller_state}"
