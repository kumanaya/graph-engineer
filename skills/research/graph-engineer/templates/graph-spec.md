# Graph Spec

Fill every section. Prefer the diamond unless the stop rule says stay one agent.

## Goal

- **Request (one sentence):**
- **Success criteria:**
- **Irreversible actions (if any):**

## Stop rule check

- **Where does the work split into independent jobs?**
- **Do any proposed parallel jobs need each other's outputs mid-flight?** (If yes, do not parallelize those.)
- **Decision:** `[ ] diamond graph` / `[ ] one agent` — reason:

## Jobs (boxes)

| ID | Job (one assistant) | Output path (unique) |
|----|---------------------|----------------------|
| J1 | | |
| J2 | | |
| J3 | | |

## Edges (arrows)

| From | To | Real or fake? | What work flows? |
|------|-----|---------------|------------------|
| | | | |

Fake edges to delete:

-

## Diamond layout (if graph)

1. **Split:**
2. **Workers (parallel):** list angles / jobs
3. **Verifier lenses** (distinct questions):
   - Correctness:
   - Freshness / currency:
   - Source quality:
   - Fit to request:
4. **Merge:** how survivors become one result
5. **Result path:**

## Human gate

- **Where the last yes sits:**
- **Why undo would be expensive there:**
- **Pauses required mid-graph:** (e.g. positioning doc)

## Wiring caps

- **Max loop rounds:** (default 3)
- **Spawn cap:** (default 5)
- **Seen / dedupe:** how
- **One writer per file:** confirmed paths above
- **Plan owns edges:** routing rules (if/else):

## Running notes

What travels with the work (found / decided / left):

-

## Runnable prompt

Paste-ready. Must include `use a workflow:`.

```text
[write the full prompt here]
```

## Verification

- [ ] No fake edges remain
- [ ] Verifier is a separate job; lenses are distinct
- [ ] Verify before merge
- [ ] Caps set; unique writers
- [ ] Gate placed; no irreversible action without approval
