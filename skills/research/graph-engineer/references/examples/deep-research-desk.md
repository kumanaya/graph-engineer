# EXAMPLE ONLY — Deep Research Desk

> **Not a Run / Execute menu item.** Load this only when the user wants an illustration of the diamond + skeptic pattern in the wild. For real work, design jobs for *their* goal in Execute mode.

**What it illustrates:** fan-out to N independent angles → a separate skeptic tries to kill every finding → merge the survivors → human gate before the decision.

## The graph

Every arrow carries an artifact. A node waits only because it reads something.

```text
question (seed file, supplied by the user)
    │ artifact:question
    ▼
split-question — splitter   produces: research-plan
    │ artifact:research-plan@v1   (each worker gets it by path; no other input)
    ├──────────────────────┬──────────────────────┐
    ▼                      ▼                      ▼
angle-a (worker)      angle-b (worker)      angle-c (worker)      one round, one batch
produces findings-a   produces findings-b   produces findings-c   one lens each
    └──────────────────────┴──────────────────────┘
                           │ artifacts: findings-a, findings-b, findings-c
                           ▼
              verify-angles — verifier · lens: kill weak findings
                           │ produces: verdict
                           ▼
              findings-*@v(n) verified      ← consumers wait for the verified version
                           │ artifacts: findings-a, findings-b, findings-c
                           ▼
              merge-report — code node (not spawned)
                           │ produces: research-report
                           ▼
              gate-report — gate (human)         lane: reversible, wide
```

`<root>` below is the graph root passed to `--root` (default `.graph`). Versions are assigned at dispatch, so no worker ever guesses `v<n>`.

## Nodes

| Node | Kind | `requires` (artifact) | `produces` | Writer path | Green condition |
|------|------|-----------------------|-----------|-------------|-----------------|
| `split-question` | splitter | `question` (seed) | `research-plan` | `.graph/research-desk/artifacts/research-plan.v<n>.md` | no two angles can return the same finding, and each angle names one lens |
| `angle-a` … `angle-c` | worker | `research-plan` | `findings-a` … `findings-c` | `.graph/research-desk/artifacts/findings-a.v<n>.md` | ≥1 finding, each with a live source link and a date |
| `verify-angles` | verifier | `findings-a`, `findings-b`, `findings-c` | `verdict` | `.graph/research-desk/artifacts/verdict.v<n>.json` | every finding survives with its source re-checked, or is marked red with the failing check named |
| `merge-report` | code | `findings-a`, `findings-b`, `findings-c` (verified) | `research-report` | `.graph/research-desk/artifacts/research-report.v<n>.md` | one report file, ranked, sources attached, corrected findings listed |
| `gate-report` | gate | `research-report` | — | — | explicit user yes |

One artifact, one producer, one writer path. `verify-angles` covers three artifacts, so it sets no `on_red.corrects` — its verdict's `unit` names the artifact it returns.

## Rounds

| Round | Dispatch — one `delegate_task(tasks=[…])` batch | Envelope carries | Commit |
|-------|--------------------------------------------------|------------------|--------|
| 1 | `split-question` | the `question` seed path | `research-plan@v1` |
| 2 | `angle-a`, `angle-b`, `angle-c` — parallel, one batch | `research-plan@v1` each (its own copy of the path) | `findings-a@v1`, `findings-b@v1`, `findings-c@v1` |
| 3 | `verify-angles` | the three committed findings artifacts | `verdict@v1` |
| 4 | none — `merge-report` arrives under `local_nodes` | the verified findings | `research-report@v1` |
| 5 | none — `gate-report` is `WAITING_HUMAN` | — | the user's own words |

A round is one `dispatch` → one `delegate_task(tasks=[…])` batch → one commit pass. The scheduler recomputes READY after every commit: when the third finding commits, `verify-angles` flips from PENDING to READY with no message sent between nodes.

Round 2 as commands:

