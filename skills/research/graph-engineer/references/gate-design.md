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

## What the gate reads, in order

1. **Deterministic results** — tests, type check, diff scope, contract comparison.
2. **The trajectory of this run** — did it converge, or thrash and rewrite?
3. **History of this node** — how often has its work been rolled back before?
4. **The model's own assessment** — last, and only inside an open lane.

## While it runs

- The human is the **slowest node in the graph**: the graph runs exactly as fast as a person reads things. Gate the last step — not intermediate output, not every step.
- Gate on everything → you are the bottleneck. Gate on nothing → nobody is watching.
- A mid-graph pause needs a named reason: expensive downstream work, or a decision only the user can make.
- Never send, publish, refund, invoice, or go live without explicit approval.
- Approve the merge. Choose which fixes ship. One step, at the highest consequence.
