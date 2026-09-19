---
name: graph-engineer
description: >-
  Use when designing or executing autonomous agent graphs, diamond workflows,
  multi-agent fan-out/verify/merge pipelines, loops with machine-checkable green
  conditions, code nodes, return paths, human gates on blast radius, fake edges,
  or the stop rule. Builds a reusable workflow structure for any goal — not a
  fixed task menu.
version: 3.0.0
author: Kumanaya
license: MIT
metadata:
  hermes:
    tags: [graph-engineering, diamond, workflows, autonomous-agents, multi-agent, loops, human-gate]
    category: autonomous-ai-agents
---

# Graph Engineer

## Overview

A graph is a plan for autonomous AI work: which jobs must run, and which job waits for which. Each job is one assistant-sized task. An arrow is real only when work flows through it. Running notes travel with the work (what was found, decided, and left).

Two layers, and you need both. A **loop** makes one unit of work correct without you: produce → check → correct → repeat until green. A **graph** decides which units exist, in what order, and what happens to the ones that fail. The loop lives **inside** a box; the graph lives **between** boxes. A graph without loops in its boxes produces unverified work in parallel — worse than serially, because there is more of it. A loop without a graph around it is one very good step in a queue nobody designed.

Nodes come in four kinds — **splitter, worker, code node, gate** — and one of them is not a model.

The default paying pattern is the **diamond**: split → parallel workers → separate verifier kills weak findings → merge into one result. You are the **human gate** before anything irreversible.

This skill is a **generic workflow framework**. For any user goal: design the graph, then execute it. It is not a menu of SEO, GTM, or other fixed products. Course builds under `references/examples/` are illustrations only — load them when the user asks for an example, never as the Execute menu.

## When to Use

- User wants a multi-agent workflow / agent graph for any goal
- User mentions diamond pattern, fake edges, stop rule, human gate, or graph engineering
- User mentions loops, checks that can fail, code nodes, return/feedback edges, or gate lanes
- User asks to audit an existing AI pipeline for wasted waits
- User wants a reusable `use a workflow:` structure designed and run for *their* task

**Don't use for:** a single sequential task where every step needs the full prior result and nothing splits into independent jobs. Stay one agent (stop rule). Do not force a diamond.

## Operating Modes

Pick **one** mode per request. Announce it before acting.

| Mode | When | Load |
|------|------|------|
| **Execute** (default) | User wants the work done via a workflow | `templates/graph-spec.md` (briefly) + method refs as needed |
| **Design** | User wants the graph/spec/prompt only — no run | `templates/graph-spec.md` + `references/playbook.md` |
| **Audit** | User has an existing AI system / pipeline | `references/vocabulary.md`, `references/playbook.md` |
| **Teach** | User wants the method / vocabulary / rules | Only the needed file under `references/` |

If the user does not specify a mode and wants a result, choose **Execute**.

Load extras on demand:

```text
skill_view("graph-engineer", "references/vocabulary.md")
skill_view("graph-engineer", "references/diamond-pattern.md")
skill_view("graph-engineer", "references/loop-design.md")
skill_view("graph-engineer", "references/node-types.md")
skill_view("graph-engineer", "references/gate-design.md")
skill_view("graph-engineer", "references/return-paths.md")
skill_view("graph-engineer", "references/wiring-rules.md")
skill_view("graph-engineer", "references/playbook.md")
skill_view("graph-engineer", "templates/graph-spec.md")
```

Examples (illustration only — never the Execute menu):

```text
skill_view("graph-engineer", "references/examples/deep-research-desk.md")
skill_view("graph-engineer", "references/examples/seo-content-machine.md")
skill_view("graph-engineer", "references/examples/go-to-market-kit.md")
```

## Hard Rules (always on)

