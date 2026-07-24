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

1. **Fake edges first** — Nothing new runs until no-work arrows are gone.
2. **Split only what never reads back** — One agent keeps everything step-by-step.
3. **No finding travels unchecked** — And no two checkers ask the same question.
4. **Every loop has a maximum number of rounds.**
5. **One writer per file** — The plan lives in written steps; the AI fills the jobs.
6. **The last yes** sits exactly where a mistake would be expensive to undo.
7. **One tool is enough** until you can name the reason it isn't.

Skip that last yes and the graph ships its first confident mistake straight to a customer.

## First move (any system)

1. Draw the current AI system: just the jobs and the arrows between them.
2. Count the fake edges; delete them.
3. That usually removes more waiting than any tool you could buy.

## Human gate design

- You are the most important node in your own graph
- Route to a human before anything irreversible: send, publish, refund, invoice
- Gate on everything → bottleneck; gate on nothing → unwatched
- Judge the system on numbers that cannot argue back: money landed, customers stayed, tests ran — not only self-graded reports

## Wiring (summary)

See `references/wiring-rules.md` for full detail:

- Loop cap + seen list
- One writer per file
- Code/plan owns edges; model fills nodes
- Spawn cap always on

## Diamond (summary)

See `references/diamond-pattern.md`:

- Split → parallel workers → separate verifier → merge survivors
- Verify first, merge second
- Never same agent grades itself

## Vocabulary (summary)

See `references/vocabulary.md`: box, arrow, running notes, fake edge, diamond, gate.
