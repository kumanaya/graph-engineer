# EXAMPLE ONLY — Go-to-Market Kit

> **Not a Run / Execute menu item.** Load this only when the user wants an illustration of mid-graph human pause + second fan-out + checker against a foundation doc. For real work, design jobs for *their* goal in Execute mode.

**What it illustrates:** parallel research → merge to a foundation doc → **mandatory human pause** → parallel producers → checker vs foundation → package.

## The graph

Every arrow carries an artifact.

```text
product-brief (seed file: product, audience, what the user already knows)
    │ artifact:product-brief
    ├──────────────────────┬──────────────────────┐
    ▼                      ▼                      ▼
research-buyer        research-channels     research-competitors    one round, one batch
produces buyer-voice  produces channel-map  produces competitor-pitch
    └──────────────────────┴──────────────────────┘
                           │ artifacts: buyer-voice, channel-map, competitor-pitch
                           ▼
                merge-positioning — code node (not spawned)
                           │ produces: positioning-doc
                           ▼
                ★ gate-positioning — gate (human)     lane: hard to reverse
                           │ produces: positioning-decision  (the user's answer, as an artifact)
    ┌──────────────────────┼──────────────────────┐
    ▼                      ▼                      ▼   each writer requires
write-landing         write-posts            write-outreach       positioning-decision@v1
produces landing-copy produces launch-posts  produces outreach    + positioning-doc@v1
    └──────────────────────┴──────────────────────┘
                           │ artifacts: landing-copy, launch-posts, outreach
                           ▼
                check-assets — verifier · lens: off-positioning claims
                           │ produces: check-verdict
                           ▼
                all three assets verified    ← the kit cannot be assembled before this
                           │ artifacts: the three verified assets
                           ▼
                assemble-kit — code node (not spawned)
                           │ produces: launch-kit
```

`<root>` below is the graph root passed to `--root` (default `.graph`).

## Nodes

| Node | Kind | `requires` (artifact) | `produces` | Writer path | Green condition |
|------|------|-----------------------|-----------|-------------|-----------------|
| `research-buyer` | worker | `product-brief` (seed) | `buyer-voice` | `.graph/gtm-kit/artifacts/buyer-voice.v<n>.md` | every quote is traceable to a real page, and the profile states what the buyer is trying to get done |
| `research-channels` | worker | `product-brief` (seed) | `channel-map` | `.graph/gtm-kit/artifacts/channel-map.v<n>.md` | every channel is named with the evidence that the buyer is there |
| `research-competitors` | worker | `product-brief` (seed) | `competitor-pitch` | `.graph/gtm-kit/artifacts/competitor-pitch.v<n>.md` | every pitch claim is quoted from the competitor's own page |
| `merge-positioning` | code | `buyer-voice`, `channel-map`, `competitor-pitch` | `positioning-doc` | `.graph/gtm-kit/artifacts/positioning-doc.v<n>.md` | one page; every line cites the research artifact it came from, or is dropped |
| `gate-positioning` | gate | `positioning-doc` | `positioning-decision` | `.graph/gtm-kit/artifacts/positioning-decision.v<n>.json` | explicit user yes |
| `write-landing` | worker | `positioning-decision`, `positioning-doc` | `landing-copy` | `.graph/gtm-kit/artifacts/landing-copy.v<n>.md` | every claim in the copy traces to a line in the positioning doc |
| `write-posts` | worker | `positioning-decision`, `positioning-doc` | `launch-posts` | `.graph/gtm-kit/artifacts/launch-posts.v<n>.md` | each post traces to a line in the positioning doc and names its channel |
| `write-outreach` | worker | `positioning-decision`, `positioning-doc` | `outreach` | `.graph/gtm-kit/artifacts/outreach.v<n>.md` | each message traces to a line in the positioning doc and fits its channel |
| `check-assets` | verifier | `landing-copy`, `launch-posts`, `outreach` | `check-verdict` | `.graph/gtm-kit/artifacts/check-verdict.v<n>.json` | every asset line traces to a line in the positioning doc, or is returned with the line named |
| `assemble-kit` | code | the three assets (verified) | `launch-kit` | `.graph/gtm-kit/artifacts/launch-kit.v<n>.md` | `launch-kit/` holds the three verified assets plus an index that names each file |

