import math

import numpy as np


def two_prop_p(k1: int, n1: int, k2: int, n2: int) -> float:
    if n1 == 0 or n2 == 0:
        return 1.0
    p1, p2 = k1 / n1, k2 / n2
    pooled = (k1 + k2) / (n1 + n2)
    se = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    if se == 0:
        return 1.0
    z = (p1 - p2) / se
    return math.erfc(abs(z) / math.sqrt(2))


def holm(pvals: list[float]) -> list[float]:
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvals[i]))
        adj[i] = running
    return adj


def best_probabilities(succ: list[int], fail: list[int], seed: int, draws: int = 4000) -> list[float]:
    rng = np.random.default_rng(seed)
    a = np.asarray(succ, dtype=float) + 1
    b = np.asarray(fail, dtype=float) + 1
    samples = rng.beta(a, b, size=(draws, len(a)))
    winners = np.argmax(samples, axis=1)
    return [float((winners == i).mean()) for i in range(len(a))]


def tv(a: dict, b: dict) -> float:
    keys = sorted(set(a) | set(b))
    return 0.5 * sum(abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in keys)


SCALE = 10000


def to_int(w: dict) -> dict:
    total = sum(max(float(v), 0.0) for v in w.values())
    if total <= 0:
        raise ValueError("weights sum to zero")
    raw = {k: max(float(v), 0.0) * SCALE / total for k, v in w.items()}
    out = {k: int(math.floor(v)) for k, v in raw.items()}
    short = SCALE - sum(out.values())
    for k in sorted(raw, key=lambda k: raw[k] - out[k], reverse=True)[:short]:
        out[k] += 1
    return {k: v for k, v in out.items() if v > 0}


def shares(w: dict) -> dict:
    return {k: v / SCALE for k, v in to_int(w).items()}


def step_toward(cur: dict, target: dict, max_shift: float, margin: float = 0.002) -> dict:
    keys = sorted(set(cur) | set(target))
    cur_n = {k: cur.get(k, 0.0) for k in keys}
    tgt_n = {k: target.get(k, 0.0) for k in keys}
    d = tv(cur_n, tgt_n)
    if d <= max_shift - margin:
        return to_int(tgt_n)
    frac = (max_shift - margin) / d
    return to_int({k: cur_n[k] + frac * (tgt_n[k] - cur_n[k]) for k in keys})


def rate(num: int, den: int) -> float:
    return num / den if den else 0.0
