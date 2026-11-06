import json

from controller import stats
from controller.ingest import ingest_chunk, minute_of
from controller.store import Store


def test_holm_is_monotone_and_capped():
    adj = stats.holm([0.01, 0.04, 0.03])
    assert adj == [0.03, 0.06, 0.06]
    assert all(a <= 1.0 for a in stats.holm([0.9, 0.95]))


def test_two_prop_detects_real_gap_and_ignores_noise():
    assert stats.two_prop_p(600, 1000, 500, 1000) < 0.001
    assert stats.two_prop_p(505, 1000, 500, 1000) > 0.5


def test_to_int_sums_to_scale_and_round_trips():
    for w in ({"a": 1, "b": 1, "c": 1}, {"a": 0.2, "b": 0.3, "c": 0.25, "d": 0.25}, {"a": 0.9, "b": 0.1}):
        ints = stats.to_int(w)
        assert sum(ints.values()) == stats.SCALE
        back = {k: v / stats.SCALE for k, v in ints.items()}
        assert stats.to_int(back) == ints


def test_step_toward_respects_max_shift():
    cur = {"D1": 0.5, "D2": 0.5}
    target = {"D1": 0.5, "D3": 0.5}
    step = stats.step_toward(cur, target, 0.2)
    shares = {k: v / stats.SCALE for k, v in step.items()}
    assert stats.tv(cur, shares) <= 0.2
    assert shares["D3"] > 0


def test_step_toward_reaches_target_when_close():
    step = stats.step_toward({"a": 0.5, "b": 0.5}, {"a": 0.6, "b": 0.4}, 0.5)
    assert step == {"a": 6000, "b": 4000}


def test_best_probabilities_prefers_better_arm_and_is_seeded():
    p1 = stats.best_probabilities([600, 500], [400, 500], seed=3)
    p2 = stats.best_probabilities([600, 500], [400, 500], seed=3)
    assert p1 == p2
    assert p1[0] > 0.99


def call_line(event_id, lead="w:l1", engaged=True, qa=None):
    return json.dumps({
        "type": "call", "ts": "2027-01-04T10:15:00+05:30", "workflow_id": "w", "lead_id": lead,
        "variant": {"welcome_message": "W1", "voice": "V1", "caller_id": "D1", "prompt_version": "P1"},
        "connected": True, "engaged": engaged, "qa": qa, "event_id": event_id})


def test_ingest_counts_and_tolerates_missing_qa(tmp_path):
    store = Store(tmp_path / "s.db")
    lines = [json.dumps({"type": "lead", "ts": "2027-01-04T08:00:00+05:30", "workflow_id": "w", "campaign_id": "c",
                         "lead_id": "w:l1", "person_id": "w:p1", "features": {"lang": "hi"}, "event_id": 1}),
             call_line(2, qa=None), call_line(3, qa={"hallucination_flag": True}, engaged=False)]
    ingest_chunk(store, lines, 0)
    row = store.one("SELECT SUM(dials) d, SUM(connected) c, SUM(engaged) e, SUM(flagged) f FROM call_agg")
    assert (row["d"], row["c"], row["e"], row["f"]) == (2, 2, 1, 1)
    assert store.one("SELECT concluded FROM leads")["concluded"] == 1
    assert store.get_kv("watermark") == 0


def test_failed_chunk_rolls_back_watermark(tmp_path):
    store = Store(tmp_path / "s.db")
    bad = [call_line(1), "{not json"]
    try:
        ingest_chunk(store, bad, 5)
    except ValueError:
        pass
    assert store.get_kv("watermark") is None
    assert store.one("SELECT COUNT(*) n FROM call_agg")["n"] == 0


def test_minute_of_handles_history_and_live():
    assert minute_of("2027-01-04T00:00:00+05:30") == 0
    assert minute_of("2027-01-03T23:45:00+05:30") == -15
    assert minute_of("2027-01-05T10:00:00+05:30") == 1440 + 600
