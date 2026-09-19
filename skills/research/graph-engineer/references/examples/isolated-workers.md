# EXAMPLE ONLY — Isolated Workers

> **Not a Run / Execute menu item.** Load this only when the user wants an illustration of what the scheduler actually runs when every subagent starts with a completely fresh conversation. For real work, design jobs for *their* goal in Execute mode.

**What it illustrates:** the five shapes the scheduler runs — independent fan-out, a real dependency, a diamond, a correction loop, and a fake edge that cannot be written down. Every path, version, sha256, status block and payload below was copied from a run of `scripts/graph_state.py`; none of it is invented text.

**The runtime fact underneath all five:** a `delegate_task` child starts with a completely fresh conversation. Its `goal`, its rendered `context` and its `output_schema` are its entire world. The orchestrator owns Graph State, and the only thing that crosses an edge is a committed artifact. See `references/isolation.md`.

## How these transcripts were produced

```bash
ROOT=C:/tmp/ge-ex/a        # one root per example: /a /b /c /c2 /d /e
PY=C:/Python314/python.exe # this workstation; use whichever python runs graph_state.py for you
GS="$PY skills/research/graph-engineer/scripts/graph_state.py --root $ROOT"
```

Artifact bodies in these runs are 15–29 byte placeholders, written by a script that plays the part of an isolated child: it reads `envelopes/<node>.a<n>.json`, writes its artifact to `writer.path`, writes its contract JSON to `return_file`, and returns. The orchestrator then runs `commit --node <id> --result <return_file>`. Paths, versions, sha256 values, statuses and payloads are real; the artifact *contents* are not the point and are not shown.

Most blocks below are quoted whole. Where a block is labelled *fields of that round's `dispatch`*, it is the named fields of that run's output, same values and same formatting — the keys left out are the constant ones (`note`, `graph_id`, and the long `round_tasks` contexts, which Example B quotes in full).

| # | Shape | Rounds (dispatch → commit) | What crosses each edge |
|---|-------|----------------------------|------------------------|
| A | splitter → 3 workers → verifier → merge → gate | 4 + the gate | `split-plan@v1` into each worker; three findings paths into the verifier; three verified paths into the merge |
| B | A → B on one artifact | 2 | `x@v1` — id, version, type, absolute path, sha256 |
| C | diamond A → {B, C} → D | 3 | `b@v1` and `c@v1` by path into D |
| D | worker → verifier RED → worker v2 → verifier GREEN | 5 | one verdict: unit, reason, evidence, scope, plus a pointer to the rejected version |
| E | two tasks that look sequential | 1 | nothing — so no edge exists |

---

## Example A — Independent parallel research: three workers, one batch

```text
                        split-scope                      ROUND 1   spawn
                             │  split-plan@v1
        ┌────────────────────┼────────────────────┐       ROUND 2   ONE delegate_task(tasks=[…])
        ▼                    ▼                    ▼
   audit-auth           audit-jobs         audit-billing
        │                    │                    │       findings-*@v1, one path each
        └────────────────────┼────────────────────┘       ROUND 3   spawn
                             ▼
                     verify-evidence ── verdict@v1 (green)
                             │  the three verified paths
                             ▼
                      merge-report (code)                ROUND 4   local_nodes, no spawn
                             │  release-report@v1
                             ▼
                          gate-1                         human approval
```

**`graph.json`** — accepted by `init` (exit 0):

