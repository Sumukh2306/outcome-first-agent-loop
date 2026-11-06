import copy
import hashlib
import json

from . import stats

OPEN = ("intent", "pending", "approved", "applying")


def clean(cfg: dict) -> dict:
    out = copy.deepcopy(cfg)
    for dim, dist in out["allocations"]["default"].items():
        out["allocations"]["default"][dim] = stats.to_int(dist)
    return out


class Governance:
    def __init__(self, store, api, log):
        self.store = store
        self.api = api
        self.log = log

    def recent_requests(self, wid, now, window=1440):
        row = self.store.one(
            "SELECT COUNT(*) n FROM approvals WHERE workflow_id=? AND created_minute > ? AND status != 'api_error'"
            " AND kind != 'auto'", (wid, now - window))
        return row["n"]

    def open_for(self, wid):
        q = ",".join("?" * len(OPEN))
        return self.store.all(f"SELECT * FROM approvals WHERE workflow_id=? AND status IN ({q})", (wid, *OPEN))

    def make_pid(self, wid, now, body):
        digest = hashlib.sha1(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()[:10]
        return f"{wid}-m{now}-{digest}"

    def propose(self, *, wid, now, kind, base_version, proposed, dims, summary, rationale, diff,
                affected, dry_run, impact, incident_id=None, evidence=None):
        body = {"workflow_id": wid, "base_version": base_version, "proposed_config": clean(proposed),
                "change_summary": summary, "diff": diff, "affected_leads": int(affected), "dry_run": dry_run,
                "impact_score": round(float(impact), 4), "rationale": rationale}
        if evidence:
            body["evidence"] = evidence
        pid = self.make_pid(wid, now, body)
        body["proposal_id"] = pid
        with self.store.tx():
            self.store.db.execute(
                "INSERT INTO approvals (proposal_id, workflow_id, kind, status, base_version, body_json,"
                " dims_json, summary, incident_id, created_minute, updated_minute)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (pid, wid, kind, "intent", base_version, json.dumps(body), json.dumps(dims), summary,
                 incident_id, now, now))
        return self.submit(pid)

    def submit(self, pid):
        row = self.store.one("SELECT * FROM approvals WHERE proposal_id=?", (pid,))
        body = json.loads(row["body_json"])
        status, resp = self.api.post("/approvals", json=body)
        now = row["created_minute"]
        if status == 200:
            self._set(pid, "pending", approval_id=resp["approval_id"])
            self.log(row["workflow_id"], "approval_requested",
                     f"{row['kind']} proposal {resp['approval_id']}: {row['summary']}", {"proposal_id": pid,
                                                                                         "dims": json.loads(row["dims_json"])})
            return resp
        if status == 409 and isinstance(resp, dict) and resp.get("error") == "duplicate_proposal_id":
            found = next((a for a in self.api.get("/approvals", params={"workflow_id": row["workflow_id"]})[1]
                          if a["proposal_id"] == pid), None)
            if found:
                self._set(pid, found["status"], approval_id=found["approval_id"])
                return found
            self._set(pid, "api_error", reason="duplicate with no matching approval")
            return None
        if status == 409 and isinstance(resp, dict) and resp.get("error") == "stale_base_version":
            self._set(pid, "stale", reason=str(resp.get("detail")))
            self.log(row["workflow_id"], "proposal_stale", f"proposal {pid} built on an old config version",
                     {"proposal_id": pid, "detail": resp.get("detail")})
            return None
        self._set(pid, "api_error", reason=str(resp)[:500])
        self.log(row["workflow_id"], "proposal_error", f"proposal {pid} rejected by API ({status})",
                 {"proposal_id": pid, "response": resp})
        return None

    def _set(self, pid, status, **extra):
        cols = {"status": status}
        if "approval_id" in extra:
            cols["approval_id"] = extra["approval_id"]
        if "reason" in extra:
            cols["reasons_json"] = json.dumps([extra["reason"]])
        sets = ", ".join(f"{k}=?" for k in cols)
        self.store.db.execute(f"UPDATE approvals SET {sets} WHERE proposal_id=?", (*cols.values(), pid))

    def sync(self, wid, now):
        for row in self.open_for(wid):
            if row["status"] not in ("pending",) or not row["approval_id"]:
                continue
            status, a = self.api.get(f"/approvals/{row['approval_id']}")
            if status != 200:
                continue
            if a["status"] != "pending":
                with self.store.tx():
                    self.store.db.execute(
                        "UPDATE approvals SET status=?, reasons_json=?, decided_minute=?, updated_minute=?"
                        " WHERE proposal_id=?",
                        (a["status"], json.dumps(a.get("reasons", [])), now, now, row["proposal_id"]))
                self.log(wid, f"approval_{a['status']}",
                         f"{row['approval_id']} {a['status']}" + (f": {', '.join(a.get('reasons', []))}"
                                                                  if a.get("reasons") else ""),
                         {"approval_id": row["approval_id"], "reasons": a.get("reasons", [])})

    def apply_approved(self, wid, now):
        applied = []
        for row in self.store.all("SELECT * FROM approvals WHERE workflow_id=? AND status='approved'", (wid,)):
            self._set(row["proposal_id"], "applying")
            status, resp = self.api.post(f"/workflows/{wid}/apply", json={"approval_id": row["approval_id"]})
            if status == 200:
                self.store.db.execute("UPDATE approvals SET status='applied', applied_version=?, updated_minute=?"
                                      " WHERE proposal_id=?", (resp["version"], now, row["proposal_id"]))
                self.log(wid, "approval_applied", f"{row['approval_id']} applied as v{resp['version']}",
                         {"approval_id": row["approval_id"], "version": resp["version"]})
                applied.append(row)
            elif status == 410:
                self._set(row["proposal_id"], "lapsed", reason="apply window passed")
                self.log(wid, "approval_lapsed", f"{row['approval_id']} lapsed before apply", {})
            elif status == 409 and resp.get("error") == "stale_base_version":
                self._set(row["proposal_id"], "stale", reason=str(resp.get("detail")))
                self.log(wid, "proposal_stale", f"{row['approval_id']} went stale when applied", {})
            else:
                self._set(row["proposal_id"], "approved", reason=f"apply returned {status}")
                self.log(wid, "apply_error", f"{row['approval_id']} apply returned {status}",
                         {"response": resp})
        return applied

    def auto(self, *, wid, now, proposed, base_version, dims, rationale, summary, evidence=None):
        body = {"proposal_id": None, "base_version": base_version, "proposed_config": clean(proposed),
                "rationale": rationale}
        pid = self.make_pid(wid, now, body)
        body["proposal_id"] = pid
        with self.store.tx():
            self.store.db.execute(
                "INSERT INTO approvals (proposal_id, workflow_id, kind, status, base_version, body_json,"
                " dims_json, summary, created_minute, updated_minute) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (pid, wid, "auto", "auto_intent", base_version, json.dumps(body), json.dumps(dims), summary,
                 now, now))
        return self.put_auto(pid)

    def put_auto(self, pid):
        row = self.store.one("SELECT * FROM approvals WHERE proposal_id=?", (pid,))
        body = json.loads(row["body_json"])
        status, resp = self.api.put(f"/workflows/{row['workflow_id']}/config", json=body)
        wid = row["workflow_id"]
        if status == 200:
            self._set(pid, "auto_applied")
            self.store.db.execute("UPDATE approvals SET applied_version=? WHERE proposal_id=?",
                                  (resp["version"], pid))
            self.log(wid, "auto_applied", row["summary"], {"proposal_id": pid, "version": resp["version"],
                                                          "dims": json.loads(row["dims_json"])})
            return True
        if status == 409 and isinstance(resp, dict) and resp.get("error") == "duplicate_proposal_id":
            hist = self.api.get(f"/workflows/{wid}/config/history")[1]
            if any(h["proposal_id"] == pid for h in hist):
                self._set(pid, "auto_applied")
                return True
            self._set(pid, "api_error", reason="duplicate proposal id with no matching version")
            return False
        if status == 403:
            self._set(pid, "auto_rejected", reason=str(resp.get("detail")))
            self.log(wid, "auto_apply_rejected", row["summary"], {"proposal_id": pid, "problems": resp.get("detail")})
            return False
        if status == 409:
            self._set(pid, "stale", reason=str(resp.get("detail")))
            self.log(wid, "proposal_stale", f"auto-apply on stale base: {pid}", {"response": resp})
            return False
        self._set(pid, "api_error", reason=str(resp)[:500])
        self.log(wid, "apply_error", f"auto-apply {pid} returned {status}", {"response": resp})
        return False

    def reconcile(self, wid):
        hist = self.api.get(f"/workflows/{wid}/config/history")[1]
        by_pid = {h["proposal_id"]: h for h in hist if h.get("proposal_id")}
        by_aid = {h["approval_id"]: h for h in hist if h.get("approval_id")}
        for row in self.store.all("SELECT * FROM approvals WHERE workflow_id=? AND status IN"
                                  " ('applying','auto_intent')", (wid,)):
            if row["proposal_id"] in by_pid:
                self._set(row["proposal_id"], "auto_applied" if row["status"] == "auto_intent" else "applied")
            elif row["approval_id"] in by_aid:
                self._set(row["proposal_id"], "applied")
            elif row["status"] == "auto_intent":
                self.put_auto(row["proposal_id"])
            else:
                self._set(row["proposal_id"], "approved")
        for row in self.store.all("SELECT * FROM approvals WHERE workflow_id=? AND status='intent'", (wid,)):
            self.submit(row["proposal_id"])
