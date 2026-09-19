# Graph State: One Owner, Versioned Artifacts, One Commit Step

Workers are isolated, so nothing is true because a worker said so. Something is true when the **orchestrator commits it**.

```text
worker result
      ↓
contract validation      (Hermes validates output_schema; the commit step re-checks the graph's own rules)
      ↓
verification if declared (a separate verifier node, never the producer)
      ↓
commit
      ↓
Graph State
```

## One writer

```text
Workers produce outputs. The orchestrator commits them.
```

- **Only the orchestrator writes `state.json`.** No worker, no verifier, no code node touches it. Three agents writing `state.json` is a race with no owner and no last-writer-wins story worth telling.
- Each worker writes exactly one artifact at the path its envelope named. One writer per path.
- A worker that writes anywhere else is rejected at commit — the path is compared, not trusted.

That is the whole concurrency story. It is boring on purpose.

## Where state lives

```text
<root>/<graph-id>/
  state.json                  ← the only authoritative record; orchestrator-only
  artifacts/<id>.v<n>.<ext>   ← artifact bodies, one file per version, never overwritten
  envelopes/<node>.a<n>.json  ← the exact envelope handed to each attempt
  results/<node>.a<n>.json    ← the child's returned contract, verbatim
  discarded/                  ← artifact files from attempts that never committed
<root>/constraints.json       ← learning constraints, shared by every graph under this root
```

Default root: `.graph` under the workspace. Absolute paths are what the envelopes carry, so a child resolves them directly. Two Hermes settings change where that root must be — see `references/hermes-runtime.md`.

## Artifacts are first-class

An artifact is output one node produces and another node consumes.

```yaml
artifact: auth-findings
producer: audit-auth
version: 2
type: findings
path: .graph/repo-audit/artifacts/auth-findings.v2.md
sha256: 9aa42157…
verified: true
```

Types are free-form (`findings`, `evidence`, `code-change`, `plan`, `test-result`, `data`, `report`, `verdict`, `constraint`, `intermediate`) — they exist so a reader can tell what crosses an edge.

Rules:

1. **Versioned, never overwritten.** A correction produces `v(n+1)`; `v(n)` stays on disk for inspection. No ambiguous overwriting, ever.
2. **One producer.** An artifact id has exactly one producing node. Two writers would make "which version is real" undecidable.
3. **Verified or unverified.** If the graph declares a verifier for an artifact, consumers wait for `verified_version`. Unverified output does not flow downstream.
4. **Superseding verified output is explicit.** Revising an artifact other nodes already consumed requires a stated reason (`--supersedes`), which flags those consumers instead of silently rewriting them.
5. **Referenced, not pasted.** Envelopes carry id, version, type, path, sha256 — not the text.

## Node records

Every node carries its status, its attempt history, and — per attempt — the exact artifact versions it was given. That last part is what makes staleness detectable instead of invisible:

```yaml
node: audit-auth
status: GREEN
attempts:
  - attempt: 1
    inputs: [{artifact: inventory, version: 1}]
    artifact_target: …/auth-findings.v1.md
    artifact_version: 1
```

If `inventory` later becomes `v2`, the attempt above is visibly built on `v1`. The graph does not pretend otherwise.

## Statuses

```text
PENDING   not yet runnable — an input is not committed (the record says which)
READY     every required input is committed and verified; eligible to dispatch
RUNNING   dispatched; an attempt is open
GREEN     committed: contract valid, artifact on disk, verification passed where declared
RED       the attempt failed, or a verifier rejected this unit — eligible for correction while attempts remain
BLOCKED   an upstream producer died terminally (ESCALATED) — this node will not run with incomplete inputs
ESCALATED attempts exhausted: stop correcting and return to graph design
WAITING_HUMAN  a gate: no model can open it
```

`PENDING`, `READY` and `BLOCKED` are **recomputed from dependencies**, not remembered. A consumer whose producer recovers unblocks by itself — nothing has to send it a message.

## The commit step is code, not a model call

Deterministic work belongs to code. The commit step does all of this without a single token:

```text
parse the child's contract JSON
validate it against the node's output contract
confirm the artifact exists at the declared path and hash it
assign the version, record the sha256
record the attempt's inputs
flip the node, re-arm its verifier, recompute READY/BLOCKED
cascade: which consumers are now runnable, stale, or blocked
append to the history log
```