```json
{
  "graph": {
    "id": "release-audit",
    "goal": "decide whether auth, jobs and billing can ship in the next release",
    "gate": {"lane": "reversible, wide", "action": "hand the verified release report to the release owner"},
    "caps": {"max_attempts": 3, "spawn_cap": 5, "spawn_budget": 20}
  },
  "constraints": [
    "every claim cites a file path and a line number",
    "this run produces findings and a report; it changes no code"
  ],
  "artifacts": {
    "split-plan":       {"type": "plan",     "ext": "md", "producer": "split-scope"},
    "findings-auth":    {"type": "findings", "ext": "md", "producer": "audit-auth",    "verifier": "verify-evidence"},
    "findings-jobs":    {"type": "findings", "ext": "md", "producer": "audit-jobs",    "verifier": "verify-evidence"},
    "findings-billing": {"type": "findings", "ext": "md", "producer": "audit-billing", "verifier": "verify-evidence"},
    "verdict":          {"type": "verdict",  "ext": "md", "producer": "verify-evidence"},
    "release-report":   {"type": "report",   "ext": "md", "producer": "merge-report"}
  },
  "nodes": [
    {"id": "split-scope", "kind": "splitter", "lens": "decomposition only — do not audit anything",
     "goal": "carve the release audit into exactly three independent subsystems",
     "green_condition": "the plan names three subsystems, one artifact per subsystem, no overlap",
     "requires": [], "produces": "split-plan",
     "output_contract": {"type": "object",
       "properties": {"node": {"type": "string"},
                      "status": {"type": "string", "enum": ["done", "failed"]},
                      "summary": {"type": "string", "minLength": 1},
                      "artifact_path": {"type": "string"},
                      "evidence": {"type": "array", "items": {"type": "string"}}},
       "required": ["node", "status", "summary", "artifact_path"]}},

    {"id": "audit-auth", "kind": "worker", "lens": "authentication and session handling",
     "goal": "audit the auth subsystem named in the plan",
     "green_condition": "every finding cites path:line",
     "requires": [{"artifact": "split-plan"}], "produces": "findings-auth",
     "output_contract": {"type": "object",
       "properties": {"node": {"type": "string"},
                      "status": {"type": "string", "enum": ["done", "failed"]},
                      "summary": {"type": "string", "minLength": 1},
                      "artifact_path": {"type": "string"},
                      "evidence": {"type": "array", "items": {"type": "string"}}},
       "required": ["node", "status", "summary", "artifact_path"]}},

    {"id": "audit-jobs", "kind": "worker", "lens": "background jobs, retries and idempotency",
     "goal": "audit the jobs subsystem named in the plan",
     "green_condition": "every finding cites path:line",
     "requires": [{"artifact": "split-plan"}], "produces": "findings-jobs",
     "output_contract": {"type": "object",
       "properties": {"node": {"type": "string"},
                      "status": {"type": "string", "enum": ["done", "failed"]},
                      "summary": {"type": "string", "minLength": 1},
                      "artifact_path": {"type": "string"},
                      "evidence": {"type": "array", "items": {"type": "string"}}},
       "required": ["node", "status", "summary", "artifact_path"]}},

    {"id": "audit-billing", "kind": "worker", "lens": "billing, invoicing and money paths",
     "goal": "audit the billing subsystem named in the plan",
     "green_condition": "every finding cites path:line",
     "requires": [{"artifact": "split-plan"}], "produces": "findings-billing",
     "output_contract": {"type": "object",
       "properties": {"node": {"type": "string"},
                      "status": {"type": "string", "enum": ["done", "failed"]},
                      "summary": {"type": "string", "minLength": 1},
                      "artifact_path": {"type": "string"},
                      "evidence": {"type": "array", "items": {"type": "string"}}},
       "required": ["node", "status", "summary", "artifact_path"]}},

    {"id": "verify-evidence", "kind": "verifier", "lens": "reproducible evidence for every claim",
     "goal": "check every finding in all three artifacts against its cited source",
     "green_condition": "each finding resolves to cited code, or is reported red with evidence",
     "requires": [{"artifact": "findings-auth"}, {"artifact": "findings-jobs"}, {"artifact": "findings-billing"}],
     "produces": "verdict",
     "output_contract": {"type": "object",
       "properties": {"node": {"type": "string"},
                      "status": {"type": "string", "enum": ["done", "failed"]},
                      "summary": {"type": "string", "minLength": 1},
                      "artifact_path": {"type": "string"},
                      "verdict": {"type": "string", "enum": ["green", "red"]},
                      "unit": {"type": "string"},
                      "reason": {"type": "string"},
                      "scope": {"type": "string"},
                      "evidence": {"type": "array", "items": {"type": "string"}}},
       "required": ["node", "status", "summary", "artifact_path", "verdict", "unit", "reason", "scope"]}},

    {"id": "merge-report", "kind": "code",
     "goal": "merge the three verified artifacts into one release report, ranked by severity",
     "green_condition": "one report exists with every finding tagged by subsystem",
     "requires": [{"artifact": "findings-auth"}, {"artifact": "findings-jobs"}, {"artifact": "findings-billing"}],
     "produces": "release-report",
     "output_contract": {"type": "object",
       "properties": {"node": {"type": "string"},
                      "status": {"type": "string", "enum": ["done", "failed"]},
                      "summary": {"type": "string", "minLength": 1},
                      "artifact_path": {"type": "string"},
                      "evidence": {"type": "array", "items": {"type": "string"}}},
       "required": ["node", "status", "summary", "artifact_path"]}},

    {"id": "gate-1", "kind": "gate",
     "goal": "approve handing the report to the release owner",
     "green_condition": "an explicit user yes is recorded",
     "requires": [{"artifact": "release-report"}]}
  ]
}
```

Commands, in order:

```bash
$GS init --spec spec.json --force                                  # exit 0
$GS dispatch                                                       # ROUND 1 → split-scope
$GS commit --node split-scope    --result results/split-scope.a1.json
$GS dispatch                                                       # ROUND 2 → three tasks, one batch
$GS commit --node audit-auth     --result results/audit-auth.a1.json
$GS commit --node audit-jobs     --result results/audit-jobs.a1.json
$GS commit --node audit-billing  --result results/audit-billing.a1.json
$GS status
$GS dispatch                                                       # ROUND 3 → verify-evidence
$GS commit --node verify-evidence --result results/verify-evidence.a1.json
$GS dispatch                                                       # ROUND 4 → local_nodes: ["merge-report"]
$GS commit --node merge-report   --result results/merge-report.a1.json
$GS status
$GS gate --status approved --user-approval '"yes, hand it to the release owner"'
```

Round 2 is one `delegate_task(tasks=[...])` call. The `bindings` array from that round's `dispatch` shows the batch and each task's index:

```json
"bindings": [
    {
      "node": "audit-auth",
      "attempt": 1,
      "task_index": 0,
      "envelope": "C:\\tmp\\ge-ex\\a\\release-audit\\envelopes\\audit-auth.a1.json"
    },
    {
      "node": "audit-jobs",
      "attempt": 1,
      "task_index": 1,
      "envelope": "C:\\tmp\\ge-ex\\a\\release-audit\\envelopes\\audit-jobs.a1.json"
    },
    {
      "node": "audit-billing",
      "attempt": 1,
      "task_index": 2,
      "envelope": "C:\\tmp\\ge-ex\\a\\release-audit\\envelopes\\audit-billing.a1.json"
    }
  ],
```

Their task `goal` strings, read out of the same output (the raw JSON escapes the em dash as `\u2014`):

```text
audit the auth subsystem named in the plan — graph node audit-auth (attempt 1). Green condition: every finding cites path:line
audit the jobs subsystem named in the plan — graph node audit-jobs (attempt 1). Green condition: every finding cites path:line
audit the billing subsystem named in the plan — graph node audit-billing (attempt 1). Green condition: every finding cites path:line
```

`$GS status` after the three commits — the verifier is READY, the merge is PENDING because the artifacts it consumes are not verified yet, and the gate is waiting:

