# The Scheduler: Rounds, Readiness, Failure

Graph Engineer does not spawn a group of agents and hope they coordinate. It computes which nodes are runnable, spawns exactly those, commits what comes back, and recomputes.

```text
while the graph has unfinished work:

    determine READY nodes          (dependencies committed, verification passed)
    spawn READY nodes              (up to the spawn cap, as ONE delegate_task batch)
    collect outputs                (Hermes delivers the batch when the call finishes)
    validate outputs               (contract, artifact on disk, verification where declared)
    commit accepted outputs        (Graph State is updated by the orchestrator only)
    process failures               (correction, block downstream, or escalate)
    recompute READY
    continue
```

Hermes is the execution substrate. Graph Engineer owns the schedule.

## Readiness is computed, never remembered

A node is `READY` when:

```text
every required input artifact has a committed version
AND, if the graph declares a verifier for that artifact, that version is verified
AND the node is not already RUNNING, GREEN, or ESCALATED
AND attempts remain
```

Three properties fall out of that, for free:

- **Verify-before-consume.** A consumer of a verified artifact cannot run before its verifier is GREEN. "Verify first, merge second" is not a discipline anyone has to remember; it is what `READY` means.
- **No downstream execution on incomplete inputs.** A node whose required artifact is missing is `PENDING`, and the record says which artifact and why.
- **Recovery is automatic.** When a producer goes GREEN, consumers recompute from `PENDING` to `READY`. No worker needs to be told.

Optional inputs (`required: false`) are included when available and never gate anything.

**Gates are part of readiness.** A gate node is never dispatched and never opens itself; a human answers it. If the gate produces a decision artifact, every node that requires it waits — `PENDING — gate X has not been answered yet`, or `BLOCKED — gate X was rejected`. That is what makes a mid-graph pause a real dependency rather than a promise to stop (`references/gate-design.md`).

The graph itself carries one status, recomputed from the nodes:

| Graph status | Meaning |
|--------------|---------|
| `planned` | designed and validated; nothing dispatched yet |
| `running` | work is in flight or runnable |
| `gated` | a declared gate is unanswered and nothing is in flight — the only thing outstanding is the human |
| `blocked` | the gate was rejected, or a dependency died terminally |
| `needs_plan_review` | a node hit its attempt cap or committed work was reopened: fix the plan, do not spawn attempt N+1 |
| `done` | every non-gate node is GREEN and any declared gate is approved |

## Rounds

A round is one `dispatch` → one `delegate_task(tasks=[...])` batch → one commit pass.

```text
        A
       / \
      B   C
       \ /
        D

ROUND 1   dispatch → [A]        commit A
ROUND 2   dispatch → [B, C]     one batch: B and C run in parallel, one consolidated result
                                commit B, commit C
ROUND 3   dispatch → [D]        D's envelope carries B@v1 and C@v1
                                commit D
```

**B and C never communicate.** They do not need to. Neither does D need their conversations — it needs their committed artifacts, and those are paths in its envelope.

Hermes batches results per call: a top-level `delegate_task` returns a handle immediately and delivers the batch between turns. That turn boundary is the round boundary — not a limitation to engineer around, just where the scheduler ticks. Inside an orchestrator child (nested delegation), the batch is waited on in-turn instead.

With `delegation.independent_completions: true`, results can land **per node** (or per `group`) as each finishes, which gives finer-grained rounds at the cost of more orchestrator turns. Grouping controls delivery only — everything in a call still runs in parallel. Either way, a node is committed when its result lands and its contract checks out; never before.

## Concurrency

- Spawn cap default **5** per round, and never more than Hermes' `delegation.max_concurrent_children` (default 10 — a larger batch is a tool error, not a truncation).
- More READY nodes than the cap → the surplus is **deferred to the next round**, named in the dispatch output. Nothing is silently dropped.
- A spawn budget (default 20) bounds the whole run. At the budget, stop spawning and return to graph design.
- **Code nodes are not spawned.** `dispatch` returns them under `local_nodes` with their envelopes; the orchestrator runs them with `execute_code`/`terminal` and commits the result. Deterministic work costs no spawn and no model call.

## Failure semantics

Every one of these is a state transition, not a judgement call:

| What happened | Node | Downstream |
|---------------|------|------------|
| Child returns `status: done`, contract valid, artifact on disk | GREEN (after verification if declared) | recompute → READY |
| Child returns `status: failed` | RED, reason recorded | waits |
| Contract invalid after Hermes' one bounded retry | RED, `schema_valid: false`, raw text kept | waits |
| Verifier returns `verdict: red` for a unit | that producer RED, with the verdict attached | only that unit returns |
| Child `status: failed` / `timeout` / `interrupted` / `stalled` | RED — an interruption is not evidence about the unit | waits; re-dispatch is a new attempt |
| Child `exit_reason: max_iterations`, `truncated: true` | RED, scope too big for one node | escalate if it repeats |
| Artifact file missing at the declared path | commit rejected; the unit is RED | waits |
| Required input never committed | PENDING with the artifact named | — |
| Producer ESCALATED | its consumers BLOCKED | escalate to graph design |
| Attempt cap reached | ESCALATED | graph status `needs_plan_review` |
| Spawn budget reached | no further spawns | escalate to graph design |
| Human gate rejected | gate BLOCKED | graph stops; nothing ships |

Two rules keep this honest:

> **Do not continue with incomplete context.** A node whose required input failed becomes BLOCKED. It never receives a half-populated envelope and a hopeful instruction.

> **At the cap, suspect the plan.** A unit that fails its attempts is not a unit failure — the split, the check, or the brief is wrong. Escalate with the verdict, reason and evidence, and fix the graph. Do not spawn attempt four.

## The correction loop, in scheduler terms

```text
verify-findings  →  verdict: red, unit: auth-findings, reason, evidence, scope
                 ↓  commit
auth-findings rejected (verified_version cleared)
audit-auth       →  RED, correction payload attached
                 ↓  next dispatch
audit-auth attempt 2: envelope = its own last artifact @v1 + the verdict + the scope
                 ↓  commit
auth-findings @v2  →  verifier re-armed (PENDING), because the version changed
                 ↓  dispatch
verify-findings attempt 2  →  verdict green
                 ↓  commit
auth-findings verified @v2 → consumers recompute to READY
```

Only the failed unit re-runs. Siblings keep their GREEN status and are never re-dispatched. The verifier re-arms because a new version exists — that is the graph's own integrity rule, not a retry policy.

## Stale inputs

If a producer commits a new version of an artifact that a downstream node **already consumed**, the graph does not silently re-run the batch. It marks the consumer `stale_input`, records it as a failure, and returns the graph to `needs_plan_review`. That situation means the graph let an unverified artifact flow, or revised accepted output — a design problem, and the honest response is a decision, not a cascade.

## Caps

| Cap | Default | Behaviour at the cap |
|-----|---------|----------------------|
| attempts per node | 3 | ESCALATED → graph design |
| concurrent spawns per round | 5 | defer the surplus to the next round |
| spawn budget per run | 20 | stop spawning → graph design |
| loop rounds inside a node | the same 3 attempts | the unit returns with evidence, then escalate |

Caps exist so the scheduler terminates. Nothing in this design loops without a bound.
