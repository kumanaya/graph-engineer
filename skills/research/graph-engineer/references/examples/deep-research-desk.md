# EXAMPLE ONLY — Deep Research Desk

> **Not a Run / Execute menu item.** Load this only when the user wants an illustration of the diamond + skeptic pattern in the wild. For real work, design jobs for *their* goal in Execute mode.

**What it illustrates:** fan-out to N independent angles → separate skeptic tries to kill each finding → merge survivors → human gate before the decision.

## Node map

```text
Your question
    │
    ├─→ Angle 1 … N (independent; source + date required)
              │
              ▼
         The Skeptic ──→ fails dropped
              │
              ▼
      One ranked report (sources attached)
              │
              ▼
         Your read (human gate)
```

Angles must fit the question — do not force domain-specific angles onto unrelated goals.

## Pattern notes

- Every finding needs a **source link** and a **date** — that is the green condition each angle is checked against
- Skeptic tries to **disprove** every finding
- Drop what fails; merge survivors ranked by confidence. A failed angle goes back to its own researcher, not to the whole set
- Output shape in this example: `research-report.md`
- Human gate: user reads before anything is treated as decided

## Historical prompt (example)

```text
i need decision-grade research on: [your question]. use a workflow: split the question into 5 distinct angles, run one researcher per angle in parallel, every finding needs a source link and a date, then run a skeptic against each finding that tries to disprove it, drop what fails, merge the survivors into one report ranked by confidence, save it as research-report.md and show me the top findings
```
