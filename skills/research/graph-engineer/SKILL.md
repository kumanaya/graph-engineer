---
name: graph-engineer
description: >-
  Design and run agent graphs for any goal: diamonds, fan-out/verify/merge,
  loops with machine-checkable green conditions, code nodes, return paths,
  human gates on blast radius, fake edges, and the stop rule. Built for
  isolated Hermes subagents: the orchestrator owns Graph State, every node gets
  a self-contained envelope, and facts cross edges as versioned artifacts.
version: 4.0.0
author: Kumanaya
license: MIT
metadata:
  hermes:
    tags: [graph-engineering, diamond, workflows, autonomous-agents, multi-agent, delegation, isolated-subagents, graph-state, artifacts, loops, human-gate]
    category: autonomous-ai-agents
---

# Graph Engineer

## Overview

A graph is a plan for autonomous AI work: which jobs must run, and which job waits for which. Each job is one assistant-sized task. An arrow is real only when **an artifact crosses it**.

The runtime fact everything here is built on:

```text
SUBAGENTS ARE ISOLATED.
```

A Hermes subagent spawned with `delegate_task` starts with a completely fresh conversation. It cannot see the parent's history, a sibling's findings, another worker's reasoning, or the state of the graph. Only its final summary comes back. So:

> **Workers are isolated. The graph is not.**

The orchestrator owns Graph State, and it hands every node a self-contained **envelope**: job, green condition, lens, input artifacts by path, constraints, writer path, output contract. Facts move between nodes only as committed, versioned artifacts.

Two layers, and you need both. A **loop** makes one unit of work correct without you: produce → check → correct → repeat until green. A **graph** decides which units exist, in what order, and what happens to the ones that fail. The loop lives **inside** a node; the graph lives **between** nodes.

Nodes come in five kinds — **splitter, worker, verifier, code node, gate** — and two of them are not model calls.

The default paying pattern is the **diamond**: split → parallel workers → separate verifier kills weak findings → merge into one result. You are the **human gate** before anything irreversible.

This skill is a **generic workflow framework**. For any user goal: design the graph, then execute it. It is not a menu of SEO, GTM, or other fixed products. Course builds under `references/examples/` are illustrations only — load them when the user asks for an example, never as the Execute menu.

## When to Use

- User wants a multi-agent workflow / agent graph for any goal
- User mentions diamond pattern, fake edges, stop rule, human gate, or graph engineering
- User mentions loops, checks that can fail, code nodes, return/feedback edges, or gate lanes
- User asks to audit an existing AI pipeline for wasted waits or for workers that assume shared context
- User wants a reusable `use a workflow:` structure designed and run for *their* task

**Don't use for:** a single sequential task where every step needs the full prior result and nothing splits into independent jobs. Stay one agent (stop rule). Do not force a diamond — and do not build Graph State machinery for a one-node graph.

## Operating Modes

Pick **one** mode per request. Announce it before acting.

| Mode | When | Load |
|------|------|------|
| **Execute** (default) | User wants the work done via a workflow | `references/isolation.md`, `references/graph-state.md`, `references/scheduler.md`, `templates/graph-spec.md` |
| **Design** | User wants the graph/spec/prompt only — no run | `templates/graph-spec.md`, `templates/node-contract.md`, `references/playbook.md` |
| **Audit** | User has an existing AI system / pipeline | `references/vocabulary.md`, `references/isolation.md`, `references/playbook.md` |
| **Teach** | User wants the method / vocabulary / rules | Only the needed file under `references/` |

If the user does not specify a mode and wants a result, choose **Execute**.

Load extras on demand:

```text
skill_view("graph-engineer", "references/isolation.md")        ← the invariant + envelopes + context policy
skill_view("graph-engineer", "references/graph-state.md")      ← state, artifacts, commit, command surface
skill_view("graph-engineer", "references/scheduler.md")        ← readiness, rounds, failure semantics, caps
skill_view("graph-engineer", "references/hermes-runtime.md")   ← what Hermes actually provides, and its limits
skill_view("graph-engineer", "references/vocabulary.md")
skill_view("graph-engineer", "references/diamond-pattern.md")
skill_view("graph-engineer", "references/loop-design.md")
skill_view("graph-engineer", "references/node-types.md")
skill_view("graph-engineer", "references/gate-design.md")
skill_view("graph-engineer", "references/return-paths.md")
skill_view("graph-engineer", "references/wiring-rules.md")
skill_view("graph-engineer", "references/playbook.md")
skill_view("graph-engineer", "templates/graph-spec.md")
skill_view("graph-engineer", "templates/node-contract.md")
```

Examples (illustration only — never the Execute menu):

