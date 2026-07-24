# Graph 3 — The Go-to-Market Kit

Full launch kit in one run, with human approval on positioning and on every asset. Nothing goes live on its own.

## Node map

```text
Product + audience (one line each)
    │
    ├─→ Buyer & exact words
    ├─→ Where they spend time online
    └─→ How competitors pitch them
              │
              ▼
    One-page positioning doc
              │
              ▼
    ★ PAUSE — human gate (read before writers)
              │
    ├─→ Landing page copy
    ├─→ A week of launch posts
    └─→ Outreach messages
              │
              ▼
         The checker (vs positioning)
              │
              ▼
         launch-kit/
              │
              ▼
    Approve piece by piece (human gate)
```

## Stage 1 — Research (parallel)

| Job | Focus |
|-----|--------|
| Buyer | Interview-style insights, real quotes, pain points, beliefs, objections |
| Channels | Platforms, communities, content engagement, influencers/creators |
| Competitors | Core messages, offers, angles, gaps to exploit |

Merge into a **one-page positioning doc**: who we help, the job we do, why we're different, proof we can deliver, the promise we make.

**Mandatory pause:** Show the positioning page to the user. Do not start writers until they approve or edit. This page is the foundation every asset gets checked against — the one step never to skip.

## Stage 2 — Build + check + package (after approval)

| Job | Elements |
|-----|----------|
| Landing | Headline + subheadline, features + benefits, proof + FAQ + CTA |
| Posts | 7 post ideas, hooks + angles, captions + CTAs |
| Outreach | Cold email, follow-up sequence, DM templates |

**Checker** flags drift from positioning: wrong audience, off-message, missing proof, weak promises, inconsistent tone.

Save to `launch-kit/` (copy, assets, variants, notes, checklist). Change nothing after that without asking the user. Approve piece by piece — nothing ships without them.

## Constraints

- Start with clarity, not assumptions (product + audience in one line each)
- Parallel writers use separate files; merge/package at the end
- Human gates: (1) after positioning, (2) before anything goes live
- Spawn: 3 researchers, then 3 writers (after gate) — respect global spawn cap

## Run steps

1. Name the product and the person it is for, one line each.
2. Fill the prompt; run research → positioning → **pause**.
3. After user approval, run three writers in parallel.
4. Run checker; present flags.
5. Save to `launch-kit/`; wait for piece-by-piece approval.

## Prompt (verbatim)

```text
i'm launching [product] for [audience]. use a workflow: run three research jobs in parallel, one profiles the buyer and collects the exact words they use, one maps where these buyers spend time online, one collects how competitors pitch them, merge into a one-page positioning doc and pause to show it to me, then run three writers in parallel from that doc: landing page copy, a week of launch posts, a set of outreach messages, then run a checker that compares every asset against the positioning doc and flags anything off, save everything to launch-kit/ and change nothing after that without asking me
```

Replace `[product]` and `[audience]` with the user's values.
