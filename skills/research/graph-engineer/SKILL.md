---
name: graph-engineer
description: >-
  Use when designing or running agent graphs, diamond workflows, parallel
  research/SEO/GTM pipelines, human gates, or when the user mentions graph
  engineering, fake edges, or the stop rule. Teaches the method and executes
  the three business builds.
version: 1.0.0
author: Kumanaya
license: MIT
metadata:
  hermes:
    tags: [graph-engineering, diamond, workflows, research, seo, gtm]
    category: research
---

# Graph Engineer

## Overview

A graph is a plan for AI work: which jobs must run, and which job waits for which. Each job is one assistant-sized task. An arrow is real only when work flows through it. Running notes travel with the work (what was found, decided, and left).

The default paying pattern is the **diamond**: split → parallel workers → separate verifier kills weak findings → merge into one result. You are the **human gate** before anything irreversible (send, publish, refund, invoice).

This skill teaches the method, audits fake edges, runs three business graphs, and designs new graphs from the playbook.

## When to Use

- User asks to design, audit, or run an agent graph / workflow
- User wants decision-grade research, SEO drafts, or a go-to-market kit via parallel agents
- User mentions diamond pattern, fake edges, stop rule, human gate, or graph engineering
- User wants a reusable “use a workflow: …” prompt for Hermes / Claude Code-style agents

**Don't use for:** a single sequential task where every step needs the full prior result and nothing splits into independent jobs. Stay one agent (stop rule).

## Operating Modes

Pick **one** mode per request. Announce it before acting.

| Mode | When | Load |
|------|------|------|
| **Audit** | User has an existing AI system / pipeline | `references/vocabulary.md`, `references/playbook.md` |
| **Teach** | User wants the method / vocabulary / rules | Only the needed file under `references/` |
| **Run** | User wants Graph 1, 2, or 3 executed | Matching file under `references/graphs/` |
| **Design** | User wants a new custom graph | `templates/graph-spec.md` + `references/playbook.md` |

Load extras on demand:

```text
skill_view("graph-engineer", "references/vocabulary.md")
skill_view("graph-engineer", "references/diamond-pattern.md")
skill_view("graph-engineer", "references/wiring-rules.md")
skill_view("graph-engineer", "references/playbook.md")
skill_view("graph-engineer", "references/graphs/deep-research-desk.md")
skill_view("graph-engineer", "references/graphs/seo-content-machine.md")
skill_view("graph-engineer", "references/graphs/go-to-market-kit.md")
skill_view("graph-engineer", "templates/graph-spec.md")
```

## Hard Rules (always on)

1. **Stop rule:** A graph buys breadth, not better judgment. Split only jobs that never read each other's results. If every step needs the full picture, use one agent.
2. **Fake edges first:** For every “and then,” ask whether the next job needs the last job's result. If no, delete the wait.
3. **No self-grading:** Never let the same agent verify its own findings. Verifier is a separate job.
4. **Verify first, merge second:** Drop failures before synthesis. Ship one answer, not a pile.
5. **Distinct checker questions:** Correctness, freshness, source quality, fit — not the same lens twice.
6. **Wiring:** Every loop has a max rounds + seen list; one writer per file; routing lives in written steps (code/plan owns edges); spawn cap on parallel agents.
7. **Human gate:** Last yes sits where a mistake is expensive to undo — not on every step, not on none.
8. **Irreversible actions:** Never send, publish, refund, invoice, or go live without explicit user approval.

Default caps (override only if the user sets them): max **3** loop rounds; max **5** parallel workers unless a named graph specifies otherwise; one writer per output path.

## Audit Procedure

**Done when:** Jobs and arrows are listed, fake edges are named and removed, and a stay-one-agent vs graph recommendation is clear.

1. List every job (one-assistant tasks) and every “and then.”
2. For each arrow: does B need A's result? Mark real or fake.
3. Delete fake edges (parallelize or decouple those jobs).
4. Find the first real split (independent subtasks). If none → recommend one agent.
5. If a graph pays: propose diamond placement (workers, verifier lenses, merge, gate) and caps.
6. Deliver a short before/after sketch (jobs + arrows only).