```text
GRAPH: release-audit  [running]
goal: decide whether auth, jobs and billing can ship in the next release
GATE: not_reached (lane: reversible, wide) — action: hand the verified release report to the release owner
caps: attempts<=3  spawn<=5  budget 4/20

READY
  ○ verify-evidence         artifact: verdict (not produced yet)

PENDING
  ○ merge-report            artifact: release-report (not produced yet)  — findings-auth@latest is not verified yet (verifier: verify-evidence); findings-jobs@latest is not verified yet (verifier: verify-evidence); findings-billing@latest is not verified yet (verifier: verify-evidence)

WAITING_HUMAN
  ★ gate-1

GREEN
  ✓ split-scope             artifact: split-plan@v1
  ✓ audit-auth              artifact: findings-auth@v1 (unverified)
  ✓ audit-jobs              artifact: findings-jobs@v1 (unverified)
  ✓ audit-billing           artifact: findings-billing@v1 (unverified)
```

The verifier's GREEN commit unlocks the merge, and nothing else changed (`next_ready` from that `commit`):

```json
"next_ready": [
    "merge-report"
  ]
```

Round 4 has no spawn at all — a code node comes back under `local_nodes` instead. Fields of that round's `dispatch`:

```json
{
  "bindings": [],
  "local_nodes": [
    "merge-report"
  ],
  "local_envelopes": [
    {
      "node": "merge-report",
      "attempt": 1,
      "envelope": "C:\\tmp\\ge-ex\\a\\release-audit\\envelopes\\merge-report.a1.json",
      "artifact_path": "C:\\tmp\\ge-ex\\a\\release-audit\\artifacts\\release-report.v1.md",
      "return_file": "C:\\tmp\\ge-ex\\a\\release-audit\\results\\merge-report.a1.json"
    }
  ],
  "deferred_to_next_round": []
}
```

`$GS status` before the gate:

```text
GRAPH: release-audit  [gated]
goal: decide whether auth, jobs and billing can ship in the next release
GATE: waiting (lane: reversible, wide) — action: hand the verified release report to the release owner
caps: attempts<=3  spawn<=5  budget 5/20

WAITING_HUMAN
  ★ gate-1

GREEN
  ✓ split-scope             artifact: split-plan@v1
  ✓ audit-auth              artifact: findings-auth@v1
  ✓ audit-jobs              artifact: findings-jobs@v1
  ✓ audit-billing           artifact: findings-billing@v1
  ✓ verify-evidence         artifact: verdict@v1
  ✓ merge-report            artifact: release-report@v1
```

`gate --status approved --user-approval …` records the user's own words and closes the run:

```json
{
  "gate": {
    "lane": "reversible, wide",
    "action": "hand the verified release report to the release owner",
    "status": "approved",
    "approvals": [
      {
        "at": "2026-09-19T23:01:36Z",
        "user": "\"yes, hand it to the release owner\"",
        "note": null
      }
    ]
  },
  "waiting_on": [],
  "graph_status": "done",
  "graph_id": "release-audit"
}
```

Artifact flow across the whole run, from `status --json`:

| Artifact | Type | Producer | Verifier | verified_version | latest |
|----------|------|----------|----------|------------------|--------|
| `split-plan` | plan | split-scope | — | 1 | 1 |
| `findings-auth` | findings | audit-auth | verify-evidence | 1 | 1 |
| `findings-jobs` | findings | audit-jobs | verify-evidence | 1 | 1 |
| `findings-billing` | findings | audit-billing | verify-evidence | 1 | 1 |
| `verdict` | verdict | verify-evidence | — | 1 | 1 |
| `release-report` | report | merge-report | — | 1 | 1 |

**What the scheduler does.** Round 1 spawns the splitter alone; round 2 spawns the three workers together in one batch because all three become READY in the same pass; round 3 spawns the verifier once, because the verifier's READY condition is three committed artifacts; round 4 spawns nothing, because `merge-report` is kind `code` and `dispatch` returns it under `local_nodes`. The gate never dispatches — it is `WAITING_HUMAN` until a gate command records the user's approval.

This gate declares no `produces`, so it is the last thing in the graph and nothing waits on it. A gate that *does* declare `produces` pointing at a `decision` artifact becomes a real dependency instead: consumers of that artifact are `PENDING — gate gate-1 has not been answered yet` until the human answers, and `BLOCKED — gate gate-1 was rejected — nothing downstream runs` if the answer is no. Use the no-`produces` form for a final pause and the `decision` form when later work must not start without the human; see `references/gate-design.md`.

**What crosses each edge.** The plan crosses as `split-plan@v1` (path plus sha256) inside each worker's envelope, and only the worker with a matching lens receives it. The three findings cross to the verifier as three paths; the verifier reads files, not siblings. The verified findings cross to the merge as three paths, and the merge would have stayed PENDING until `verified_version` existed for each of them.

**What the workers do NOT see.** `audit-auth` never sees `audit-jobs` or `audit-billing` (those paths are absent from its envelope, and it has no channel to ask for them). No worker sees the verifier's reasoning, the verdict file, the release report, `state.json`, or any other node's conversation. Nothing a worker returns is true until the orchestrator commits it.

---

## Example B — A real dependency: one artifact crosses the edge

```text
      a  (splitter)  ── x@v1 ──▶  b  (worker)
      ROUND 1                      ROUND 2
```

Letters map to the pattern: `a` produces `x`, `b` requires `x` and produces `y`.

**`graph.json`** — accepted by `init` (exit 0):