No model is asked to compare, route, dedupe, or update state. This is the same rule as code nodes (`references/node-types.md`), applied to the graph's own plumbing: **one correct answer means code.**

## The command surface

One stdlib-only script ships with the skill: `scripts/graph_state.py`. It is the commit step, the scheduler's bookkeeping, and the envelope generator. The orchestrator calls it; nobody else does.

```bash
GS="python ${HERMES_SKILL_DIR}/scripts/graph_state.py --root .graph"

$GS init --spec graph.json          # validate the design, create state.json
$GS status                          # what ran, what is ready, what waits and why
$GS dispatch                        # emit ready nodes as delegate_task payloads
$GS commit --node audit-auth --result results/audit-auth.a1.json
$GS escalate --node audit-auth --reason "split is wrong"
$GS reopen --node audit-auth --reason "the user says the evidence is wrong" --user-approval "…"
$GS gate --status approved --user-approval "yes, merge it"
$GS learn --constraint "adapters preserve kwargs" --node port-utils --promote --user-approval "yes"
$GS validate                        # check state invariants
```

What `init` refuses to accept, and why each refusal is a rule rather than a style preference:

| Refusal | Rule it protects |
|---------|------------------|
| Unknown node keys (`depends_on`, `after`, …) | Edges exist only as artifact requirements — fake edges are unrepresentable |
| `requires` naming an artifact with no producer and no seed | Every edge has a named thing crossing it |
| Two producers for one artifact | Unambiguous artifact ownership |
| A verifier that does not require what it verifies | The verifier reads the artifact, not the producer's reasoning |
| A verifier covering several artifacts while naming one `on_red.corrects` | One unit returns, not a batch — the verdict's `unit` picks it |
| A contract missing `node`/`status`/`summary`/`artifact_path` | Every commit can be checked without a model |
| A verifier contract missing `verdict`/`unit`/`reason`/`scope` | The correction edge has a payload |
| Cycles | A dependency plan, not a loop |

## Reading the status view

`status` renders committed state — never a chain of thought. Execution state, artifacts, versions, dependencies and verdicts only:

```text
GRAPH: repo-audit  [running]
goal: Audit the auth + api subsystems and produce one report
GATE: not_reached (lane: reversible, wide) — action: merge report into docs/audit.md
caps: attempts<=3  spawn<=5  budget 4/20

READY
  ○ audit-auth              artifact: auth-findings@v1 (unverified)

PENDING
  ○ merge-report            artifact: report (not produced yet)  — auth-findings@latest is not verified yet (verifier: verify-findings)

WAITING_HUMAN
  ★ gate-1

GREEN
  ✓ inventory               artifact: inventory@v1
  ✓ audit-api               artifact: api-findings@v1 (unverified)
  ✓ verify-findings         artifact: findings-verdict@v1

FAILURES (last 5)
  verification audit-auth: no repro for finding 3
```

The user can answer "why is this waiting?" without asking anyone: the reason names the artifact, the version requirement, and the verifier holding it. `--json` gives the same facts to a script.

## Constraints: how learning enters state

Graph-local constraints live in the graph's state; promoted learning constraints live in `<root>/constraints.json` and are rendered into **every later envelope**, including graphs that have not been designed yet. That is what makes a learning edge change future execution rather than decorate a report.

A constraint is `proposed` until a human promotes it: only an accepted (GREEN) outcome may propose one, and promotion needs explicit approval. See `references/return-paths.md`.

## The gate record

The gate is part of state, not a vibe in the conversation:

```yaml
gate:
  lane: hard to reverse
  action: publish to production
  status: waiting
  approvals: []          # every entry records the user's own words
```

A `hard to reverse` lane cannot be approved without an explicit user approval quoted into the record. Model confidence is not an input.

When a gate node declares a `decision` artifact, the answer is also committed as a versioned artifact — so anything downstream that requires it is held by the scheduler rather than by the orchestrator's discipline, and the pause is auditable like any other artifact. A rejection marks the decision rejected (consumers BLOCKED); a later explicit approval commits a new version and releases them.
