# The Diamond: Split, Parallel Workers, Verify, Merge

The one pattern that pays: work splits, workers dig side by side, something checks what they found, everything merges into one answer.

**Philosophy:** parallelize independent work → verify mercilessly → merge only what survives → output you can trust.

## Flow

1. **Split the job** — break the request into independent subtasks. The **split dimension** decides whether this works at all: pick the one where two workers cannot return the same finding. The splitter commits its units as an artifact.
2. **Workers (parallel)** — each explores a different angle, in **its own context**, from its own envelope. They are dispatched as one batch and run simultaneously. None of them can see another's work — that is the design, not a gap.
3. **Verifier (gate)** — tries to kill each finding. A separate node that requires the artifacts it inspects. Different lens per verifier: factual correctness, freshness, source quality, fit to the request. A verifier that inherits the producer's reasoning is the same agent grading its own homework.
4. **Merge** — a **code node**: dedupe, rank, filter, combine the survivors. Deterministic, zero tokens, no variance. It runs only after the artifacts it consumes are verified. Ship one answer, not a pile.
5. **One result you can trust** — clean, complete, ready to act.

Each worker is itself a **loop**: produce → check → correct, one attempt at a time, until green. Give it the green condition up front — see `references/loop-design.md`.

**Golden rule:** verify first, merge second — enforced by the scheduler, not by discipline.

## Rounds, not a swarm

```text
        split
       /     \
     wa       wc            ← ROUND 2: one delegate_task(tasks=[…]) batch
       \     /
        verify              ← ROUND 3: requires findings-a@v1 and findings-c@v1
          |
        merge               ← ROUND 4: code node, runs locally
          |
        gate                ← human, by blast radius
```

- **Round 2 dispatches wa and wc together.** They do not communicate. Neither needs to.
- **Round 3's verifier** gets both findings by path — not by conversation, not by memory.
- **Round 4's merge** cannot start until the verifier is GREEN, because its inputs are verified artifacts.
- Nothing is spawned "to coordinate". Every crossing is an artifact on disk, and every wait is a declared input.

A worker that discovers something another worker needs is not a coordination failure — it is a missing edge. Either that finding belongs in the worker's committed artifact and a downstream node reads it, or the two nodes were never independent and the split was wrong.

## Why the checker is non-negotiable

Models miss most of their own mistakes. Never let the same agent grade its own homework. Give checking to a separate node whose only task is to kill weak findings, and give every checker a different question.

A verifier returns `verdict`, `unit`, `reason`, `evidence`, `scope`. On RED, only the unit named in `unit` returns — never the batch (`references/return-paths.md`).

## Where it pays

**Use the diamond when** subtasks never read each other's output: independent research, idea generation, data pulls, alternative approaches.

**Avoid the diamond when** step 4 must read step 3. Tight dependencies → one agent wins (stop rule).

## Cost notes

- Parallel graphs use far more tokens than a single-prompt chat; that is expected.
- Artifacts travel by path: a 40 KB findings file costs one line in an envelope until a node reads it.
- Deduping and filtering in code costs zero tokens.
- Verification costs tokens; engineering (caps, verification gating, deterministic edges) saves them.
- Four workers sharing one context buy one opinion, three times. Separate envelopes are what you are paying for.
- A graph with more rounds than nodes is usually a graph with fake edges in it.

## Return path

A failed unit goes back to **the node that produced it**, carrying the verdict, the evidence and a scope line — never back to the whole batch, which rewrites work that was correct (`references/return-paths.md`).

## How to run it

1. Define the request and success criteria.
2. Apply the stop rule. If nothing splits, stay one agent.
3. Split into disjoint units by one dimension; commit the units as an artifact.
4. Write each node's green condition and output contract.
5. `dispatch` → spawn the ready batch → `commit` each result.
6. Verify hard; let only the failed unit return.
7. Merge survivors as a code node; stop at the gate.

## Legend

| Node | Role |
|------|------|
| Split | Creates parallel units (its own artifact crosses to each worker) |
| Worker | One unit, one lens, one envelope, one writer path |
| Verifier | Kills weak findings — separate node, distinct lens, requires what it inspects |
| Merge | Code node: dedupe, rank, combine survivors |
| Result | One you can trust |
| Return | Failed unit → its producer only; accepted → a constraint in `constraints.json` |
