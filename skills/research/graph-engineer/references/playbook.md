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

## Playbook (in order)

1. **Write the check first** — Before the work exists, name the green condition a program could settle. “No errors were raised” is not a check.
2. **Fake edges first** — Nothing new runs until no-work arrows are gone.
3. **Split only what never reads back** — One agent keeps everything step-by-step. Split by the dimension where two workers cannot return the same finding.
4. **No finding travels unchecked** — And no two checkers ask the same question.
5. **Every loop has a maximum number of rounds.** At the cap, the plan is at fault, not the unit.
6. **Return the unit, not the batch** — A bad slice goes back alone, with its evidence and a scope line.
7. **One writer per file** — The plan lives in written steps; the AI fills the jobs. Deterministic steps are code, not prompts.
8. **The last yes** sits exactly where a mistake would be expensive to undo.
9. **One tool is enough** until you can name the reason it isn't.

Skip that last yes and the graph ships its first confident mistake straight to a customer.

## Build order (starting from nothing)

1. **The check.** Everything gets easier once something can fail loudly. A graph without one is just a faster way to produce unverified output.
2. **The lanes.** Splitter and the split dimension; workers with their own context.
3. **The learning edge**, last — you cannot derive constraints from accepted results until something is accepting results.

And put the human on one step: the point of highest consequence and lowest reversibility.

## First move (any system)

1. Draw the current AI system: just the jobs and the arrows between them.
2. Count the fake edges; delete them.
3. That usually removes more waiting than any tool you could buy.

## Human gate design

- You are the most important node in your own graph
- Route to a human before anything irreversible: send, publish, refund, invoice
- Gate on everything → bottleneck; gate on nothing → unwatched
- Judge the system on numbers that cannot argue back: money landed, customers stayed, tests ran — not only self-graded reports
- **Open on blast radius, not confidence** — confidence is the one input the model can influence. Hard-to-reverse work (migrations, deletions, production data, money) does not open, regardless of score. See `references/gate-design.md`.

## Wiring (summary)

See `references/wiring-rules.md` for full detail:

- Loop cap + seen list; at the cap, the plan is at fault
- One writer per file; correction returns are per-unit
- Code/plan owns edges; model fills nodes
- Deterministic steps are code nodes
- Spawn cap always on

## Diamond (summary)

See `references/diamond-pattern.md`:

- Split → parallel workers (own contexts) → separate verifier → merge survivors
- Verify first, merge second
- Never same agent grades itself
- Merge/dedupe/rank is a code node

## Loop (summary)

See `references/loop-design.md`:

- Produce → check → correct → repeat until green
- Green conditions a program could settle, written before the work
- Loop inside a box, graph between boxes
- Cap the rounds; escalate to the plan after three

## Return paths (summary)

See `references/return-paths.md`:

- Correction edge (short): failed unit → the box that produced it, with evidence and scope
- Learning edge (long): accepted result → a constraint in the splitter's brief
- Return the unit, never the batch
- Two shapes only: correction fixes this run, learning fixes every run after

## Node types (summary)

See `references/node-types.md`: splitter, worker, code node, gate. One of them is not a model. Workers get their own context, or the fan-out buys one opinion and three echoes.

## Vocabulary (summary)

See `references/vocabulary.md`: box, arrow, running notes, fake edge, diamond, gate — then the loop, the code node, and the return edges.
