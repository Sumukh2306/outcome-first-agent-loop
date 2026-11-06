#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
SCENARIO="${1:?usage: scripts/evaluate.sh <scenario.yaml> <name>}"
NAME="${2:?usage: scripts/evaluate.sh <scenario.yaml> <name>}"
PORT="${PORT:-8700}"
rm -rf "runs/$NAME" "runs/state_$NAME"
[ -d "runs/base_$NAME" ] || python3 -m sim baseline --scenario "$SCENARIO" --run-dir "runs/base_$NAME" > /dev/null
python3 -m sim serve --scenario "$SCENARIO" --run-dir "runs/$NAME" --port "$PORT" > "runs/$NAME.sim.log" 2>&1 &
SIM=$!
trap 'kill $SIM 2>/dev/null || true' EXIT
for _ in $(seq 1 60); do curl -sf "localhost:$PORT/health" > /dev/null && break; sleep 1; done
CONTROLLER_STATE="runs/state_$NAME" ./run.sh "http://127.0.0.1:$PORT" > "runs/$NAME.ctrl.log" 2>&1
mkdir -p reports
python3 -m sim grade --run "runs/$NAME" --baseline "runs/base_$NAME" --out "runs/$NAME.grade.md" > /dev/null
sed -n 5,9p "runs/$NAME.grade.md"
sed -n 14p "runs/$NAME.grade.md"