```bash
GS="python ${HERMES_SKILL_DIR}/scripts/graph_state.py --root .graph"

$GS init --spec graph.json                    # validates the spec below, writes state.json
$GS dispatch --tasks-file round2.json         # bindings: angle-a (index 0), angle-b (1), angle-c (2)
#   → pass round2.json to delegate_task(tasks=[...]) verbatim — goal, context and output_schema are the envelope
$GS commit --node angle-a --result .graph/research-desk/results/angle-a.a1.json
$GS commit --node angle-b --result .graph/research-desk/results/angle-b.a1.json
$GS commit --node angle-c --result .graph/research-desk/results/angle-c.a1.json
$GS status                                    # verify-angles: READY ; merge-report: PENDING (findings not verified yet)
```

`local_nodes: []` and `deferred_to_next_round: []` for that round. N angles are bounded by the spawn cap: with more READY nodes than the cap, the surplus is named in `deferred_to_next_round` and dispatched in the next round — never dropped, never oversubscribed.

## Who sees what

**The three workers never see each other.** Nothing one of them produces is visible to another until the orchestrator commits it. Each one's `context` is its own **Node Input Envelope** — node spec, green condition, lens, input artifacts by path, constraints, writer path, output contract, and nothing else — and that envelope says so:

```text
You are an isolated subagent. This envelope is everything you may rely on: no other worker's
conversation, findings, or reasoning is visible to you, and your work is visible to no one until
the orchestrator commits it.
```

Facts cross edges as committed files, referenced by path:

| Edge | Artifact that crosses | How the consumer receives it |
|------|----------------------|------------------------------|
| `split-question` → `angle-a`/`b`/`c` | `research-plan@v1` | absolute path + sha256 in `inputs` |
| `angle-a`/`b`/`c` → `verify-angles` | `findings-a`, `findings-b`, `findings-c` | three `requires` entries; committed versions only |
| `angle-a`/`b`/`c` → `merge-report` | the same three findings, at their verified versions | readiness holds `merge-report` at PENDING until `verified_version` exists for all three (the verifier gates it, it does not feed it) |
| `merge-report` → `gate-report` | `research-report` | the gate's `requires` |

The verifier gets the producers' **artifacts**, never their reasoning: `verify-angles` is spawned after `findings-a`/`b`/`c` are committed, and its envelope lists those three paths. Re-reading the sources is the verifier's own job — it runs checks with its own terminal.

## Correction

The skeptic does not delete a weak finding, and it does not re-run the batch. It returns one unit:

```text
verify-angles   verdict: red · unit: findings-b
                reason: "the cited source is a press release, not the data it claims to report"
                evidence: "findings-b p.2: 'unit cost fell 40%' with no source"
                scope: "replace only the unsourced claim in findings-b"
      │ commit
      ▼
angle-b  RED — correction payload attached; angle-a and angle-c keep GREEN and are never re-spawned
      │ next dispatch → angle-b only
      ▼
findings-b@v2 → verify-angles re-armed (PENDING), because the version changed
      │ dispatch
      ▼
verify-angles attempt 2 → verdict green → findings-b verified@v2 → merge-report recomputes to READY
```

`merge-report` then receives exactly what it needs, and nothing else:

```text
inputs: findings-a@v1, findings-b@v2, findings-c@v1
```

The attempt-2 envelope is the normal envelope plus one field:

```json
"correction": {"unit": "findings-b", "reason": "…", "evidence": ["…"], "scope": "…",
               "verdict_artifact": {"artifact": "verdict", "version": 1, "path": "…"},
               "verified_artifact": {"artifact": "findings-b", "version": 1, "path": "…"}}
```

The `verdict` artifact is consumed by that correction edge, not by a `requires`; nothing downstream needs to read the skeptic's file to benefit from it, and the corrected unit commits its new version without ceremony because a new version re-arms its verifier by rule. Revising an artifact that committed nodes already ran on is the separate, explicit case (`--supersedes <reason>`, see `references/graph-state.md`) — accepted output is never silently rewritten.

## Human gate

- **Lane: reversible, wide.** A wrong report costs a rerun, and the user reads it before anything is decided.
- `gate-report` requires `research-report`; when every non-gate node is GREEN the graph status becomes `gated` and the node sits at `WAITING_HUMAN`.
- Approval records the user's own words. Without a quote the command refuses:

```bash
$GS gate --status approved
graph_state: an approved gate needs --user-approval quoting the user's yes        # exit 3

$GS gate --status approved --user-approval "yes, the sourcing is good enough - send it to me"
# → gate: approved ; graph status: done
```

