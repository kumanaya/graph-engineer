# The Graph Engineering Vocabulary

Eleven ideas. Six describe the **shape** of every graph; five make it **run**.

One thing to know before the words: **workers are isolated.** A spawned agent starts with a fresh conversation — it sees no sibling's findings, no parent history, no shared notes. The graph, however, is not isolated: the orchestrator owns it and moves every fact between nodes on purpose. Every word below follows from that.

## 1. The Box (a node)

One job you would hand to one assistant. Research this, write that, check this.

- One box = one clear outcome
- If you need two assistants, you need two boxes

## 2. The Arrow (a hand-off)

B consumes A's output. That is the only thing an arrow means.

- Real arrow: a named artifact crosses it (`auth-findings@v2`)
- Not an arrow: "and then" that sounds sequential but shares no data
- An arrow is written as a requirement, never as an ordering rule — so a fake edge cannot be written down at all

## 3. The Artifact

Output one node produces and another consumes, committed to disk with an id and a version.

```text
auth-findings@v2   producer: audit-auth   verified: true
```

Artifacts are findings, evidence, plans, code changes, test results, extracted data, reports, verdicts, constraints. They travel by **path**, not by pasting: an envelope names the file, and the node reads it.

Versioned, never overwritten. A correction produces `v3`; `v2` stays on disk.

## 4. The Fake Edge

An arrow where **no work flows**. If the next job does not need the last job's output, the wait is pure waste.

Example: "summarize this file and then check my calendar" — the calendar step never needs the summary. Delete the wait; those jobs never had to block each other.

**Audit habit:** for every "and then", name the artifact that crosses. When you cannot, there is no edge — run both nodes in the same round.

## 5. The Diamond

Split the job, run workers at the same time, check their work, merge into one result.

Shape: split → parallel workers → verifier → merge → one trusted result.

The workers never talk to each other. They do not need to: the merge reads their committed artifacts. See `references/diamond-pattern.md`.

## 6. The Gate (the last yes)

The one human approval before anything irreversible. It sits where a mistake would be **expensive to undo**.

- Gate on everything → you are the bottleneck
- Gate on nothing → nobody is watching
- Place the gate where risk is highest (send, publish, refund, invoice, go live)
- A gate is opened by blast radius, never by confidence

## Tier 2: the machinery

### 7. The Loop (inside a box)

Produce → check → correct → repeat until green. The check is the whole thing, and it must be something a program could settle: "the test suite exits 0" is a check, "no errors were raised" is not.

In execution terms, each pass is an **attempt** on that node. See `references/loop-design.md`.

### 8. The Code node (not a model)

Merging, ranking, deduplicating, comparing exports, filtering, routing. One correct answer, a few lines of code. Running those through a model adds cost, latency and variance to a step that had none.

If you can describe the transformation without the words *judge*, *decide*, *assess* or *summarize*, it is code. See `references/node-types.md`.

### 9. The Return edges (correction and learning)

The short edge sends a failed unit back to the node that produced it — and only that unit, never the batch — carrying the verdict, the reason, the evidence and the scope. The long edge turns an accepted outcome into a constraint that lands in every later node envelope, so the next run starts where this one ended.

A graph with neither is a pipeline: it produces output and forgets. See `references/return-paths.md`.

### 10. Graph State

The orchestrator's authoritative record of what has happened: nodes, statuses, attempts, artifacts and their versions, constraints, decisions, failures, and the gate.

```text
one logical owner  ·  one file  ·  written only by the orchestrator
```

Workers never maintain competing versions of global state, because workers never write it at all. See `references/graph-state.md`.

### 11. The Node Input Envelope, the Scheduler, and the Commit

Three words for the three steps between designing a node and trusting its output.

- **Envelope** — the self-contained package every node receives: its job, green condition, lens, input artifacts by path, constraints, writer path, output contract. If a node could not do its job with the envelope as its entire world, the envelope is incomplete. See `references/isolation.md`.
- **Scheduler** — the loop that decides which nodes are runnable, dispatches them as a batch, and recomputes after every commit. Readiness is computed from committed dependencies, never remembered. See `references/scheduler.md`.
- **Commit** — the step that turns a worker's result into graph truth: validate the contract, confirm the artifact exists and hash it, assign the version, re-arm the verifier, unblock consumers. It is code, not a model call.

There is no separate "reducer" to learn. The commit step is code, and the orchestrator is the only thing that runs it.

## Why this vocabulary

A straight line where every job waits for the one before it works, but it is the slowest possible way: one stuck job blocks everything. Graphs are decades-old dependency plans wearing a new name — that is the good news: the pattern already runs critical systems. The new part is the discipline of moving every fact explicitly, because nothing moves implicitly.
