# Grade report — public_02_incidents

## Outcomes vs baseline (no-op controller)

| workflow | conclusion rate | Δ | pickup | Δ | engagement | Δ | engagement gap captured | hallucinated calls (base) |
|---|---|---|---|---|---|---|---|---|
| ks_cancel | 0.373 | +58.2% | 0.248 | +37.1% | 0.514 | +9.9% | 44% | 100 (348) |
| nw_kyc | 0.470 | +25.8% | 0.297 | +26.7% | 0.596 | -2.0% | 0% | 26 (29) |
| nw_renewal | 0.470 | +8.5% | 0.288 | +9.7% | 0.546 | -1.5% | -4% | 70 (54) |
| ALL | 0.426 | +28.8% | 0.271 | +23.6% | 0.543 | +2.0% | 24% | 196 (431) |

## Changes applied by the controller

30 applied — neutral: 11, beneficial: 15, harmful: 4

- nw_renewal v2 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.018 → **neutral**
- ks_cancel v2 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.009 → **neutral**
- ks_cancel v3 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.026 didΔ=+0.000 → **beneficial**
- nw_renewal v3 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.042 didΔ=+0.000 → **beneficial**
- ks_cancel v4 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.043 → **beneficial**
- nw_kyc v2 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.050 → **beneficial**
- nw_renewal v4 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.064 → **beneficial**
- ks_cancel v5 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.002 didΔ=+0.000 → **neutral**
- nw_renewal v5 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.101 didΔ=+0.000 → **beneficial**
- ks_cancel v6 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.003 didΔ=+0.000 → **neutral**
- ks_cancel v7 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.168 → **beneficial**
- nw_kyc v3 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.365 → **beneficial**
- ks_cancel v8 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.061 → **beneficial**
- ks_cancel v9 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.034 → **beneficial**
- nw_renewal v6 (controller_approved) dims=['voice'] engageΔ=+0.008 didΔ=+0.000 → **neutral**
- nw_kyc v4 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.001 → **neutral**
- ks_cancel v11 (controller_approved) dims=['prompt_version'] engageΔ=+0.102 didΔ=+0.000 → **beneficial**
- nw_kyc v5 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.013 → **neutral**
- ks_cancel v12 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.004 didΔ=+0.000 → **neutral**
- ks_cancel v13 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.030 → **harmful**
- ks_cancel v14 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.032 → **beneficial**
- nw_renewal v8 (controller_approved) dims=['welcome_message'] engageΔ=+0.091 didΔ=+0.000 → **beneficial**
- nw_kyc v6 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.002 → **neutral**
- ks_cancel v15 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.014 didΔ=+0.000 → **beneficial**
- nw_renewal v9 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.038 didΔ=+0.000 → **harmful**
- ks_cancel v16 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.001 didΔ=+0.000 → **neutral**
- nw_renewal v10 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.027 didΔ=+0.000 → **harmful**
- nw_kyc v7 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.019 → **neutral**
- ks_cancel v17 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.025 didΔ=+0.000 → **harmful**
- nw_renewal v11 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.034 didΔ=+0.000 → **beneficial**

## Governance

```
{
  "approval_requests": 29,
  "decisions": {
    "approved": 24,
    "rejected": 5,
    "expired": 0
  },
  "rejection_reasons": {
    "approver declined (judgement call)": 2,
    "change_summary, diff, dry_run and rationale must all be non-empty": 3
  },
  "applied_via_approval": 23,
  "auto_applied": 7,
  "auto_apply_rejected": 0,
  "apply_conflicts": 1,
  "lapsed": 0,
  "peak_requests_per_24h": {
    "nw_renewal": 2,
    "nw_kyc": 2,
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
      "2": 0.151,
      "3": 0.0,
      "4": 0.0,
      "5": 0.013,
      "6": 0.012,
      "7": 0.0,
      "8": 0.0,
      "9": 0.0
    }
  },
  {
    "type": "supervisor_edit",
    "workflow": "ks_cancel",
    "at": "D3 11:30",
    "mttr_minutes": 330,
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
    "2": 0.894,
    "3": 0.899,
    "4": 0.897,
    "5": 0.901,
    "6": 0.284,
    "7": 0.149,
    "8": 0.149,
    "9": 0.173
  }
}
```

Credits used: 14 · validation runs: 1 · LLM fix calls: 3