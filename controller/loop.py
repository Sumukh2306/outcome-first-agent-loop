import hashlib
import json
import sys
import time
import traceback
from pathlib import Path

from .api import Api
from .governance import Governance
from .ingest import ingest_chunk
from .policy import Policy
from .store import Store

STEP_MINUTES = 60


class Logger:
    def __init__(self, store):
        self.store = store
        self.now = 0

    def __call__(self, wid, kind, summary, payload=None):
        self.store.audit(self.now, wid, kind, summary, payload)


def open_store(api: Api, state_dir: str):
    state = api.get("/sim/state")[1]
    first = [line for _, line in zip(range(2), api.chunk_lines(0))]
    fp = hashlib.sha1("\n".join(first).encode()).hexdigest()[:10]
    path = Path(state_dir) / f"{state['scenario']}-{fp}.db"
    store = Store(path)
    seen = store.get_kv("sim_seen")
    if seen and (state["sim_minute"] < seen["sim_minute"] or state["last_event_id"] < seen["last_event_id"]):
        store.db.close()
        stamp = time.strftime("%Y%m%d%H%M%S")
        path.rename(path.with_name(f"{path.name}.stale-{stamp}"))
        store = Store(path)
    return store, state


def pull_events(api, store):
    wm = store.get_kv("watermark", -1)
    chunks = []
    for kind in ("history", "events"):
        chunks += api.get("/events/chunks", params={"kind": kind, "after": wm})[1]
    totals = {"events": 0, "calls": 0, "supervisor_changes": 0}
    for ch in sorted(chunks, key=lambda c: c["chunk"]):
        counts = ingest_chunk(store, api.chunk_lines(ch["chunk"]), ch["chunk"])
        for k, v in counts.items():
            totals[k] += v
    return totals


def run(url: str, state_dir: str):
    api = Api(url)
    store, state = open_store(api, state_dir)
    log = Logger(store)
    gov = Governance(store, api, log)
    policy = Policy(store, api, gov, log)
    reconciled = store.get_kv("reconciled_world", False)
    print(f"scenario {state['scenario']} at {state['ts']}", file=sys.stderr)

    while True:
        t0 = time.time()
        state = api.get("/sim/state")[1]
        now = state["sim_minute"]
        log.now = now
        store.set_kv("credits_remaining", state["credits_remaining"])
        store.set_kv("sim_seen", {"sim_minute": now, "last_event_id": state["last_event_id"]})
        totals = pull_events(api, store)
        workflows = api.get("/workflows")[1]
        specs = {w["workflow_id"]: api.get(f"/workflows/{w['workflow_id']}")[1] for w in workflows}
        if not reconciled:
            for wid in specs:
                gov.reconcile(wid)
            store.set_kv("reconciled_world", True)
            reconciled = True
        decisions = 0
        for wid, wf in specs.items():
            try:
                gov.sync(wid, now)
                gov.apply_approved(wid, now)
            except Exception:
                log(wid, "controller_error", "sync failed", {"trace": traceback.format_exc()[-1500:]})
        for wid, wf in specs.items():
            before = store.one("SELECT COUNT(*) n FROM audit")["n"]
            try:
                policy.run(wid, wf, now)
            except Exception:
                log(wid, "controller_error", "policy step failed", {"trace": traceback.format_exc()[-1500:]})
            decisions += store.one("SELECT COUNT(*) n FROM audit")["n"] - before
        store.db.execute(
            "INSERT OR REPLACE INTO loop_health VALUES (?,?,?,?,?,?)",
            (now, round((time.time() - t0) * 1000, 1), totals["events"], decisions,
             state["credits_remaining"], store.get_kv("watermark", -1)))
        if state["finished"]:
            break
        api.post("/sim/advance", json={"minutes": STEP_MINUTES})
    log.now = state["sim_minute"]
    log("", "controller_finished", "scenario finished", {"credits_remaining": state["credits_remaining"]})
