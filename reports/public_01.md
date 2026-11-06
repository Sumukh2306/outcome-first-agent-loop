# Grade report — public_01_dev

## Outcomes vs baseline (no-op controller)

| workflow | conclusion rate | Δ | pickup | Δ | engagement | Δ | engagement gap captured | hallucinated calls (base) |
|---|---|---|---|---|---|---|---|---|
| ks_cancel | 0.384 | +12.3% | 0.259 | +5.8% | 0.518 | +5.3% | 37% | 58 (57) |
| nw_kyc | 0.435 | +18.8% | 0.284 | +17.4% | 0.594 | -0.6% | 0% | 38 (21) |
| nw_renewal | 0.460 | +10.6% | 0.280 | +5.9% | 0.561 | +3.5% | 19% | 47 (54) |
| ALL | 0.420 | +13.0% | 0.271 | +8.0% | 0.548 | +3.6% | 21% | 143 (132) |

## Changes applied by the controller

20 applied — neutral: 5, beneficial: 10, harmful: 5

- nw_renewal v2 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.009 → **neutral**
- ks_cancel v2 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.009 → **neutral**
- ks_cancel v3 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.002 didΔ=+0.000 → **neutral**
- nw_renewal v3 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.070 didΔ=+0.000 → **beneficial**
- ks_cancel v4 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.046 → **beneficial**
- nw_kyc v2 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.053 → **beneficial**
- nw_renewal v4 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.052 → **harmful**
- ks_cancel v5 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.087 didΔ=+0.000 → **beneficial**
- nw_renewal v5 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.113 → **beneficial**
- ks_cancel v6 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.014 didΔ=+0.000 → **beneficial**
- nw_renewal v6 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.061 didΔ=+0.000 → **beneficial**
- ks_cancel v7 (controller_approved) dims=['welcome_message'] engageΔ=-0.011 didΔ=+0.000 → **harmful**
- nw_renewal v7 (controller_approved) dims=['voice'] engageΔ=-0.000 didΔ=+0.000 → **neutral**
- nw_kyc v3 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.222 → **beneficial**
- ks_cancel v8 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.035 didΔ=+0.000 → **harmful**
- nw_renewal v8 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.005 didΔ=+0.000 → **neutral**
- ks_cancel v9 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.043 didΔ=+0.000 → **beneficial**
- nw_renewal v9 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=-0.023 didΔ=+0.000 → **harmful**
- ks_cancel v10 (controller_approved) dims=['voice'] engageΔ=-0.059 didΔ=+0.000 → **harmful**
- nw_renewal v10 (controller_approved) dims=['welcome_message', 'voice'] engageΔ=+0.104 didΔ=+0.000 → **beneficial**

## Governance

```
{
  "approval_requests": 19,
  "decisions": {
    "approved": 17,
    "rejected": 2,
    "expired": 0
  },
  "rejection_reasons": {
    "approver declined (judgement call)": 2
  },
  "applied_via_approval": 17,
  "auto_applied": 3,
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
[]
```

## Decaying variants — share of in-population calls still on the variant, by day after onset

```
{
  "nw_renewal:welcome_message=W3": {
    "3": 0.886,
    "4": 0.719,
    "5": 0.782,
    "6": 0.875,
    "7": 0.391
  }
}
```

Credits used: 0 · validation runs: 0 · LLM fix calls: 0