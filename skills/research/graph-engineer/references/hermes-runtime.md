# The Hermes Runtime: What Actually Exists

Everything in this skill is built on the primitives below, as documented for current Hermes. Nothing here is aspirational: if a capability is not in this file, the skill does not use it.

## `delegate_task` — the execution primitive

```python
delegate_task(tasks=[                # one entry per node; a batch runs concurrently
    {
        "goal": "…",                 # the job, one paragraph
        "context": "…",              # everything the child needs; it has nothing else
        "output_schema": {…},        # JSON Schema the child's final answer must validate against
        "images": ["/abs/path.png"], # optional, max 8 — for tasks that must see pixels
        "group": "bench",            # optional — groups result delivery (see below)
    },
])
```

The legacy single-task shape (`goal=` / `context=` / `output_schema=` at top level) is still accepted but unadvertised. `role=` is accepted for wire compatibility and **ignored**: a child's role is derived from its depth, not from the argument.

| Fact | Consequence for a graph |
|------|-------------------------|
| Children start with a **completely fresh conversation** | The envelope is the entire input. There is no "it already knows" |
| Only `goal`, `context`, `output_schema` and optional `images` cross into the child | Graph State must be rendered into an envelope, per node, per attempt |
| The workspace's project context files (`.hermes.md` → `AGENTS.md` → `CLAUDE.md` → `.cursorrules`) are injected | Repo conventions arrive for free; graph-specific facts do not |
| Only the child's **final summary** enters the parent's context | Intermediate reasoning stays out of the parent; artifacts are read from disk |
| Results carry `status` (`completed`/`failed`/`timeout`/`interrupted`/`stalled`, plus `error` and `unknown`), `error`, `exit_reason`, `truncated`, `summary` | Failure semantics are state transitions, not guesses (`references/scheduler.md`) |
| `output_schema` is shown to the child up front as a contract | Output contracts are native, not a prompt convention |
| On a contract miss, Hermes sends **one** bounded correction turn with the validation errors | The graph gets one free, bounded repair per attempt — then `schema_valid: false` with the raw text preserved |
| A failed validation does not discard the work | The commit step can still salvage a raw-text result instead of re-running an hour of work |
| Children inherit the parent's toolsets; the model cannot widen them | A node cannot be granted capabilities the parent lacks — design within them |
| Leaf children **cannot** call `delegate_task`, `clarify`, `memory`, `send_message`, `cronjob` | No worker can talk to the user, mutate shared memory, or spawn its own swarm. The orchestrator owns all of that |
| Children retain `execute_code` and their own terminal | Verifiers can run checks; code nodes are real code |
| Concurrency: `delegation.max_concurrent_children`, default 10; **a larger batch is a tool error**, not truncation | The spawn cap must be `min(graph cap, configured limit)` |
| Top-level batches run in the background and deliver **between turns** | A round is a turn boundary — dispatch, then commit what came back |
| Orchestrator children wait for their workers in-turn | Nested delegation is the only way to run a subgraph synchronously |
| `delegation.independent_completions: true` (opt-in) delivers results **per unit or per `group`** instead of one consolidated message; `group` is only advertised when that option is on | Optional: finer-grained rounds at the cost of more orchestrator turns. Grouping controls delivery, never execution — everything in a call still runs in parallel |
| `max_iterations` (default 250) caps a child's turns; `exit_reason: max_iterations`, `truncated: true` | "Scope too big for one node" is detectable and means escalate, not retry |
| No wall-clock timeout by default; a progress-based stall monitor interrupts frozen children (450s idle / 1200s in a tool) | A wedged child cannot hold a run forever; a busy one is never killed |
| `delegation.model` pins **all** children to one model; there is no per-task model parameter | A graph cannot give its verifier a stronger model or its workers a cheaper one |
| `delegation.worktree_isolation: true` gives each child its own git worktree — git-only, local-terminal-backend-only, and it **degrades silently** to a shared checkout otherwise | Absolute artifact paths outside the repo stay shared; paths inside the repo do not. Keep the graph root out of the repo, or turn the setting off for the run |
| Live transcripts: `<hermes_home>/cache/delegation/live/<delegation_id>/task-<n>.log` + `manifest.json` | Observability beyond the summary, without polluting the parent's context |
| Control: `{"action": "list"}`, `{"action": "steer", "subagent_id": …, "message": …}`, `{"action": "stop", "subagent_id": …}` | The orchestrator can inspect, mid-run redirect, and stop its own children. A steer that arrives too late comes back as `missed_steer` — never as silent success |
| Nested delegation requires `delegation.max_spawn_depth > 1` (default 1 = flat) and `delegation.orchestrator_enabled: true`; the runtime derives a child's role from its depth | Nested graphs are opt-in and must not be assumed. The `role` argument is ignored |
| One-shot runs (`hermes chat -q`) cap total spawns (`delegation.oneshot_max_children`, default 2) | A graph run inside a one-shot session will hit a hard wall — say so before designing one |
| A process restart does not resume a running child; its record becomes `unknown` | There is no durable execution here. For that, Hermes points at `cronjob` or the Kanban board |
| No session-scoped shared-state primitive exists (`todo` is per-agent, in-memory) | "One writer" is a convention the skill enforces with a script, not a runtime guarantee |

