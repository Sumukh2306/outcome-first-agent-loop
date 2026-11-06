# Grade report — public_02_incidents

## Outcomes vs baseline (no-op controller)

| workflow | conclusion rate | Δ | pickup | Δ | engagement | Δ | engagement gap captured | hallucinated calls (base) |
|---|---|---|---|---|---|---|---|---|
| ks_cancel | 0.355 | +50.7% | 0.250 | +37.8% | 0.489 | +4.5% | 29% | 91 (348) |
| nw_kyc | 0.463 | +23.8% | 0.289 | +23.2% | 0.601 | -1.3% | 0% | 36 (29) |
| nw_renewal | 0.489 | +13.0% | 0.288 | +9.8% | 0.566 | +2.0% | 13% | 77 (54) |
| ALL | 0.423 | +27.8% | 0.270 | +23.2% | 0.540 | +1.4% | 19% | 204 (431) |

## Changes applied by the controller

18 applied — neutral: 6, beneficial: 11, harmful: 1

- nw_renewal v2 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.018 → **neutral**
- ks_cancel v2 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.009 → **neutral**
- ks_cancel v3 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.043 → **beneficial**
- nw_renewal v3 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.060 → **beneficial**
- nw_kyc v2 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.050 → **beneficial**
- nw_renewal v4 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.012 → **neutral**
- nw_renewal v5 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.000 → **neutral**
- ks_cancel v4 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.168 → **beneficial**
- ks_cancel v5 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.061 → **beneficial**
- nw_kyc v3 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.383 → **beneficial**
- ks_cancel v6 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.034 → **beneficial**
- ks_cancel v8 (controller_approved) dims=['prompt_version'] engageΔ=+0.102 didΔ=+0.000 → **beneficial**
- nw_kyc v4 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.005 → **neutral**
- nw_kyc v5 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.013 → **neutral**
- ks_cancel v9 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.030 → **harmful**
- nw_renewal v7 (controller_approved) dims=['welcome_message'] engageΔ=+0.062 didΔ=+0.000 → **beneficial**
- ks_cancel v10 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.031 → **beneficial**
- nw_renewal v8 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.037 didΔ=+0.000 → **beneficial**

## Governance

```
{
  "approval_requests": 29,
  "decisions": {
    "rejected": 19,
    "approved": 10,
    "expired": 0
  },
  "rejection_reasons": {
    "change_summary, diff, dry_run and rationale must all be non-empty": 18,
    "approver declined (judgement call)": 1
  },
  "applied_via_approval": 10,
  "auto_applied": 8,
  "auto_apply_rejected": 0,
  "apply_conflicts": 0,
  "lapsed": 0,
  "peak_requests_per_24h": {
    "nw_renewal": 2,
    "nw_kyc": 1,
    "ks_cancel": 2
  }
}
```

## Incidents

```
[
  {
    "type": "did_flagged",
    "workflow": "ks_cancel",
    "at": "D2 10:00",
    "flagged_did_share_by_day": {
      "2": 0.157,
      "3": 0.0,
      "4": 0.0,
      "5": 0.011,
      "6": 0.013,
      "7": 0.0,
      "8": 0.0,
      "9": 0.0
    }
  },
  {
    "type": "supervisor_edit",
    "workflow": "ks_cancel",
    "at": "D3 11:30",
    "mttr_minutes": 390,
    "fixed_by": "controller_approved"
  },
  {
    "type": "supervisor_edit",
    "workflow": "nw_renewal",
    "at": "D5 15:00"
  }
]
```

## Decaying variants — share of in-population calls still on the variant, by day after onset

```
{
  "nw_renewal:welcome_message=W3": {
    "8": 0.778,
    "9": 0.907
  }
}
```

Credits used: 14 · validation runs: 1 · LLM fix calls: 3