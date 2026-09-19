# Wiring Rules: Keep a Graph From Becoming an Expensive Accident

Five guardrails. Apply them every time you build or run a graph.

## 1. Bounded everything

**Rule:** Every cycle carries a cap; every run has a budget.

| Cap | Default | At the cap |
|-----|---------|-----------|
| attempts per node | 3 | ESCALATED → back to graph design |
| spawns per round | 5 | defer the surplus to the next round |
| spawn budget per run | 20 | stop spawning → back to graph design |

- The attempt count lives in Graph State. A worker cannot extend its own budget, and no loop is unbounded.
- Spawn cap is `min(graph cap, delegation.max_concurrent_children)` — Hermes rejects an oversized batch rather than truncating it.
- **When the cap hits, stop correcting.** A unit that fails three attempts is not failing; the plan that produced it is. Escalate with the verdict, reason and evidence — then fix the split, the check, or the brief.

## 2. One writer per path — including state

**Rule:** every artifact has exactly one producing node; only the orchestrator writes Graph State.

| Good | Avoid |
|------|--------|
| `audit-auth` → `auth-findings.v1.md`, `audit-api` → `api-findings.v1.md` | both writing `findings.md` |
| orchestrator commits every result | workers writing `state.json` |
| merge is a code node producing `report.v1.md` | two nodes appending to the report |

Parallel writers collide, and a shared mutable state file has no owner and no last-writer-wins story worth telling. Workers produce outputs; the orchestrator commits them.

The commit step enforces this rather than trusting it: the artifact path in a worker's contract is compared to the path its envelope designated, and a mismatch is rejected.

**Correction returns are per-unit.** Send a failed unit back to the node that produced it, never the whole batch: batching rewrites work that was correct, re-verifies all of it, and stops converging (`references/return-paths.md`).

## 3. Deterministic routing: code owns the edges

**Rule:** the graph owns the edges; the model fills the nodes.

- Edges are declared as artifact requirements and computed by the scheduler. A model never invents a next step.
- Readiness, blocking, versioning, hashing, contract re-validation and state updates are code (`scripts/graph_state.py`).
- Anything with exactly one correct answer (compare, dedupe, rank, filter, route) is a **code node**, not a model call (`references/node-types.md`).
- A conditional edge is a declared condition evaluated by code — not a label the model hopes matches something.

```text
if report.severity >= high:  gate(block)      # written in the plan, evaluated by code
else:                        merge
```

A hallucinated output with no matching edge goes nowhere. Design the fallback, or make the missing case impossible.

## 4. Verification gates consumption

**Rule:** if an artifact declares a verifier, no consumer runs until that verifier is GREEN.

"Verify first, merge second" is enforced by readiness, not by discipline. An unverified artifact is not an input — the consumer's status says so, with the reason and the verifier's name.

A verifier that only re-reads the producer's reasoning is the same agent grading its own homework. It requires the artifact, not the conversation.

## 5. Spawning executes; it does not define the graph

**Rule:** the graph decides what runs; `delegate_task` runs it.

- Nodes are not spawned "to coordinate". If two nodes need to exchange something, an artifact crosses between them and the scheduler orders the rounds.
- The spawn cap is a control, not polish. Block overflow instead of letting a prototype spawn dozens of subagents.
- Never nest a graph inside a node unless the subgraph genuinely improves it — and remember the parent still has to know which artifact the subgraph produces (`references/scheduler.md`).
- A code node is not a spawn. Deterministic work runs locally and costs no context.

## Quick checklist

- [ ] Attempt cap, spawn cap and spawn budget set
- [ ] Every artifact has one producer; only the orchestrator writes state
- [ ] Every edge names the artifact it carries; no ordering-only waits
- [ ] Every node declares inputs, green condition, output contract, writer path
- [ ] Verifiers require what they verify; consumers wait for verification
- [ ] Deterministic steps run as code nodes, not model calls
- [ ] Correction returns carry unit · verdict · reason · evidence · scope, and only the unit
- [ ] Cap exhaustion escalates to the plan, not to another attempt
- [ ] Every node's status is explainable from committed state (`status` shows why it waits)
