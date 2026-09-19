# Return Paths: Correction and Learning

A graph without a way back is a pipeline. It produces output and forgets; next week it starts from the same place with the same blind spots.

Working graphs have two return paths, doing different jobs.

| Edge | Length | Carries | Fixes |
|------|--------|---------|-------|
| **Correction edge** | short — verifier → the node that produced the failed unit | the failed unit, its verdict, its evidence, its scope, and the latest artifact version | this run |
| **Learning edge** | long — an accepted outcome → a constraint in `constraints.json` | a derived constraint, promoted by a human | every run after |

Almost everyone builds the first and skips the second. The tell is a system that is fast and never gets smarter.

## Return the unit, not the batch

The most expensive mistake on the return path.

Four slices were ported. One fails its tests. If the whole batch goes back, three correct slices get rewritten. Their next version is different, not better — nothing was wrong with them. Now you re-verify all four, and any of the three may fail this time for unrelated reasons: one failure became four uncertain outcomes, and you paid for the privilege. Do it twice in a run and it never converges.

From the outside this looks like the model failing repeatedly. It is a return path destroying correct work.

**This is structural here, not a policy.** A verifier's verdict names exactly one `unit`, the commit step resolves that unit against the artifacts the verifier actually required, and only that node goes RED. Siblings keep their GREEN status and are never re-dispatched. A verifier cannot reject "everything" — `init` refuses a verdict contract without `unit`.

## Five fields travel with a return

| Field | Example | Job |
|-------|---------|-----|
| **UNIT** | `auth-findings` | what comes back — nothing else |
| **VERDICT** | red | it failed |
| **REASON** | `test_auth_redirect` failed | the single failing check |
| **EVIDENCE** | expected 302, got 200, `handlers/auth.py:88` | so the fix does not start with an investigation |
| **SCOPE** | fix this file only, do not touch other slices | bounds the correction |

**SCOPE matters more than it looks.** Without it a returned unit grows: the agent opens the file, notices two adjacent issues, fixes those too, and your one-slice correction becomes a four-file diff nobody reviewed.

## What the correction envelope contains

The corrected node does not get the batch, and it does not get a fresh start from zero. It gets:

```text
its own last artifact        auth-findings@v1   (the work being fixed)
the verdict artifact         findings-verdict@v1 (the judgement)
unit · reason · evidence · scope
its normal inputs            inventory@v1
its writer path              auth-findings.v2.md   ← a NEW version, never an overwrite
```

After the correction commits, the artifact is `auth-findings@v2` and **the verifier re-arms automatically** — a new version invalidates the old verdict. Consumers recompute to READY only when the corrected version is verified.

```text
verify-findings  →  red (unit: auth-findings)
                 →  audit-auth RED, correction attached
                 →  audit-auth attempt 2 → auth-findings@v2
                 →  verify-findings attempt 2 → green
                 →  auth-findings@v2 verified → merge READY
```

## Steering a running node (optional, and not a substitute)

Hermes can queue a message into a **running** child:

```json
{"action": "steer", "subagent_id": "sa-…", "message": "ignore the vendored directory"}
```

Useful when a node has drifted and the work in flight is still worth keeping — a correction that costs one message instead of one attempt.

Two honest limits:

- **It is not the correction edge.** A steer changes nothing in Graph State: no verdict, no new version, no verification. If the green condition was not met, the node still returns RED and the normal path applies.
- **Delivery is not guaranteed.** A steer that arrives after the child's final answer comes back as `missed_steer`. Treat it as best-effort guidance, never as the record of what happened.

The correction edge is the one that counts. Steering only avoids paying for a whole attempt.

## The learning edge

It does not carry the output. It carries a constraint derived from it.

```text
ACCEPTED   utils slice ported, green on first pass
DERIVED    adapters preserve keyword args exactly
LANDS IN   <root>/constraints.json → rendered into every later envelope
```

Notice where it lands: not in the worker's instructions, in the envelope that shapes how the work is cut and executed next time. A confirmed cause becomes a rule, so the next break starts where this one ended.

**Guard this edge.** A constraint derived from one accepted run is a hypothesis, not a law:

- derive it from a **confirmed cause** — a green run only says the check passed
- make it a **constraint**, not a narrative: "preserve keyword args exactly", not "we learned a lot about adapters"
- keep it **dated and reversible**, with the node, the artifact version and the run it came from
- **only an accepted (GREEN) outcome may propose one**, and promotion to active goes through a human:

```bash
graph_state.py learn --constraint "adapters preserve kwargs exactly" \
                     --node port-utils --evidence … --promote --user-approval "yes"
```

A constraint sits in `proposed` state until that approval, and it constrains nothing until then. Otherwise it becomes superstition with a changelog.

**A verdict that does not change what runs next is a report.**
