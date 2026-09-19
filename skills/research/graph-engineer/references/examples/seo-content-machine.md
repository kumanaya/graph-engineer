# EXAMPLE ONLY — SEO Content Machine

> **Not a Run / Execute menu item.** Load this only when the user wants an illustration of parallel research → merge → draft → fact-check → human gate. For real work, design jobs for *their* goal in Execute mode.

**What it illustrates:** three independent research jobs → outline merge → produce → separate fact-checker → folder output → never ship without the human.

## The graph

Every arrow carries an artifact. The three research jobs share no state — they share a seed file and nothing else.

```text
topic (seed file: query + audience, written by the user)
    │ artifact:topic
    ├──────────────────────┬──────────────────────┐
    ▼                      ▼                      ▼
research-coverage     research-questions    research-gaps     one round, one batch
produces coverage     produces questions    produces gaps     one lens each
    └──────────────────────┴──────────────────────┘
                           │ artifacts: coverage, questions, gaps
                           ▼
                merge-outline — code node (not spawned)
                           │ produces: outline
                           ▼
                write-draft — worker · lens: write it straight
                           │ produces: draft
                           ▼
                fact-check — verifier · lens: flag every claim without a live source
                           │ produces: fact-verdict
                           ▼
                draft verified    ← the pack cannot be assembled before this
                           │ artifact:draft (verified version)
                           ▼
                assemble-drafts — code node (not spawned)
                           │ produces: drafts-pack
                           ▼
                gate-publish — gate (human)        lane: hard to reverse
```

`<root>` below is the graph root passed to `--root` (default `.graph`).

## Nodes

| Node | Kind | `requires` (artifact) | `produces` | Writer path | Green condition |
|------|------|-----------------------|-----------|-------------|-----------------|
| `research-coverage` | worker | `topic` (seed) | `coverage` | `.graph/seo-content-machine/artifacts/coverage.v<n>.md` | every covered subtopic carries the URL it was read from; nothing outside the ranking pages is invented |
| `research-questions` | worker | `topic` (seed) | `questions` | `.graph/seo-content-machine/artifacts/questions.v<n>.md` | every question is quoted from a real page or search surface, with its source |
| `research-gaps` | worker | `topic` (seed) | `gaps` | `.graph/seo-content-machine/artifacts/gaps.v<n>.md` | every gap names the pages it is missing from and why the reader would care |
| `merge-outline` | code | `coverage`, `questions`, `gaps` | `outline` | `.graph/seo-content-machine/artifacts/outline.v<n>.md` | one outline; every section traces to at least one committed research artifact |
| `write-draft` | worker | `outline` | `draft` | `.graph/seo-content-machine/artifacts/draft.v<n>.md` | a complete draft whose headings match the outline order, every claim sourced or flagged |
| `fact-check` | verifier | `draft` | `fact-verdict` | `.graph/seo-content-machine/artifacts/fact-verdict.v<n>.json` | each claim is either sourced and verified, or listed as flagged at the top of the draft |
| `assemble-drafts` | code | `draft` (verified) | `drafts-pack` | `.graph/seo-content-machine/artifacts/drafts-pack.v<n>.md` | `drafts/<slug>.md` exists and equals the verified draft; the manifest lists every flagged claim |
| `gate-publish` | gate | `drafts-pack` | — | — | explicit user yes |

`fact-check` covers exactly one artifact, so it sets `on_red.corrects: "write-draft"` — the correction edge is declared, not improvised. The draft is declared with a verifier, so `assemble-drafts` cannot run until the draft has a `verified_version`.

## Rounds

| Round | Dispatch — one `delegate_task(tasks=[…])` batch | Envelope carries | Commit |
|-------|--------------------------------------------------|------------------|--------|
| 1 | `research-coverage`, `research-questions`, `research-gaps` — parallel, one batch | the `topic` seed path + one lens each | `coverage@v1`, `questions@v1`, `gaps@v1` |
| 2 | none — `merge-outline` arrives under `local_nodes` | the three committed research artifacts | `outline@v1` |
| 3 | `write-draft` | `outline@v1` | `draft@v1` |
| 4 | `fact-check` | `draft@v1` | `fact-verdict@v1` |
| 5 | none — `assemble-drafts` under `local_nodes` | `draft@v(n)` verified | `drafts-pack@v1` |
| 6 | none — `gate-publish` is `WAITING_HUMAN` | — | the user's own words |

