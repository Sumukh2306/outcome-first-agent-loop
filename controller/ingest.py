import json
from datetime import datetime

D0 = datetime.fromisoformat("2027-01-04T00:00:00+05:30")


def minute_of(ts: str) -> int:
    return int((datetime.fromisoformat(ts) - D0).total_seconds() // 60)


def local_hour(ts: str) -> int:
    return datetime.fromisoformat(ts).hour


def ingest_chunk(store, lines, chunk_no: int) -> dict:
    counts = {"events": 0, "calls": 0, "supervisor_changes": 0}
    db = store.db
    with store.tx():
        for line in lines:
            if not line.strip():
                continue
            ev = json.loads(line)
            counts["events"] += 1
            kind = ev["type"]
            if kind == "campaign_created":
                db.execute("INSERT OR IGNORE INTO campaigns VALUES (?,?,?,?)",
                           (ev["campaign_id"], ev["workflow_id"], minute_of(ev["ts"]), ev["leads"]))
            elif kind == "lead":
                f = ev["features"]
                db.execute(
                    "INSERT OR IGNORE INTO leads (lead_id, workflow_id, campaign_id, person_id, lang, city_tier,"
                    " age_band, value_band, campaign_minute) VALUES (?,?,?,?,?,?,?,?,?)",
                    (ev["lead_id"], ev["workflow_id"], ev["campaign_id"], ev["person_id"], f.get("lang"),
                     f.get("city_tier"), f.get("age_band"), f.get("value_band"), minute_of(ev["ts"])))
            elif kind == "call":
                counts["calls"] += 1
                _call(store, ev)
            elif kind == "config_changed":
                actor = ev["actor"]
                if actor == "supervisor":
                    counts["supervisor_changes"] += 1
                store.audit(minute_of(ev["ts"]), ev["workflow_id"], "config_changed",
                            f"config v{ev['version']} by {actor}: {', '.join(ev['changed_dims']) or 'no dims'}",
                            ev)
            elif kind == "approval_decided":
                db.execute(
                    "UPDATE approvals SET status=?, reasons_json=?, decided_minute=COALESCE(decided_minute, ?),"
                    " updated_minute=? WHERE approval_id=? AND status IN ('submitted','pending')",
                    (ev["status"], json.dumps(ev.get("reasons", [])), minute_of(ev["ts"]),
                     minute_of(ev["ts"]), ev["approval_id"]))
        store.set_kv("watermark", chunk_no)
    return counts


def _call(store, ev):
    v = ev["variant"]
    minute = minute_of(ev["ts"])
    day = minute // 1440
    flagged = 1 if (ev.get("qa") or {}).get("hallucination_flag") else 0
    store.db.execute(
        "INSERT INTO call_agg (workflow_id, day, hour, prompt, welcome, voice, caller_id, dials, connected,"
        " engaged, flagged) VALUES (?,?,?,?,?,?,?,1,?,?,?)"
        " ON CONFLICT (workflow_id, day, hour, prompt, welcome, voice, caller_id) DO UPDATE SET"
        " dials = dials + 1, connected = connected + excluded.connected,"
        " engaged = engaged + excluded.engaged, flagged = flagged + excluded.flagged",
        (ev["workflow_id"], day, local_hour(ev["ts"]), v["prompt_version"], v["welcome_message"], v["voice"],
         v["caller_id"], int(ev["connected"]), int(ev["engaged"]), flagged))
    if ev["engaged"]:
        store.db.execute("UPDATE leads SET concluded=1 WHERE lead_id=?", (ev["lead_id"],))
