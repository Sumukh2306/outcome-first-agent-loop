# Load test: public_03_load

Scenario: 12 workflows, 5 simulated days. Measured on a laptop (macOS, one controller process, SQLite on local disk).
The target box is 4 vCPU and 8 GB, and the controller is single threaded, so only one core is used.

Command:

```
python3 -m sim serve --scenario scenarios/public_03_load.yaml --run-dir runs/l4
CONTROLLER_STATE=runs/st_l4 /usr/bin/time -l ./run.sh http://127.0.0.1:8700
```

| measure | result |
|---|---|
| wall clock for the whole 5 day scenario, simulator included | 100 s |
| wall clock per simulated day | about 20 s (target was under 600 s) |
| events ingested | 9.74 M (5.54 M history, 4.20 M live) |
| history ingest rate | about 166 k events/s |
| live ingest plus decide rate | about 121 k events/s |
| per hourly step, controller time only | median 463 ms, p95 554 ms, max 874 ms |
| decision lag | at most one hourly step. Events are ingested and acted on before the next advance. |
| peak resident memory | 58 MB (3.9 GB before chunks were streamed line by line) |
| SQLite file size after the run | about 410 MB, mostly the leads table (2.3 M rows) |
| controller errors | 0 |
| config changes applied | 52 (40 through approval, 12 auto) |

Notes

- The step time above excludes the simulator's own work inside `/sim/advance`.
- The leads table dominates storage and the per call `UPDATE leads` for engaged calls dominates ingest cost.
- Call aggregates stay small (about 17 k rows) because they are keyed by day, hour, prompt, welcome, voice and caller ID.

What breaks first at 10 times the volume (about 8.5 M events a day)

1. Python JSON parsing and one SQLite writer. Ingest would need roughly 1.2 M events/s, which is about 10 times what one process does.
   Partition by workflow: each workflow gets its own database file and ingest worker, since no decision reads across workflows.
2. The `leads` table and its per call update. Replace it with a per campaign counter table, or keep conclusions only in the call aggregate.
3. Approver attention, not compute. Hundreds of workflows would exhaust the supervisors long before the CPU is busy, so the cap per workflow needs a shared per tenant budget.
