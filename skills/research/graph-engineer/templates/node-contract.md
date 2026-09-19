# Node Contract

The `output_contract` is the node's output schema. Hermes enforces it natively: pass it as `output_schema` on the `delegate_task` task, and the child's final answer must validate against it (one bounded correction turn if it does not). The commit step re-checks it, so a node cannot be committed on a claim alone.

Every contract is a JSON Schema object. Only these keywords are validated: `type`, `properties`, `required`, `items`, `enum`, `additionalProperties`, `minItems`, `minLength`, `description`, `title`, `default`, `examples`.

## Required in every node contract

```json
{
  "type": "object",
  "properties": {
    "node":          {"type": "string", "description": "the node id, verbatim"},
    "status":        {"type": "string", "enum": ["done", "failed"]},
    "summary":       {"type": "string", "minLength": 1, "description": "what happened, under 60 words"},
    "artifact_path": {"type": "string", "description": "the exact writer path from the envelope"},
    "evidence":      {"type": "array", "items": {"type": "string"},
                      "description": "file:line, URL, command, or measurement supporting the claim"}
  },
  "required": ["node", "status", "summary", "artifact_path"]
}
```

`artifact_path` is not decoration: the commit step compares it to the path the envelope designated. A worker that writes somewhere else is rejected — one writer per path.

## Worker

Add what makes the finding checkable in the domain. Example — a research worker:

```json
{
  "type": "object",
  "properties": {
    "node": {"type": "string"},
    "status": {"type": "string", "enum": ["done", "failed"]},
    "summary": {"type": "string", "minLength": 1},
    "artifact_path": {"type": "string"},
    "evidence": {"type": "array", "items": {"type": "string"}},
    "claims": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "properties": {
          "claim": {"type": "string"},
          "source": {"type": "string"},
          "date": {"type": "string"}
        },
        "required": ["claim", "source", "date"]
      }
    }
  },
  "required": ["node", "status", "summary", "artifact_path", "claims"]
}
```

## Verifier

The four extra fields are what make the correction edge possible. All four are required.

```json
{
  "type": "object",
  "properties": {
    "node": {"type": "string"},
    "status": {"type": "string", "enum": ["done", "failed"]},
    "summary": {"type": "string", "minLength": 1},
    "artifact_path": {"type": "string"},
    "evidence": {"type": "array", "items": {"type": "string"}},
    "verdict": {"type": "string", "enum": ["green", "red"]},
    "unit": {"type": "string",
             "description": "the artifact or node id being rejected — only one it inspected"},
    "reason": {"type": "string", "description": "the single failing check"},
    "scope": {"type": "string", "description": "what the correction may touch, and nothing else"}
  },
  "required": ["node", "status", "summary", "artifact_path", "verdict", "unit", "reason", "scope"]
}
```

`unit` is resolved by the commit step against the artifacts that verifier actually required. A verifier cannot reject something it never read, and it cannot reject "everything".

## Splitter

Add the units it decided, so the split is a committed artifact rather than a paragraph:

```json
{
  "properties": {
    "units": {
      "type": "array",
      "minItems": 2,
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "lens": {"type": "string"},
          "artifact": {"type": "string"}
        },
        "required": ["id", "lens", "artifact"]
      }
    }
  },
  "required": ["units"]
}
```

The split dimension must make two workers unable to return the same finding. If it cannot, the split is wrong — fix the design, not the prompt.

## Code node

Deterministic work returns the same five fields plus whatever the check needs. Example — a merge that reports what it dropped:

```json
{
  "properties": {
    "kept": {"type": "integer"},
    "dropped": {"type": "integer"},
    "dropped_reasons": {"type": "array", "items": {"type": "string"}}
  },
  "required": ["kept"]
}
```

## Gate

Gates are not spawned and return no contract. They are recorded through the state script:

```bash
graph_state.py gate --status approved --user-approval "the user's own words"
```

A `hard to reverse` lane refuses approval without that explicit quote.

## Failure is part of the contract

A node that cannot satisfy its green condition returns `status: "failed"` with a real `summary` — that is a valid, useful result. It is not a contract miss, and it must never be replaced by an invented success. The scheduler turns it into `RED` and the graph decides what happens next.
