# Graph Spec

Domain-agnostic checklist. Fill for *this* goal. Prefer the diamond unless the stop rule says stay one agent.

## Goal

- **Request (one sentence):**
- **Success criteria:**
- **Irreversible actions (if any):** send / publish / refund / invoice / go-live / other:
- **Output path(s) for the final merge:**

## Stop rule check

- **Where does the work split into independent jobs?**
- **Do any proposed parallel jobs need each other's outputs mid-flight?** (If yes, do not parallelize those.)
- **Decision:** `[ ] diamond graph` / `[ ] one agent` — reason:

## Jobs (boxes)

| ID | Job (one assistant) | Angle / lens | Output path (unique) |
|----|---------------------|--------------|----------------------|
| J1 | | | |
| J2 | | | |
| J3 | | | |

Add/remove rows as needed. Cap parallel workers (default 5).

## Edges (arrows)

| From | To | Real or fake? | What work flows? |
|------|-----|---------------|------------------|
| | | | |

Fake edges to delete:

-

## Diamond layout (if graph)

1. **Split:** how the request becomes independent jobs
2. **Workers (parallel):** list by ID
3. **Verifier lenses** (distinct questions — adapt to domain):
   - Lens A:
   - Lens B:
   - Lens C:
4. **Merge:** how survivors become one result
5. **Result path:**

## Human gate

- **Where the last yes sits:**
- **Why undo would be expensive there:**
- **Mid-graph pauses (if any):** what the user must approve before continuing

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

Paste-ready. Must include `use a workflow:`. Describe *this* goal's jobs — do not copy a fixed SEO/GTM/research menu.

```text
[write the full prompt here]
```

## Verification

- [ ] Designed for this goal (not a canned example menu)
- [ ] No fake edges remain
- [ ] Verifier is a separate job; lenses are distinct
- [ ] Verify before merge
- [ ] Caps set; unique writers
- [ ] Gate placed; no irreversible action without approval
