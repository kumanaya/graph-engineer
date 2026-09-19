# Node Types

Four kinds. One of them is not a model.

| Node | Job | Written by |
|------|-----|-----------|
| **Splitter** | cuts the work into units; sits at the front | plan (model may draft it) |
| **Worker** | one unit, one lens, its own context | model |
| **Code node** | merge, dedupe, rank, compare, filter, route | code |
| **Gate** | one human yes, where undo is expensive | human |

A **verifier** is a worker whose lens is “kill this”. The **merge** is usually a code node, not a model call.

## Splitter — decides more than any other node

Split by the wrong dimension and everything downstream is wasted. Cut a repository by folder and four workers audit the same three files. Cut by blast radius and each one sees something the others cannot.

The dimension is not fixed. Pick the one that makes the units **disjoint**:

- by **subsystem × concern** — owners of a hot path, callers outside it, tests, docs
- by **claim** — one worker per hypothesis under test
- by **source class** — primary docs, source code, issues, third parties
- by **blast radius** — what breaks if this piece is wrong

Test the split before you spend on it: **can two workers return the same finding?** If yes, the dimension is wrong.

## Worker — own context, or the fan-out is a costume

One unit each, one lens, **its own context window**. That last part gets skipped constantly.

Give four workers a shared window and they converge: the first writes a finding, the rest read it, and all four reports centre on the same thing. You paid four times for one opinion and three echoes.

All three, or it is theatre: separate context + distinct question + disjoint split dimension.

## Code node — the one people forget exists

Merging, ranking, deduplicating, comparing every export before and after, checking the diff against the plan's file list, routing on a score. None of that is reasoning. Each has exactly one correct answer, each is a few lines of code, and running it through a model adds cost, latency and variance to a step that had none.

**Test:** if you can describe the transformation without the words *judge*, *decide*, *assess* or *summarize*, it is code.

A graph where every node is a model pays rent on its own wiring.

## Gate

One node, one human, placed by blast radius — never by confidence. See `references/gate-design.md`.

## How they fit

```text
        ┌─────────────── splitter (plan)
        │
   ┌────┴────┬─────────┐
 worker    worker    worker      ← own context, own green condition
   └────┬────┴─────────┘
        ▼
    verifier (distinct lens, tries to kill)
        ▼
    code node (merge, dedupe, rank)
        ▼
    gate (human, by blast radius)
        │
        └── correction edge → the worker that failed
        └── learning edge  → the splitter's brief
```