```text
skill_view("graph-engineer", "references/examples/isolated-workers.md")
skill_view("graph-engineer", "references/examples/deep-research-desk.md")
skill_view("graph-engineer", "references/examples/seo-content-machine.md")
skill_view("graph-engineer", "references/examples/go-to-market-kit.md")
```

## Hard Rules (always on)

1. **Workers are isolated; the graph is not.** A worker may rely only on its envelope: node spec, supplied context, supplied artifacts, supplied constraints, available tools. Anything else it needs must be put there.
2. **Stop rule:** A graph buys breadth, not better judgment. Split only jobs that never read each other's results. If every step needs the full picture, use one agent.
3. **Check first:** Before the work exists, name the green condition a program could evaluate. "No errors were raised" is not a check, and neither is the model's confidence.
4. **Loop in the node, graph between nodes:** the node repeats produce → check → correct; the graph owns split, fan-out, verify, merge, gate, and return.
5. **Fake edges first:** For every "and then," name the artifact that crosses. If you cannot, there is no edge — run both nodes in the same round. An ordering-only edge is not expressible here, by design.
6. **One writer:** every artifact has exactly one producing node, and only the orchestrator writes Graph State. Workers produce outputs; the orchestrator commits them.
7. **No self-grading:** Never let the same agent verify its own findings. The verifier is a separate node that requires the artifact, not the producer's reasoning.
8. **Verify before consume:** declare a verifier on an artifact and no consumer runs until that artifact is verified. Verify first, merge second.
9. **Distinct checker lenses:** correctness, freshness, source quality, fit — not the same lens twice. Adapt lenses to the domain; keep them distinct.
10. **Own envelope per worker:** separate context + distinct lens + disjoint split dimension. All three, or four workers buy one opinion and three echoes.
11. **Code nodes for deterministic steps:** compare, dedupe, rank, filter, route — and the graph's own bookkeeping (readiness, versions, commits). One correct answer = code, not a model call.
12. **Return the unit, not the batch:** a failed unit goes back to the node that produced it, with unit · verdict · reason · evidence · scope, and produces a **new version**. Never send the batch back — it rewrites work that was correct.
13. **Learning changes future envelopes:** an accepted result may propose a constraint; only a human promotes it, and only then does it bind later runs.
14. **Wiring:** attempt cap + spawn cap + spawn budget; one writer per path; code owns readiness and routing; at the cap, the plan is at fault, not the unit.
15. **Human gate:** the last yes sits where a mistake is expensive to undo — opened by blast radius, never by confidence. Hard-to-reverse work does not open.
16. **Irreversible actions:** never send, publish, refund, invoice, or go live without explicit user approval.
17. **No fixed task menu:** Invent nodes for *this* request. Do not default to research/SEO/GTM examples unless the user asks for those illustrations.

Default caps (override only if the user sets them): max **3** attempts per node (then escalate to the plan); max **5** concurrent spawns per round; spawn budget **20** per run; one writer per path.

## Execute Procedure (default)

**Done when:** a graph was designed for this goal (or one-agent was correctly chosen), every node ran to its stated green condition or was honestly flagged, survivors were merged into the named outputs, and the human gate paused where required.

1. Clarify goal, success criteria, and irreversible actions. Do not invent user business facts.
2. Apply the **stop rule**. No independent split → stay one agent; do the work without a fake diamond or a state file.
3. **Write the green condition and output contract first**, per node, before any work exists. Contracts follow `templates/node-contract.md`.
4. If a graph pays: write the spec (goal, artifacts with producers/verifiers, nodes with `requires`/`produces`/contracts) and validate it:
   ```bash
   python ${HERMES_SKILL_DIR}/scripts/graph_state.py --root .graph init --spec graph.json
   ```
   (`python` on Windows, `python3` on macOS/Linux; stdlib only, no install step.) `init` refuses fake edges, unowned artifacts, cycles, verifier contracts without a verdict payload, and unknown keys. Every refusal is one of the hard rules — fix the design, not the message.
5. Announce the graph in a short sketch: split dimension · nodes by kind · verifier lenses · rounds · return paths · gate lane · caps.
6. **Run the scheduler loop** until nothing is READY:
   ```bash
   python ${HERMES_SKILL_DIR}/scripts/graph_state.py --root .graph dispatch
   ```
   - Pass `round_tasks` to `delegate_task(tasks=[…])` **verbatim** — goal, context and output_schema are the envelope and the contract. Do not paraphrase them.
   - Run every node listed under `local_nodes` yourself with `execute_code`/`terminal` (they are code nodes; they are not spawned).
   - Hermes delivers the batch between turns. When it lands, commit each node:
     ```bash
     python ${HERMES_SKILL_DIR}/scripts/graph_state.py --root .graph commit \
         --node audit-auth --result .graph/repo-audit/results/audit-auth.a1.json
     ```
     The child writes that file itself (its envelope told it to); if it did not, write the JSON it returned there first. Never commit a claim you cannot find on disk.
   - Then `dispatch` again. `status` shows what ran, what is ready, and exactly why anything waits.