The three assets are declared with a verifier, so `assemble-kit` cannot run until each has a `verified_version`. `check-assets` covers three artifacts, so it sets no `on_red.corrects` — its verdict's `unit` names the asset that returns. The gate's own artifact is a `decision`: the human's answer, versioned like everything else, so the pause is an edge and not a convention.

## Rounds

| Round | Dispatch — one `delegate_task(tasks=[…])` batch | Envelope carries | Commit |
|-------|--------------------------------------------------|------------------|--------|
| 1 | `research-buyer`, `research-channels`, `research-competitors` — parallel, one batch | the `product-brief` seed path + one lens each | `buyer-voice@v1`, `channel-map@v1`, `competitor-pitch@v1` |
| 2 | none — `merge-positioning` arrives under `local_nodes` | the three committed research artifacts | `positioning-doc@v1` |
| — | **PAUSE** — nothing is dispatchable: `gate-positioning` is `WAITING_HUMAN`, and its consumers sit `PENDING` on `positioning-decision` | — | `positioning-decision@v1` — the user's answer, committed as an artifact |
| 3 | `write-landing`, `write-posts`, `write-outreach` — parallel, one batch | `positioning-decision@v1` + `positioning-doc@v1` each | `landing-copy@v1`, `launch-posts@v1`, `outreach@v1` |
| 4 | `check-assets` | the three committed assets | `check-verdict@v1` |
| 5 | none — `assemble-kit` under `local_nodes` | the three verified assets | `launch-kit@v1` |

Rounds 1 and 3 as commands:

```bash
GS="python ${HERMES_SKILL_DIR}/scripts/graph_state.py --root .graph"

$GS init --spec graph.json
$GS dispatch --tasks-file round1.json       # 3 bindings → delegate_task(tasks=[...]) verbatim
$GS commit --node research-buyer       --result .graph/gtm-kit/results/research-buyer.a1.json
$GS commit --node research-channels    --result .graph/gtm-kit/results/research-channels.a1.json
$GS commit --node research-competitors --result .graph/gtm-kit/results/research-competitors.a1.json

$GS dispatch                                # local_nodes: ["merge-positioning"] — run it, then commit it
$GS commit --node merge-positioning --result .graph/gtm-kit/results/merge-positioning.a1.json

$GS status                                  # gate-positioning: WAITING_HUMAN
                                            # write-landing/posts/outreach: PENDING — "gate gate-positioning
                                            #   has not been answered yet"
$GS dispatch                                # bindings: [] and local_nodes: [] — the gate holds the graph

$GS gate --status approved                  # exit 3: this lane is hard to reverse
$GS gate --status approved --user-approval "yes - this is the positioning, write the kit"
                                            # commits positioning-decision@v1
$GS dispatch --tasks-file round3.json       # 3 bindings, each carrying positioning-decision@v1
                                            #   and positioning-doc@v1
```

The three researchers never see each other; the three writers never see each other either. Each worker gets its own **Node Input Envelope**, built at dispatch from committed Graph State. What the round-3 workers share is a **file**: each envelope names `positioning-decision@v1` and `positioning-doc@v1`, with absolute paths and sha256. The worker that wrote the landing page cannot see what the worker writing the posts decided, and does not need to — the positioning doc is the contract between them, and the decision is the door. The checker is no different: `check-assets` receives the three committed asset files by path, never a producer's account of its own work.

## The mid-graph pause

- **Lane: hard to reverse.** Everything downstream of the pause is copy written for a live audience: one wrong positioning line propagates into the landing page, a week of posts and the outreach messages at once, and undoing it means editing live content and correcting what already went out. The gate does not open on confidence; it opens on the user reading one page.
- **The pause is a dependency, not round discipline.** `gate-positioning` requires `positioning-doc` and produces `positioning-decision` (type `decision`). Every asset writer requires that decision, so the moment `merge-positioning` commits, the writers are `PENDING` — not "READY, but we agreed not to dispatch them":

```text
WAITING_HUMAN
  ★ gate-positioning        artifact: positioning-decision (not produced yet)

PENDING
  ○ write-landing           — gate gate-positioning has not been answered yet
  ○ write-posts             — gate gate-positioning has not been answered yet
  ○ write-outreach          — gate gate-positioning has not been answered yet
```

