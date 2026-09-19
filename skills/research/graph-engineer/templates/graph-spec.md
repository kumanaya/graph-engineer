# Graph Spec

The design canvas. Fill it for *this* goal, then hand the machine-readable half to `graph_state.py init`.

Prefer the diamond unless the stop rule says stay one agent. A one-node graph is a fine answer — and it needs no state machinery at all.

## 1. Goal

- **Request (one sentence):**
- **Success criteria:**
- **Irreversible actions (if any):** send / publish / refund / invoice / go-live / other:
- **Final output path(s):**

## 2. Stop rule check

- **Where does the work split into independent jobs?**
- **Do any proposed parallel jobs need each other's output mid-flight?** If yes they are not parallel — one waits on the other's committed artifact.
- **Decision:** `[ ] graph` / `[ ] one agent` — reason:

> If one agent can do this correctly, stay one agent. Do not instantiate Graph State to look sophisticated.

## 3. Green conditions (write these first)

| Node | Green condition — a program could settle it | Settled by |
|------|---------------------------------------------|------------|
| | | script / check / diff / query |

Nothing here that can fail the work? Say so plainly — that node is **unverified**, not done. Not a check: "looks good", "the model is confident", "no errors were raised".

## 4. Node canvas

One block per node. Every field is required; `—` is a valid answer only where marked.

```text
NODE            id (lowercase)
KIND            splitter | worker | verifier | code | gate
JOB             what exact job does it perform, in one sentence
LENS            the one angle it owns (workers/verifiers; must be distinct per worker)
INPUTS          artifact id @ version expectation — required or optional
DEPENDENCIES    derived: the producers of those artifacts (do not write these by hand)
GREEN CONDITION what objectively means success
OUTPUT CONTRACT the JSON schema it must return (see templates/node-contract.md)
CONTEXT         the minimum that must be in its envelope: graph goal + inputs + constraints
FAILURE         where RED goes: which unit returns, to which node, with what scope
WRITER          the artifact path this node may write — one writer per path
```

Repeat per node. If two nodes would write the same path, one of them is wrong.

A **gate** fills the same block, minus the contract: it requires what it approves, and it should produce a `decision` artifact whenever anything runs after it — that is what makes the pause a real dependency (`references/gate-design.md`).

## 5. Edges

An edge exists because an artifact crosses it. Nothing else creates an edge.

| FROM (producer) | TO (consumer) | CARRIES (artifact) | REQUIRED / OPTIONAL |
|-----------------|---------------|--------------------|---------------------|
| | | | |

**If `CARRIES` cannot be named, the edge is fake.** Delete the wait and run both nodes in the same round. There is no field for an ordering-only dependency, and that is deliberate.

## 6. Artifacts

| Artifact | Type | Producer | Verifier | Notes |
|----------|------|----------|----------|-------|
| | findings / evidence / plan / code-change / test-result / data / report / verdict / decision | | | |

Rules: one producer per artifact · versioned, never overwritten · if a verifier is declared, consumers wait for the verified version · a `decision` artifact is produced by a gate, and anything downstream that requires it is genuinely held until the human answers.

## 7. Rounds (what runs together)

| Round | Dispatch (one `delegate_task` batch) | Local code nodes | Commits |
|-------|--------------------------------------|------------------|---------|
| 1 | | | |
| 2 | | | |

State explicitly which nodes run **concurrently** and what each one receives.

## 8. Verification

- **Verifier node(s):** which artifact(s) each one inspects
- **Lens per verifier** (distinct questions — adapt to the domain):
  - Lens A:
  - Lens B:
- **Verdict contract:** `verdict` (green/red) · `unit` · `reason` · `evidence` · `scope`
- **On RED:** which unit returns, to which node, with which evidence and scope

## 9. Return paths

- **Correction edge (this run):** unit → producer, carrying the verdict + the latest artifact version. A new version is produced; nothing else re-runs.
- **Learning edge (every run after):** which accepted outcome yields which constraint, and the evidence it is derived from.
  ```text
  ACCEPTED   (node, artifact@version)
  DERIVED    (constraint, one line, imperative)
  LANDS IN   <root>/constraints.json → every later envelope
  ```
- **Promotion:** who approves a proposed constraint becoming active (a human; `--promote --user-approval`).

## 10. Human gate

- **Lane:** `[ ] reversible, contained` / `[ ] reversible, wide` / `[ ] hard to reverse` — the third does not open on its own
- **Action after approval:**
- **Why undo would be expensive there:**
- **What the gate reads, in order:** deterministic results → this run's trajectory → this node's rollback history → model assessment (last)
- **Mid-graph pauses (if any):** what the user must approve before continuing

## 11. Caps and wiring

- **Attempt cap per node:** 3 (at the cap → escalate to graph design, not to another attempt)
- **Spawn cap per round:** 5, and never above `delegation.max_concurrent_children`
- **Spawn budget for the run:** 20
- **One writer per path:** confirmed in the node canvas
- **Routing:** which edges are conditional, and the exact condition (code decides; the model does not invent labels)

## 12. Machine-readable spec

The half that `init` validates. Paste-ready skeleton — see `templates/node-contract.md` for the contracts.

```json
{
  "graph": {
    "id": "lowercase-graph-id",
    "goal": "one sentence",
    "gate": {"lane": "reversible, wide", "action": "what happens after approval"},
    "caps": {"max_attempts": 3, "spawn_cap": 5, "spawn_budget": 20}
  },
  "constraints": ["binding rule for every node"],
  "artifacts": {
    "example-findings": {"type": "findings", "ext": "md", "producer": "audit-a", "verifier": "verify-findings"},
    "example-verdict": {"type": "verdict", "producer": "verify-findings"},
    "example-report": {"type": "report", "producer": "merge"}
  },
  "nodes": [
    {
      "id": "audit-a",
      "kind": "worker",
      "lens": "one angle no sibling owns",
      "goal": "the one job",
      "green_condition": "a program could settle it",
      "requires": [{"artifact": "seed-notes"}],
      "produces": "example-findings",
      "output_contract": {"type": "object", "properties": {}, "required": []}
    }
  ]
}
```

## 13. Runnable prompt

Paste-ready. Must include `use a workflow:` and describe *this* goal's nodes — never a canned example menu.

```text
[write the full prompt here]
```

## 14. Verification

- [ ] Stop rule applied (or one agent chosen and justified)
- [ ] Green condition per node, written before the work
- [ ] Every edge names the artifact it carries; no fake edges remain
- [ ] Every node declares inputs, output contract, failure path and writer
- [ ] Verifier is a separate node with a distinct lens; consumers wait for verification
- [ ] `init` accepts the spec (`graph_state.py init --spec …`)
- [ ] Caps set: attempts, spawns per round, spawn budget
- [ ] Gate lane named by blast radius; no irreversible action without explicit approval
- [ ] Correction path returns the unit only; learning path lands in `constraints.json`