7. **Handle what comes back** (never improvise):
   - RED from a verifier → only that unit returns, automatically, with the verdict and scope attached. Do not re-spawn siblings.
   - RED from execution → dispatch again while attempts remain; the cap is enforced by state.
   - BLOCKED → an upstream node died terminally. Do not spawn it with a partial envelope.
   - ESCALATED → stop. Return to step 3/4 and fix the split, the check, or the brief. Never attempt N+1.
   - Accepted work turns out wrong (the user says so, or a later gate reveals it) → `reopen --node <id> --reason … [--user-approval …]`. That is the only way a GREEN node runs again: it goes RED with the reason recorded, its consumers are flagged stale, and the rewrite still needs `--supersedes` at commit. Never re-dispatch committed work silently.
8. **Merge** survivors into the named output path(s) as a code node, and commit it.
9. **Pause at the human gate.** Summarize from committed state (`status` + the artifacts): what ran, what passed, what failed, what was corrected, which artifact versions are being accepted, which deterministic checks passed, what remains uncertain, what happens after approval, whether it is reversible. Wait for the user. Record it:
   ```bash
   python ${HERMES_SKILL_DIR}/scripts/graph_state.py --root .graph gate \
       --status approved --user-approval "<the user's own words>"
   ```
   If anything runs after the gate, declare a `decision` artifact on the gate node and make those nodes require it — otherwise the pause is only as strong as your round discipline. A rejection blocks them; a later explicit approval releases them.
10. If a cause was confirmed, offer the constraint for promotion — never promote it silently:
    ```bash
    python ${HERMES_SKILL_DIR}/scripts/graph_state.py --root .graph learn \
        --constraint "…" --node <id> --promote --user-approval "<the user's own words>"
    ```

**Before the first spawn, check the run is possible:** the batch must fit `delegation.max_concurrent_children`, a one-shot session caps total spawns (`delegation.oneshot_max_children`, default 2), and if `delegation.worktree_isolation` is on, keep the graph root outside the repo or the children will not share it. See `references/hermes-runtime.md`.

Do **not** load `references/examples/*` during Execute unless the user explicitly asks for an example pattern.

## Design Procedure

**Done when:** a filled graph spec exists — nodes, artifacts, edges, contracts, rounds, return paths and gate lane — a validated `graph.json` is accepted by `init`, and a paste-ready `use a workflow:` prompt is delivered, without running the graph.

1. Load `templates/graph-spec.md`, `templates/node-contract.md` and `references/playbook.md`.
2. Clarify goal, success criteria, and where a mistake is expensive (gate lane).
3. Name the green condition and output contract per node before naming the work.
4. Name nodes with their kind; declare artifacts with their producer (and verifier where the work needs checking); express every edge as a `requires`.
5. For each edge ask: **what exactly crosses this edge?** If the answer is nothing, delete the edge and run both nodes in the same round.
6. Prefer the diamond unless the work cannot split — then document why one agent wins.
7. Assign verifier lenses (distinct questions); set attempt/spawn caps and the spawn budget.
8. Name the correction edge (which unit, from which verifier, with what scope) and the learning edge (which accepted outcome yields which constraint).
9. Fill the template; validate the spec with `init`; write a single runnable prompt that includes `use a workflow:`.
10. Offer to **Execute** immediately if the user wants the work done now.

## Audit Procedure

**Done when:** nodes and edges are listed, fake edges are named and removed, nodes that assume knowledge they never receive are flagged, boxes without a failing check are flagged, and a stay-one-agent vs graph recommendation is clear.

