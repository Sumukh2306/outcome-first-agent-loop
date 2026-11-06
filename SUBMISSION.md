# Outcome-First Agent Loop: Submission

**Name:** Sumukha DN · **Date:** 6 Nov 2026 · **Hours actually spent:** about 14, an estimate I did not time. AI coding tools helped with drafting and debugging, and I reviewed and ran everything myself. · **Language / storage:** Python 3, SQLite (WAL, synchronous FULL)

## 0. TL;DR

- One always-on Python process polls the simulator every simulated hour, ingests events, decides, and acts only through `/approvals` or the one auto-apply the policy allows (caller ID).
- public_02: conclusion rate +28.4% over the no-op baseline, pickup +22.1%, engagement +3.0%. public_01: +14.7%, +7.3%, +5.5%.
- Hallucination incident on ks_cancel was fixed through an approved prompt switch with validation evidence, 390 minutes after the supervisor edit that caused it.
- Killed with SIGKILL four to five times mid run, it finished with no duplicate proposals and the same grade as an uncrashed run. public_03 runs in 100 s of wall clock for 5 days.
- Not built: per person call time (C4), fair credit and approver allocation across tenants (C15). Per cohort optimisation is only partly done.

## 1. Assumptions

1. The grader's "guardrail" of 0.02 on engagement is read as an absolute drop of 2 percentage points. A relative reading would be stricter. nw_kyc and nw_renewal sit near -2% relative engagement in public_02, so this matters.
2. Pickup and engagement are never blended. Experiments optimise engagement given connected, and pickup is only a guardrail and the target of caller ID decisions.
3. Welcome message and voice are customer facing. They always go through approval, even where the policy would allow auto-apply (Kestrel). Only caller ID is auto-applied.
4. A cohort for experiments is a workflow plus prompt version. Anything finer fragments traffic at this volume.
5. A supervisor edit is intentional and correct until proven otherwise. The controller never reverts it silently and pauses experiments on the touched dimension for 24 hours.
6. Credits are cheap in the sim but I spend them only where they change a decision: 3 per suggest-fixes call, ceil(n/100) per validation.
7. Simulator time is the only clock. Everything is keyed on the event timestamp and the `sim_minute`, never on wall time.
8. An expired or rejected proposal says nothing about the underlying idea. It is re-planned on fresh data.
9. I follow the signed policy (approver hours, 4 requests per 24h) and not Anita's stricter personal limits. Experiment asks go out at the first approver hour, so for Kestrel that can be before 11:00. I did not build a per supervisor override.

## 2. Scope decisions

| # | Capability | Status | Why | What it would take to finish |
|---|---|---|---|---|
| C1 | Ingestion at scale | Built | 9.74 M events in 100 s, per chunk watermark committed with the aggregates | Per workflow DB shards for 10x |
| C2 | Joins and shared cohort object | Partial | One cohort definition (workflow, prompt) used by detection, experiments and view. Lead features are stored but not used to split | Feature based cohort splitting with a minimum size |
| C3 | Bootstrapping from history | Built | History chunks go through the same ingest, so D0 starts with evidence | None |
| C4 | Call time optimisation | Cut | Needs per lead timing models and a lot of care around windows. Highest cost, hardest to explain to compliance | Hour of day uptake model per cohort, then per person |
| C5 | Caller ID health | Built | Flag at 100+ dials in 24h and pickup at or below 0.65 of peer pickup, exclude for 3 days, 5% probe share afterwards, stepwise removal within max_shift | Smarter exploration of new DIDs |
| C6 | Welcome and voice experiments | Built | Thompson shares, 10% floor, Holm corrected z test, 300 per arm minimum | Interaction aware design, per cohort arms |
| C7 | Promotion, decay, rollback | Partial | Decay check on a 24h window against a pooled comparator works. In public_02 the decaying W3 fell from 0.90 to 0.05 of traffic by day 8 | Faster reaction and a clean rollback proposal path under sparse data |
| C8 | Hallucination response | Built | Detect, suggest, validate, propose with evidence, verify after apply | Handling several simultaneous incidents |
| C9 | Governance client | Built | Intent before action, deterministic ids, stale, lapsed, duplicate and 403 paths, restart reconcile | Per tenant fairness |
| C10 | Honest impact and dry run | Partial | Impact score is affected leads times predicted change from measured rates. Dry run uses historic cohort rates, not a replay | Real counterfactual replay |
| C11 | Supervisor view | Partial | `python -m controller view` prints the one screen Anita asked for. No web UI | Thin web page on the same queries |
| C12 | Audit store | Built | Every decision, proposal, apply and incident row lands in `audit`. `why` reads it | Retention policy and export |
| C13 | Crash recovery | Built | Kill test in `scripts/crash_test.sh`, results in section 9 | None |
| C14 | Loop observability | Partial | `loop_health` table per step (ms, events, decisions, credits, watermark). No alert sender | Export to the existing metrics stack |
| C15 | Fair allocation across tenants | Cut | Needs a shared budget and more than three workflows to be meaningful | A per tenant token bucket for approver attention and credits |

