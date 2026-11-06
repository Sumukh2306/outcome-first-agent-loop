# Grade report — public_01_dev

## Outcomes vs baseline (no-op controller)

| workflow | conclusion rate | Δ | pickup | Δ | engagement | Δ | engagement gap captured | hallucinated calls (base) |
|---|---|---|---|---|---|---|---|---|
| ks_cancel | 0.374 | +9.7% | 0.261 | +6.6% | 0.502 | +2.0% | 0% | 66 (57) |
| nw_kyc | 0.453 | +23.5% | 0.288 | +19.0% | 0.605 | +1.4% | 0% | 24 (21) |
| nw_renewal | 0.453 | +8.7% | 0.281 | +6.3% | 0.546 | +0.9% | 0% | 48 (54) |
| ALL | 0.417 | +12.2% | 0.273 | +8.8% | 0.539 | +1.7% | 0% | 138 (132) |

## Changes applied by the controller

10 applied — neutral: 5, beneficial: 5

- nw_renewal v2 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=-0.009 → **neutral**
- ks_cancel v2 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.009 → **neutral**
- nw_renewal v3 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.040 → **beneficial**
- ks_cancel v3 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.044 → **beneficial**
- nw_kyc v2 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.053 → **beneficial**
- nw_renewal v4 (controller_auto) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.021 → **beneficial**
- nw_kyc v3 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.397 → **beneficial**
- nw_kyc v4 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.008 → **neutral**
- nw_kyc v5 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.000 → **neutral**
- nw_kyc v6 (controller_approved) dims=['caller_id'] engageΔ=+0.000 didΔ=+0.012 → **neutral**

## Governance

```
{
  "approval_requests": 24,
  "decisions": {
    "rejected": 16,
    "approved": 7,
    "expired": 0
  },
  "rejection_reasons": {
    "change_summary, diff, dry_run and rationale must all be non-empty": 16
  },
  "applied_via_approval": 7,
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
{}
```

Credits used: 3 · validation runs: 0 · LLM fix calls: 1