- `dispatch` releases nothing while the gate is unanswered — `bindings: []`, `local_nodes: []` — however many times it is called. Nothing downstream of a human gate can run, and no orchestrator discipline is needed to hold it back.
- **Approval is the user's words, or nothing:**

```bash
$GS gate --status approved
graph_state: lane 'hard to reverse' is hard to reverse: an explicit --user-approval quoting the
user's yes is required. Never approximate approval from model confidence.      # exit 3

$GS gate --status approved --user-approval "yes - this is the positioning, write the kit"
# → positioning-decision@v1 committed ; the three writers recompute to READY ; graph status: running
```

- **A no is a version too.** `gate --status rejected --user-approval "…"` commits the decision as rejected (the words are required here as well), sets `gate-positioning` to `BLOCKED`, and every writer becomes `BLOCKED — gate gate-positioning was rejected — nothing downstream runs`. A later explicit yes commits `v2` and releases them; the rejected version stays on disk for inspection. A rejected gate is never silently overwritten.
- The decision artifact is not verified by a node — the human is the verifier — and no model can write it: leaf children cannot reach the user, and only the orchestrator runs `gate`.

## Correction

The checker reads three artifacts and can return exactly one of them:

```text
check-assets   verdict: red · unit: launch-posts
               reason: "post 3 claims a metric the positioning doc dropped"
               evidence: "post 3: '2x faster' — not in positioning-doc@v1"
               scope: "launch-posts only: cut post 3 or restate it from the doc"
        │ commit
        ▼
write-posts  RED — correction payload attached; write-landing and write-outreach keep GREEN
        │ next dispatch → write-posts only
        ▼
launch-posts@v2 → check-assets re-armed (PENDING), because the version changed
        │ dispatch
        ▼
check-assets attempt 2 → verdict green → all three assets verified → assemble-kit recomputes to READY
```

Off-asset work returns along the **correction edge** to its own producer, never to the batch: the landing page and the outreach messages were not rewritten, and their versions did not change.

## Graph spec (`graph.json`)

Validated: `graph_state.py --root <root> init --spec graph.json` exits 0. Every non-gate node below carries an `output_contract`: the base contract from `templates/node-contract.md`, plus the verifier's four verdict fields where declared. A gate has no contract — its artifact is the human's decision, and this gate's `decision` artifact is what holds the second fan-out.

