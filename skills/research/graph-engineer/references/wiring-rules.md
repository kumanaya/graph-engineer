# Wiring Rules: Keep a Graph From Becoming an Expensive Accident

Four guardrails. Apply them every time you build or run a graph.

## 1. Loop prevention

**Rule:** Every cycle carries a cap and dedupes against everything seen.

- Set a **max rounds** (default: 3). Stop when the cap hits.
- Maintain a **seen list** so the same finding/path is not reprocessed.
- Without both, agents loop and burn budget.
- The loop lives **inside** a box, not around the graph: each box repeats produce → check → correct until its own green condition passes (`references/loop-design.md`).

**When the cap hits, stop correcting.** A unit that fails three corrections is not failing; the plan that produced it is. Escalate with the verdict, reason and evidence — then fix the split, the check, or the brief.

## 2. Concurrency: one writer per file

**Rule:** Parallel writers collide; merge at the end instead.

| Good | Avoid |
|------|--------|
| Agent A → `FileA.md`, Agent B → `FileB.md` | Agent A and Agent B both write `FileA.md` |

Each parallel job owns a unique path. A final merge job combines into the shared result — and that merge is usually a **code node** (dedupe, rank, concat), not a model call.

**Correction returns are per-unit.** Send a failed unit back to the box that produced it, never the whole batch: batching rewrites work that was correct, re-verifies all of it, and stops converging (`references/return-paths.md`).

## 3. Deterministic routing: code owns the edges

**Rule:** The plan (written steps / if-else) owns the edges; the model fills the nodes.

Example shape:

```text
if score >= 0.7:
    go("high_path")
else:
    go("low_path")
```

- Routing decisions are explicit in the workflow plan
- The model produces content inside jobs, not invents next-step labels
- A hallucinated output with no matching edge goes nowhere — design fallbacks in the plan
- Anything with exactly one correct answer (compare, dedupe, rank, filter, route) is a **code node**, not a model call (`references/node-types.md`)

## 4. Resource control: spawn limits

**Rule:** Spawn limits are a control, not polish.

- Cap active parallel agents (default: 5 unless a named graph specifies otherwise)
- Block overflow instead of letting prototypes spawn dozens of subagents
- Track active workers; refuse new spawns above the cap until a slot frees

## Quick checklist

- [ ] Max rounds set on every loop
- [ ] Seen list / dedupe in place
- [ ] Every box names a green condition a program could settle
- [ ] Cap exhaustion escalates to the plan, not to another round
- [ ] Unique output path per parallel writer
- [ ] Deterministic steps run as code nodes
- [ ] Correction returns carry unit · verdict · reason · evidence · scope
- [ ] Edges written as plan logic, not left to the model
- [ ] Spawn cap set and enforced
