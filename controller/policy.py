import copy
import hashlib
import json
from collections import defaultdict

from . import stats

MIN_ARM = 300
MIN_DID = 100
DID_RATIO = 0.65
HALLUC_FLOOR = 0.02
HALLUC_MARGIN = 0.015
HALLUC_MIN_CONNECTED = 200
HALLUC_MIN_VALIDATION = 0.97
GUARD_DROP = 0.02
EFFECT = 0.02
ALPHA = 0.05
EXPLORE_FLOOR = 0.1
WINNER_SHARE = 0.9
MATERIAL = 0.1
PROBE_SHARE = 0.05
DID_KNOWN_DIALS = 50
CALLER_ID_DIM = "caller_id"
EXPERIMENT_DIMS = ("welcome_message", "voice")
VALIDATION_N = 500
VALIDATION_COST = 5
SUGGEST_COST = 3
MIN_CREDITS_FOR_VALIDATION = 12
ENGAGE_TOLERANCE = 0.01
DID_EXCLUSION_MINUTES = 3 * 1440


def _h(minute):
    return minute // 60


class Policy:
    def __init__(self, store, api, gov, log):
        self.store = store
        self.api = api
        self.gov = gov
        self.log = log
        self.now_hour = 0

    def window(self, wid, now, hours):
        return self.store.all(
            "SELECT welcome, voice, caller_id, prompt, SUM(dials) d, SUM(connected) c, SUM(engaged) e,"
            " SUM(flagged) f FROM call_agg WHERE workflow_id=? AND day*24+hour >= ?"
            " GROUP BY welcome, voice, caller_id, prompt", (wid, _h(now) - hours))

    @staticmethod
    def marginal(rows, dim, prompt=None):
        tab = defaultdict(lambda: {"d": 0, "c": 0, "e": 0, "f": 0})
        key = {"welcome_message": "welcome", "voice": "voice", "caller_id": "caller_id"}[dim]
        for r in rows:
            if prompt is not None and r["prompt"] != prompt:
                continue
            t = tab[r[key]]
            for k in ("d", "c", "e", "f"):
                t[k] += r[k]
        return dict(tab)

    def recent_supervisor_dims(self, wid, now):
        dims = set()
        for row in self.store.all("SELECT payload_json FROM audit WHERE workflow_id=? AND kind='config_changed'"
                                  " AND sim_minute > ?", (wid, now - 1440)):
            p = json.loads(row["payload_json"])
            if p.get("actor") == "supervisor":
                dims.update(p.get("changed_dims", []))
        return dims

    def open_incidents(self, wid, kind=None):
        sql = "SELECT * FROM incidents WHERE workflow_id=? AND status != 'resolved'"
        args = [wid]
        if kind:
            sql += " AND kind=?"
            args.append(kind)
        return [dict(r, detail=json.loads(r["detail_json"])) for r in self.store.all(sql, args)]

    def set_incident(self, inc_id, **fields):
        detail = fields.pop("detail", None)
        if detail is not None:
            fields["detail_json"] = json.dumps(detail, default=str)
        sets = ", ".join(f"{k}=?" for k in fields)
        self.store.db.execute(f"UPDATE incidents SET {sets} WHERE incident_id=?", (*fields.values(), inc_id))

    def open_incident(self, wid, kind, subject, now, detail):
        digest = hashlib.sha1(f"{wid}{kind}{subject}{now}".encode()).hexdigest()[:8]
        inc_id = f"inc-{wid}-{kind}-{digest}"
        self.store.db.execute(
            "INSERT INTO incidents (incident_id, workflow_id, kind, subject, status, opened_minute, detail_json)"
            " VALUES (?,?,?,?,?,?,?)", (inc_id, wid, kind, subject, "open", now, json.dumps(detail, default=str)))
        self.log(wid, "incident_opened", f"{kind} incident on {subject}", {"incident_id": inc_id, **detail})
        return inc_id

    def resolve(self, inc_id, wid, now, note):
        inc = self.store.one("SELECT * FROM incidents WHERE incident_id=?", (inc_id,))
        self.store.db.execute("UPDATE incidents SET status='resolved', resolved_minute=? WHERE incident_id=?",
                              (now, inc_id))
        self.log(wid, "incident_resolved", f"{inc['kind']} on {inc['subject']} resolved: {note}",
                 {"incident_id": inc_id, "time_to_fix_minutes": now - inc["opened_minute"]})

    def run(self, wid, wf, now):
        self.now_hour = now // 60
        cur_rec = self.api.get(f"/workflows/{wid}/config")[1]
        cur = cur_rec["config"]
        version = cur_rec["version"]
        gov_spec = wf["governance"]
        lo, hi = gov_spec["approver_hours"]
        hour = (now % 1440) // 60
        in_hours = lo <= hour < hi
        first_slot = (now % 1440) == lo * 60
        pending = [r for r in self.gov.open_for(wid)]
        pending_dims = set()
        for r in pending:
            pending_dims.update(json.loads(r["dims_json"]))

        self.did_health(wid, wf, now, cur)
        requests = self.hallucination(wid, wf, now, cur, version, in_hours)
        requests.append(self.caller_id_actions(wid, wf, now, cur, version, pending_dims))
        if wf["objective"]["primary"] == "engagement_rate":
            requests += self.experiments(wid, wf, now, cur, version, first_slot)
        requests = [r for r in requests if r]
        if not requests or not in_hours:
            return
        if pending:
            self.log(wid, "deferred", "approval already pending, requests held",
                     {"pending": [p["proposal_id"] for p in pending], "requests": [r["summary"] for r in requests]})
            return
        cap = gov_spec["max_requests_per_24h"]
        used = self.gov.recent_requests(wid, now)
        urgent = [r for r in requests if r["kind"] == "incident"]
        if used >= cap or (used >= cap - 1 and not urgent):
            self.log(wid, "deferred", f"approver request budget used ({used}/{cap} in 24h)",
                     {"requests": [r["summary"] for r in requests]})
            return
        merged = self.merge(requests, wid, wf, cur)
        if merged is None:
            return
        self.gov.propose(wid=wid, now=now, base_version=version, **merged)

    def merge(self, requests, wid, wf, cur):
        proposed = copy.deepcopy(cur)
        dims, summaries, rationales, diffs, dry, evidence, kind, incident_ids = [], [], [], {}, {}, None, \
            "experiment", []
        impact = 0.0
        for r in requests:
            if r["kind"] == "incident":
                kind = "incident"
            if r.get("incident_id"):
                incident_ids.append(r["incident_id"])
            if r.get("prompt"):
                proposed["prompt_version"] = r["prompt"]
                evidence = r.get("evidence")
            for dim, dist in r.get("dists", {}).items():
                proposed["allocations"]["default"][dim] = dist
                dims.append(dim)
            summaries.append(r["summary"])
            rationales.append(r["rationale"])
            diffs.update(r.get("diff", {}))
            dry.update(r.get("dry_run", {}))
            impact = max(impact, r["impact"])
        if evidence:
            dims.append("prompt_version")
        dims = sorted(set(dims))
        if not dims:
            return None
        affected = self.active_leads(wid)
        return {"kind": kind, "proposed": proposed, "dims": dims, "summary": "; ".join(summaries),
                "rationale": " ".join(rationales), "diff": diffs, "affected": affected,
                "dry_run": dry or {"note": "no replay"}, "impact": impact,
                "incident_id": incident_ids[0] if incident_ids else None, "evidence": evidence}

    def active_leads(self, wid):
        row = self.store.one("SELECT COUNT(*) n FROM leads WHERE workflow_id=? AND concluded=0", (wid,))
        return row["n"]

    def hallucination(self, wid, wf, now, cur, version, in_hours):
        prompt = cur["prompt_version"]
        inc_list = self.open_incidents(wid, "hallucination")
        recent = self.window(wid, now, 6)
        c = sum(r["c"] for r in recent if r["prompt"] == prompt)
        f = sum(r["f"] for r in recent if r["prompt"] == prompt)
        base = self.history_rate(wid, prompt)
        if not inc_list:
            if c >= HALLUC_MIN_CONNECTED and f / c >= max(HALLUC_FLOOR, base + HALLUC_MARGIN):
                detail = {"prompt": prompt, "rate_6h": round(f / c, 4), "connected_6h": c,
                          "baseline_rate": round(base, 4), "stage": "open", "tried": [], "suggestions": [],
                          "validations": []}
                self.open_incident(wid, "hallucination", prompt, now, detail)
            return []
        inc = inc_list[0]
        d = inc["detail"]
        if inc["status"] == "mitigating":
            return self.verify_mitigation(wid, inc, now, cur, prompt, c, f, d)
        if d["stage"] == "open":
            cur_prompt = prompt
            status, body = self.api.post("/llm/suggest-fixes", json={"workflow_id": wid,
                                                                    "problem": f"hallucination rate {d['rate_6h']} on {prompt}"})
            d["suggestions"] = body.get("suggestions", []) if status == 200 else []
            d["stage"] = "suggested"
            self.set_incident(inc["incident_id"], detail=d)
            self.log(wid, "llm_suggestions", f"{len(d['suggestions'])} fix candidates for {cur_prompt}",
                     {"suggestions": d["suggestions"], "status": status})
            return []
        if d["stage"] == "suggested":
            ref = self.prompt_stats(wid, prompt, 24)
            cands = []
            for s in d["suggestions"]:
                if s["prompt_version"] not in cands and s["prompt_version"] != prompt:
                    cands.append(s["prompt_version"])
            known_good = self.known_good_prompt(wid, prompt)
            if known_good and known_good not in cands:
                cands.insert(0, known_good)
            cands = [p for p in cands if p not in d["tried"]]
            measured = []
            for p in cands:
                st = self.prompt_stats(wid, p, None)
                if st["c"] < HALLUC_MIN_CONNECTED:
                    d.setdefault("skipped_unmeasured", []).append(p)
                    continue
                if ref["c"] and st["e"] < ref["e"] - ENGAGE_TOLERANCE:
                    d.setdefault("skipped_regression", []).append(p)
                    continue
                measured.append((p, st))
            passing = []
            for p, st in measured:
                if self.budget_for_validation() is False:
                    break
                status, run = self.api.post("/validation/runs", json={"workflow_id": wid, "prompt_version": p,
                                                                      "n": VALIDATION_N})
                if status != 200:
                    continue
                self.store.db.execute("INSERT OR REPLACE INTO validations VALUES (?,?,?,?,?,?)",
                                      (run["validation_run_id"], wid, p, run["n"], run["pass_rate"], now))
                d["validations"].append({"prompt": p, "validation_run_id": run["validation_run_id"],
                                         "pass_rate": run["pass_rate"], "engage_rate": round(st["e"], 4)})
                if run["pass_rate"] >= HALLUC_MIN_VALIDATION:
                    passing.append((st["e"], p, run["validation_run_id"], run["pass_rate"]))
            if not passing:
                d["stage"] = "no_candidate"
                self.set_incident(inc["incident_id"], detail=d)
                self.log(wid, "incident_stuck", "no measured, validated fix candidate yet",
                         {"validations": d["validations"], "skipped_unmeasured": d.get("skipped_unmeasured", []),
                          "skipped_regression": d.get("skipped_regression", [])})
                return []
            _, p, vid, pr = max(passing)
            d["chosen"] = {"prompt": p, "validation_run_id": vid, "pass_rate": pr}
            d["stage"] = "proposed"
            self.set_incident(inc["incident_id"], detail=d)
            return [self.prompt_request(wid, inc, p, vid, pr, prompt, now)]
        if d["stage"] == "proposed":
            ch = d["chosen"]
            row = self.store.one("SELECT status FROM approvals WHERE incident_id=? ORDER BY created_minute DESC",
                                 (inc["incident_id"],))
            if row and row["status"] in ("applied",):
                d["stage"] = "mitigating"
                d["applied_minute"] = now
                self.set_incident(inc["incident_id"], status="mitigating", detail=d)
                self.log(wid, "incident_mitigating", f"prompt {ch['prompt']} applied, verifying",
                         {"incident_id": inc["incident_id"]})
                return []
            if row and row["status"] in ("rejected", "expired", "lapsed", "stale", "api_error"):
                d["tried"].append(ch["prompt"])
                d["stage"] = "suggested"
                self.set_incident(inc["incident_id"], detail=d)
            return []
        if d["stage"] == "no_candidate" and in_hours:
            d["stage"] = "suggested"
            d["tried"] = []
            self.set_incident(inc["incident_id"], detail=d)
        return []

    def verify_mitigation(self, wid, inc, now, cur, prompt, c, f, d):
        if now - d["applied_minute"] < 180:
            return []
        recent = [r for r in self.window(wid, now, 3) if r["prompt"] == prompt]
        cc = sum(r["c"] for r in recent)
        ff = sum(r["f"] for r in recent)
        if cc >= 150 and ff / cc <= HALLUC_FLOOR:
            self.resolve(inc["incident_id"], wid, now, f"{prompt} flagged rate {ff / cc:.3f} after applied fix")
            return []
        if now - d["applied_minute"] >= 720:
            d["stage"] = "open"
            d["tried"] = []
            self.set_incident(inc["incident_id"], status="open", detail=d)
            self.log(wid, "incident_reopened", "mitigation did not hold, reopening", {"prompt": prompt})
        return []

    def budget_for_validation(self):
        row = self.store.one("SELECT v FROM kv WHERE k='credits_remaining'")
        if row is None:
            return True
        return float(json.loads(row["v"])) >= MIN_CREDITS_FOR_VALIDATION

    def prompt_request(self, wid, inc, prompt, vid, pr, old, now):
        d = inc["detail"]
        return {"kind": "incident", "prompt": prompt, "evidence": {"validation_run_id": vid},
                "summary": f"switch prompt {old} to {prompt} (hallucination incident)",
                "rationale": (f"{old} flagged {d['rate_6h']:.3f} of connected calls in the last 6h against a baseline"
                              f" of {d['baseline_rate']:.3f}. {prompt} passed validation at {pr:.3f} on {VALIDATION_N}"
                              " synthetic conversations."),
                "diff": {"prompt_version": {"from": old, "to": prompt}},
                "dry_run": {"method": "validation run on synthetic conversations", "validation_run_id": vid,
                            "pass_rate": pr, "n": VALIDATION_N, "observed_flag_rate_before": d["rate_6h"]},
                "impact": min(1.0, d["rate_6h"] / 0.05), "incident_id": inc["incident_id"], "dists": {}}

    def history_rate(self, wid, prompt):
        row = self.store.one("SELECT SUM(connected) c, SUM(flagged) f FROM call_agg WHERE workflow_id=? AND day < 0"
                             " AND prompt=?", (wid, prompt))
        if not row or not row["c"] or row["c"] < HALLUC_MIN_CONNECTED:
            return 0.01
        return row["f"] / row["c"]

    def prompt_stats(self, wid, prompt, hours):
        if hours is None:
            row = self.store.one("SELECT SUM(connected) c, SUM(engaged) e, SUM(flagged) f FROM call_agg"
                                 " WHERE workflow_id=? AND prompt=?", (wid, prompt))
        else:
            row = self.store.one("SELECT SUM(connected) c, SUM(engaged) e, SUM(flagged) f FROM call_agg"
                                 " WHERE workflow_id=? AND prompt=? AND day*24+hour >= ?",
                                 (wid, prompt, self.now_hour - hours))
        c = row["c"] or 0
        return {"c": c, "e": (row["e"] or 0) / c if c else 0.0}

    def known_good_prompt(self, wid, prompt):
        rows = self.store.all("SELECT prompt, SUM(connected) c, SUM(flagged) f FROM call_agg WHERE workflow_id=?"
                              " GROUP BY prompt", (wid,))
        ok = [r for r in rows if r["prompt"] != prompt and r["c"] >= HALLUC_MIN_CONNECTED]
        if not ok:
            return None
        return min(ok, key=lambda r: r["f"] / r["c"])["prompt"]

    def did_health(self, wid, wf, now, cur):
        rows = self.window(wid, now, 24)
        tab = self.marginal(rows, CALLER_ID_DIM)
        qual = {k: v for k, v in tab.items() if v["d"] >= MIN_DID}
        open_inc = {i["subject"]: i for i in self.open_incidents(wid, "did_flagged")}
        excluded = self.excluded_dids(wid, now)
        live = cur["allocations"]["default"][CALLER_ID_DIM]
        for did, t in qual.items():
            if did in open_inc or did in excluded or live.get(did, 0) <= 0:
                continue
            peers = [v for k, v in qual.items() if k != did]
            if not peers:
                continue
            med = sum(v["c"] for v in peers) / sum(v["d"] for v in peers)
            if med > 0 and (t["c"] / t["d"]) / med <= DID_RATIO:
                self.open_incident(wid, "did_flagged", did, now,
                                   {"pickup_rate_24h": round(t["c"] / t["d"], 4),
                                    "peer_median_pickup": round(med, 4), "dials_24h": t["d"]})
        for did, inc in open_inc.items():
            if live.get(did, 0) == 0:
                self.resolve(inc["incident_id"], wid, now, f"{did} is out of rotation")

    def excluded_dids(self, wid, now):
        rows = self.store.all("SELECT DISTINCT subject FROM incidents WHERE workflow_id=? AND kind='did_flagged'"
                              " AND opened_minute > ?", (wid, now - DID_EXCLUSION_MINUTES))
        return {r["subject"] for r in rows}

    def caller_target(self, wid, wf, now, healthy):
        tab = self.marginal(self.window(wid, now, 24), CALLER_ID_DIM)
        known = [o for o in healthy if tab.get(o, {"d": 0})["d"] >= DID_KNOWN_DIALS]
        unknown = [o for o in healthy if o not in known]
        if not known:
            return None
        spare = 1.0 - PROBE_SHARE * len(unknown)
        target = {o: spare / len(known) for o in known}
        target.update({o: PROBE_SHARE for o in unknown})
        return target

    def caller_id_actions(self, wid, wf, now, cur, version, pending_dims):
        opts = wf["options"][CALLER_ID_DIM]
        flagged = self.excluded_dids(wid, now)
        healthy = [o for o in opts if o not in flagged]
        if not healthy or CALLER_ID_DIM in pending_dims:
            return None
        cur_dist = cur["allocations"]["default"][CALLER_ID_DIM]
        target = self.caller_target(wid, wf, now, healthy)
        if target is None:
            return None
        urgent = bool(set(cur_dist) & flagged)
        if stats.tv(cur_dist, target) < MATERIAL / 2 and not urgent:
            return None
        tab = self.marginal(self.window(wid, now, 24), CALLER_ID_DIM)
        other = "eng" if wf["objective"]["primary"] == "pickup_rate" else "pick"
        guard_change = self.predict(tab, cur_dist, target, other)
        if guard_change < -GUARD_DROP and not urgent:
            self.log(wid, "guardrail_blocked", f"caller_id move blocked: predicted {other} change {guard_change:+.3f}",
                     {"target": target, "predicted": guard_change})
            return None
        auto = wf["governance"]["auto_apply"]
        if auto["enabled"] and CALLER_ID_DIM in auto["allowed_dims"]:
            today_auto = self.store.one(
                "SELECT COUNT(*) n FROM approvals WHERE workflow_id=? AND kind='auto' AND status='auto_applied'"
                " AND created_minute > ?", (wid, now - 1440))["n"]
            if urgent or today_auto == 0:
                step = stats.step_toward(cur_dist, target, auto["max_shift"])
                proposed = copy.deepcopy(cur)
                proposed["allocations"]["default"][CALLER_ID_DIM] = step
                note = ("a flagged DID is being removed from rotation" if urgent
                        else "rebalancing caller IDs across healthy DIDs")
                self.gov.auto(wid=wid, now=now, proposed=proposed, base_version=version,
                              dims=[CALLER_ID_DIM], rationale=f"{note}; target {target}",
                              summary=f"caller_id step to {step}")
                return None
        if not urgent and self.gov.recent_requests(wid, now) >= wf["governance"]["max_requests_per_24h"] - 1:
            return None
        pred = self.predict(tab, cur_dist, target, "pick" if other == "eng" else "eng")
        return {"kind": "incident" if urgent else "experiment", "dists": {CALLER_ID_DIM: target},
                "diff": {f"allocations.default.{CALLER_ID_DIM}": target},
                "dry_run": {CALLER_ID_DIM: {"target": target, "predicted_pickup_rel_change": pred,
                                            "method": "reweight 24h per-DID pickup by target shares"}},
                "summary": f"caller_id to {', '.join(f'{k} {v:.2f}' for k, v in sorted(target.items()))}"
                           + (" (flagged DID removed)" if urgent else ""),
                "rationale": "per-DID pickup over 24h; a DID with at least 100 dials and pickup 35% below its"
                             " peers is removed; remaining healthy DIDs share traffic evenly.",
                "impact": min(1.0, abs(pred) / 0.10) if pred else 0.05, "incident_id": None}

    def experiments(self, wid, wf, now, cur, version, first_slot):
        prompt = cur["prompt_version"]
        if not first_slot:
            return []
        if self.gov.recent_requests(wid, now) >= wf["governance"]["max_requests_per_24h"] - 1:
            return []
        last_rejected = self.store.one(
            "SELECT created_minute FROM approvals WHERE workflow_id=? AND kind='experiment' AND status IN"
            " ('rejected','expired','lapsed') ORDER BY created_minute DESC LIMIT 1", (wid,))
        if last_rejected and now - last_rejected["created_minute"] < 1440:
            return []
        held = self.recent_supervisor_dims(wid, now)
        rows = self.window(wid, now, 48)
        rows24 = self.window(wid, now, 24)
        out = []
        dists, notes, diffs, dry = {}, [], {}, {}
        gap = {}
        for dim in EXPERIMENT_DIMS:
            if dim in held:
                notes.append(f"{dim} held: supervisor changed it within 24h")
                continue
            tab = self.marginal(rows, dim, prompt)
            arms = wf["options"][dim]
            target, winner, detail = self.experiment_target(wid, dim, arms, tab, now, wf["governance"])
            prev = self.store.one("SELECT winner, state FROM experiments WHERE workflow_id=? AND dim=?", (wid, dim))
            if prev and prev["winner"]:
                if self.winner_decayed(prev["winner"], dim, arms, self.marginal(rows24, dim, prompt)):
                    self.log(wid, "winner_decayed",
                             f"{dim} {prev['winner']} stopped winning in the last 24h, back to exploration",
                             {"dim": dim, "winner": prev["winner"]})
                    winner = None
                    target = {a: 1.0 / len(arms) for a in arms}
            self.store.db.execute("INSERT OR REPLACE INTO experiments VALUES (?,?,?,?,?,?)",
                                  (wid, dim, "exploit" if winner else "explore", winner, now,
                                   json.dumps(detail, default=str)))
            cur_dist = cur["allocations"]["default"].get(dim, {})
            if stats.tv(cur_dist, target) < MATERIAL:
                continue
            dists[dim] = target
            diffs[f"allocations.default.{dim}"] = target
            pred = self.predict(tab, cur_dist, target)
            dry[dim] = {"arm_rates": detail["rates"], "predicted_engagement_rel_change": pred,
                        "replay_window_hours": 48, "method": "reweight 48h connected-call arm rates by proposed shares"}
            notes.append(f"{dim}: {detail['mode']}" + (f" winner {winner}" if winner else ""))
            gap[dim] = pred
        if not dists:
            return []
        pred_total = max(gap.values(), key=abs) if gap else 0.0
        return [{"kind": "experiment", "dists": dists, "diff": diffs, "dry_run": dry,
                 "summary": "; ".join(notes), "rationale": "; ".join(notes) + ". Shares use 48h of connected calls"
                 " for this prompt. Winners need Holm-adjusted p<0.05 and at least 2pp lift; otherwise Thompson"
                 f" sampling with a {int(EXPLORE_FLOOR * 100)}% exploration floor. Pickup guardrail excludes arms more than 2pp below the"
                 " workflow's pickup.",
                 "impact": min(1.0, abs(pred_total) / 0.10), "incident_id": None}]

    def experiment_target(self, wid, dim, arms, tab, now, gov):
        k = len(arms)
        overall_c = sum(tab.get(a, {"c": 0})["c"] for a in arms)
        overall_d = sum(tab.get(a, {"d": 0})["d"] for a in arms)
        pick = overall_c / overall_d if overall_d else 0.0
        rates = {}
        ok = {}
        for a in arms:
            t = tab.get(a, {"d": 0, "c": 0, "e": 0})
            rates[a] = round(t["e"] / t["c"], 4) if t["c"] else None
            ok[a] = (t["c"] / t["d"] >= pick - GUARD_DROP) if t["d"] else True
        qual = [a for a in arms if tab.get(a, {"c": 0})["c"] >= MIN_ARM]
        detail = {"arms": {a: tab.get(a, {"d": 0, "c": 0, "e": 0}) for a in arms}, "rates": rates,
                  "pickup_guardrail_ok": ok, "pickup": round(pick, 4)}
        winner = None
        if len(qual) >= 2:
            best = max(qual, key=lambda a: tab[a]["e"] / tab[a]["c"])
            others = [a for a in qual if a != best]
            pb = tab[best]
            pvals = [stats.two_prop_p(pb["e"], pb["c"], tab[o]["e"], tab[o]["c"]) for o in others]
            adj = stats.holm(pvals)
            lift_ok = all(pb["e"] / pb["c"] - tab[o]["e"] / tab[o]["c"] >= EFFECT for o in others)
            if all(p < ALPHA for p in adj) and lift_ok and ok.get(best, True):
                winner = best
        if winner:
            others = [a for a in arms if a != winner]
            target = {winner: WINNER_SHARE}
            for o in others:
                target[o] = (1 - WINNER_SHARE) / len(others)
            detail["mode"] = "exploit"
            return target, winner, detail
        ids = [a for a in arms]
        succ = [tab.get(a, {"e": 0})["e"] for a in ids]
        fail = [tab.get(a, {"c": 0, "e": 0})["c"] - tab.get(a, {"e": 0})["e"] for a in ids]
        seed = int(hashlib.sha1(f"{wid}{dim}{now // 1440}".encode()).hexdigest()[:8], 16)
        pbest = stats.best_probabilities(succ, fail, seed)
        raw = {a: EXPLORE_FLOOR / k + (1 - EXPLORE_FLOOR) * p for a, p in zip(ids, pbest)}
        for a in arms:
            if not ok[a] and any(ok.values()):
                raw[a] = 0.0
        detail["mode"] = "explore"
        detail["thompson_best_probability"] = {a: round(p, 3) for a, p in zip(ids, pbest)}
        return stats.shares(raw), None, detail

    def winner_decayed(self, winner, dim, arms, tab24):
        w = tab24.get(winner)
        others = [a for a in arms if a != winner]
        oc = sum(tab24.get(a, {"c": 0})["c"] for a in others)
        oe = sum(tab24.get(a, {"e": 0})["e"] for a in others)
        if not w or w["c"] < MIN_ARM or oc < 100:
            return False
        return w["e"] / w["c"] < oe / oc - EFFECT

    def predict(self, tab, old, new, metric="eng"):
        def rate(t):
            if metric == "eng":
                return t["e"] / t["c"] if t["c"] else None
            return t["c"] / t["d"] if t["d"] else None
        rates = {a: rate(t) for a, t in tab.items() if rate(t) is not None}
        if not rates:
            return 0.0
        num = sum(t["e"] if metric == "eng" else t["c"] for t in tab.values())
        den = sum(t["c"] if metric == "eng" else t["d"] for t in tab.values())
        pooled = num / den if den else 0.0
        r = {a: rates.get(a, pooled) for a in sorted(set(old) | set(new))}
        base = sum(old.get(a, 0) * r[a] for a in r)
        after = sum(new.get(a, 0) * r[a] for a in r)
        return round(after / base - 1, 5) if base else 0.0