```json
{
  "graph": {
    "id": "gtm-kit",
    "goal": "Turn a product brief into a launch kit: research the buyer, stop for the user's yes on the positioning, then produce and check every asset against it.",
    "gate": {"lane": "hard to reverse", "action": "the user approves the positioning doc; the assets may then be written, and nothing goes to a customer"},
    "caps": {"max_attempts": 3, "spawn_cap": 5, "spawn_budget": 20}
  },
  "constraints": [
    "Every line in the positioning doc traces to a research artifact or is dropped.",
    "Nothing is sent, posted, or scheduled by any node."
  ],
  "artifacts": {
    "product-brief": {"type": "source", "seed": true, "path": "C:/work/gtm-kit/product-brief.md", "description": "product, audience, and what the user already knows, written by the user"},
    "buyer-voice": {"type": "findings", "ext": "md", "producer": "research-buyer"},
    "channel-map": {"type": "findings", "ext": "md", "producer": "research-channels"},
    "competitor-pitch": {"type": "findings", "ext": "md", "producer": "research-competitors"},
    "positioning-doc": {"type": "plan", "ext": "md", "producer": "merge-positioning"},
    "positioning-decision": {"type": "decision", "ext": "json", "producer": "gate-positioning"},
    "landing-copy": {"type": "asset", "ext": "md", "producer": "write-landing", "verifier": "check-assets"},
    "launch-posts": {"type": "asset", "ext": "md", "producer": "write-posts", "verifier": "check-assets"},
    "outreach": {"type": "asset", "ext": "md", "producer": "write-outreach", "verifier": "check-assets"},
    "check-verdict": {"type": "verdict", "ext": "json", "producer": "check-assets"},
    "launch-kit": {"type": "package", "ext": "md", "producer": "assemble-kit"}
  },
  "nodes": [
    {"id": "research-buyer", "kind": "worker", "lens": "the buyer's own words",
     "goal": "Profile the buyer using their own words.",
     "green_condition": "every quote is traceable to a real page, and the profile states what the buyer is trying to get done",
     "requires": [{"artifact": "product-brief"}],
     "produces": "buyer-voice",
     "output_contract": {"type": "object", "properties": {"node": {"type": "string"}, "status": {"type": "string", "enum": ["done", "failed"]}, "summary": {"type": "string"}, "artifact_path": {"type": "string"}, "evidence": {"type": "array", "items": {"type": "string"}}}, "required": ["node", "status", "summary", "artifact_path"]}},
    {"id": "research-channels", "kind": "worker", "lens": "channels and communities",
     "goal": "Map where this buyer already spends time.",
     "green_condition": "each channel is named with the evidence that the buyer is there",
     "requires": [{"artifact": "product-brief"}],
     "produces": "channel-map",
     "output_contract": {"type": "object", "properties": {"node": {"type": "string"}, "status": {"type": "string", "enum": ["done", "failed"]}, "summary": {"type": "string"}, "artifact_path": {"type": "string"}, "evidence": {"type": "array", "items": {"type": "string"}}}, "required": ["node", "status", "summary", "artifact_path"]}},
    {"id": "research-competitors", "kind": "worker", "lens": "how competitors pitch",
     "goal": "Collect how competitors pitch to this same buyer.",
     "green_condition": "each pitch claim is quoted from the competitor's own page",
     "requires": [{"artifact": "product-brief"}],
     "produces": "competitor-pitch",
     "output_contract": {"type": "object", "properties": {"node": {"type": "string"}, "status": {"type": "string", "enum": ["done", "failed"]}, "summary": {"type": "string"}, "artifact_path": {"type": "string"}, "evidence": {"type": "array", "items": {"type": "string"}}}, "required": ["node", "status", "summary", "artifact_path"]}},
    {"id": "merge-positioning", "kind": "code",
     "goal": "Merge the three research artifacts into one page of positioning; drop any line with no research behind it.",
     "green_condition": "one page exists and every line cites the research artifact it came from",
     "requires": [{"artifact": "buyer-voice"}, {"artifact": "channel-map"}, {"artifact": "competitor-pitch"}],
     "produces": "positioning-doc",
     "output_contract": {"type": "object", "properties": {"node": {"type": "string"}, "status": {"type": "string", "enum": ["done", "failed"]}, "summary": {"type": "string"}, "artifact_path": {"type": "string"}, "evidence": {"type": "array", "items": {"type": "string"}}}, "required": ["node", "status", "summary", "artifact_path"]}},
    {"id": "gate-positioning", "kind": "gate",
     "goal": "the user reads the positioning doc before any asset is written",
     "green_condition": "explicit user yes",
     "requires": [{"artifact": "positioning-doc"}],
     "produces": "positioning-decision"},
    {"id": "write-landing", "kind": "worker", "lens": "landing page copy",
     "goal": "Write the landing page copy from the approved positioning doc.",
     "green_condition": "every claim in the copy traces to a line in the positioning doc",
     "requires": [{"artifact": "positioning-decision"}, {"artifact": "positioning-doc"}],
     "produces": "landing-copy",
     "output_contract": {"type": "object", "properties": {"node": {"type": "string"}, "status": {"type": "string", "enum": ["done", "failed"]}, "summary": {"type": "string"}, "artifact_path": {"type": "string"}, "evidence": {"type": "array", "items": {"type": "string"}}}, "required": ["node", "status", "summary", "artifact_path"]}},
    {"id": "write-posts", "kind": "worker", "lens": "launch posts",
     "goal": "Write one week of launch posts from the approved positioning doc.",
     "green_condition": "each post traces to a line in the positioning doc and names its channel",
     "requires": [{"artifact": "positioning-decision"}, {"artifact": "positioning-doc"}],
     "produces": "launch-posts",
     "output_contract": {"type": "object", "properties": {"node": {"type": "string"}, "status": {"type": "string", "enum": ["done", "failed"]}, "summary": {"type": "string"}, "artifact_path": {"type": "string"}, "evidence": {"type": "array", "items": {"type": "string"}}}, "required": ["node", "status", "summary", "artifact_path"]}},
    {"id": "write-outreach", "kind": "worker", "lens": "outreach messages",
     "goal": "Write the outreach messages from the approved positioning doc.",
     "green_condition": "each message traces to a line in the positioning doc and fits the channel it is written for",
     "requires": [{"artifact": "positioning-decision"}, {"artifact": "positioning-doc"}],
     "produces": "outreach",
     "output_contract": {"type": "object", "properties": {"node": {"type": "string"}, "status": {"type": "string", "enum": ["done", "failed"]}, "summary": {"type": "string"}, "artifact_path": {"type": "string"}, "evidence": {"type": "array", "items": {"type": "string"}}}, "required": ["node", "status", "summary", "artifact_path"]}},
    {"id": "check-assets", "kind": "verifier", "lens": "off-positioning claims",
     "goal": "Check every asset against the positioning doc.",
     "green_condition": "every asset line either traces to a line in the positioning doc or is returned with the line named",
     "requires": [{"artifact": "landing-copy"}, {"artifact": "launch-posts"}, {"artifact": "outreach"}],
     "produces": "check-verdict",
     "output_contract": {"type": "object", "properties": {"node": {"type": "string"}, "status": {"type": "string", "enum": ["done", "failed"]}, "summary": {"type": "string"}, "artifact_path": {"type": "string"}, "evidence": {"type": "array", "items": {"type": "string"}}, "verdict": {"type": "string", "enum": ["green", "red"]}, "unit": {"type": "string"}, "reason": {"type": "string"}, "scope": {"type": "string"}}, "required": ["node", "status", "summary", "artifact_path", "verdict", "unit", "reason", "scope"]}},
    {"id": "assemble-kit", "kind": "code",
     "goal": "Package the three verified assets into launch-kit/ and write the index.",
     "green_condition": "launch-kit/ contains the three verified assets and an index that names each file",
     "requires": [{"artifact": "landing-copy"}, {"artifact": "launch-posts"}, {"artifact": "outreach"}],
     "produces": "launch-kit",
     "output_contract": {"type": "object", "properties": {"node": {"type": "string"}, "status": {"type": "string", "enum": ["done", "failed"]}, "summary": {"type": "string"}, "artifact_path": {"type": "string"}, "evidence": {"type": "array", "items": {"type": "string"}}}, "required": ["node", "status", "summary", "artifact_path"]}}
  ]
}
```

