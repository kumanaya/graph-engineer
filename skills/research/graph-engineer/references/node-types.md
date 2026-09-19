# Node Types

Five kinds. One of them is not a model, and one of them is not an agent.

| Node | Job | Executed by | Spawned? |
|------|-----|-------------|----------|
| **Splitter** | cuts the work into units; sits at the front | model | yes |
| **Worker** | one unit, one lens, its own context | model | yes |
| **Verifier** | a worker whose lens is "kill this" | model | yes |
| **Code node** | merge, dedupe, rank, compare, filter, route | code | no — the orchestrator runs it |
| **Gate** | one human yes, where undo is expensive | human | never |

Every kind declares the same four things, and the scheduler reads them instead of trusting anyone's memory:

```text
INPUTS          which artifacts it requires (this IS its dependencies)
OUTPUT CONTRACT what JSON its result must satisfy
GREEN CONDITION what objectively means success
WRITER          the artifact path it may write — one writer per path
```

## Splitter — decides more than any other node

Split by the wrong dimension and everything downstream is wasted. Cut a repository by folder and four workers audit the same three files. Cut by blast radius and each one sees something the others cannot.

The dimension is not fixed. Pick the one that makes the units **disjoint**:

- by **subsystem × concern** — owners of a hot path, callers outside it, tests, docs
- by **claim** — one worker per hypothesis under test
- by **source class** — primary docs, source code, issues, third parties
- by **blast radius** — what breaks if this piece is wrong

Test the split before you spend on it: **can two workers return the same finding?** If yes, the dimension is wrong.

The split is a committed artifact, not a paragraph: its contract returns the units, each with an id, a lens and the artifact it will produce. Downstream nodes are then built from that artifact — the splitter's output crosses a real edge.

## Worker — own context, or the fan-out is a costume

One unit each, one lens, its own context. It receives an envelope and nothing else: no sibling's findings, no parent history, no ambient knowledge of the graph.

Give four workers a shared window and they converge: the first writes a finding, the rest read it, and all four reports centre on the same thing. You paid four times for one opinion and three echoes.

All three, or it is theatre: separate context + distinct question + disjoint split dimension.

A worker writes exactly one artifact, at the path its envelope named. Everything it wants another node to know must be in that artifact — that is the only channel there is.

## Verifier — evaluates the artifact, not the author's reasoning

A separate node, never the producer. It requires the artifact under review, plus any evidence the lens needs, and it returns a structured verdict:

```yaml
verdict: red
unit: auth-findings          # only something it actually inspected
reason: finding 3 cites no reproducible evidence
evidence: [handlers/auth.py:88 returns 200 where the finding claims 302]
scope: fix finding 3 only, do not touch other findings
```

Why it must be separate, and why it must not inherit the producer's conversation: a verifier that reads the producer's reasoning inherits the producer's blind spots. It reads the artifact, the green condition, the lens and the evidence — and it tries to kill the work.

Its inputs are explicit, which is the point:

```text
NODE SPEC + GREEN CONDITION + ARTIFACT TO VERIFY + RELEVANT EVIDENCE + VERIFICATION LENS
```

**Verify before consume.** When an artifact declares a verifier, the scheduler will not let any consumer run until that verifier is GREEN. "Verify first, merge second" is not a habit anyone has to keep — it is what `READY` means (`references/scheduler.md`).

## Code node — the one people forget exists

Merging, ranking, deduplicating, comparing every export before and after, checking the diff against the plan's file list, routing on a score. None of that is reasoning. Each has exactly one correct answer, each is a few lines of code, and running it through a model adds cost, latency and variance to a step that had none.

Code nodes are **not spawned**: `dispatch` returns them under `local_nodes` with their envelopes, the orchestrator runs them with `execute_code`/`terminal`, and the result is committed like any other. No model call, no spawn, no context to isolate.

**Test:** if you can describe the transformation without the words *judge*, *decide*, *assess* or *summarize*, it is code.

The graph's own plumbing obeys the same rule: readiness, blocking, versioning, hashing, contract re-validation, routing and state updates are code (`scripts/graph_state.py`). A graph where every node is a model pays rent on its own wiring.

## Gate

One node, one human, placed by blast radius — never by confidence. It requires the artifact it approves, so it cannot open before the work exists.

It should produce a **decision** artifact whenever anything runs after it: downstream nodes require the decision, and the scheduler holds them until the human answers. That turns "we will pause here" into a dependency the graph cannot skip.

No worker can approve anything. Subagents cannot talk to the user (`clarify` is blocked for them), so every gate is handled in the orchestrator's turn. See `references/gate-design.md`.

## How they fit

```text
        ┌─────────────── splitter (plan artifact)
        │
   ┌────┴────┬─────────┐
 worker    worker    worker      ← own envelope, own lens, own green condition
   └────┬────┴─────────┘
        │  artifacts: findings-a@v1, findings-b@v1, findings-c@v1
        ▼
    verifier (distinct lens, tries to kill, requires what it verifies)
        │  verdict: green  → artifacts become verified
        ▼
    code node (merge, dedupe, rank — runs locally, costs no spawn)
        │  report@v1
        ▼
    gate (human, by blast radius, requires the report)
        │
        ├── correction edge → the node whose unit failed (verdict + evidence + scope)
        └── learning edge  → constraints.json → every later envelope
```
