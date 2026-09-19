# Return Paths: Correction and Learning

A graph without a way back is a pipeline. It produces output and forgets; next week it starts from the same place with the same blind spots.

Working graphs have two return paths, doing different jobs.

| Edge | Length | Carries | Fixes |
|------|--------|---------|-------|
| **Correction edge** | short — gate → the box that produced the unit | the failed unit, with its verdict and evidence | this run |
| **Learning edge** | long — accepted result → the splitter | a constraint derived from it | every run after |

Almost everyone builds the first and skips the second. The tell is a system that is fast and never gets smarter.

## Return the unit, not the batch

The most expensive mistake on the return path.

Four slices were ported. One fails its tests. If the whole batch goes back, three correct slices get rewritten. Their next version is different, not better — nothing was wrong with them. Now you re-verify all four, and any of the three may fail this time for unrelated reasons: one failure became four uncertain outcomes, and you paid for the privilege. Do it twice in a run and it never converges.

From the outside this looks like the model failing repeatedly. It is a return path destroying correct work.

## Five fields travel with a return

| Field | Example | Job |
|-------|---------|-----|
| **UNIT** | handlers slice | what comes back — nothing else |
| **VERDICT** | red | it failed |
| **REASON** | `test_auth_redirect` failed | the single failing check |
| **EVIDENCE** | expected 302, got 200, `handlers/auth.py:88` | so the fix does not start with an investigation |
| **SCOPE** | fix this file only, do not touch other slices | bounds the correction |

**SCOPE matters more than it looks.** Without it a returned unit grows: the agent opens the file, notices two adjacent issues, fixes those too, and your one-slice correction becomes a four-file diff nobody reviewed.

## The learning edge

It does not carry the output. It carries a constraint derived from it.

```text
ACCEPTED   utils slice ported, green on first pass
DERIVED    adapters preserve keyword args exactly
LANDS IN   the splitter's brief for every later slice
```

Notice where it lands: not in the worker's instructions, in the brief that shapes how the work gets cut. A confirmed cause becomes a rule, so the next break starts where this one ended.

**Guard this edge.** A constraint derived from one accepted run is a hypothesis, not a law:

- derive it from a **confirmed cause** — a green run only says the check passed
- make it a **constraint**, not a narrative: “preserve keyword args exactly”, not “we learned a lot about adapters”
- keep it **dated and reversible**, with the run it came from
- promotion to a permanent rule goes through a human, or it becomes superstition with a changelog

**A verdict that does not change what runs next is a report.**
