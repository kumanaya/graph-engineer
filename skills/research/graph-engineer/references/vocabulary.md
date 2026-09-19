# The Graph Engineering Vocabulary

Six ideas describe the **shape** of every graph. Learn them in order; they build. Three more, at the end, make it **run**.

## 1. The Box (a job)

One job you would hand to one assistant. Research this, write that, check this.

- One box = one clear outcome
- If you need two assistants, you need two boxes

## 2. The Arrow (a hand-off)

This job **needs the result** of that job before it can start. That is the only thing an arrow means.

- Real arrow: work flows (B cannot start without A's output)
- Not an arrow: “and then” that sounds sequential but shares no dependency

## 3. The Running Notes

The **notes that travel** with the work: what was found, what was decided, what is left.

- Shared state across jobs
- Keep them small and current
- Notes move with the work

## 4. The Fake Edge

An arrow where **no work flows**. If the next job does not need the last job's result, the waiting is wasted.

Example: “summarize this file and then check my calendar” — the calendar step never needs the summary. Delete the wait; those jobs never had to block each other.

**Audit habit:** For every “and then,” ask whether the next job needs the last job's result. When the answer is no, the arrow is fake.

## 5. The Diamond

Split the job, run workers **at the same time**, check their work, merge into one result.

Shape: start → parallel workers → verifier → merge → one trusted result.

See `references/diamond-pattern.md`.

## 6. The Gate (the last yes)

The one human approval before anything irreversible. It sits where a mistake would be **expensive to undo**.

- Gate on everything → you are the bottleneck
- Gate on nothing → nobody is watching
- Place the gate where risk is highest (send, publish, refund, invoice, go live)

## Tier 2: the machinery

The six above are the shape. Three more make it run — a shape with no check and no way back is a diagram.

### 7. The Loop (inside a box)

Produce → check → correct → repeat until green. The check is the whole thing, and it must be something a program could settle: “the test suite exits 0” is a check, “no errors were raised” is not.

The loop lives **inside** a box; the graph lives **between** boxes. See `references/loop-design.md`.

### 8. The Code node (not a model)

Merging, ranking, deduplicating, comparing exports, filtering, routing. One correct answer, a few lines of code. Running those through a model adds cost, latency and variance to a step that had none.

If you can describe the transformation without the words *judge*, *decide*, *assess* or *summarize*, it is code. See `references/node-types.md`.

### 9. The Return edges (correction and learning)

The short edge sends a failed unit back to the box that produced it — and only that unit, never the batch. The long edge sends an accepted result back to the splitter as a constraint, so the next run starts where this one ended.

A graph with neither is a pipeline: it produces output and forgets. See `references/return-paths.md`.

## Why this vocabulary

A straight line where every job waits for the one before it works, but it is the slowest possible way: one stuck job blocks everything. Graphs are decades-old dependency plans wearing a new name — that is the good news: the pattern already runs critical systems.