1. **Stop rule:** A graph buys breadth, not better judgment. Split only jobs that never read each other's results. If every step needs the full picture, use one agent.
2. **Check first:** Before the work exists, name the green condition a program could evaluate. “No errors were raised” is not a check, and neither is the model's confidence. No condition that can fail while you are away = a scheduler, not a loop.
3. **Loop in the box, graph between boxes:** the box repeats produce → check → correct; the graph owns split, fan-out, verify, merge, gate, and return. Neither substitutes for the other.
4. **Fake edges first:** For every “and then,” ask whether the next job needs the last job's result. If no, delete the wait.
5. **No self-grading:** Never let the same agent verify its own findings. Verifier is a separate job.
6. **Verify first, merge second:** Drop failures before synthesis. Ship one answer, not a pile.
7. **Distinct checker questions:** Correctness, freshness, source quality, fit — not the same lens twice. Adapt lenses to the domain; keep them distinct.
8. **Own context per worker:** Separate context + distinct question + disjoint split dimension. All three, or four workers buy one opinion and three echoes.
9. **Disjoint split:** Cut by the dimension where two workers cannot return the same finding.
10. **Code nodes for deterministic steps:** Compare, dedupe, rank, filter, route, and check the diff against the plan's file list. One correct answer = code, not a model call.
11. **Return the unit, not the batch:** A failed unit goes back to the box that produced it, with unit · verdict · reason · evidence · scope. Never send the batch back — it rewrites work that was correct. An accepted result may send a constraint to the splitter's brief (learning edge), promoted only with the user's knowledge.
12. **Wiring:** Every loop has a max rounds + seen list; one writer per file; routing lives in written steps (plan owns edges); spawn cap on parallel agents. At the cap, the plan is at fault, not the unit.
13. **Human gate:** Last yes sits where a mistake is expensive to undo — opened by blast radius, never by confidence. Hard-to-reverse work (migrations, deletions, production data, money) does not open.
14. **Irreversible actions:** Never send, publish, refund, invoice, or go live without explicit user approval.
15. **No fixed task menu:** Invent jobs for *this* request. Do not default to research/SEO/GTM examples unless the user asks for those illustrations.

Default caps (override only if the user sets them): max **3** loop rounds (then escalate to the plan); max **5** parallel workers; one writer per output path.

## Execute Procedure (default)

**Done when:** A graph was designed for this goal (or one-agent was correctly chosen), every box ran to a stated green condition or was honestly flagged as unverified, survivors are merged into named outputs, and the human gate has paused where required.

1. Clarify goal, success criteria, and irreversible actions. Do not invent user business facts.
2. Apply the **stop rule**. If there is no independent split → stay one agent; do the work without a fake diamond.
3. **Write the green condition first** — one per job, stated before the work exists, in a form a program could settle. If nothing can fail a job, say so plainly instead of inventing a check.
4. If a graph pays: name jobs (boxes) with their **node kind** (splitter / worker / code node / gate), real vs fake edges, unique output paths, verifier lenses, merge shape, **gate lane** (blast radius), **return paths** (correction + learning), caps. Use `templates/graph-spec.md` as the mental checklist (fill briefly or aloud — need not write the full file unless useful).
5. Announce the graph in a short sketch: split dimension · workers · verifier · merge · return path · gate lane · caps.
6. Execute as a **workflow**: coordinated team, not a single straight line.
7. Fan out independent workers **in separate contexts** (respect spawn cap; one writer per file). Each worker loops produce → check → correct to its own green condition.
8. Run a **separate** skeptic/checker with distinct lenses; drop or flag failures; never merge unchecked findings.
9. **Return failed units only** — unit · verdict · reason · evidence · scope — to the box that produced them. Never re-run the batch. Cap at 3 corrections, then escalate to the split, the check, or the brief.
10. Merge survivors into one structured result, dedupe/rank/filter as **code nodes**, at the agreed path(s).
11. **Pause at the human gate** before any irreversible action (and at any mid-graph pause you designed). State the lane: reversible-contained, reversible-wide, or hard-to-reverse.
12. Show what survived / what was flagged; wait for the user's yes or edits. If a cause was confirmed, offer the constraint for the splitter's brief — never promote it silently.

Do **not** load `references/examples/*` during Execute unless the user explicitly asks for an example pattern.

## Design Procedure

**Done when:** A filled graph spec exists — green conditions, node kinds, return paths and gate lane included — and a paste-ready `use a workflow:` prompt is delivered, without running the graph.