```json
{
  "graph": {"id": "two-stage", "goal": "turn a rough brief into a reviewed outline"},
  "artifacts": {
    "x": {"type": "plan",   "ext": "md", "producer": "a"},
    "y": {"type": "report", "ext": "md", "producer": "b"}
  },
  "nodes": [
    {"id": "a", "kind": "splitter", "lens": "decomposition only",
     "goal": "split the brief into the sections the outline must cover",
     "green_condition": "the plan names every section and what each one must say",
     "requires": [], "produces": "x",
     "output_contract": {"type": "object",
       "properties": {"node": {"type": "string"},
                      "status": {"type": "string", "enum": ["done", "failed"]},
                      "summary": {"type": "string", "minLength": 1},
                      "artifact_path": {"type": "string"},
                      "evidence": {"type": "array", "items": {"type": "string"}}},
       "required": ["node", "status", "summary", "artifact_path"]}},

    {"id": "b", "kind": "worker", "lens": "outline structure and ordering",
     "goal": "draft the outline from the committed plan",
     "green_condition": "every section in the plan has a heading and two bullet points",
     "requires": [{"artifact": "x"}], "produces": "y",
     "output_contract": {"type": "object",
       "properties": {"node": {"type": "string"},
                      "status": {"type": "string", "enum": ["done", "failed"]},
                      "summary": {"type": "string", "minLength": 1},
                      "artifact_path": {"type": "string"},
                      "evidence": {"type": "array", "items": {"type": "string"}}},
       "required": ["node", "status", "summary", "artifact_path"]}}
  ]
}
```

Commands:

```bash
$GS init --spec spec.json                                          # exit 0
$GS dispatch                                                       # ROUND 1 → a
$GS status                                                         # b is PENDING, and says why
$GS status --json
$GS commit --node a --result results/a.a1.json                     # x@v1 committed
$GS dispatch --tasks-file tasks.json                               # ROUND 2 → b, with the envelope below
```

Before `a` commits, `b` is not waiting on a human or a turn — it is not runnable:

```text
GRAPH: two-stage  [running]
goal: turn a rough brief into a reviewed outline
caps: attempts<=3  spawn<=5  budget 1/20

RUNNING
  → a                       artifact: x (not produced yet)  attempt 1

PENDING
  ○ b                       artifact: y (not produced yet)  — x has no committed version yet (producer: a)
```

The same reason, machine-readable: `status --json` → `nodes.b`:

```json
{
  "kind": "worker",
  "status": "PENDING",
  "attempts": 0,
  "artifact": null,
  "waiting": "x has no committed version yet (producer: a)",
  "stale_input": null
}
```

`status --json` → `artifacts` — nothing has a committed version yet:

```json
{
  "x": {
    "verified_version": null,
    "latest": null
  },
  "y": {
    "verified_version": null,
    "latest": null
  }
}
```

After `commit --node a` (which also shows what that unlocks):

```json
{
  "node": "a",
  "status": "GREEN",
  "artifact": {
    "version": 1,
    "path": "C:\\tmp\\ge-ex\\b\\two-stage\\artifacts\\x.v1.md",
    "sha256": "a7fc5bca7a8418263bca40434d679b3995c714ca9a4685b27e134a1513fe14a3",
    "type": "plan",
    "producer": "a",
    "attempt": 1,
    "at": "2026-09-19T23:01:10Z",
    "verified": true,
    "bytes": 15
  },
  "graph_status": "running",
  "next_ready": [
    "b"
  ],
  "graph_id": "two-stage"
}
```

`b` is now READY, and its `dispatch` entry is one task whose `context` is this — the complete Node Input Envelope, verbatim:

```text
# Graph node: b (worker, attempt 1)

## Graph goal
turn a rough brief into a reviewed outline

## Your job
draft the outline from the committed plan

## Green condition — written before the work
every section in the plan has a heading and two bullet points

## Your lens
outline structure and ordering

## Inputs (read these files)
- x@v1 (plan) — C:\tmp\ge-ex\b\two-stage\artifacts\x.v1.md

## Write your artifact
Write the artifact (y@v1) to exactly this path, and nothing else may write it:
C:\tmp\ge-ex\b\two-stage\artifacts\y.v1.md

## Return
Write your final JSON to this file as well: C:\tmp\ge-ex\b\two-stage\results\b.a1.json
It must validate against the attached output schema: return ONLY the JSON value, no prose, no code fence.
`artifact_path` must be the exact path above, and `node` must be `b`.

## Isolation rule
You are an isolated subagent. This envelope is everything you may rely on: no other worker's
conversation, findings, or reasoning is visible to you, and your work is visible to no one until
the orchestrator commits it. If an input you need is missing, say so with status "failed" —
never guess what a sibling found, and never invent a passing result.
```

The same envelope as the machine-readable record (`envelopes/b.a1.json`), `inputs` shown in full so the pinned version is unambiguous:

```json
"inputs": [
  {
    "artifact": "x",
    "version": 1,
    "type": "plan",
    "path": "C:\\tmp\\ge-ex\\b\\two-stage\\artifacts\\x.v1.md",
    "sha256": "a7fc5bca7a8418263bca40434d679b3995c714ca9a4685b27e134a1513fe14a3",
    "required": true
  }
]
```

**What the scheduler does.** It does not ask `a` to hand anything over. `a` commits, and the recompute turns `b` from PENDING to READY on its own; the envelope is generated at that moment from the committed version, so `b` reads exactly `x@v1` and never a draft that was never committed.

**What crosses the edge.** Artifact metadata only: id, version, type, absolute path, sha256, required. The body stays on disk — one line in the envelope, zero tokens until `b` opens the file.

**What the worker does NOT see.** `a`'s conversation, `a`'s reasoning, the splitter's lens, any other artifact, `state.json`, and the orchestrator's framing of the task. If `x` were missing, the honest answer is `status: "failed"` — inventing the plan is the failure this shape exists to prevent.

