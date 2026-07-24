# Graph 1 — The Deep Research Desk

Decision-grade research: your question splits into five angles, five researchers dig at once, a skeptic attacks every finding, only survivors reach the final report with sources attached.

Use for questions with money behind them: price changes, offers, markets, strategic bets.

## Node map

```text
Your question
    │
    ├─→ Angle 1: Retention / core levers (source + date required)
    ├─→ Angle 2: Onboarding / early value (source + date required)
    ├─→ Angle 3: Pricing & packaging (source + date required)
    ├─→ Angle 4: Expansion strategy (source + date required)
    └─→ Angle 5: Support & success (source + date required)
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

Angles above are examples for a churn-style question. For any question: split into **5 distinct angles** relevant to that question — do not force churn angles onto unrelated topics.

## Constraints

- Every finding needs a **source link** and a **date**
- Skeptic tries to **disprove** every finding (challenge assumptions, bias, data, claims; prefer primary sources)
- Drop what fails; merge survivors ranked by confidence
- Research vs rumor collection happens at the skeptic
- Output: `research-report.md`
- Human gate: only survivors enter the decision after the user reads the report
- Never take irreversible action from the report without user approval

## Run steps

1. Write the question in one sentence (money behind it).
2. Fill the prompt below; execute as a workflow (parallel researchers → skeptic → merge).
3. Save `research-report.md`; show top findings.
4. Pause for the user's read before anything is treated as decided.

## Prompt (verbatim)

```text
i need decision-grade research on: [your question]. use a workflow: split the question into 5 distinct angles, run one researcher per angle in parallel, every finding needs a source link and a date, then run a skeptic against each finding that tries to disprove it, drop what fails, merge the survivors into one report ranked by confidence, save it as research-report.md and show me the top findings
```

Replace `[your question]` with the user's real question.
