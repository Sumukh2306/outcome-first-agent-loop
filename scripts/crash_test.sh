#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
SCENARIO="${1:-scenarios/public_02_incidents.yaml}"
KILLS="${KILLS:-4}"
RUN=runs/crash_$$
STATE=runs/crash_state_$$
rm -rf "$RUN" "$STATE"
python3 -m sim serve --scenario "$SCENARIO" --run-dir "$RUN" > "$RUN.sim.log" 2>&1 &
SIM=$!
trap 'kill $SIM 2>/dev/null || true' EXIT
sleep 4
for i in $(seq 1 "$KILLS"); do
  CONTROLLER_STATE="$STATE" ./run.sh http://127.0.0.1:8700 > "$RUN.ctrl$i.log" 2>&1 &
  PID=$!
  if [ "$i" = 1 ]; then LO=2.2; HI=3.0; else LO=0.5; HI=1.1; fi
  sleep "$(python3 -c "import random;print(round(random.uniform($LO,$HI),2))")"
  if kill -0 $PID 2>/dev/null; then
    kill -9 $PID
    wait $PID 2>/dev/null || true
    echo "kill $i: sent SIGKILL at sim minute $(curl -s localhost:8700/sim/state | python3 -c 'import sys,json;print(json.load(sys.stdin)["sim_minute"])')"
  else
    echo "kill $i: controller had already finished"
  fi
done
CONTROLLER_STATE="$STATE" ./run.sh http://127.0.0.1:8700 > "$RUN.final.log" 2>&1
echo "final state: $(curl -s localhost:8700/sim/state)"
DB=$(ls "$STATE"/*.db | head -1)
echo "duplicate proposal ids: $(sqlite3 "$DB" 'select count(*) from (select proposal_id from approvals group by 1 having count(*)>1)')"
echo "intents left unresolved: $(sqlite3 "$DB" "select count(*) from approvals where status in ('intent','auto_intent','applying')")"
python3 - "$RUN" <<'PY'
import json, sys
from collections import Counter
log = [json.loads(l) for l in open(sys.argv[1] + "/sim_log.jsonl")]
applied = Counter(r["approval_id"] for r in log if r["kind"] == "approval_applied")
auto = Counter(r["proposal_id"] for r in log if r["kind"] == "auto_applied")
print("approvals applied more than once:", sum(1 for v in applied.values() if v > 1))
print("auto-applies repeated:", sum(1 for v in auto.values() if v > 1))
PY
python3 -m sim baseline --scenario "$SCENARIO" --run-dir "$RUN.base" > /dev/null 2>&1
python3 -m sim grade --run "$RUN" --baseline "$RUN.base" --out "$RUN.grade.md" > /dev/null
sed -n 5,9p "$RUN.grade.md"