---

## Example C — Diamond: two workers in one batch, then the merge

```text
        split                     ROUND 1   spawn
          │  a@v1
    ┌─────┴─────┐                 ROUND 2   ONE batch: worker-b and worker-c
    ▼           ▼
 worker-b    worker-c
    │           │  b@v1, c@v1
    └─────┬─────┘                 ROUND 3   local_nodes: ["merge"], no spawn
          ▼
        merge  (code)
```

**`graph.json`** — accepted by `init` (exit 0):

```json
{
  "graph": {"id": "diamond", "goal": "produce one merged result from two independent angles"},
  "artifacts": {
    "a": {"type": "plan",     "ext": "md", "producer": "split"},
    "b": {"type": "findings", "ext": "md", "producer": "worker-b"},
    "c": {"type": "findings", "ext": "md", "producer": "worker-c"},
    "d": {"type": "report",   "ext": "md", "producer": "merge"}
  },
  "nodes": [
    {"id": "split", "kind": "splitter", "lens": "decomposition only",
     "goal": "name the two independent angles",
     "green_condition": "the plan states two angles that share no input",
     "requires": [], "produces": "a",
     "output_contract": {"type": "object",
       "properties": {"node": {"type": "string"},
                      "status": {"type": "string", "enum": ["done", "failed"]},
                      "summary": {"type": "string", "minLength": 1},
                      "artifact_path": {"type": "string"}},
       "required": ["node", "status", "summary", "artifact_path"]}},

    {"id": "worker-b", "kind": "worker", "lens": "angle 1",
     "goal": "work angle 1",
     "green_condition": "the angle-1 artifact answers every question in the plan",
     "requires": [{"artifact": "a"}], "produces": "b",
     "output_contract": {"type": "object",
       "properties": {"node": {"type": "string"},
                      "status": {"type": "string", "enum": ["done", "failed"]},
                      "summary": {"type": "string", "minLength": 1},
                      "artifact_path": {"type": "string"}},
       "required": ["node", "status", "summary", "artifact_path"]}},

    {"id": "worker-c", "kind": "worker", "lens": "angle 2",
     "goal": "work angle 2",
     "green_condition": "the angle-2 artifact answers every question in the plan",
     "requires": [{"artifact": "a"}], "produces": "c",
     "output_contract": {"type": "object",
       "properties": {"node": {"type": "string"},
                      "status": {"type": "string", "enum": ["done", "failed"]},
                      "summary": {"type": "string", "minLength": 1},
                      "artifact_path": {"type": "string"}},
       "required": ["node", "status", "summary", "artifact_path"]}},

    {"id": "merge", "kind": "code",
     "goal": "merge the two committed artifacts into one result",
     "green_condition": "one result exists and every line traces to b@v1 or c@v1",
     "requires": [{"artifact": "b"}, {"artifact": "c"}], "produces": "d",
     "output_contract": {"type": "object",
       "properties": {"node": {"type": "string"},
                      "status": {"type": "string", "enum": ["done", "failed"]},
                      "summary": {"type": "string", "minLength": 1},
                      "artifact_path": {"type": "string"}},
       "required": ["node", "status", "summary", "artifact_path"]}}
  ]
}
```

Commands:

```bash
$GS init --spec spec.json --force                                  # exit 0
$GS dispatch                          # ROUND 1 → split
$GS commit --node split    --result results/split.a1.json
$GS dispatch                          # ROUND 2 → worker-b and worker-c, one batch
$GS commit --node worker-b --result results/worker-b.a1.json
$GS commit --node worker-c --result results/worker-c.a1.json
$GS status                            # merge is READY
$GS dispatch                          # ROUND 3 → local_nodes: ["merge"]
$GS commit --node merge    --result results/merge.a1.json
$GS status                            # done — every node GREEN
```

Round 2, verbatim from `dispatch`:

```json
"bindings": [
    {
      "node": "worker-b",
      "attempt": 1,
      "task_index": 0,
      "envelope": "C:\\tmp\\ge-ex\\c\\diamond\\envelopes\\worker-b.a1.json"
    },
    {
      "node": "worker-c",
      "attempt": 1,
      "task_index": 1,
      "envelope": "C:\\tmp\\ge-ex\\c\\diamond\\envelopes\\worker-c.a1.json"
    }
  ],
```

After both commits:

```text
GRAPH: diamond  [running]
goal: produce one merged result from two independent angles
caps: attempts<=3  spawn<=5  budget 3/20

READY
  ○ merge                   artifact: d (not produced yet)

GREEN
  ✓ split                   artifact: a@v1
  ✓ worker-b                artifact: b@v1
  ✓ worker-c                artifact: c@v1
```

Round 3 has no spawn either. Fields of that round's `dispatch`:

```json
{
  "bindings": [],
  "local_nodes": [
    "merge"
  ],
  "local_envelopes": [
    {
      "node": "merge",
      "attempt": 1,
      "envelope": "C:\\tmp\\ge-ex\\c\\diamond\\envelopes\\merge.a1.json",
      "artifact_path": "C:\\tmp\\ge-ex\\c\\diamond\\artifacts\\d.v1.md",
      "return_file": "C:\\tmp\\ge-ex\\c\\diamond\\results\\merge.a1.json"
    }
  ]
}
```

That merge envelope's `inputs`, in full — this is the whole of what crosses from round 2 to round 3:

