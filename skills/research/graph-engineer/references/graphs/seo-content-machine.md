# Graph 2 — The SEO Content Machine

One ranking-ready draft per run. Never publishes without the human.

Three researchers work side by side (top pages, real questions, gaps), merge into an outline, draft, fact-check, land in `drafts/` for your yes.

## Node map

```text
The topic (one search intent)
    │
    ├─→ Job A: what the top pages cover
    ├─→ Job B: the real questions people ask
    └─→ Job C: what everyone misses
              │
              ▼
           Outline
              │
              ▼
          Full draft
              │
              ▼
         Fact-checker (no source → flagged at top)
              │
              ▼
           drafts/
              │
              ▼
         Your yes (human gate — never publish)
```

## Constraints

- One topic per run; one primary promise / search intent
- Parallel research must not write the same file; merge at outline
- Fact-checker verifies every claim; claims without sources flagged at the top
- Quality gates before treating draft as ready: coverage complete, claims verified, value unique
- **Never publish anything** — user publishes manually after edits
- Output package: outline + draft + sources + score/flags in `drafts/`

## Research job briefs

| Job | Focus |
|-----|--------|
| A | Scan top-ranking pages; extract headings/angles; map content depth |
| B | Related searches, People Also Ask, community questions |
| C | Content gaps, weak evidence, original angles |

## Run steps

1. Pick the one topic customers type into Google.
2. Fill the prompt below; execute as a workflow.
3. Land draft in `drafts/` with flagged claims listed at the top.
4. User reads, fixes what only they know, publishes themselves.
5. Optionally save the workflow for weekly re-run (one command instead of one afternoon).

## Prompt (verbatim)

```text
i want an article that can rank for: [topic]. use a workflow: run three research jobs in parallel, one lists what the current top-ranking pages cover, one collects the real questions people ask about this topic, one finds what the top pages skip, merge all three into an outline, write a full draft from the outline, then run a fact-checker that flags every claim without a source, save the draft to drafts/ with the flagged claims listed at the top, never publish anything
```

Replace `[topic]` with the user's topic.
