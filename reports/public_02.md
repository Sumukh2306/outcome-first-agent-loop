# Grade report — public_02_incidents

## Outcomes vs baseline (no-op controller)

| workflow | conclusion rate | Δ | pickup | Δ | engagement | Δ | engagement gap captured | hallucinated calls (base) |
|---|---|---|---|---|---|---|---|---|
| ks_cancel | 0.342 | +45.1% | 0.227 | +25.1% | 0.522 | +11.6% | 52% | 99 (348) |
| nw_kyc | 0.442 | +18.4% | 0.281 | +19.9% | 0.597 | -1.9% | 0% | 21 (29) |
| nw_renewal | 0.480 | +10.8% | 0.290 | +10.5% | 0.554 | -0.1% | 23% | 57 (54) |
| ALL | 0.409 | +23.7% | 0.259 | +18.0% | 0.550 | +3.3% | 36% | 177 (431) |

## Changes applied by the controller

39 applied — neutral: 10, beneficial: 24, harmful: 5

- nw_renewal v2 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.018 → **neutral**
- ks_cancel v2 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.009 → **neutral**
- ks_cancel v3 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.026 didΔ=+0.000 → **beneficial**
- nw_kyc v2 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.037 → **beneficial**
- ks_cancel v4 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.043 → **beneficial**
- nw_renewal v3 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.042 didΔ=+0.000 → **beneficial**
- ks_cancel v5 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.029 → **beneficial**
- ks_cancel v6 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.028 → **beneficial**
- ks_cancel v7 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.026 → **beneficial**
- nw_renewal v4 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.066 → **beneficial**
- ks_cancel v8 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.009 → **neutral**
- ks_cancel v9 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.026 didΔ=+0.000 → **beneficial**
- nw_renewal v5 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.117 didΔ=+0.000 → **beneficial**
- ks_cancel v10 (controller_approved) dims=['voice'] engageΔ=-0.007 didΔ=+0.000 → **neutral**
- nw_renewal v6 (controller_approved) dims=['voice'] engageΔ=+0.007 didΔ=+0.000 → **neutral**
- ks_cancel v12 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.007 → **neutral**
- ks_cancel v13 (controller_approved) dims=['prompt_version'] engageΔ=+0.102 didΔ=+0.000 → **beneficial**
- ks_cancel v14 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.110 → **beneficial**
- ks_cancel v15 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.096 → **beneficial**
- ks_cancel v16 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.023 → **beneficial**
- nw_kyc v3 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.168 → **beneficial**
- nw_renewal v7 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.026 didΔ=+0.000 → **beneficial**
- ks_cancel v17 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.007 didΔ=+0.000 → **neutral**
- ks_cancel v18 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.054 → **beneficial**
- ks_cancel v19 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.050 → **beneficial**
- ks_cancel v20 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.024 → **beneficial**
- nw_kyc v4 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.081 → **beneficial**
- ks_cancel v21 (controller_approved) dims=['welcome_message'] engageΔ=+0.013 didΔ=+0.000 → **beneficial**
- nw_renewal v8 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.037 didΔ=+0.000 → **beneficial**
- nw_renewal v10 (controller_approved) dims=['welcome_message'] engageΔ=+0.003 didΔ=+0.000 → **neutral**
- ks_cancel v22 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.021 didΔ=+0.000 → **harmful**
- ks_cancel v23 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.024 → **harmful**
- nw_renewal v11 (controller_approved) dims=['voice'] engageΔ=-0.013 didΔ=+0.000 → **harmful**
- ks_cancel v24 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.025 didΔ=+0.000 → **beneficial**
- nw_renewal v12 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.064 didΔ=+0.000 → **harmful**
- nw_kyc v5 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.004 → **neutral**
- ks_cancel v25 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.058 didΔ=+0.000 → **harmful**
- nw_renewal v13 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.059 didΔ=+0.000 → **beneficial**
- nw_kyc v6 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.015 → **neutral**

## Governance

```
{
  "approval_requests": 29,
  "decisions": {
    "approved": 26,
    "rejected": 3,
    "expired": 0
  },
  "rejection_reasons": {
    "approver declined (judgement call)": 3
  },
  "applied_via_approval": 25,
  "auto_applied": 14,
  "auto_apply_rejected": 0,
  "apply_conflicts": 1,
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
      "2": 0.0,
      "3": 0.022,
      "4": 0.0,
      "5": 0.0,
      "6": 0.0,
      "7": 0.052,
      "8": 0.055,
      "9": 0.046
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
    "2": 0.859,
    "3": 0.869,
    "4": 0.523,
    "5": 0.206,
    "6": 0.041,
    "7": 0.036,
    "8": 0.16,
    "9": 0.104
  }
}
```

Credits used: 8 · validation runs: 1 · LLM fix calls: 1