```json
[
  {
    "artifact": "b",
    "version": 1,
    "type": "findings",
    "path": "C:\\tmp\\ge-ex\\c\\diamond\\artifacts\\b.v1.md",
    "sha256": "271dda102f8382be2e681facf0f5b915962d9e9373468f6109fa6c6ae051073f",
    "required": true
  },
  {
    "artifact": "c",
    "version": 1,
    "type": "findings",
    "path": "C:\\tmp\\ge-ex\\c\\diamond\\artifacts\\c.v1.md",
    "sha256": "20e4e49286d4c7831cdfd226769025a9731aaab376f483f1609f8481aa9baba3",
    "required": true
  }
]
```

Spawning more ready nodes than the spawn cap does not drop work — it defers it, and `dispatch` names what it deferred. Same graph, `"caps": {"spawn_cap": 1}`, `--root C:/tmp/ge-ex/c2`; fields of the deferring `dispatch`:

```json
{
  "bindings": [
    {
      "node": "worker-b",
      "attempt": 1,
      "task_index": 0,
      "envelope": "C:\\tmp\\ge-ex\\c2\\diamond-capped\\envelopes\\worker-b.a1.json"
    }
  ],
  "deferred_to_next_round": [
    "worker-c"
  ]
}
```

This graph declares no gate node, so it closes on the last commit — no `GATE` line, no `[gated]`:

```text
GRAPH: diamond  [done]
goal: produce one merged result from two independent angles
caps: attempts<=3  spawn<=5  budget 3/20

GREEN
  ✓ split                   artifact: a@v1
  ✓ worker-b                artifact: b@v1
  ✓ worker-c                artifact: c@v1
  ✓ merge                   artifact: d@v1
```

**What the scheduler does.** Three rounds, and the middle one is one batch of two. `worker-b` and `worker-c` never communicate: each has `a@v1` in its envelope, its own lens, its own writer path. The merge cannot start until both commits land, because its READY condition is two committed artifacts — and it is a code node, so it costs no spawn.

**What crosses each edge.** `a@v1` (path plus sha256) into both workers; then `b@v1` and `c@v1` (paths plus sha256) into the merge. Only those two lines differ between the merge's envelope and a worker's.

**What the merge does NOT get.** `worker-b`'s and `worker-c`'s conversations, their intermediate reasoning, their lenses, the splitter's framing, and any file that was never committed. It gets paths, so it reads exactly the two versions that were committed.

---

## Example D — Correction: one verdict, one unit returns, one new version

```text
        research-a    research-b                ROUND 1   one batch
             │             │
     findings-a@v1   findings-b@v1             ROUND 2
             └──────┬──────┘         commit skeptic: verdict red, unit findings-a
                    ▼
                 skeptic ─────▶ research-a RED (correction payload attached)
                                   │
                                   ▼          ROUND 3   only research-a re-runs
                             findings-a@v2
                                   │          commit → verifier re-armed
                                   ▼
                 skeptic (attempt 2) → GREEN ROUND 4
                                   │
                                   ▼          ROUND 5   local_nodes: ["merge"]
                                 merge
```

**`graph.json`** — accepted by `init` (exit 0):

```json
{
  "graph": {"id": "research-skeptic",
            "goal": "produce one brief from two researched angles, each held to reproducible evidence"},
  "artifacts": {
    "findings-a": {"type": "findings", "ext": "md", "producer": "research-a", "verifier": "skeptic"},
    "findings-b": {"type": "findings", "ext": "md", "producer": "research-b", "verifier": "skeptic"},
    "verdict":    {"type": "verdict",  "ext": "md", "producer": "skeptic"},
    "brief":      {"type": "report",   "ext": "md", "producer": "merge"}
  },
  "nodes": [
    {"id": "research-a", "kind": "worker", "lens": "angle 1",
     "goal": "research angle 1",
     "green_condition": "every claim carries a source link and a date",
     "requires": [], "produces": "findings-a",
     "output_contract": {"type": "object",
       "properties": {"node": {"type": "string"},
                      "status": {"type": "string", "enum": ["done", "failed"]},
                      "summary": {"type": "string", "minLength": 1},
                      "artifact_path": {"type": "string"}},
       "required": ["node", "status", "summary", "artifact_path"]}},

    {"id": "research-b", "kind": "worker", "lens": "angle 2",
     "goal": "research angle 2",
     "green_condition": "every claim carries a source link and a date",
     "requires": [], "produces": "findings-b",
     "output_contract": {"type": "object",
       "properties": {"node": {"type": "string"},
                      "status": {"type": "string", "enum": ["done", "failed"]},
                      "summary": {"type": "string", "minLength": 1},
                      "artifact_path": {"type": "string"}},
       "required": ["node", "status", "summary", "artifact_path"]}},

    {"id": "skeptic", "kind": "verifier",
     "lens": "disproof: missing sources, stale dates, unsupported numbers",
     "goal": "try to disprove every claim in both artifacts",
     "green_condition": "each claim either survives with its source or is reported red with evidence",
     "requires": [{"artifact": "findings-a"}, {"artifact": "findings-b"}],
     "produces": "verdict",
     "output_contract": {"type": "object",
       "properties": {"node": {"type": "string"},
                      "status": {"type": "string", "enum": ["done", "failed"]},
                      "summary": {"type": "string", "minLength": 1},
                      "artifact_path": {"type": "string"},
                      "verdict": {"type": "string", "enum": ["green", "red"]},
                      "unit": {"type": "string"},
                      "reason": {"type": "string"},
                      "scope": {"type": "string"},
                      "evidence": {"type": "array", "items": {"type": "string"}}},
       "required": ["node", "status", "summary", "artifact_path", "verdict", "unit", "reason", "scope"]}},

    {"id": "merge", "kind": "code",
     "goal": "merge the surviving claims into one brief",
     "green_condition": "one brief exists with every surviving claim's source attached",
     "requires": [{"artifact": "findings-a"}, {"artifact": "findings-b"}],
     "produces": "brief",
     "output_contract": {"type": "object",
       "properties": {"node": {"type": "string"},
                      "status": {"type": "string", "enum": ["done", "failed"]},
                      "summary": {"type": "string", "minLength": 1},
                      "artifact_path": {"type": "string"}},
       "required": ["node", "status", "summary", "artifact_path"]}}
  ]
}
```

