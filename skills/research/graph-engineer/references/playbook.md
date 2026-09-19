# Graph Engineering Playbook

Operational checklist for every audit, run, and design.

## The stop rule

More agents is not automatically better.

- Teams win on work that **splits into independent pieces**
- Teams lose when each step needs the previous one
- A graph buys **breadth**, not better judgment
- Before adding an agent, ask: **where does my work split?**
- If every step needs the full picture → stay with one agent
- The moment jobs never read each other's results → the graph starts paying

If one agent can do the job correctly, stay one agent. Do not instantiate Graph State machinery to look sophisticated. A one-node graph needs no state file, no scheduler, and no commit step.

## The invariant, restated

```text
Workers are isolated. The graph is not.
```

A spawned worker sees only its envelope: goal, inputs by path, constraints, green condition, writer path, output contract. Everything else it needs must be put there, or the node is not ready.

## Playbook (in order)

1. **Write the check first** — before the work exists, name the green condition a program could settle. "No errors were raised" is not a check.
2. **Fake edges first** — for every "and then", name the artifact that crosses. If you cannot, there is no edge: run both nodes in the same round.
3. **Split only what never reads back** — one agent keeps everything step-by-step. Split by the dimension where two workers cannot return the same finding.
4. **Give every node an envelope** — job, green condition, lens, inputs by path, constraints, writer path, output contract. If the envelope were all it knew, could it succeed?
5. **No finding travels unchecked** — and no two checkers ask the same question. A verifier requires the artifact; it does not inherit the producer's reasoning.
6. **Verify before consume** — declare a verifier on an artifact and the scheduler holds every consumer until it is GREEN.
7. **Every loop has a maximum number of attempts** — at the cap, the plan is at fault, not the unit. Escalate.
8. **Return the unit, not the batch** — a bad unit goes back alone, with its evidence and a scope line; a new version is produced, never an overwrite.
9. **One writer per path, including state** — workers produce outputs; the orchestrator commits them.
10. **Deterministic steps are code** — compare, dedupe, rank, filter, route, and the graph's own bookkeeping. No model call where one answer exists.
11. **The last yes** sits exactly where a mistake would be expensive to undo — by blast radius, never by confidence.
12. **One tool is enough** until you can name the reason it isn't.

Skip that last yes and the graph ships its first confident mistake straight to a customer.

## Build order (starting from nothing)

1. **The check.** Everything gets easier once something can fail loudly. A graph without one is just a faster way to produce unverified output.
2. **The lanes.** Splitter and the split dimension; workers with their own envelopes.
3. **Verification.** The verifier node and the artifact it guards.
4. **The learning edge, last** — you cannot derive constraints from accepted results until something is accepting results.

And put the human on one step: the point of highest consequence and lowest reversibility.

## First move (any system)

1. Draw the current AI system: just the jobs and the arrows between them.
2. For each arrow, name the artifact that crosses. Delete the ones you cannot name.
3. That usually removes more waiting than any tool you could buy.
4. Then ask what could fail in each remaining box while you are out of the room.

## Running one round

```bash
graph_state.py dispatch      # ready nodes → delegate_task(tasks=[…]) payload + local code nodes
# pass round_tasks to delegate_task verbatim; children write artifacts + contract files
graph_state.py commit --node <id> --result results/<id>.a1.json   # per node
graph_state.py status        # what ran, what is ready, what waits and why
```

Hermes delivers a batch when the call finishes, so a round is a turn boundary: dispatch, then commit what came back, then dispatch again.

## Human gate design

- You are the most important node in your own graph
- Route to a human before anything irreversible: send, publish, refund, invoice
- Gate on everything → bottleneck; gate on nothing → unwatched
- Judge the system on numbers that cannot argue back: money landed, customers stayed, tests ran — not only self-graded reports
- **Open on blast radius, not confidence** — confidence is the one input the model can influence. Hard-to-reverse work (migrations, deletions, production data, money) does not open, regardless of score. See `references/gate-design.md`.

## Wiring (summary)

See `references/wiring-rules.md`:

- Attempt cap + spawn cap + spawn budget; at the cap, the plan is at fault
- One writer per path; only the orchestrator writes state; correction returns are per-unit
- Code owns readiness, routing, versions and state updates; the model fills nodes
- Deterministic steps are code nodes, executed locally — not spawns

## Isolation and state (summary)

See `references/isolation.md` and `references/graph-state.md`:

- A worker may rely only on its envelope — nothing else exists for it
- Facts cross edges as versioned artifacts, referenced by path
- One logical owner of state; one commit step; versioned artifacts, never overwritten
- Minimum sufficient context: no sibling conversations, no full graph history

## Scheduler (summary)

See `references/scheduler.md`:

- READY is computed from committed, verified dependencies — never remembered
- Rounds: dispatch a batch, commit results, recompute
- Failures are state transitions; incomplete inputs mean BLOCKED, never a hopeful spawn
- Caps terminate everything; escalation returns control to graph design

## Hermes runtime (summary)

See `references/hermes-runtime.md`:

- `delegate_task` children are isolated; `output_schema` is the contract; only the summary returns
- Children cannot `clarify`, so every human gate belongs to the orchestrator
- Concurrency is capped by config; nested delegation is opt-in and off by default

## Diamond (summary)

See `references/diamond-pattern.md`:

- Split → parallel workers (own envelopes) → separate verifier → merge survivors
- Verify first, merge second — enforced by readiness
- Never the same agent grading itself
- Merge/dedupe/rank is a code node

## Loop (summary)

See `references/loop-design.md`:

- Produce → check → correct, one attempt at a time
- Green conditions a program could settle, written before the work
- Loop inside a node, graph between nodes
- Cap the attempts; escalate to the plan after three

## Return paths (summary)

See `references/return-paths.md`:

- Correction edge (short): failed unit → its producer, with verdict, evidence and scope; a new version, never an overwrite
- Learning edge (long): accepted outcome → a constraint in `constraints.json` → every later envelope
- Return the unit, never the batch
- Two shapes only: correction fixes this run, learning fixes every run after

## Node types (summary)

See `references/node-types.md`: splitter, worker, verifier, code node, gate. One is not a model; one is not an agent. Workers get their own envelope, or the fan-out buys one opinion and three echoes.

## Vocabulary (summary)

See `references/vocabulary.md`: box, arrow, artifact, fake edge, diamond, gate — then the loop, the code node, the return edges, Graph State, and the envelope/scheduler/commit trio.
