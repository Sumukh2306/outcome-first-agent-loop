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


def parse_at(text: str) -> int:
    day, clock = text.upper().lstrip("D").split()
    hh, mm = clock.split(":")
    return int(day) * 1440 + int(hh) * 60 + int(mm)


def stamp(minute: int) -> str:
    day, rest = divmod(minute, 1440)
    return f"D{day} {rest // 60:02d}:{rest % 60:02d}"


def cmd_why(args):
    from .store import Store
    store = Store(find_db(args.state_dir, args.scenario))
    at = parse_at(args.at)
    rows = store.all(
        "SELECT sim_minute, kind, summary FROM audit WHERE workflow_id=? AND sim_minute BETWEEN ? AND ?"
        " ORDER BY seq", (args.workflow, at - args.window, at + args.window))
    print(f"{args.workflow} around {stamp(at)} (+/- {args.window} min)")
    for r in rows:
        print(f"  {stamp(r['sim_minute'])}  {r['kind']:<20} {r['summary']}")
    props = store.all(
        "SELECT * FROM approvals WHERE workflow_id=? AND created_minute BETWEEN ? AND ? ORDER BY created_minute",
        (args.workflow, at - 1440, at + args.window))
    for a in props:
        body = json.loads(a["body_json"])
        print(f"  proposal {a['approval_id'] or a['proposal_id']} ({a['kind']}, {a['status']}) made {stamp(a['created_minute'])}")
        print(f"    summary: {a['summary']}")
        print(f"    rationale: {body.get('rationale')}")
        print(f"    affected leads: {body.get('affected_leads')}, impact score: {body.get('impact_score')}")
        if a["reasons_json"]:
            print(f"    approver notes: {a['reasons_json']}")
    if not rows and not props:
        print("  nothing recorded in that window")


def cmd_view(args):
    from .store import Store
    store = Store(find_db(args.state_dir, args.scenario))
    seen = store.get_kv("sim_seen", {"sim_minute": 0})
    now = seen["sim_minute"]
    print(f"Supervisor view at {stamp(now)}, credits left {store.get_kv('credits_remaining')}")
    for w in store.all("SELECT DISTINCT workflow_id FROM call_agg ORDER BY workflow_id"):
        wid = w["workflow_id"]
        print(f"\n{wid}")
        print("  Being tested / winning")
        for e in store.all("SELECT dim, state, winner FROM experiments WHERE workflow_id=?", (wid,)):
            print(f"    {e['dim']}: {e['state']}" + (f", winner {e['winner']}" if e["winner"] else ""))
        print("  Needs your decision")
        asks = store.all("SELECT approval_id, summary, status FROM approvals WHERE workflow_id=? AND status IN"
                         " ('pending','approved') ORDER BY created_minute", (wid,))
        for a in asks or []:
            print(f"    {a['approval_id']} [{a['status']}] {a['summary']}")
        if not asks:
            print("    nothing")
        print("  Changed in the last 24h")
        recent = store.all("SELECT sim_minute, summary FROM audit WHERE workflow_id=? AND kind='config_changed'"
                           " AND sim_minute > ? ORDER BY seq", (wid, now - 1440))
        for r in recent:
            print(f"    {stamp(r['sim_minute'])} {r['summary']}")
        if not recent:
            print("    nothing")
        print("  Incidents")
        incs = store.all("SELECT kind, subject, status, opened_minute, resolved_minute FROM incidents"
                         " WHERE workflow_id=? ORDER BY opened_minute", (wid,))
        for i in incs:
            end = f", fixed {stamp(i['resolved_minute'])}" if i["resolved_minute"] is not None else ""
            print(f"    {i['kind']} {i['subject']} opened {stamp(i['opened_minute'])} [{i['status']}]{end}")
        if not incs:
            print("    none")


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
    w.add_argument("--at", required=True, help='simulated time such as "D3 14:00"')
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