1. List every job and every "and then".
2. For each arrow: **name the artifact that crosses.** Nothing named → fake edge → delete the wait and parallelize.
3. For each node: what does it actually receive? Anything it needs but is not handed (a sibling's findings, "the current state", a decision made elsewhere) is a **missing edge or a missing envelope** — not a prompt problem.
4. For each node: **what can fail here while you are out of the room?** No machine-settleable condition → it is a scheduler step, not a loop.
5. Mark deterministic steps running through a model: those are code nodes.
6. Check the return path: does a failure return one unit with evidence and scope, and does anything from an accepted result reach the next run's envelopes?
7. Check the writers: is any path written by two nodes? Does anything other than the orchestrator write state?
8. If a graph pays: propose the diamond placement (split dimension, workers, verifier lenses, merge, gate lane) and the caps.
9. Deliver a short before/after sketch (nodes + edges only). Offer Execute if they want it run.

## Teach Procedure

**Done when:** the user's question is answered from the right reference, without dumping the whole course.

1. Map the question: isolation / state / scheduler / diamond / wiring / loops / node types / gate / return paths / runtime / playbook.
2. Load that file via `skill_view`.
3. Answer with definitions, the relevant rule, and one concrete (domain-agnostic) example.
4. Load `references/examples/*` only if the user wants a worked illustration of the pattern in the wild.
5. Offer Execute or Design for their real goal.

## Common Pitfalls

1. **Assuming workers share context** — "Worker B picks up where A left off." There is no channel. Fix: pass it in B's envelope, or add the edge that produces it as an artifact.
2. **State kept in the conversation** — the graph's truth lives in someone's context and dies with compaction. Fix: Graph State on disk, committed by the orchestrator only.
3. **Fake edges left in place** — calendar-after-summary waits. Fix: name the artifact or delete the arrow; run both nodes in one round.
4. **Treating examples as the product** — SEO/GTM/research files are illustrations. Fix: design nodes for the user's actual goal.
5. **Incomplete envelopes** — a node spawned without the input it needs, expected to "figure it out". Fix: the readiness question — could it succeed if the envelope were all it knew?
6. **Same agent grades its homework** — models miss most of their own mistakes. Fix: a separate verifier node that requires the artifact.
7. **Verification after merge** — rumors enter the result. Fix: declare a verifier on the artifact; readiness holds consumers until it is verified.
8. **Whole-batch corrections** — three correct units rewritten because one failed. Fix: the verdict names one `unit`; only that node returns.
9. **Overwriting accepted artifacts** — the previous version disappears and consumers silently drift. Fix: versioned artifacts; revising consumed output needs a stated reason and flags consumers.
10. **Workers writing shared state** — three agents rewriting `state.json`. Fix: one writer per path, and the orchestrator owns state.
11. **Deterministic work through a model** — dedupe, rank, compare, route, update state. Fix: a code node, run locally; no spawn, no tokens, no variance.
12. **Unbounded correction** — attempt four, five, six. Fix: cap at three and escalate to the plan.
13. **Downstream execution on incomplete inputs** — a merge running on two of three findings. Fix: BLOCKED, with the missing artifact named.
14. **"No errors were raised" as the check** — absence of an error is not evidence of correctness. Fix: name a condition a program can settle.
15. **Confidence as the gate input** — the only input the model can influence. Fix: sort by blast radius; hard-to-reverse work does not open.
16. **Graph on sequential work** — the team loses when step N needs step N−1. Fix: stop rule; stay one agent.
17. **Graph machinery on a one-node job** — state files and a scheduler for work one agent does. Fix: the stop rule; complexity proportional to the graph.

## Verification Checklist

### Any mode
- [ ] Mode announced (Execute / Design / Audit / Teach)
- [ ] Stop rule applied (graph only where work splits independently)
- [ ] Every node names a green condition a program could settle (or is honestly marked unverified)
- [ ] Every node has an output contract, inputs, and exactly one writer path
- [ ] Every edge names the artifact that crosses it; no ordering-only waits
- [ ] No self-verification; verifiers require what they inspect
- [ ] Workers have separate envelopes and a disjoint split dimension
- [ ] Deterministic steps run as code nodes (including state updates)
- [ ] One logical owner of Graph State; workers never write it
- [ ] Return path named: failed unit → its producer; accepted result → a constraint
- [ ] Caps set: attempts, spawns per round, spawn budget
- [ ] Gate lane stated by blast radius; no irreversible action without explicit approval
- [ ] Examples were not used as a fixed task menu

### Execute mode
- [ ] Spec validated by `init` (refusals fixed, not worked around)
- [ ] `round_tasks` passed to `delegate_task` verbatim; `local_nodes` run locally
- [ ] Every commit traced to a contract file on disk, not to a claim
- [ ] Corrections returned per unit; siblings never re-spawned
- [ ] Escalation instead of attempt N+1 at the cap
- [ ] Output written to the named path(s) and committed
- [ ] Gate summary assembled from committed state; user's own words recorded
- [ ] Learning constraint proposed, not silently promoted

### Design mode
- [ ] `templates/graph-spec.md` filled; contracts follow `templates/node-contract.md`
- [ ] `graph.json` accepted by `init`
- [ ] Green conditions and contracts stated per node, before the work
- [ ] Node kinds assigned (splitter / worker / verifier / code / gate)
- [ ] Rounds named: what dispatches together, what waits for what
- [ ] Correction and learning edges named; gate lane named
- [ ] Paste-ready `use a workflow:` prompt delivered

### Self-check (optional, cheap)
- [ ] `python ${HERMES_SKILL_DIR}/scripts/selftest.py` — the seven execution scenarios still pass
