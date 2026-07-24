# The Graph Engineering Vocabulary

Six ideas explain every graph. Learn them in order; they build.

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

## Why this vocabulary

A straight line where every job waits for the one before it works, but it is the slowest possible way: one stuck job blocks everything. Graphs are decades-old dependency plans wearing a new name — that is the good news: the pattern already runs critical systems.