1. Load `templates/graph-spec.md` and `references/playbook.md`.
2. Clarify goal, success criteria, and where a mistake is expensive (gate lane).
3. Name the green condition per job before naming the jobs' work.
4. Name jobs with their node kind; mark model vs code vs human; mark real vs fake edges; apply the stop rule.
5. Prefer diamond unless the work cannot split — then document why one agent wins.
6. Assign verifier lenses (distinct questions); set loop/spawn/writer caps.
7. Name the correction edge (what comes back, to where, with what) and the learning edge (which constraint lands in the splitter's brief).
8. Fill the template; write a single runnable prompt that includes `use a workflow:`.
9. Offer to **Execute** immediately if the user wants the work done now.

## Audit Procedure

**Done when:** Jobs and arrows are listed, fake edges are named and removed, boxes without a failing check are flagged, and a stay-one-agent vs graph recommendation is clear.

1. List every job (one-assistant tasks) and every “and then.”
2. For each arrow: does B need A's result? Mark real or fake.
3. For each box: **what can fail here while you are out of the room?** No machine-settleable condition → label it a scheduler step, not a loop.
4. Delete fake edges (parallelize or decouple those jobs).
5. Find the first real split (independent subtasks). If none → recommend one agent.
6. Mark deterministic steps that are running through a model: those are code nodes.
7. Check the return path: is a failure sent back as a single unit with evidence, and does anything from an accepted result reach the next run's plan?
8. If a graph pays: propose diamond placement (workers, split dimension, verifier lenses, merge, gate lane) and caps.
9. Deliver a short before/after sketch (jobs + arrows only). Offer Execute if they want it run.

## Teach Procedure

**Done when:** The user's question is answered from the right reference, without dumping the whole course.

1. Map the question: vocabulary / diamond / wiring / loops / node types / gate design / return paths / playbook.
2. Load that file via `skill_view`.
3. Answer with definitions, the relevant rule, and one concrete (domain-agnostic) example.
4. Load `references/examples/*` only if the user wants a worked illustration of the pattern in the wild.
5. Offer Execute or Design for their real goal.

## Common Pitfalls

1. **Treating examples as the product** — SEO/GTM/research files are illustrations. Fix: design jobs for the user's actual goal.
2. **Fake edges left in place** — Calendar-after-summary style waits. Fix: delete the arrow; run independent jobs in parallel.
3. **Same agent grades its homework** — Models miss most of their own mistakes. Fix: separate skeptic/checker job.
4. **Graph on sequential work** — Team loses when step N needs step N-1. Fix: stop rule; stay one agent.
5. **Gate everywhere or nowhere** — Everywhere bottlenecks; nowhere ships confident mistakes. Fix: gate only expensive-to-undo edges.
6. **Unbounded spawn / loops** — Cost explosions. Fix: spawn cap + max rounds + seen list.
7. **Parallel writers on one file** — Collisions. Fix: one writer per path; merge at the end.
8. **Model owns routing** — Hallucinated labels with no edge go nowhere. Fix: written if/else plan owns edges; model fills nodes.
9. **Merge before verify** — Rumors enter the result. Fix: verify first, merge second.
10. **“No errors were raised” as the check** — Absence of an error is not evidence of correctness; the loop repeats the mistake confidently, with a clean log. Fix: name a condition a program can settle.
11. **The whole batch returned** — Rewrites work that was correct, re-verifies all of it, stops converging. Fix: return the unit alone, with evidence and a scope line.
12. **Deterministic work through a model** — Dedupe, rank, compare, route: one right answer, and a model adds cost, latency, variance. Fix: code node.
13. **Workers sharing one context** — Four reports, one opinion. Fix: separate contexts + distinct questions + a disjoint split dimension.
14. **Confidence as the gate input** — The only input the model can influence. Fix: sort by blast radius; hard-to-reverse work does not open.
15. **A pipeline with no way back** — Output produced and forgotten; the next run starts with the same blind spots. Fix: correction edge for this run, learning edge for every run after.
16. **Correcting past the cap** — A unit that fails three times is a plan failure. Fix: escalate to the split, the check, or the brief.

## Verification Checklist

### Any mode
- [ ] Mode announced (Execute / Design / Audit / Teach)
- [ ] Stop rule applied (graph only where work splits independently)
- [ ] Every box names a green condition a program could settle (or is honestly marked unverified)
- [ ] Loop is inside boxes; graph is between them
- [ ] Fake edges identified or confirmed absent
- [ ] No self-verification; checker is a separate job
- [ ] Parallel workers have separate contexts and a disjoint split dimension
- [ ] Deterministic steps run as code nodes
- [ ] Return path named: failed unit → its producer; accepted result → splitter's brief
- [ ] Caps set: loop rounds, spawn, one writer per file
- [ ] Gate lane stated by blast radius; no irreversible action without approval
- [ ] Examples were not used as a fixed task menu

### Execute mode
- [ ] Graph (or one-agent choice) designed for *this* goal
- [ ] Parallel workers completed with distinct jobs/angles, each against its own green condition
- [ ] Failed units returned individually with verdict, reason, evidence and scope
- [ ] Failures dropped or flagged before merge
- [ ] Output written to the named path(s)
- [ ] User shown survivors / flags and asked for the last yes where required

### Design mode
- [ ] `templates/graph-spec.md` filled
- [ ] Green conditions stated per job, before the work
- [ ] Node kinds assigned (splitter / worker / code node / gate)
- [ ] Correction and learning edges named; gate lane named
- [ ] Paste-ready `use a workflow:` prompt delivered
- [ ] Verifier questions are distinct; gate and caps explicit
