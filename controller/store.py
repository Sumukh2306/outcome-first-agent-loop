import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS leads (
    lead_id TEXT PRIMARY KEY, workflow_id TEXT NOT NULL, campaign_id TEXT NOT NULL,
    person_id TEXT NOT NULL, lang TEXT, city_tier TEXT, age_band TEXT, value_band TEXT,
    campaign_minute INTEGER NOT NULL, concluded INTEGER NOT NULL DEFAULT 0);
CREATE INDEX IF NOT EXISTS leads_wf ON leads (workflow_id, concluded);
CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id TEXT PRIMARY KEY, workflow_id TEXT NOT NULL, minute INTEGER NOT NULL, leads INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS call_agg (
    workflow_id TEXT NOT NULL, day INTEGER NOT NULL, hour INTEGER NOT NULL, prompt TEXT NOT NULL,
    welcome TEXT NOT NULL, voice TEXT NOT NULL, caller_id TEXT NOT NULL,
    dials INTEGER NOT NULL DEFAULT 0, connected INTEGER NOT NULL DEFAULT 0,
    engaged INTEGER NOT NULL DEFAULT 0, flagged INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (workflow_id, day, hour, prompt, welcome, voice, caller_id));
CREATE TABLE IF NOT EXISTS approvals (
    proposal_id TEXT PRIMARY KEY, approval_id TEXT, workflow_id TEXT NOT NULL, kind TEXT NOT NULL,
    status TEXT NOT NULL, base_version INTEGER NOT NULL, body_json TEXT NOT NULL,
    dims_json TEXT NOT NULL, summary TEXT, incident_id TEXT, created_minute INTEGER NOT NULL,
    decided_minute INTEGER, applied_version INTEGER, reasons_json TEXT, updated_minute INTEGER);
CREATE INDEX IF NOT EXISTS approvals_wf ON approvals (workflow_id, status);
CREATE TABLE IF NOT EXISTS audit (
    seq INTEGER PRIMARY KEY AUTOINCREMENT, sim_minute INTEGER NOT NULL, workflow_id TEXT,
    kind TEXT NOT NULL, summary TEXT NOT NULL, payload_json TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS audit_wf ON audit (workflow_id, sim_minute);
CREATE TABLE IF NOT EXISTS incidents (
    incident_id TEXT PRIMARY KEY, workflow_id TEXT NOT NULL, kind TEXT NOT NULL, subject TEXT,
    status TEXT NOT NULL, opened_minute INTEGER NOT NULL, resolved_minute INTEGER, detail_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS validations (
    validation_run_id TEXT PRIMARY KEY, workflow_id TEXT NOT NULL, prompt TEXT NOT NULL,
    n INTEGER NOT NULL, pass_rate REAL NOT NULL, minute INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS experiments (
    workflow_id TEXT NOT NULL, dim TEXT NOT NULL, state TEXT NOT NULL, winner TEXT,
    minute INTEGER NOT NULL, detail_json TEXT NOT NULL, PRIMARY KEY (workflow_id, dim));
CREATE TABLE IF NOT EXISTS loop_health (
    sim_minute INTEGER PRIMARY KEY, wall_ms REAL, events INTEGER, decisions INTEGER,
    credits_remaining REAL, watermark INTEGER);
"""


class Store:
    def __init__(self, path: str | Path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path), isolation_level=None, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript(SCHEMA)

    @contextmanager
    def tx(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield self.db
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        self.db.execute("COMMIT")

    def one(self, sql, args=()):
        row = self.db.execute(sql, args).fetchone()
        return dict(row) if row else None

    def all(self, sql, args=()):
        return [dict(r) for r in self.db.execute(sql, args).fetchall()]

    def get_kv(self, k, default=None):
        row = self.one("SELECT v FROM kv WHERE k=?", (k,))
        return json.loads(row["v"]) if row else default

    def set_kv(self, k, v):
        self.db.execute("INSERT INTO kv (k, v) VALUES (?, ?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",
                        (k, json.dumps(v)))

    def audit(self, minute, workflow_id, kind, summary, payload=None):
        self.db.execute(
            "INSERT INTO audit (sim_minute, workflow_id, kind, summary, payload_json) VALUES (?,?,?,?,?)",
            (minute, workflow_id, kind, summary, json.dumps(payload or {}, default=str)))