Principle: I built what keeps customers and regulated clients safe and what the grade measures (governance, incidents, caller ID, experiments, recovery) before the things that look good in a demo. Per person call time was the summit headline, but it was the least explainable change and the one most likely to hurt a cohort, so I said no.

## 3. Stakeholders

### 01 Sales (Nikhil Rao)
- **Accepted:** speed. Winners get 90% share as soon as the test passes. The decision loop runs hourly.
- **Pushed back:** a single blended score (violates Product's definition and constraint 3). Customer facing changes stay behind approval even at Kestrel. Rolling out the "persuasive" prompt: not without validation, and the sim shows it is the risky one.
- **Wrong claims:** Kestrel auto-apply does not cover everything. The policy excludes prompt and cohorts, and max_shift is 0.2. Northwind KYC has auto-apply disabled, so the QBR remark is not what the contract says.
- **Reply:** "Nikhil, you will get two numbers per client, conclusion rate and engagement, because blending them hides harm. Winners go live within a day of passing the test. Kestrel auto-apply only covers caller ID rotation, not scripts or prompts, and Northwind KYC has none, so those changes wait for a human. I would rather show a summit audience a rollback in action than a hesitant agent. I will not roll out the persuasive prompt anywhere without validation evidence. Happy to walk you through the dashboard before the summit."

### 02 Compliance (Meera Iyer, Northwind)
- **Accepted:** every customer facing change is a named approval request with validation evidence in the rationale. Audit answers come from `why`. Requests are only sent inside approver hours.
- **Pushed back:** nothing material. I went further than asked: I do not use the operational latitude on KYC automatically, because KYC has no auto-apply at all, and caller ID changes there also go through approval.
- **Wrong claims:** she assumes operational settings are freely changeable. On KYC they are not.
- **Reply:** "Meera, every change a customer can hear, and caller ID changes on KYC, goes to your approvers with the evidence attached. Script changes carry validation results. We only send requests inside 10:00 to 19:00 (KYC to 18:00). Any date and customer can be traced to the variant and reason with one command, well inside 24 hours. If a change looks worse than the old setting, we propose the rollback, we do not wait."

### 03 SRE (Kabir Menon)
- **Accepted:** kill test, idempotency, no new infrastructure (SQLite on local disk), loop health table, speed target.
- **Pushed back:** I did not ship alert wiring. Without his on-call stack I would be guessing. I list the alerts in section 10.
- **Wrong claims:** none found.
- **Reply:** "Kabir, the controller is one process plus one SQLite file, no new services. We killed it with SIGKILL four to five times mid run and the final result matched an uncrashed run, with zero duplicate proposals. One simulated day of public_03 takes about 20 seconds on a laptop, one core. `loop_health` has ingest, decisions and credits per step. Alert wiring is left until I know your paging stack, and the proposed pages are in the doc."

### 04 Ops supervisor (Anita Desai, Kestrel)
- **Accepted:** her edits are never undone silently (24h experiment hold on touched dimensions). One screen via `view`. At most one experiment proposal per workflow per day, with one slot kept for incidents. Batching: several dimension changes go in one request.
- **Pushed back:** "no requests before 11:00". I did not build it. The policy lets approvers start at 10:00 and my experiment asks go out then.
- **Wrong claims:** her limits are stricter than policy (four per 24h, approvers from 10:00), so they are preferences and not contract. Peak load in public_02 was 2 requests per 24h on every workflow, which happens to meet her cap of two.
- **Reply:** "Anita, your edits stay. If you change a prompt, we pause tests on that part for 24 hours and never undo it quietly. You get at most one routine request a day for your line, with everything in it, plus one slot kept for an incident. I could not promise nothing before 11:00, since the policy lets approvers start at 10:00. The new `view` command shows what is being tested, what is winning, what we need from you and what changed today. We will not do anything that makes the bot read the compliance script word for word."

### 05 Product (Tara Kulkarni)
- **Accepted:** separate KPIs, one cohort object, expired equals rejected and re-planned, only what ran counts as evidence (variant recorded per call), config updates stay per workflow. Minimum arm 300 connected calls, 48h window; this trades speed for fewer false winners.
- **Pushed back:** per person call time as P0. Cut.
- **Wrong claims:** none found.
- **Reply:** "Tara, KPIs stay separate everywhere. Cohort is one object in detection, experiments and the view. Minimum arm size is 300 connected calls with Holm corrected tests, which costs about a day of waiting but keeps false winners low. Expired proposals are re-planned on fresh data. Per person call time is cut for this round because I could not make it safe and explainable. Caller ID health and the supervisor view are in."

### 06 CTO (Aryamann)
- **Accepted:** explainability over lift, credit discipline, a plain scope table, and docs for the person on call.
- **Pushed back:** none.
- **Wrong claims:** he warned the memos may be wrong, and several are (sections above).
- **Reply:** "Aryamann, I said no to per person call time and fair credit allocation, and I kept a smaller scope that is explainable and crash safe. Results and limits are in the doc, including the harmful changes I am not happy about."

## 4. Architecture

```
simulator HTTP
  /events/chunks  /workflows  /approvals  /sim/state
        |
   api.py (retries, streaming)
        |
   ingest.py ---> SQLite: call_agg, leads, kv(watermark)  (one tx per chunk)
        |
   loop.py (hourly step)
        |-> governance.py  sync approvals, apply approved, auto-apply, reconcile
        |-> policy.py      incidents, caller ID, experiments, decay
        |-> store.py       audit, incidents, experiments, loop_health
        v
   PUT /workflows/{id}/config   POST /approvals
```

State lives only in `controller_state/<scenario>-<fingerprint>.db`. On restart the loop reads the watermark, re-ingests anything after it, then runs `reconcile` once: it checks config history to see whether an intended apply already happened before the crash. Deterministic proposal ids make a repeated POST return 409 duplicate, which is treated as success. If the simulator world was restarted (clock behind what was last seen), the old DB is renamed and a new one starts.

## 5. The learning loop

- **Cohorts:** workflow plus prompt version, with arms of welcome message and voice taken from `default` allocations. Minimum 300 connected calls per arm, chosen so a 2pp lift is detectable at about the 1 in 20 level without exploding the wait. This is the speed versus false winner trade.
- **Experiment design:** Thompson sampling on engaged per connected, seeded by workflow, dimension and day so reruns are identical. 10% exploration floor. Welcome and voice are tested one dimension per day to avoid confounding. Interactions are not modelled.
- **Deciding a winner:** two proportion z test against each rival, Holm corrected, all adjusted p below 0.05 and a lift of at least 2pp. Winner gets 90% and 10% stays with a comparator. I did not measure the false winner rate on a null run; the level is nominal.
- **Decay and rollback:** on a 24h window against a pooled comparator. In public_02 the decaying W3 on nw_renewal dropped from 0.90 of calls on day 2 to 0.05 on day 8 after onset. Reaction is slower than I'd like; I report it as partial.
- **Call time and caller ID:** call time cut. Caller ID: flag at 100+ dials in 24h with pickup at or below 0.65 of peer pooled pickup, exclude for 3 days, then a 5% probe share. Unknown DIDs with fewer than 50 dials also get a 5% probe.
- **Guardrail:** any arm more than 2pp below the workflow pickup is excluded. A candidate prompt that regresses engagement by over 0.01 is rejected.

## 6. Governance

States: `draft` (intent written) → `submitted` → `pending` → `approved` → `applied`; side exits `rejected`, `expired`, `lapsed`, `stale`. Rejected and expired go back to planning with fresh data. Stale (409 base version) is re-planned, not resubmitted. Lapsed (410) is re-planned within the apply window.

- **Timing:** requests are only created at approver hours. Experiments go at the first approver hour of the day, one per workflow per day, one of the policy's requests per 24h kept free for incidents. Peak requests in 24h was 2 for every workflow in public_02, against a policy limit of 4.
- **Auto-apply:** only caller ID, in steps bounded by max_shift with a margin. Welcome, voice and prompt always ask a human, even where auto-apply is allowed.
- **Impact score and affected leads** come from the cohort's measured rate and open lead counts. The dry run is a rate based estimate, not a replay, so it is an approximation. Auto-applied rows have no impact score (I recorded None).
- **Supervisor edit mid experiment:** the experiment on that dimension is held for 24h and the edit is logged as a supervisor change. If an in-flight proposal goes stale, it is re-planned.

## 7. Incidents

Trigger: 6h hallucination rate at least max(0.02, history rate + 0.015) with at least 200 connected calls. I have not measured false positive rate separately; the floors were chosen so that normal noise at this volume stays well below it.

Pick a fix: ask the LLM for 3 candidates (3 credits), validate the best by measured engagement (500 conversations, 5 credits), reject any that regress engagement by more than 0.01, then propose with the validation score in the rationale. Verify the rate after apply.

Timeline in public_02, ks_cancel:
- D3 11:30 supervisor edits config v9 (welcome, voice, prompt).
- D3 14:00 incident opened, hallucination rate 0.078 on P2 against a baseline of 0.010.
- D3 15:00 three fix candidates. D3 16:00 proposal switching P2 to P1, validation 0.986 on 500 conversations.
- D3 18:00 approved and applied as v10. Mean time to resolve: 390 minutes after the edit.
- Total credits spent in the run: 14, one validation run, 3 LLM fix calls. Hallucinated calls fell from 348 (baseline) to 94.

## 8. Scale

public_03_load, 12 workflows, 5 simulated days, one laptop core. Full table in `reports/public_03_load.md`.

| measure | result |
|---|---|
| Wall clock, whole scenario with simulator | 100 s (about 20 s per simulated day, target was under 600 s) |
| Events | 9.74 M (5.54 M history, 4.20 M live) |
| History ingest | about 166 k events/s |
| Live ingest and decide | about 121 k events/s |
| Step time (controller only) | median 463 ms, p95 554 ms, max 874 ms |
| Decision lag | at most one hourly step |
| Peak RSS | 58 MB (3.9 GB before streaming chunks) |
| Errors | 0 |

First failures at 10x: Python JSON parsing and the single SQLite writer, then the `leads` table with per call updates, then approver attention long before CPU. Partition by workflow with one DB shard per workflow, replace the lead updates with counters, and add a per tenant approval budget.

## 9. Reliability

Method: `scripts/crash_test.sh` runs public_02 and SIGKILLs the controller at staged random delays, then restarts it each time, then runs to the end.

Result (log in `reports/crash_recovery.log`): 4 kills at sim minutes 5040, 8040, 9660 and 12420; scenario finished at 14400; 0 duplicate proposal ids; 0 unresolved intents; 0 approvals applied twice; 0 repeated auto-applies. The final grade matched the uncrashed run (conclusion rates 0.366, 0.459, 0.472). An earlier 5 kill run before the last detector change was also clean.

State lost: at most the current hourly step, which is redone. Idempotency keys: proposal ids are `{workflow}-m{minute}-{hash}`, applies are checked against config history. Simulator 5xx and transport errors are retried with backoff (up to 10 s); 409, 410 and 403 have explicit handlers. A single workflow failing logs a `controller_error` audit row and the others continue.

## 10. Audit & observability

```
$ python3 -m controller why --state-dir runs/state_e02 --workflow ks_cancel --at "D3 11:30" --window 400
ks_cancel around D3 11:30 (+/- 400 min)
  D3 10:00  approval_requested   experiment proposal apr_00011: welcome_message: explore
  D3 11:30  config_changed       config v9 by supervisor: welcome_message, voice, prompt_version
  D3 12:00  proposal_stale       apr_00011 went stale when applied
  D3 14:00  incident_opened      hallucination incident on P2
  D3 15:00  llm_suggestions      3 fix candidates for P2
  D3 16:00  approval_requested   incident proposal apr_00013: switch prompt P2 to P1 (hallucination incident)
  D3 18:00  approval_applied     apr_00013 applied as v10
  D3 18:00  incident_mitigating  prompt P1 applied, verifying
  proposal apr_00013 (incident, applied) made D3 16:00
    rationale: P2 flagged 0.078 of connected calls in the last 6h against a baseline of 0.010. P1 passed validation at 0.986 on 500 synthetic conversations.
    affected leads: 16632, impact score: 1.0
```

`python3 -m controller view` prints the supervisor screen. I did not build a per customer "what did this lead hear" query; the per call variant is in `call_agg` only in aggregate, so a per call answer for the IRDAI auditors would need the raw events, which the simulator keeps.

Page on: controller process down, ingest watermark not moving for 2 steps, credits below 20%, an approval stuck in `submitted` past its TTL, `controller_error` rows. Do not page on: rejected proposals, a single stale proposal, DID flags, normal experiment churn.

## 11. Results

public_02 (`reports/public_02.md`):

| workflow | conclusion | Δ | pickup | Δ | engagement | Δ |
|---|---|---|---|---|---|---|
| ks_cancel | 0.368 | +56.3% | 0.246 | +36.0% | 0.512 | +9.5% |
| nw_kyc | 0.467 | +24.9% | 0.291 | +24.1% | 0.605 | -0.6% |
| nw_renewal | 0.475 | +9.7% | 0.284 | +8.4% | 0.558 | +0.6% |
| ALL | 0.425 | +28.4% | 0.268 | +22.1% | 0.548 | +3.0% |

26 changes applied: 7 neutral, 16 beneficial, 3 harmful.

public_01 (`reports/public_01.md`):

| workflow | conclusion | Δ | pickup | Δ | engagement | Δ |
|---|---|---|---|---|---|---|
| ks_cancel | 0.397 | +16.2% | 0.258 | +5.3% | 0.536 | +8.9% |
| nw_kyc | 0.436 | +19.0% | 0.289 | +19.5% | 0.584 | -2.1% |
| nw_renewal | 0.460 | +10.6% | 0.274 | +3.7% | 0.573 | +5.8% |
| ALL | 0.426 | +14.7% | 0.269 | +7.3% | 0.559 | +5.5% |

19 changes applied: 8 neutral, 10 beneficial, 1 harmful.

Interpretation: most of the gain is pickup, from caller ID health and the hallucination fix. Engagement is the weak side. Experiment moves are now skipped when the dry run predicts lower engagement or a pickup drop beyond half the guardrail, which cut harmful changes in public_01 from 5 to 1 and lifted engagement in both scenarios. nw_kyc stays slightly negative because higher pickup dilutes engagement per connected call. In public_02 the remaining harmful changes include caller ID steps; earlier two caller ID steps on ks_cancel were harmful (v12 and v17, both an auto-applied DID step that worsened pickup by 0.030). I would shorten the probe period and require a pre-check that a re-probed DID is not the flagged one.

## 12. Trade-offs & rejected alternatives

| Option | Why considered | Why rejected / what instead |
|---|---|---|
| Postgres or Redis | Already run by SRE | SQLite is enough for one process and adds no new infra; revisit with sharding |
| Auto-apply welcome and voice at Kestrel | Sales wanted speed | Customer facing, and compliance pattern was to keep humans in the loop |
| Blended KPI | Sales wanted one number | Product forbids it and it hides harm |
| Bandit only, no test | Faster learning | No false winner control; I use Thompson for allocation and Holm z test for promotion |
| Per person call time | Summit headline | Cut, too risky and hard to explain |
| Wall clock timers | Simpler | Not replayable; I use sim time only |

## 13. Known weaknesses

- Some harmful changes remain (1 of 19 in public_01, 3 of 26 in public_02), mostly caller ID steps.
- Engagement on nw_kyc is slightly negative in both scenarios, partly a composition effect from higher pickup.
- Per cohort and per person optimisation is cut; only `default` allocations are used.
- Excluded DIDs get a 5% re-probe after 3 days, which can cost pickup.
- Decay rollback is slow: the decayed variant still had 0.39 of traffic at day 6.
- Impact score and dry run are estimates, not replays.
- No false winner rate or false positive rate measurement on a null scenario.
- No alert sender and no web UI.
- Credit and approver fairness across tenants is missing.

## 14. If this went to production at Formi next month

1. Week 1: deploy next to the Postgres you already run (move SQLite tables over), add a health endpoint and wire the alerts in section 10 to your stack.
2. Week 1: run in shadow mode against two live workflows. Log every proposal, send none.
3. Week 2: turn on caller ID auto-apply only, watch pickup for a week.
4. Week 2: turn on approval requests for one Kestrel workflow with Anita as the named approver.
5. Run a null experiment to measure the false winner rate, then tune the minimum sample size.
6. Build per lead audit (store the variant per call) so the IRDAI 24 hour answer is complete.
7. Fix the engagement dip on KYC and renewal before widening.

## Runbook

```
pip install -r requirements.txt
python3 -m sim serve --scenario scenarios/public_02_incidents.yaml --run-dir runs/x
./run.sh http://127.0.0.1:8700
python3 -m controller view --state-dir controller_state
python3 -m controller why --state-dir controller_state --workflow ks_cancel --at "D3 11:30"
python3 -m pytest tests
scripts/evaluate.sh scenarios/public_02_incidents.yaml name
scripts/crash_test.sh
```

If the controller misbehaves, check `controller_error` and `proposal_stale` rows in the `audit` table, then `loop_health` for step time and credit burn. To start clean delete the `.db` file; the controller rebuilds from history chunks.