The verifier covers two artifacts, so it declares no `on_red.corrects` — `init` refuses that combination, and the verdict's `unit` names the unit to correct instead.

Commands:

```bash
$GS init --spec spec.json --force                                   # exit 0
$GS dispatch                            # ROUND 1 → research-a, research-b (one batch)
$GS commit --node research-a --result results/research-a.a1.json
$GS commit --node research-b --result results/research-b.a1.json
$GS dispatch                            # ROUND 2 → skeptic
$GS commit --node skeptic --result results/skeptic.a1.json          # verdict: red, unit: findings-a
$GS status
$GS dispatch                            # ROUND 3 → research-a, attempt 2, carrying the verdict
$GS commit --node research-a --result results/research-a.a2.json    # findings-a@v2
$GS status                              # the verifier re-armed by itself
$GS dispatch                            # ROUND 4 → skeptic, attempt 2
$GS commit --node skeptic --result results/skeptic.a2.json          # verdict: green
$GS status                              # merge is READY
$GS dispatch                            # ROUND 5 → local_nodes: ["merge"]
$GS commit --node merge --result results/merge.a1.json
```

After the RED verdict is committed — the failed unit is READY to correct, the sibling keeps its GREEN status, and the merge waits:

```text
GRAPH: research-skeptic  [running]
goal: produce one brief from two researched angles, each held to reproducible evidence
caps: attempts<=3  spawn<=5  budget 3/20

READY
  ○ research-a              artifact: findings-a@v1 (unverified)

PENDING
  ○ merge                   artifact: brief (not produced yet)  — findings-a@latest is not verified yet (verifier: skeptic); findings-b@latest is not verified yet (verifier: skeptic)

GREEN
  ✓ research-b              artifact: findings-b@v1 (unverified)
  ✓ skeptic                 artifact: verdict@v1

FAILURES (last 5)
  verification research-a: one claim has no source
```

The `waiting` string on the merge, from `status --json` at the same moment:

```json
{
  "kind": "code",
  "status": "PENDING",
  "attempts": 0,
  "artifact": null,
  "waiting": "findings-a@latest is not verified yet (verifier: skeptic); findings-b@latest is not verified yet (verifier: skeptic)",
  "stale_input": null
}
```

The correction payload, exactly as it sits in `state.json` under `nodes."research-a".correction` and in the attempt-2 envelope under `correction`:

```json
{
  "unit": "findings-a",
  "reason": "one claim has no source",
  "evidence": [
    "'adoption is up 40%' \u2014 no link and no date on line 3"
  ],
  "scope": "findings-a only: attach a source link and a date to every claim",
  "verdict_artifact": {
    "artifact": "verdict",
    "version": 1,
    "path": "C:\\tmp\\ge-ex\\d\\research-skeptic\\artifacts\\verdict.v1.md"
  },
  "verified_artifact": {
    "artifact": "findings-a",
    "version": 1,
    "path": "C:\\tmp\\ge-ex\\d\\research-skeptic\\artifacts\\findings-a.v1.md"
  },
  "at": "2026-09-19T23:01:55Z"
}
```

The attempt-2 dispatch returns exactly one task, and its envelope's `limits` say which attempt this is:

```json
[
  {
    "node": "research-a",
    "attempt": 2,
    "task_index": 0,
    "envelope": "C:\\tmp\\ge-ex\\d\\research-skeptic\\envelopes\\research-a.a2.json"
  }
]
```

```json
{
  "max_attempts": 3,
  "attempt": 2
}
```

Committing `findings-a@v2` re-arms the verifier without anyone asking it to re-run, and the merge stays pending until the new version is verified:

```text
GRAPH: research-skeptic  [running]
goal: produce one brief from two researched angles, each held to reproducible evidence
caps: attempts<=3  spawn<=5  budget 4/20

READY
  ○ skeptic                 artifact: verdict@v1

PENDING
  ○ merge                   artifact: brief (not produced yet)  — findings-a@latest is not verified yet (verifier: skeptic); findings-b@latest is not verified yet (verifier: skeptic)

GREEN
  ✓ research-a              artifact: findings-a@v2 (unverified)
  ✓ research-b              artifact: findings-b@v1 (unverified)

FAILURES (last 5)
  verification research-a: one claim has no source
```

After the GREEN verdict on attempt 2:

```text
GRAPH: research-skeptic  [running]
goal: produce one brief from two researched angles, each held to reproducible evidence
caps: attempts<=3  spawn<=5  budget 5/20

READY
  ○ merge                   artifact: brief (not produced yet)

GREEN
  ✓ research-a              artifact: findings-a@v2
  ✓ research-b              artifact: findings-b@v1
  ✓ skeptic                 artifact: verdict@v2

FAILURES (last 5)
  verification research-a: one claim has no source
```

`findings-a` ends at `{"verified_version": 2, "latest": 2}` — `v1` is still on disk, marked rejected, and is not deleted.

**What the scheduler does.** A red verdict is a commit like any other: the graph marks the failing unit RED, clears `verified_version`, re-arms the verifier for the *new* version only when one exists, and keeps every sibling GREEN. Attempt 2 re-runs one node, not the batch. The verifier's own re-run is not a retry policy — it is the rule that a changed version invalidates the old verdict.