A round is one `dispatch` → one `delegate_task(tasks=[…])` batch → one commit pass. The scheduler recomputes READY after every commit: the third research commit flips `merge-outline` from PENDING to READY, with nothing passed between the workers.

Round 1 as commands:

```bash
GS="python ${HERMES_SKILL_DIR}/scripts/graph_state.py --root .graph"

$GS init --spec graph.json
$GS dispatch --tasks-file round1.json      # 3 bindings, local_nodes: [], deferred_to_next_round: []
#   → pass round1.json to delegate_task(tasks=[...]) verbatim
$GS commit --node research-coverage  --result .graph/seo-content-machine/results/research-coverage.a1.json
$GS commit --node research-questions --result .graph/seo-content-machine/results/research-questions.a1.json
$GS commit --node research-gaps      --result .graph/seo-content-machine/results/research-gaps.a1.json
$GS status                                 # merge-outline: READY (a code node the orchestrator runs, not a spawn)
```

**The three research jobs never see each other's work.** They are spawned in one batch and each receives only its own **Node Input Envelope**, built at dispatch from committed Graph State: the graph goal, its lens, the seed path, the constraints, its writer path, its contract. Nothing else: no sibling findings, no memory of any other node, no visibility into what the other two jobs are doing. `merge-outline` is where their outputs meet, and it reads three committed files, not three conversations.

## Correction

One unsourced claim does not send the draft back to research, and it does not re-run the batch. It returns the draft to its writer:

```text
fact-check   verdict: red · unit: draft
             reason: "3 claims cite no source"
             evidence: "'most teams fail at step 3' has no citation"
             scope: "draft only: source or flag those 3 claims, change nothing else"
      │ commit
      ▼
write-draft  RED — correction payload attached; coverage, questions, gaps, outline keep GREEN
      │ next dispatch → write-draft only
      ▼
draft@v2 → fact-check re-armed (PENDING), because the version changed
      │ dispatch
      ▼
fact-check attempt 2 → verdict green → draft verified@v2 → assemble-drafts recomputes to READY
```

Writing the flag list at the top of the draft is the producer's job in that attempt, under the scope it was given — the verdict names one unit and one boundary, so the correction cannot sprawl into the research or the outline.

## Human gate

- **Lane: hard to reverse.** Publishing leaves the building: the article, its index state and anything already quoting it.
- The gate never opens on model confidence. Approval requires the user's own words, quoted into the record:

```bash
$GS gate --status approved
graph_state: lane 'hard to reverse' is hard to reverse: an explicit --user-approval quoting the
user's yes is required. Never approximate approval from model confidence.      # exit 3

$GS gate --status approved --user-approval "yes - publish it as is"
# → gate: approved ; graph status: done
```

Until then the graph sits at `gated` with `gate-publish: WAITING_HUMAN` and `drafts-pack@v1` on disk. No node in this graph can publish, schedule or send anything: leaf children cannot reach the user, and nothing irreversible is wired to a worker.

## Graph spec (`graph.json`)

Validated: `graph_state.py --root <root> init --spec graph.json` exits 0. Every non-gate node below carries an `output_contract`: the base contract from `templates/node-contract.md`, plus the verifier's four verdict fields where declared. A gate has no contract — its artifact is the human's decision. This gate is terminal (publish is the last step, and the graph does not publish at all), so it declares no `produces`; `references/examples/go-to-market-kit.md` shows a gate that produces a `decision` artifact and holds downstream work with it.

