# Grade report — public_01_dev

## Outcomes vs baseline (no-op controller)

| workflow | conclusion rate | Δ | pickup | Δ | engagement | Δ | engagement gap captured | hallucinated calls (base) |
|---|---|---|---|---|---|---|---|---|
| ks_cancel | 0.395 | +15.7% | 0.259 | +6.0% | 0.530 | +7.7% | 38% | 64 (57) |
| nw_kyc | 0.425 | +16.0% | 0.280 | +15.9% | 0.590 | -1.3% | 0% | 29 (21) |
| nw_renewal | 0.468 | +12.3% | 0.280 | +6.0% | 0.570 | +5.2% | 29% | 51 (54) |
| ALL | 0.426 | +14.5% | 0.271 | +7.8% | 0.556 | +5.0% | 25% | 144 (132) |

## Changes applied by the controller

23 applied — neutral: 9, beneficial: 11, harmful: 3

- nw_renewal v2 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.009 → **neutral**
- ks_cancel v2 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.009 → **neutral**
- ks_cancel v3 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.002 didΔ=+0.000 → **neutral**
- nw_renewal v3 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.070 didΔ=+0.000 → **beneficial**
- ks_cancel v4 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.046 → **beneficial**
- nw_renewal v4 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.044 → **beneficial**
- nw_kyc v2 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.053 → **beneficial**
- ks_cancel v5 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.090 didΔ=+0.000 → **beneficial**
- nw_renewal v5 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.021 → **beneficial**
- ks_cancel v6 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.016 didΔ=+0.000 → **harmful**
- nw_renewal v6 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.059 didΔ=+0.000 → **beneficial**
- nw_renewal v7 (controller_approved) dims=['voice'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- nw_kyc v3 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.332 → **beneficial**
- nw_kyc v4 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.011 → **neutral**
- nw_renewal v8 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.007 didΔ=+0.000 → **neutral**
- nw_kyc v5 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.001 → **neutral**
- ks_cancel v7 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.020 didΔ=+0.000 → **beneficial**
- nw_renewal v9 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.026 didΔ=+0.000 → **harmful**
- ks_cancel v8 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.046 didΔ=+0.000 → **harmful**
- nw_renewal v10 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.039 didΔ=+0.000 → **beneficial**
- nw_kyc v6 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.000 → **neutral**
- ks_cancel v9 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.005 didΔ=+0.000 → **neutral**
- nw_renewal v11 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.032 didΔ=+0.000 → **beneficial**

## Governance

```
{
  "approval_requests": 23,
  "decisions": {
    "approved": 20,
    "rejected": 3,
    "expired": 0
  },
  "rejection_reasons": {
    "change_summary, diff, dry_run and rationale must all be non-empty": 2,
    "approver declined (judgement call)": 1
  },
  "applied_via_approval": 20,
  "auto_applied": 3,
  "auto_apply_rejected": 0,
  "apply_conflicts": 0,
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
[]
```

## Decaying variants — share of in-population calls still on the variant, by day after onset

```
{
  "nw_renewal:welcome_message=W3": {
    "3": 0.862,
    "4": 0.516,
    "5": 0.473,
    "6": 0.413,
    "7": 0.155
  }
}
```

Credits used: 3 · validation runs: 0 · LLM fix calls: 1