## Mapping: primitive → what the graph uses it for

| Graph concept | Hermes primitive |
|---------------|------------------|
| Node execution | one entry in `delegate_task(tasks=[…])` |
| Node Input Envelope | that entry's `goal` + `context` + `output_schema` (+ `images` when the node must see pixels) |
| Output contract | `output_schema` (Hermes validates; the commit step re-checks) |
| Worker's result | the child's contract JSON, written to the path the envelope names — a **skill convention**: Hermes has no `return_file` field. Hermes returns the same text as `summary`, plus `schema_valid` / `schema_errors` |
| Artifact | a file under the graph root, hashed and versioned at commit |
| Scheduler round | one batch dispatch + one commit pass |
| Spawn cap | `min(graph cap, delegation.max_concurrent_children)` |
| Observability | `graph_state.py status` (state), plus Hermes live transcripts (per child) |
| Human gate | the parent's turn — children cannot `clarify`, so no worker can approve anything |
| Nested subgraph | `delegation.max_spawn_depth > 1` + `orchestrator_enabled` (opt-in; the `role` argument is ignored) |
| Durable/queued execution | Kanban board (a different primitive; see below) |

Also available, and used only where a node needs it: `images` (up to 8) for visual inputs; `failure_reason` / `timeout_seconds` / `timeout_phase` on failed results; `orphaned_processes` and `unread_completions` so a child's background work is never silently lost; `process_manage(action="handoff")` when a child must hand a running process to the parent.

## Kanban, and why this skill does not use it

Hermes also ships a durable task board (`kanban_*` tools, SQLite, dispatcher, links, per-task model override, human comments). It is the right substrate when work must survive restarts, cross agent identities, or wait on humans over days.

Graph Engineer does not use it, because the semantics needed here are different:

- a graph needs **artifact-typed edges and versioned commits**, not task links;
- a graph needs **one authoritative state owner** in the current session, not a peer-writable queue;
- the skill must stay portable and dependency-free.

If a graph must outlive the session, Kanban is the documented escape hatch — but say so explicitly instead of pretending `delegate_task` is durable.

## Limitations

### Solved inside Graph Engineer

- **Isolated workers.** Handled by envelopes generated from committed state: nothing a worker needs is assumed to be in its head.
- **Cross-node knowledge transfer.** Handled by artifacts on disk referenced by path — not by prompts, not by history.
- **State ownership.** Handled by a single writer (the orchestrator) and a single `state.json`.
- **Determinism.** Readiness, blocking, versioning, contract re-validation, hashing, routing, dedupe and state updates are code (`scripts/graph_state.py`), not model calls.
- **Contract enforcement.** `output_schema` for the child + a commit-time re-check for the graph's own rules (artifact exists, path matches, unit resolvable).
- **Bounded execution.** Attempt cap, spawn cap, spawn budget, escalation to graph design.
- **Worktree isolation.** Handled by keeping the artifact root outside the repo, or by disabling the setting for the run.

### Would require Hermes core changes (documented, not depended on)

1. **Structured child results.** The parent gets the child's summary text plus `schema_valid`/`schema_errors`; a validated payload is not exposed as a first-class field. The skill works around it by having each child write its contract JSON to the path its envelope names (the envelope's `return_file` is **skill vocabulary**, not a Hermes field) and committing that file. *Core improvement: expose the parsed, validated result payload to the parent.*
2. **Per-node model choice.** `delegation.model` is global. A graph cannot run its verifier on a stronger model and its workers on a cheaper one. *Core improvement: a per-task model override on `delegate_task` (Kanban already has one).*
3. **A session-scoped shared state store.** There is no KV/state primitive with locking, so "one writer" is a convention enforced by the skill rather than by the runtime. *Core improvement: a session-scoped state store with a single-writer lease.*
4. **A declared artifact contract per task.** Nothing tells the runtime that a child must leave a file at a given path, so the commit step has to verify it. *Core improvement: an `expected_artifacts` field, verified by the runtime and reported on the result.*
5. **In-turn waiting for top-level batches.** Rounds tick at turn boundaries unless delegation is nested (which requires raising `max_spawn_depth`). *Core improvement: an opt-in synchronous wait for a top-level batch.*
6. **Durable execution.** A restart mid-run leaves the child `unknown`; there is no resumption. *Core improvement: none needed — use Kanban or `cronjob` for that class of work.*
