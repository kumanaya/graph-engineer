# Isolation: What a Worker May Rely On

The runtime fact this whole skill is built on:

```text
SUBAGENTS ARE ISOLATED.
```

A Hermes subagent (`delegate_task`) starts with a **completely fresh conversation**. It cannot see the parent's history, a sibling's findings, or any other worker's reasoning. Only its final summary enters the parent's context.

So a worker may depend on exactly five things:

```text
1. its node specification
2. explicitly supplied context
3. explicitly supplied input artifacts
4. explicitly supplied constraints
5. tools/resources intentionally available to it
```

Nothing else. Not "what the other worker probably found". Not "the state of the repo as of a minute ago". Not "the plan we discussed".

**Workers are isolated. The graph is not.** The orchestrator owns the graph, and it moves every fact between nodes on purpose.

## The failure this replaces

The old vocabulary called it *running notes*: "shared state across jobs, notes move with the work". There is no such channel. There is no shared window, no shared memory, no ambient awareness. Written that way, a graph silently becomes one of these:

| Written as | Actually happens |
|------------|------------------|
| "Worker B picks up where A left off" | B starts blank and guesses, or invents |
| "The verifier sees the findings" | The verifier sees only what the envelope carried |
| "Workers coordinate on the split" | They can't. There is no channel — they converge or they diverge |
| "State lives in the context" | Context is per-agent and compacted; state must be on disk |

Both bad outcomes are real: **missing context** (a node runs with inputs it never received) and **shared context** (a node inherits a sibling's framing and echoes it). The fix is neither bigger prompts nor more history. It is explicit state.

## The Node Input Envelope

Before a node is spawned, the orchestrator builds one self-contained envelope. It is the node's entire world.

```text
NODE            id, kind, attempt
GRAPH GOAL      the one sentence everything serves
NODE GOAL       this node's single job
GREEN CONDITION what objectively means success — written before the work
LENS            the angle this worker owns (distinct per worker)
INPUTS          artifact id @ version, type, absolute path, sha256
CONSTRAINTS     binding rules (graph-local + promoted learning constraints)
WRITER          the exact artifact path this node may write — one writer per path
RETURN          where to write its contract JSON (a skill convention; Hermes has no such field)
OUTPUT CONTRACT the JSON schema its answer must satisfy
LIMITS          attempt n of max
```

For a correction attempt, the envelope additionally carries the verifier's verdict (see `references/return-paths.md`).

The readiness test, asked before every spawn:

> **Could this agent complete its job correctly if this envelope were literally everything it knew about this graph?**

If no, the node is not ready or the envelope is incomplete. Do not spawn it and hope.

## Output contracts, not vibes

Hermes validates the contract for you: pass the node's contract as `output_schema` on the task, and the child's final answer must validate against it. On failure Hermes sends the child **one** bounded correction turn carrying the validation errors, then reports `schema_valid: false` with the raw text — it does not discard the work, and it does not retry forever.

That gives the graph a machine-checkable edge between "a worker spoke" and "an artifact exists":

```text
child returns contract JSON  →  schema_valid?  →  artifact file exists at the declared path?
                                              →  commit (or reject and correct)
```

A contract miss is a `RED`, not a conversation.

## Context policy: minimum sufficient

A worker receives:

```text
global goal
+ its local goal
+ required artifacts (by reference, not pasted)
+ relevant constraints
+ green condition
+ output contract
+ its writer path
```

It generally does not receive:

```text
all sibling conversations
all intermediate reasoning
all unrelated artifacts
the complete graph history
the parent's framing of the problem
```

Two reasons, and both matter:

1. **Anchoring.** Give four workers one shared window and the first finding frames the other three. You pay four times for one opinion and three echoes. Isolation is not a limitation to work around — it is what makes a fan-out worth paying for.
2. **Cost.** Artifacts travel by path. A 40 KB findings file is one line in an envelope and zero tokens until a node actually reads it.

Isolation is preserved. Coordination is added. Not the other way round.

## Edges carry artifacts, or they are fake

An edge means *B consumes A's output*. In this skill an edge is written as a requirement, and nothing else:

```yaml
# node verify-findings
requires:
  - artifact: auth-findings     # ← the edge. The producer of this artifact is the dependency.
```

Consequences worth internalising:

- **Execution order is not a dependency.** "And then" is not an edge. If B does not read A's output, B must not wait for A — run them together.
- **An ordering-only edge cannot be written.** There is no `depends_on`, no `after`, no priority field. If you cannot name the artifact that crosses, there is no edge, and the graph runs the work in parallel.
- **Required vs optional.** `required: false` means "use it if it exists". Optional inputs never gate a node.

If you want a node to wait without consuming anything, that is the fake edge the whole rule exists to delete.

## The three sentences

> Workers are isolated. The graph is not.

> Agents do not coordinate through shared conversations. They coordinate through explicit graph state, artifacts, dependencies, and the orchestrator.

> Spawning executes nodes; it does not define the graph.
