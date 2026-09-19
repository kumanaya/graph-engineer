# The Diamond: Split, Parallel Workers, Verify, Merge

The one pattern that pays: work splits, workers dig side by side, something checks what they found, everything merges into one answer.

**Philosophy:** parallelize independent work → verify mercilessly → merge only what survives → output you can trust.

## Flow

1. **Split the job** — Break the request into independent subtasks. Split early to explore more ideas. More workers increase chance of a great finding when jobs do not depend on each other. The **split dimension** decides whether this works at all: pick the one where two workers cannot return the same finding (`references/node-types.md`).
2. **Workers (parallel)** — Each explores a different approach or angle, in **its own context**. Run simultaneously. They must not need each other's outputs mid-flight. Shared context makes them converge on one opinion with echoes; separate context is part of the pattern, not a detail.
3. **Verifier (gate)** — Tries to kill each finding. Separate job from the workers. Different lens per verifier: factual correctness, freshness, source quality, fit to the request. A verifier that only re-reads the finding is the same agent grading its own homework.
4. **Merge** — Combine only findings that pass. Dedupe, rank, synthesize, structure. Filtering, ranking and deduping are **code nodes**: deterministic, zero tokens, no variance. Ship one answer, not a pile.
5. **One result you can trust** — Clean, complete, ready to act.

Each worker is itself a **loop**: produce, check, correct, repeat until green. Give it the green condition up front — see `references/loop-design.md`.

**Golden rule:** verify first, merge second.

## Why the checker is non-negotiable

Models miss most of their own mistakes. Never let the same agent grade its own homework. Give checking to a separate job whose only task is to kill weak findings. Give every checker a different question.

## Where it pays

**Use the diamond when** subtasks never read each other's output: independent research, idea generation, data pulls, alternative approaches.

**Avoid the diamond when** work is sequential and step 4 must read step 3. Tight dependencies → one agent wins (stop rule).

## Cost notes

- Parallel graphs use far more tokens than a single-prompt chat; that is expected.
- Deduping and filtering between stages in code costs zero tokens.
- Verification costs tokens; engineering (caps, filters, deterministic edges) saves them.
- Four workers sharing one context buy one opinion, three times. Separate contexts are what you are paying for.

## Return path

A failed finding goes back to **the worker that produced it**, with the failing check and its evidence — never back to the whole batch, which rewrites work that was correct (`references/return-paths.md`).

## How to run it

1. Define the request and success criteria.
2. Split into independent subtasks.
3. Run workers in parallel with clear instructions.
4. Verify hard and filter aggressively.
5. Merge survivors and deliver one result.

## Legend

| Node | Role |
|------|------|
| Split | Create parallel paths (its own context each) |
| Worker | Do the work, to a stated green condition |
| Verifier | Kill weak findings — separate job, distinct lens |
| Merge | Code node: dedupe, rank, combine survivors |
| Result | One you can trust |
| Return | Failed unit → its worker only; accepted → splitter's brief |