```json
{
  "graph": {
    "id": "seo-content-machine",
    "goal": "Produce one publish-ready article for a search intent: three independent research passes, one outline, one draft, an independent fact-check, and no publish without the user.",
    "gate": {"lane": "hard to reverse", "action": "publish the article"},
    "caps": {"max_attempts": 3, "spawn_cap": 5, "spawn_budget": 20}
  },
  "constraints": [
    "Every claim in the draft carries a source link or is flagged at the top of the draft.",
    "No node publishes, schedules, or sends anything."
  ],
  "artifacts": {
    "topic": {"type": "source", "seed": true, "path": "C:/work/seo-machine/topic.md", "description": "the target query and audience, written by the user"},
    "coverage": {"type": "findings", "ext": "md", "producer": "research-coverage"},
    "questions": {"type": "findings", "ext": "md", "producer": "research-questions"},
    "gaps": {"type": "findings", "ext": "md", "producer": "research-gaps"},
    "outline": {"type": "plan", "ext": "md", "producer": "merge-outline"},
    "draft": {"type": "draft", "ext": "md", "producer": "write-draft", "verifier": "fact-check"},
    "fact-verdict": {"type": "verdict", "ext": "json", "producer": "fact-check"},
    "drafts-pack": {"type": "package", "ext": "md", "producer": "assemble-drafts"}
  },
  "nodes": [
    {"id": "research-coverage", "kind": "worker", "lens": "what the ranking pages cover",
     "goal": "List what the current top-ranking pages for this query actually cover.",
     "green_condition": "each covered subtopic is recorded with the URL it was read from, and nothing outside the top results is invented",
     "requires": [{"artifact": "topic"}],
     "produces": "coverage",
     "output_contract": {"type": "object", "properties": {"node": {"type": "string"}, "status": {"type": "string", "enum": ["done", "failed"]}, "summary": {"type": "string"}, "artifact_path": {"type": "string"}, "evidence": {"type": "array", "items": {"type": "string"}}}, "required": ["node", "status", "summary", "artifact_path"]}},
    {"id": "research-questions", "kind": "worker", "lens": "the questions people actually ask",
     "goal": "Collect the questions people actually ask about this topic.",
     "green_condition": "every question is quoted from a real page or search surface, with its source",
     "requires": [{"artifact": "topic"}],
     "produces": "questions",
     "output_contract": {"type": "object", "properties": {"node": {"type": "string"}, "status": {"type": "string", "enum": ["done", "failed"]}, "summary": {"type": "string"}, "artifact_path": {"type": "string"}, "evidence": {"type": "array", "items": {"type": "string"}}}, "required": ["node", "status", "summary", "artifact_path"]}},
    {"id": "research-gaps", "kind": "worker", "lens": "what the top pages skip",
     "goal": "Find what the ranking pages skip.",
     "green_condition": "every gap names the pages it is missing from and why it matters to the reader",
     "requires": [{"artifact": "topic"}],
     "produces": "gaps",
     "output_contract": {"type": "object", "properties": {"node": {"type": "string"}, "status": {"type": "string", "enum": ["done", "failed"]}, "summary": {"type": "string"}, "artifact_path": {"type": "string"}, "evidence": {"type": "array", "items": {"type": "string"}}}, "required": ["node", "status", "summary", "artifact_path"]}},
    {"id": "merge-outline", "kind": "code",
     "goal": "Merge the three research artifacts into one outline: dedupe, order by search intent, drop anything with no source.",
     "green_condition": "one outline file exists; every section traces to at least one committed research artifact",
     "requires": [{"artifact": "coverage"}, {"artifact": "questions"}, {"artifact": "gaps"}],
     "produces": "outline",
     "output_contract": {"type": "object", "properties": {"node": {"type": "string"}, "status": {"type": "string", "enum": ["done", "failed"]}, "summary": {"type": "string"}, "artifact_path": {"type": "string"}, "evidence": {"type": "array", "items": {"type": "string"}}}, "required": ["node", "status", "summary", "artifact_path"]}},
    {"id": "write-draft", "kind": "worker",
     "goal": "Write the full draft from the outline, in outline order.",
     "green_condition": "a complete draft exists, its headings match the outline order, and every claim carries a source",
     "requires": [{"artifact": "outline"}],
     "produces": "draft",
     "output_contract": {"type": "object", "properties": {"node": {"type": "string"}, "status": {"type": "string", "enum": ["done", "failed"]}, "summary": {"type": "string"}, "artifact_path": {"type": "string"}, "evidence": {"type": "array", "items": {"type": "string"}}}, "required": ["node", "status", "summary", "artifact_path"]}},
    {"id": "fact-check", "kind": "verifier", "lens": "flag every claim without a live source",
     "goal": "Check every claim in the draft against its cited source.",
     "green_condition": "each claim is either sourced and verified, or listed as flagged at the top of the draft",
     "requires": [{"artifact": "draft"}],
     "produces": "fact-verdict",
     "on_red": {"corrects": "write-draft"},
     "output_contract": {"type": "object", "properties": {"node": {"type": "string"}, "status": {"type": "string", "enum": ["done", "failed"]}, "summary": {"type": "string"}, "artifact_path": {"type": "string"}, "evidence": {"type": "array", "items": {"type": "string"}}, "verdict": {"type": "string", "enum": ["green", "red"]}, "unit": {"type": "string"}, "reason": {"type": "string"}, "scope": {"type": "string"}}, "required": ["node", "status", "summary", "artifact_path", "verdict", "unit", "reason", "scope"]}},
    {"id": "assemble-drafts", "kind": "code",
     "goal": "Copy the verified draft to the user-facing drafts/ path and write the pack manifest.",
     "green_condition": "drafts/<slug>.md exists and equals the verified draft; the manifest lists the flagged claims",
     "requires": [{"artifact": "draft"}],
     "produces": "drafts-pack",
     "output_contract": {"type": "object", "properties": {"node": {"type": "string"}, "status": {"type": "string", "enum": ["done", "failed"]}, "summary": {"type": "string"}, "artifact_path": {"type": "string"}, "evidence": {"type": "array", "items": {"type": "string"}}}, "required": ["node", "status", "summary", "artifact_path"]}},
    {"id": "gate-publish", "kind": "gate",
     "goal": "the user decides whether to publish",
     "green_condition": "explicit user yes",
     "requires": [{"artifact": "drafts-pack"}]}
  ]
}
```