Model confidence is not an input to this decision at any point.

## Graph spec (`graph.json`)

Validated: `graph_state.py --root <root> init --spec graph.json` exits 0 and prints the node list. Every non-gate node below carries an `output_contract`: the base contract from `templates/node-contract.md`, plus the verifier's four verdict fields where declared. A gate has no contract — its artifact is the human's decision. This gate is terminal (nothing runs after it), so it declares no `produces`; `references/examples/go-to-market-kit.md` shows a gate that produces a `decision` artifact and holds downstream work with it. A real graph also adds the domain fields that make the green condition checkable (here: each finding carrying `claim`, `source`, `date`).

```json
{
  "graph": {
    "id": "research-desk",
    "goal": "Answer one question at decision grade: independent angles, sourced and dated findings, adversarial review, one ranked report.",
    "gate": {"lane": "reversible, wide", "action": "the user reads the ranked report and decides"},
    "caps": {"max_attempts": 3, "spawn_cap": 5, "spawn_budget": 20}
  },
  "constraints": [
    "Every finding carries a source link and a date.",
    "A node writes only the artifact path its envelope names."
  ],
  "artifacts": {
    "question": {"type": "source", "seed": true, "path": "C:/work/research-desk/question.md", "description": "the user's question, verbatim"},
    "research-plan": {"type": "plan", "ext": "md", "producer": "split-question"},
    "findings-a": {"type": "findings", "ext": "md", "producer": "angle-a", "verifier": "verify-angles"},
    "findings-b": {"type": "findings", "ext": "md", "producer": "angle-b", "verifier": "verify-angles"},
    "findings-c": {"type": "findings", "ext": "md", "producer": "angle-c", "verifier": "verify-angles"},
    "verdict": {"type": "verdict", "ext": "json", "producer": "verify-angles"},
    "research-report": {"type": "report", "ext": "md", "producer": "merge-report"}
  },
  "nodes": [
    {"id": "split-question", "kind": "splitter",
     "goal": "Cut the question into N disjoint angles and name the artifact and writer path each angle owns.",
     "green_condition": "no two angles can return the same finding, and each angle names one lens",
     "requires": [{"artifact": "question"}],
     "produces": "research-plan",
     "output_contract": {"type": "object", "properties": {"node": {"type": "string"}, "status": {"type": "string", "enum": ["done", "failed"]}, "summary": {"type": "string"}, "artifact_path": {"type": "string"}, "evidence": {"type": "array", "items": {"type": "string"}}}, "required": ["node", "status", "summary", "artifact_path"]}},
    {"id": "angle-a", "kind": "worker", "lens": "angle A from the plan",
     "goal": "Answer the question from angle A only.",
     "green_condition": "at least one finding, each with a live source link and a date",
     "requires": [{"artifact": "research-plan"}],
     "produces": "findings-a",
     "output_contract": {"type": "object", "properties": {"node": {"type": "string"}, "status": {"type": "string", "enum": ["done", "failed"]}, "summary": {"type": "string"}, "artifact_path": {"type": "string"}, "evidence": {"type": "array", "items": {"type": "string"}}}, "required": ["node", "status", "summary", "artifact_path"]}},
    {"id": "angle-b", "kind": "worker", "lens": "angle B from the plan",
     "goal": "Answer the question from angle B only.",
     "green_condition": "at least one finding, each with a live source link and a date",
     "requires": [{"artifact": "research-plan"}],
     "produces": "findings-b",
     "output_contract": {"type": "object", "properties": {"node": {"type": "string"}, "status": {"type": "string", "enum": ["done", "failed"]}, "summary": {"type": "string"}, "artifact_path": {"type": "string"}, "evidence": {"type": "array", "items": {"type": "string"}}}, "required": ["node", "status", "summary", "artifact_path"]}},
    {"id": "angle-c", "kind": "worker", "lens": "angle C from the plan",
     "goal": "Answer the question from angle C only.",
     "green_condition": "at least one finding, each with a live source link and a date",
     "requires": [{"artifact": "research-plan"}],
     "produces": "findings-c",
     "output_contract": {"type": "object", "properties": {"node": {"type": "string"}, "status": {"type": "string", "enum": ["done", "failed"]}, "summary": {"type": "string"}, "artifact_path": {"type": "string"}, "evidence": {"type": "array", "items": {"type": "string"}}}, "required": ["node", "status", "summary", "artifact_path"]}},
    {"id": "verify-angles", "kind": "verifier", "lens": "kill weak findings",
     "goal": "Try to disprove every finding in the three angle artifacts.",
     "green_condition": "every finding either survives with its source re-checked at its date, or is marked red with the failing check named",
     "requires": [{"artifact": "findings-a"}, {"artifact": "findings-b"}, {"artifact": "findings-c"}],
     "produces": "verdict",
     "output_contract": {"type": "object", "properties": {"node": {"type": "string"}, "status": {"type": "string", "enum": ["done", "failed"]}, "summary": {"type": "string"}, "artifact_path": {"type": "string"}, "evidence": {"type": "array", "items": {"type": "string"}}, "verdict": {"type": "string", "enum": ["green", "red"]}, "unit": {"type": "string"}, "reason": {"type": "string"}, "scope": {"type": "string"}}, "required": ["node", "status", "summary", "artifact_path", "verdict", "unit", "reason", "scope"]}},
    {"id": "merge-report", "kind": "code",
     "goal": "Merge the verified findings into one report ranked by confidence; list every returned-and-corrected finding with its verdict reason.",
     "green_condition": "one report file exists, ranked, sources attached, dropped findings listed",
     "requires": [{"artifact": "findings-a"}, {"artifact": "findings-b"}, {"artifact": "findings-c"}],
     "produces": "research-report",
     "output_contract": {"type": "object", "properties": {"node": {"type": "string"}, "status": {"type": "string", "enum": ["done", "failed"]}, "summary": {"type": "string"}, "artifact_path": {"type": "string"}, "evidence": {"type": "array", "items": {"type": "string"}}}, "required": ["node", "status", "summary", "artifact_path"]}},
    {"id": "gate-report", "kind": "gate",
     "goal": "the user reads the ranked report",
     "green_condition": "explicit user yes",
     "requires": [{"artifact": "research-report"}]}
  ]
}
```

