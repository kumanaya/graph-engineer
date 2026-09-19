# Gate Design: Open on Blast Radius, Not Confidence

The gate is the one node where a human is the actor. Place it at the point of highest consequence and lowest reversibility.

## Why not confidence

A confidence score looks like the obvious variable. It is the weakest one, for a reason that is easy to miss: **it is the only input in the decision the model can influence.** A gate that reads the model's own assessment is a gate the model grades for itself.

## Sort the work by what a mistake costs

| Lane | What lands here | What the gate does |
|------|-----------------|--------------------|
| **Reversible, contained** | a copy change, a test, an isolated function with coverage | opens first — one bad merge costs a revert |
| **Reversible, wide** | a shared utility, a schema addition, anything a dozen callers touch | opens on deterministic checks plus a clean trajectory |
| **Hard to reverse** | migrations, deletions, anything writing to production data or moving money | **does not open** |

The third row is not a threshold set very high. It is a lane that does not open, and the distinction matters: thresholds get adjusted, closed lanes do not.

The state script enforces the closed lane: approving a gate whose lane is `hard to reverse` is refused unless the approval carries an explicit quote of the user's own words.

```bash
graph_state.py gate --status approved --user-approval "yes, publish it"   # recorded, with attribution
```

## What the gate reads, in order

1. **Deterministic results** — tests, type check, diff scope, contract comparison.
2. **The trajectory of this run** — did it converge, or thrash and rewrite?
3. **History of this node** — how often has its work been rolled back before?
4. **The model's own assessment** — last, and only inside an open lane.

## The gate node

A gate is a node like any other, with one difference: it is not spawned, and a human is its actor.

- It **requires** the artifact it approves, so it cannot open before the work exists. A gate with no input is refused at `init`.
- It **may produce a decision artifact** (type `decision`). Do that whenever anything runs after the gate: downstream nodes then `require` the decision, and the scheduler holds them until the human answers. Without one, a mid-graph pause is only as strong as your round discipline — the orchestrator could forget.
- Its record lives in Graph State: lane, action, status, and every approval with the words that granted it. The decision artifact is the same record, committed and hashed, so the pause is inspectable and auditable like any other artifact.

```yaml
# the node
- id: gate-publish
  kind: gate
  requires: [{artifact: launch-kit}]
  produces: publish-decision          # ← anything downstream requires this

# the artifact
publish-decision: {type: decision, ext: json, producer: gate-publish}

# what the human's answer does
graph_state.py gate --status approved --user-approval "yes, publish it"
```

With the decision artifact declared, `status` shows the consumers as `PENDING — gate gate-publish has not been answered yet`, and a rejection shows them as `BLOCKED — gate gate-publish was rejected`. A later explicit approval commits a new decision version and releases them: a change of mind costs one approval, not a re-run.

## What the gate presents

Before the gate, summarize **from committed state** — not from recollection:

```text
what ran
what passed           (GREEN, with artifact versions)
what failed           (RED, with reason and evidence)
what was corrected    (which unit, which version, what changed)
which artifacts are being accepted, and at which versions
which deterministic checks passed
what remains uncertain
what will happen after approval
whether that action is reversible
```

Every line of that is readable from `graph_state.py status` and the artifact files. If the summary cannot be assembled, the gate is not ready — that is a statement about the graph, not about the user's patience.

## While it runs

- The human is the **slowest node in the graph**: the graph runs exactly as fast as a person reads things. Gate the last step — not intermediate output, not every step.
- Gate on everything → you are the bottleneck. Gate on nothing → nobody is watching.
- **No worker can approve anything.** Subagents cannot talk to the user, so every gate is handled by the orchestrator in its own turn. Never delegate a decision.
- Never send, publish, refund, invoice, or go live without explicit approval.
- Approve the merge. Choose which fixes ship. One step, at the highest consequence.
- A rejected gate stops the graph. Nothing downstream runs, and nothing is quietly retried.