## Teach Procedure

**Done when:** The user's question is answered from the right reference, without dumping the whole course.

1. Map the question to one reference (vocabulary, diamond, wiring, playbook, or a graph).
2. Load that file via `skill_view`.
3. Answer with definitions, the relevant rule, and one concrete example.
4. Offer the next lesson or a Run/Design mode if useful.

## Run Procedure

**Done when:** Named outputs exist, weak findings are dropped or flagged, and the human gate has paused for approval where required.

1. Identify graph: **1** deep research desk, **2** SEO content machine, **3** go-to-market kit.
2. Load the matching `references/graphs/*.md`.
3. Collect missing inputs (question / topic / product+audience). Do not invent business facts.
4. Announce the graph: jobs, parallel fan-out, verifier, merge, output paths, gate.
5. Execute with the word **workflow** in mind: coordinated team, not a single straight line.
6. Fan out independent workers in parallel (respect spawn cap; one writer per file).
7. Run the separate skeptic/checker; drop or flag failures; never merge unchecked findings.
8. Merge survivors into one structured result at the specified path.
9. **Pause at the human gate** before any irreversible action. For Graph 3, pause after the positioning doc before writers run.
10. Show top findings / flags / kit checklist and wait for the user's yes/edits.

### Quick graph picker

| User intent | Graph | Output |
|-------------|-------|--------|
| Decision-grade research, money behind the question | 1 — Deep research desk | `research-report.md` |
| Ranking-ready article, never auto-publish | 2 — SEO content machine | `drafts/` |
| Launch kit with positioning pause | 3 — Go-to-market kit | `launch-kit/` |

## Design Procedure

**Done when:** A filled graph spec exists and a paste-ready `use a workflow:` prompt is delivered.

1. Load `templates/graph-spec.md` and `references/playbook.md`.
2. Clarify goal, success criteria, and where a mistake is expensive (gate placement).
3. Name jobs; mark real vs fake edges; apply stop rule.
4. Prefer diamond unless the work cannot split — then document why one agent wins.
5. Assign verifier lenses (distinct questions); set loop/spawn/writer caps.
6. Fill the template; write a single runnable prompt that includes `use a workflow:`.
7. Offer to Run the new graph immediately if the user wants.

## Common Pitfalls

1. **Fake edges left in place** — Calendar-after-summary style waits. Fix: delete the arrow; run independent jobs in parallel.
2. **Same agent grades its homework** — Models miss most of their own mistakes. Fix: separate skeptic/checker job.
3. **Graph on sequential work** — Team loses when step N needs step N-1. Fix: stop rule; stay one agent.
4. **Gate everywhere or nowhere** — Everywhere bottlenecks; nowhere ships confident mistakes. Fix: gate only expensive-to-undo edges.
5. **Unbounded spawn / loops** — Prototype cost explosions. Fix: spawn cap + max rounds + seen list.
6. **Parallel writers on one file** — Collisions. Fix: one writer per path; merge at the end.
7. **Model owns routing** — Hallucinated labels with no edge go nowhere. Fix: written if/else plan owns edges; model fills nodes.
8. **Merge before verify** — Rumors enter the report. Fix: verify first, merge second.

## Verification Checklist

### Any mode
- [ ] Mode announced (Audit / Teach / Run / Design)
- [ ] Stop rule applied (graph only where work splits independently)
- [ ] Fake edges identified or confirmed absent
- [ ] No self-verification; checker is a separate job
- [ ] Caps set: loop rounds, spawn, one writer per file
- [ ] Human gate placed where undo is expensive; no irreversible action without approval

### Run mode
- [ ] Correct graph reference loaded; inputs filled (not invented)
- [ ] Parallel workers completed with distinct angles
- [ ] Failures dropped or flagged before merge
- [ ] Output written to the named path(s)
- [ ] User shown survivors / flags and asked for the last yes where required

### Design mode
- [ ] `templates/graph-spec.md` filled
- [ ] Paste-ready `use a workflow:` prompt delivered
- [ ] Verifier questions are distinct; gate and caps explicit