**What crosses each edge.** Into the verifier: two committed paths. Back along the correction edge: the verdict (unit, reason, evidence, scope), the path of the verdict file, and a pointer to the rejected `findings-a@v1`. Into the merge, after the second verdict: the two verified paths.

**What the corrected worker does NOT see.** `research-a`'s envelope for attempt 2 contains no `findings-b` path, no sibling artifact of any kind, no other worker's reasoning, and no part of the orchestrator's history — only its own previous version by path, the verdict against it, and its scope. `research-b` is never re-dispatched and never learns that a sibling failed.

---

## Example E — Fake edge: the wait that cannot be written down

```text
summarize a file    ─╳─▶   check the calendar
        (no artifact crosses, so there is no edge to write)
```

The first spec tries to express "and then" with a key the schema does not have:

```json
{
  "graph": {"id": "fake-edge", "goal": "summarize a file and check a calendar"},
  "artifacts": {
    "x": {"type": "report", "ext": "md", "producer": "a"},
    "y": {"type": "data",   "ext": "md", "producer": "b"}
  },
  "nodes": [
    {"id": "a", "kind": "worker", "goal": "summarize the file",
     "green_condition": "a summary exists", "requires": [], "produces": "x",
     "output_contract": {"type": "object",
       "properties": {"node": {"type": "string"},
                      "status": {"type": "string", "enum": ["done", "failed"]},
                      "summary": {"type": "string", "minLength": 1},
                      "artifact_path": {"type": "string"}},
       "required": ["node", "status", "summary", "artifact_path"]}},

    {"id": "b", "kind": "worker", "goal": "check the calendar",
     "green_condition": "the conflicts are listed", "requires": [], "produces": "y",
     "depends_on": ["a"],
     "output_contract": {"type": "object",
       "properties": {"node": {"type": "string"},
                      "status": {"type": "string", "enum": ["done", "failed"]},
                      "summary": {"type": "string", "minLength": 1},
                      "artifact_path": {"type": "string"}},
       "required": ["node", "status", "summary", "artifact_path"]}}
  ]
}
```

`init` rejects it — exit code 2, nothing written:

```text
graph_state: node b has unknown key(s): depends_on. Edges exist ONLY as artifact requirements (`requires`), so an ordering-only dependency cannot be written down — name the artifact that crosses the edge, or delete the wait.
```

The same refusal protects the neighbouring mistake: naming an artifact in `requires` that nobody produces, or that exists but has no producer, is also an exit-2 rejection rather than a node that waits forever.

Delete the fake edge (and `depends_on` with it) — this spec is accepted by `init` (exit 0):

```json
{
  "graph": {"id": "fake-edge", "goal": "summarize a file and check a calendar"},
  "artifacts": {
    "x": {"type": "report", "ext": "md", "producer": "a"},
    "y": {"type": "data",   "ext": "md", "producer": "b"}
  },
  "nodes": [
    {"id": "a", "kind": "worker", "goal": "summarize the file",
     "green_condition": "a summary exists", "requires": [], "produces": "x",
     "output_contract": {"type": "object",
       "properties": {"node": {"type": "string"},
                      "status": {"type": "string", "enum": ["done", "failed"]},
                      "summary": {"type": "string", "minLength": 1},
                      "artifact_path": {"type": "string"}},
       "required": ["node", "status", "summary", "artifact_path"]}},

    {"id": "b", "kind": "worker", "goal": "check the calendar",
     "green_condition": "the conflicts are listed", "requires": [], "produces": "y",
     "output_contract": {"type": "object",
       "properties": {"node": {"type": "string"},
                      "status": {"type": "string", "enum": ["done", "failed"]},
                      "summary": {"type": "string", "minLength": 1},
                      "artifact_path": {"type": "string"}},
       "required": ["node", "status", "summary", "artifact_path"]}}
  ]
}
```

Both jobs run together:

```bash
$GS init --spec spec.json --force                                  # exit 0
$GS dispatch                          # ROUND 1 → a and b, one batch
$GS commit --node a --result results/a.a1.json
$GS commit --node b --result results/b.a1.json
$GS status
```

Fields of that round's `dispatch` — `b` is dispatched in the same batch as `a`:

```json
{
  "bindings": [
    {
      "node": "a",
      "attempt": 1,
      "task_index": 0,
      "envelope": "C:\\tmp\\ge-ex\\e\\fake-edge\\envelopes\\a.a1.json"
    },
    {
      "node": "b",
      "attempt": 1,
      "task_index": 1,
      "envelope": "C:\\tmp\\ge-ex\\e\\fake-edge\\envelopes\\b.a1.json"
    }
  ],
  "local_nodes": [],
  "deferred_to_next_round": []
}
```

```text
GRAPH: fake-edge  [done]
goal: summarize a file and check a calendar
caps: attempts<=3  spawn<=5  budget 2/20

GREEN
  ✓ a                       artifact: x@v1
  ✓ b                       artifact: y@v1
```

**What the scheduler does.** One round instead of two. Both nodes are READY in the same pass because neither requires the other's artifact, and they are dispatched as one batch.

**What crosses each edge.** Nothing — there is no edge. `b`'s envelope contains no input path, and no version of `x` appears anywhere in it.

**What the workers do NOT see.** Each other, entirely. `b` does not wait for `a`, does not read `a`'s summary, and cannot be told that `a` finished. If the work genuinely needed the summary, the artifact would have to cross, and that is Example B — two rounds, and a PENDING node that names what it is missing. An ordering-only dependency would cost the same two rounds and buy nothing, which is why there is no field to write it.

---

## The three sentences, checked against all five

> Workers are isolated. The graph is not.

> Agents do not coordinate through shared conversations. They coordinate through explicit graph state, artifacts, dependencies, and the orchestrator.

> Spawning executes nodes; it does not define the graph.