Seed artifacts are files the user already has. The `path` must be absolute — children resolve it directly — and it is hashed at `init`.

## Prompt (example)

```text
use a workflow: i need decision-grade research on [question] — independent angles, every finding sourced and dated, and nothing reaches me until it has survived an adversarial pass.
```

That one sentence is the whole input. Graph Engineer designs the graph from it — nodes, artifacts, contracts, rounds, gate lane. The diagram above is what that design looks like for this class of goal; it is not a menu entry.

## Pattern notes

- Every finding needs a **source link** and a **date** — that is the green condition each angle is checked against
- The skeptic tries to **disprove** every finding. A failure returns **one unit** to its own researcher, with the verdict and a scope; the other angles are untouched
- Angles must fit the question — do not force domain-specific angles onto unrelated goals
- One lens per worker, one writer per path: three angles writing `findings-*.v1.md` are three writers, not three writers on one file
- The merge is a **code node**: dedupe, rank, order — one correct answer, no spawn, no tokens
- Output shape in this example: `research-report.md`
- Human gate: the user reads the committed report; the lane is reversible and wide, and it opens on the user's words
- Caps: 3 attempts per node (at the cap the node is ESCALATED to graph design), spawn cap 5 per round, spawn budget 20 per run. A consumer of a failed producer is BLOCKED, never spawned on half its inputs — attempt four is not a plan
- Nothing waits on ordering alone: an arrow with no artifact crossing it is a fake edge, so the wait is deleted and both nodes run in the same round
- Only the orchestrator writes Graph State (`state.json`); each worker writes exactly one file, the artifact path its envelope named
- Stop rule: this graph pays because the angles are independent sources of truth. A goal where each step needs the whole prior result stays one agent, with no Graph State machinery at all
- Learning edge: an accepted run may propose a constraint for later runs (for instance, "a finding with no live source is not a finding"), and it binds nothing until a human promotes it (`learn --constraint … --node … --promote --user-approval …`)
