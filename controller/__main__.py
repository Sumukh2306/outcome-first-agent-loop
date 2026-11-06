import argparse
import json
import os
import sys
from pathlib import Path

from .loop import run as run_loop


def find_db(state_dir: str, scenario: str | None):
    dbs = sorted(Path(state_dir).glob("*.db"))
    if scenario:
        dbs = [d for d in dbs if d.name.startswith(scenario)]
    if not dbs:
        sys.exit(f"no controller state in {state_dir}")
    return dbs[-1]


def cmd_why(args):
    from .store import Store
    store = Store(find_db(args.state_dir, args.scenario))
    rows = store.all(
        "SELECT sim_minute, kind, summary, payload_json FROM audit WHERE workflow_id=? AND sim_minute BETWEEN ? AND ?"
        " ORDER BY seq", (args.workflow, args.minute - args.window, args.minute + args.window))
    for r in rows:
        h, m = divmod(r["sim_minute"], 60)
        day, hh = divmod(h, 24)
        print(f"D{day} {hh:02d}:{m:02d}  {r['kind']:<20} {r['summary']}")
    if not rows:
        print("nothing recorded in that window")


def cmd_view(args):
    from .store import Store
    store = Store(find_db(args.state_dir, args.scenario))
    for w in store.all("SELECT DISTINCT workflow_id FROM call_agg ORDER BY workflow_id"):
        wid = w["workflow_id"]
        print(f"== {wid}")
        for a in store.all("SELECT status, COUNT(*) n FROM approvals WHERE workflow_id=? GROUP BY status", (wid,)):
            print(f"   approvals {a['status']}: {a['n']}")
        for i in store.all("SELECT kind, subject, status FROM incidents WHERE workflow_id=?", (wid,)):
            print(f"   incident {i['kind']} {i['subject']}: {i['status']}")
        for e in store.all("SELECT dim, state, winner FROM experiments WHERE workflow_id=?", (wid,)):
            print(f"   experiment {e['dim']}: {e['state']} winner={e['winner']}")


def main():
    ap = argparse.ArgumentParser(prog="controller")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("url")
    r.add_argument("--state-dir", default=os.environ.get("CONTROLLER_STATE", "controller_state"))
    w = sub.add_parser("why")
    w.add_argument("--state-dir", default="controller_state")
    w.add_argument("--scenario")
    w.add_argument("--workflow", required=True)
    w.add_argument("--minute", type=int, required=True, help="minutes since D0 00:00 IST")
    w.add_argument("--window", type=int, default=60)
    v = sub.add_parser("view")
    v.add_argument("--state-dir", default="controller_state")
    v.add_argument("--scenario")
    args = ap.parse_args()
    if args.cmd == "run":
        run_loop(args.url, args.state_dir)
    elif args.cmd == "why":
        cmd_why(args)
    elif args.cmd == "view":
        cmd_view(args)


if __name__ == "__main__":
    main()
