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

## Green conditions (write these first)

| Job | Green condition — a program could settle it | Settled by |
|-----|---------------------------------------------|------------|
| J1 | | test / script / check |
| J2 | | |

Nothing here that can fail the work? Say so plainly — that job is **unverified**, not done. Not a check: “looks good”, “the model is confident”, “no errors were raised”.

## Jobs (boxes)

| ID | Job (one assistant) | Node kind | Angle / lens | Context | Output path (unique) |
|----|---------------------|-----------|--------------|---------|----------------------|
| J1 | | worker | | own | |
| J2 | | code node | | — | |
| J3 | | | | | |

Node kinds: **splitter** · **worker** · **code node** · **gate**. Cap parallel workers (default 5). A verifier is a worker whose lens is “kill this”; the merge is usually a code node.

## Edges (arrows)

| From | To | Real or fake? | What work flows? |
|------|-----|---------------|------------------|
| | | | |

Fake edges to delete:

-

## Diamond layout (if graph)

1. **Split dimension** — why can two workers not return the same finding?
2. **Workers (parallel, separate contexts):** list by ID
3. **Verifier lenses** (distinct questions — adapt to domain):
   - Lens A:
   - Lens B:
   - Lens C:
4. **Merge (code node: dedupe, rank, filter, combine):**
5. **Result path:**

## Return paths

- **Correction edge** — which unit comes back, to which job, with what evidence?
  - unit · verdict · reason · evidence · scope:
- **Learning edge** — which accepted result yields which constraint, and where does it land in the splitter's brief?
  - `ACCEPTED` / `DERIVED` / `LANDS IN`:
- **Promotion:** who approves a constraint becoming a permanent rule?

## Human gate

- **Lane:** `[ ] reversible, contained` / `[ ] reversible, wide` / `[ ] hard to reverse` (this lane does not open)
- **Where the last yes sits:**
- **Why undo would be expensive there:**
- **What the gate reads, in order:** deterministic results → this run's trajectory → this node's rollback history → model assessment (last)
- **Mid-graph pauses (if any):** what the user must approve before continuing

## Wiring caps

- **Max loop rounds:** (default 3 — at the cap, escalate to the plan, not to another round)
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
- [ ] Green condition per job, written before the work
- [ ] No fake edges remain
- [ ] Verifier is a separate job; lenses are distinct
- [ ] Verify before merge
- [ ] Correction and learning edges named
- [ ] Caps set; unique writers; deterministic steps are code
- [ ] Gate lane named; no irreversible action without approval
