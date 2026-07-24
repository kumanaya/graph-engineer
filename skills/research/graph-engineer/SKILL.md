---
name: graph-engineer
description: >-
  Use when designing or executing autonomous agent graphs, diamond workflows,
  multi-agent fan-out/verify/merge pipelines, human gates, fake edges, or the
  stop rule. Builds a reusable workflow structure for any goal — not a fixed
  task menu.
version: 2.0.0
author: Kumanaya
license: MIT
metadata:
  hermes:
    tags: [graph-engineering, diamond, workflows, autonomous-agents, multi-agent]
    category: autonomous-ai-agents
---

# Graph Engineer

## Overview

A graph is a plan for autonomous AI work: which jobs must run, and which job waits for which. Each job is one assistant-sized task. An arrow is real only when work flows through it. Running notes travel with the work (what was found, decided, and left).

The default paying pattern is the **diamond**: split → parallel workers → separate verifier kills weak findings → merge into one result. You are the **human gate** before anything irreversible.

This skill is a **generic workflow framework**. For any user goal: design the graph, then execute it. It is not a menu of SEO, GTM, or other fixed products. Course builds under `references/examples/` are illustrations only — load them when the user asks for an example, never as the Execute menu.

## When to Use

- User wants a multi-agent workflow / agent graph for any goal
- User mentions diamond pattern, fake edges, stop rule, human gate, or graph engineering
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
2. **Fake edges first:** For every “and then,” ask whether the next job needs the last job's result. If no, delete the wait.
3. **No self-grading:** Never let the same agent verify its own findings. Verifier is a separate job.
4. **Verify first, merge second:** Drop failures before synthesis. Ship one answer, not a pile.
5. **Distinct checker questions:** Correctness, freshness, source quality, fit — not the same lens twice. Adapt lenses to the domain; keep them distinct.
6. **Wiring:** Every loop has a max rounds + seen list; one writer per file; routing lives in written steps (plan owns edges); spawn cap on parallel agents.
7. **Human gate:** Last yes sits where a mistake is expensive to undo — not on every step, not on none.
8. **Irreversible actions:** Never send, publish, refund, invoice, or go live without explicit user approval.
9. **No fixed task menu:** Invent jobs for *this* request. Do not default to research/SEO/GTM examples unless the user asks for those illustrations.

Default caps (override only if the user sets them): max **3** loop rounds; max **5** parallel workers; one writer per output path.

## Execute Procedure (default)

**Done when:** A graph was designed for this goal (or one-agent was correctly chosen), survivors are merged into named outputs, and the human gate has paused where required.

1. Clarify goal, success criteria, and irreversible actions. Do not invent user business facts.
2. Apply the **stop rule**. If there is no independent split → stay one agent; do the work without a fake diamond.
3. If a graph pays: name jobs (boxes), real vs fake edges, unique output paths, verifier lenses, merge shape, gate placement, caps. Use `templates/graph-spec.md` as the mental checklist (fill briefly or aloud — need not write the full file unless useful).
4. Announce the graph in a short sketch: workers · verifier · merge path · gate · caps.
5. Execute as a **workflow**: coordinated team, not a single straight line.
6. Fan out independent workers in parallel (respect spawn cap; one writer per file).
7. Run a **separate** skeptic/checker with distinct lenses; drop or flag failures; never merge unchecked findings.
8. Merge survivors into one structured result at the agreed path(s).
9. **Pause at the human gate** before any irreversible action (and at any mid-graph pause you designed).
10. Show what survived / what was flagged; wait for the user's yes or edits.

Do **not** load `references/examples/*` during Execute unless the user explicitly asks for an example pattern.

## Design Procedure

**Done when:** A filled graph spec exists and a paste-ready `use a workflow:` prompt is delivered — without running the graph.

1. Load `templates/graph-spec.md` and `references/playbook.md`.
2. Clarify goal, success criteria, and where a mistake is expensive (gate placement).
3. Name jobs; mark real vs fake edges; apply stop rule.
4. Prefer diamond unless the work cannot split — then document why one agent wins.
5. Assign verifier lenses (distinct questions); set loop/spawn/writer caps.
6. Fill the template; write a single runnable prompt that includes `use a workflow:`.
7. Offer to **Execute** immediately if the user wants the work done now.

## Audit Procedure

**Done when:** Jobs and arrows are listed, fake edges are named and removed, and a stay-one-agent vs graph recommendation is clear.

1. List every job (one-assistant tasks) and every “and then.”
2. For each arrow: does B need A's result? Mark real or fake.
3. Delete fake edges (parallelize or decouple those jobs).
4. Find the first real split (independent subtasks). If none → recommend one agent.
5. If a graph pays: propose diamond placement (workers, verifier lenses, merge, gate) and caps.
6. Deliver a short before/after sketch (jobs + arrows only). Offer Execute if they want it run.

## Teach Procedure

**Done when:** The user's question is answered from the right reference, without dumping the whole course.

1. Map the question to vocabulary, diamond, wiring, or playbook.
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

## Verification Checklist

### Any mode
- [ ] Mode announced (Execute / Design / Audit / Teach)
- [ ] Stop rule applied (graph only where work splits independently)
- [ ] Fake edges identified or confirmed absent
- [ ] No self-verification; checker is a separate job
- [ ] Caps set: loop rounds, spawn, one writer per file
- [ ] Human gate placed where undo is expensive; no irreversible action without approval
- [ ] Examples were not used as a fixed task menu

### Execute mode
- [ ] Graph (or one-agent choice) designed for *this* goal
- [ ] Parallel workers completed with distinct jobs/angles
- [ ] Failures dropped or flagged before merge
- [ ] Output written to the named path(s)
- [ ] User shown survivors / flags and asked for the last yes where required

### Design mode
- [ ] `templates/graph-spec.md` filled
- [ ] Paste-ready `use a workflow:` prompt delivered
- [ ] Verifier questions are distinct; gate and caps explicit