## Prompt (example)

```text
use a workflow: i want an article that can rank for [topic] — three independent research passes, one outline, one draft, an independent fact-check that flags every unsourced claim, and nothing published without me.
```

That one sentence is the whole input. Graph Engineer designs the graph from it — nodes, artifacts, contracts, rounds, gate lane. The diagram above is one design for that class of goal, not a menu entry.

## Pattern notes

- Parallel jobs must not write the same file: `coverage`, `questions` and `gaps` are three artifacts with three writers
- The fact-checker is a separate node with a distinct lens; "every claim carries a source" is the green condition, and a failing claim returns the **draft only**
- Every edge names its artifact: `coverage`/`questions`/`gaps → outline`, `outline → draft`, `draft → fact-check` (whose verdict returns the draft along the correction edge), `draft → drafts-pack`
- Merging is a **code node** — dedupe, order, drop unsourced lines — not a model call
- Output shape in this example: `drafts/`, with the flagged claims listed at the top of the draft
- Gate lane is hard to reverse, so approval needs the user's words; a plain `gate --status approved` exits 3
- Caps: 3 attempts per node (at the cap the node is ESCALATED to graph design), spawn cap 5 per round, spawn budget 20 per run. A consumer of a failed producer is BLOCKED, never spawned on half its inputs
- Every wait names the artifact that crosses it; an arrow with nothing crossing it is a fake edge, deleted so both nodes run in the same round
- Stop rule: the three research jobs are independent, so the graph pays. A goal where each step needs the whole prior result stays one agent
- Only the orchestrator writes Graph State (`state.json`); the draft is versioned, so the corrected draft is `draft@v2` and `draft@v1` stays on disk
- Learning edge: a run that goes green may propose a constraint for later runs (for instance, "every claim carries a source or a flag"), and it binds nothing until a human promotes it (`learn --constraint … --node … --promote --user-approval …`)