## Prompt (example)

```text
use a workflow: i'm launching [product] for [audience] — research the buyer, the channels and the competitors in parallel, merge that into a one-page positioning doc and stop there until i say yes, then write the landing page, a week of launch posts and the outreach messages from that doc, check every one of them against it, and package the kit without sending anything.
```

That one sentence is the whole input. Graph Engineer designs the graph from it — nodes, artifacts, contracts, rounds, and where the pause sits. The diagram above is one design for that class of goal, not a menu entry.

## Pattern notes

- The pause sits before the expensive, outward-facing fan-out, and its lane is by blast radius: hard to reverse, opened only by the user's words
- A gate that produces a `decision` artifact holds its consumers as a real dependency: they stay `PENDING` until the human answers and `BLOCKED` after a no, so `dispatch` releases nothing on its own
- The checker is a separate node with a distinct lens, and it compares each asset against the **positioning doc artifact**, never against a producer's account of its own work
- "Every asset line traces to a line in the positioning doc" is the green condition, settled per asset; a failure returns that asset to its own writer
- One writer per file: `landing-copy`, `launch-posts` and `outreach` are three artifacts, not three writers on one
- Merging the research into the foundation doc is a **code node**; packaging the kit is a **code node**
- Output shape in this example: `launch-kit/`
- Nothing is sent, posted or scheduled by any node — the delivery step stays with the user
- Caps: 3 attempts per node, 5 concurrent spawns per round, 20 spawns per run. At the attempt cap the graph escalates to graph design, and its consumers in the next round become BLOCKED rather than running on half the inputs
- Only the orchestrator writes Graph State (`state.json`); each worker writes exactly one file, the artifact path its envelope named
- The learning edge: an accepted kit may propose a constraint for later runs (for instance, "every asset line traces to a line in the positioning doc"), and it binds nothing until a human promotes it (`learn --constraint … --node … --promote --user-approval …`)
