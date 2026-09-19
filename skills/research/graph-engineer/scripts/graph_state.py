#!/usr/bin/env python3
"""graph_state.py — deterministic Graph State, scheduler and commit step for graph-engineer.

Invariant this file exists to enforce:

    Workers are isolated. The graph is not.

Hermes subagents (``delegate_task``) start with a fresh conversation. They cannot see
the parent's history, a sibling's findings, or each other's reasoning. So the graph
cannot live in anyone's context:

  * the ORCHESTRATOR is the only writer of Graph State (this script, one state.json);
  * every node input is an ARTIFACT committed to disk by the graph, never a memory;
  * an EDGE exists only as a named artifact crossing it (``requires`` == edge).

Consequences worth knowing before you edit:

  * There is no way to express an ordering-only dependency. If you cannot name the
    artifact that crosses an edge, you cannot write the edge. That is the fake-edge
    rule, enforced structurally instead of by good intentions.
  * Artifacts are versioned and never overwritten. A correction produces v(n+1).
  * A node may consume an artifact only after its verifier is GREEN (when the graph
    declares one) — "verify first, merge second" as a scheduler rule.

Node kinds: splitter | worker | verifier | code | gate

  * splitter / worker / verifier are spawned (Hermes executes them);
  * code runs deterministically in the orchestrator (terminal / execute_code);
  * gate is a human (never spawned, never auto-approved).

Exit codes: 0 ok, 2 rejected (contract/invariant violation, no state change), 3 illegal
transition, 4 not found. Stdlib only. Python 3.8+.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

SCHEMA = "graph-engineer/state/1"
NODE_KINDS = ("splitter", "worker", "verifier", "code", "gate")
SPAWNABLE = ("splitter", "worker", "verifier")
TERMINAL_BAD = ("ESCALATED", "BLOCKED")
DEFAULT_CAPS = {"max_attempts": 3, "spawn_cap": 5, "spawn_budget": 20}
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


# --------------------------------------------------------------------------- io


def die(msg: str, code: int = 2) -> "None":
    sys.stderr.write("graph_state: %s\n" % msg)
    raise SystemExit(code)


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def read_json(path: Path, what: str):
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        die("%s not found: %s" % (what, path), 4)
    except json.JSONDecodeError as exc:
        die("%s is not valid JSON (%s): %s" % (what, exc, path), 2)


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(data, fh, indent=2, sort_keys=False)
            fh.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_root(args) -> Path:
    root = Path(args.root).expanduser()
    return root if root.is_absolute() else (Path.cwd() / root)


def state_path(args) -> Path:
    root = resolve_root(args)
    if args.graph:
        return root / args.graph / "state.json"
    found = sorted(p for p in root.glob("*/state.json")) if root.is_dir() else []
    if len(found) == 1:
        return found[0]
    if not found:
        die("no graph state under %s — run `init` first (or pass --graph)" % root, 4)
    die(
        "several graphs under %s (%s) — pass --graph"
        % (root, ", ".join(p.parent.name for p in found)),
        3,
    )


def load(args) -> dict:
    return read_json(state_path(args), "graph state")


def save(args, state: dict) -> None:
    state["updated"] = now()
    write_json(state_path(args), state)


def record(state: dict, event: str, **fields) -> None:
    entry = {"at": now(), "event": event}
    entry.update(fields)
    state.setdefault("history", []).append(entry)


def out(state: dict, payload: dict, code: int = 0) -> "None":
    payload.setdefault("graph_id", state["graph"]["id"])
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    raise SystemExit(code)


def constraints_file(args) -> Path:
    return resolve_root(args) / "constraints.json"


def active_constraints(args) -> list:
    path = constraints_file(args)
    if not path.exists():
        return []
    data = read_json(path, "constraints store")
    return [c["constraint"] for c in data.get("constraints", []) if c.get("status") == "active"]


# ------------------------------------------------------------------- validation


def check_id(value, what):
    if not isinstance(value, str) or not ID_RE.match(value):
        die("%s must match %s (got %r)" % (what, ID_RE.pattern, value), 2)


def check_schema_subset(schema, where: str) -> None:
    """Reject the shapes our mini-validator cannot honour, so nothing is silently skipped."""
    if not isinstance(schema, dict):
        die("%s must be a JSON Schema object" % where, 2)
    allowed = {
        "type",
        "properties",
        "required",
        "items",
        "enum",
        "additionalProperties",
        "minItems",
        "minLength",
        "description",
        "title",
        "default",
        "examples",
    }
    unknown = sorted(set(schema) - allowed)
    if unknown:
        die(
            "%s uses JSON Schema keywords graph_state.py does not validate: %s "
            "(supported: %s)" % (where, ", ".join(unknown), ", ".join(sorted(allowed))),
            2,
        )
    if schema.get("type") == "object":
        props = schema.get("properties", {})
        if not isinstance(props, dict):
            die("%s.properties must be an object" % where, 2)
        for name, sub in props.items():
            check_schema_subset(sub, "%s.properties.%s" % (where, name))
        for name in schema.get("required", []):
            if name not in props:
                die("%s.required names %r which is not in properties" % (where, name), 2)
    elif schema.get("type") == "array":
        check_schema_subset(schema.get("items", {}), "%s.items" % where)


def validate_value(value, schema, path: str, errors: list) -> None:
    t = schema.get("type")
    if t == "object":
        if not isinstance(value, dict):
            errors.append("%s: expected object, got %s" % (path, type(value).__name__))
            return
        for name in schema.get("required", []):
            if name not in value:
                errors.append("%s: missing required field %r" % (path, name))
        for name, sub in schema.get("properties", {}).items():
            if name in value:
                validate_value(value[name], sub, "%s.%s" % (path, name), errors)
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(schema.get("properties", {})))
            if extra:
                errors.append("%s: unexpected fields %s" % (path, ", ".join(extra)))
    elif t == "array":
        if not isinstance(value, list):
            errors.append("%s: expected array, got %s" % (path, type(value).__name__))
            return
        if isinstance(schema.get("minItems"), int) and len(value) < schema["minItems"]:
            errors.append("%s: needs at least %d items" % (path, schema["minItems"]))
        for i, item in enumerate(value):
            validate_value(item, schema.get("items", {}), "%s[%d]" % (path, i), errors)
    elif t == "string":
        if not isinstance(value, str):
            errors.append("%s: expected string, got %s" % (path, type(value).__name__))
        elif isinstance(schema.get("minLength"), int) and len(value) < schema["minLength"]:
            errors.append("%s: string shorter than %d" % (path, schema["minLength"]))
    elif t == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append("%s: expected integer" % path)
    elif t == "number":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append("%s: expected number" % path)
    elif t == "boolean":
        if not isinstance(value, bool):
            errors.append("%s: expected boolean" % path)
    if "enum" in schema and value not in schema["enum"]:
        errors.append("%s: %r not in %s" % (path, value, schema["enum"]))


# ----------------------------------------------------------------------- init


OBJECT_KEYS = {
    "graph": {"id", "goal", "gate", "caps"},
    "artifact": {"type", "ext", "producer", "verifier", "seed", "path", "description"},
    "node": {"id", "kind", "goal", "green_condition", "lens", "requires", "produces",
             "output_contract", "on_red"},
    "require": {"artifact", "required"},
    "on_red": {"corrects", "unit"},
}


def check_keys(obj, kind: str, where: str) -> None:
    unknown = sorted(set(obj) - OBJECT_KEYS[kind])
    if unknown:
        die(
            "%s has unknown key(s): %s. Edges exist ONLY as artifact requirements "
            "(`requires`), so an ordering-only dependency cannot be written down — "
            "name the artifact that crosses the edge, or delete the wait."
            % (where, ", ".join(unknown)),
            2,
        )


def cmd_init(args) -> "None":
    spec_path = Path(args.spec).expanduser()
    spec = read_json(spec_path, "graph spec")
    if not isinstance(spec.get("graph"), dict):
        die("spec.graph is required", 2)
    unknown_spec = sorted(set(spec) - {"graph", "artifacts", "nodes", "constraints"})
    if unknown_spec:
        die("spec has unknown key(s): %s" % ", ".join(unknown_spec), 2)
    graph = spec["graph"]
    check_keys(graph, "graph", "graph")
    check_id(graph.get("id"), "graph.id")
    if not graph.get("goal"):
        die("graph.goal is required", 2)

    artifacts = spec.get("artifacts", {})
    nodes = spec.get("nodes", [])
    if not isinstance(nodes, list) or not nodes:
        die("spec.nodes must be a non-empty list", 2)

    # --- artifacts
    for aid, art in artifacts.items():
        check_id(aid, "artifact id %r" % aid)
        if not isinstance(art, dict):
            die("artifact %s must be an object" % aid, 2)
        check_keys(art, "artifact", "artifact %s" % aid)
        if not art.get("type"):
            die("artifact %s needs a type" % aid, 2)
        if art.get("seed"):
            if not art.get("path"):
                die("seed artifact %s needs a path" % aid, 2)
            if not Path(art["path"]).expanduser().is_absolute():
                die("seed artifact %s path must be absolute (children resolve it directly)" % aid, 2)
        elif not art.get("producer"):
            die("artifact %s needs a producer (or seed: true + path)" % aid, 2)

    # --- nodes
    seen = {}
    for node in nodes:
        if not isinstance(node, dict):
            die("every node must be an object", 2)
        nid = node.get("id")
        check_id(nid, "node id %r" % nid)
        if nid in seen:
            die("duplicate node id %s" % nid, 2)
        seen[nid] = node
        check_keys(node, "node", "node %s" % nid)
        kind = node.get("kind")
        if kind not in NODE_KINDS:
            die("node %s: kind must be one of %s" % (nid, ", ".join(NODE_KINDS)), 2)
        if kind != "gate" and not node.get("goal"):
            die("node %s: goal is required" % nid, 2)
        if kind != "gate" and not node.get("green_condition"):
            die("node %s: green_condition is required (write the check first)" % nid, 2)
        produces = node.get("produces")
        if kind == "gate":
            # a gate MAY produce a decision artifact; downstream nodes that require it are
            # genuinely held until the human answers. Without one, the pause is only as
            # strong as the orchestrator's round discipline.
            if produces:
                if produces not in artifacts:
                    die("gate %s produces %r which is not declared in spec.artifacts" % (nid, produces), 2)
                if artifacts[produces].get("producer") != nid:
                    die("gate %s produces %r but its declared producer is %r"
                        % (nid, produces, artifacts[produces].get("producer")), 2)
                if artifacts[produces].get("verifier"):
                    die("gate %s: a decision artifact is not verified by a node — the human is the verifier" % nid, 2)
        else:
            if not produces:
                die("node %s: produces is required (name the artifact)" % nid, 2)
            if produces not in artifacts:
                die("node %s: produces %r which is not declared in spec.artifacts" % (nid, produces), 2)
            if artifacts[produces].get("producer") != nid:
                die(
                    "node %s produces %r but spec.artifacts[%r].producer is %r"
                    % (nid, produces, produces, artifacts[produces].get("producer")),
                    2,
                )
            contract = node.get("output_contract")
            if not isinstance(contract, dict) or contract.get("type") != "object":
                die("node %s: output_contract must be a JSON Schema with type: object" % nid, 2)
            check_schema_subset(contract, "node %s output_contract" % nid)
            required = contract.get("required", [])
            for field in ("node", "status", "summary", "artifact_path"):
                if field not in required:
                    die(
                        "node %s: output_contract.required must include %r (see templates/node-contract.md)"
                        % (nid, field),
                        2,
                    )
            if kind == "verifier":
                for field in ("verdict", "unit", "reason", "scope"):
                    if field not in required:
                        die(
                            "node %s: a verifier contract must require %r so the correction edge has a payload"
                            % (nid, field),
                            2,
                        )
                on_red = node.get("on_red")
                if on_red is not None:
                    check_keys(on_red, "on_red", "node %s on_red" % nid)
        for req in node.get("requires", []):
            if not isinstance(req, dict) or not req.get("artifact"):
                die("node %s: each requires entry needs {artifact, required}" % nid, 2)
            check_keys(req, "require", "node %s requires entry" % nid)
            if req["artifact"] not in artifacts:
                die("node %s requires undeclared artifact %r" % (nid, req["artifact"]), 2)
            prod = artifacts[req["artifact"]].get("producer")
            if prod is None and not artifacts[req["artifact"]].get("seed"):
                die("node %s requires %r which has no producer and is not a seed" % (nid, req["artifact"]), 2)
            if prod == nid:
                die("node %s requires its own artifact %r" % (nid, req["artifact"]), 2)

    for aid, art in artifacts.items():
        prod = art.get("producer")
        if prod and prod not in seen:
            die("artifact %s names producer %r which is not a node" % (aid, prod), 2)
        if prod and not art.get("seed") and seen[prod].get("produces") != aid:
            die(
                "artifact %s names producer %r, but node %s produces %r — one artifact, one producer"
                % (aid, prod, prod, seen[prod].get("produces")),
                2,
            )
        ver = art.get("verifier")
        if ver:
            if ver not in seen:
                die("artifact %s names verifier %r which is not a node" % (aid, ver), 2)
            if seen[ver]["kind"] != "verifier":
                die("artifact %s: verifier %s is kind %r, not verifier" % (aid, ver, seen[ver]["kind"]), 2)
            ver_requires = [r["artifact"] for r in seen[ver].get("requires", [])]
            if aid not in ver_requires:
                die("artifact %s: verifier %s must require it" % (aid, ver), 2)
            on_red = seen[ver].get("on_red") or {}
            if len(ver_requires) == 1 and on_red.get("corrects") != prod:
                die("artifact %s: verifier %s must set on_red.corrects = %r" % (aid, ver, prod), 2)
            if len(ver_requires) > 1 and on_red.get("corrects"):
                die(
                    "artifact %s: verifier %s covers %d artifacts, so it cannot use on_red.corrects — "
                    "leave it out and let the verdict's `unit` name the artifact or node to correct"
                    % (aid, ver, len(ver_requires)),
                    2,
                )

    # every node must be reachable from a seed/root (no orphan waiting on nothing)
    # and every artifact must be consumed by someone or be the graph's declared output
    consumed = {r["artifact"] for n in nodes for r in n.get("requires", [])}
    produced = {n.get("produces") for n in nodes if n.get("produces")}
    for n in nodes:
        if n["kind"] == "gate" and not n.get("requires"):
            die("node %s: a gate must require the artifact it approves" % n["id"], 2)

    # --- cycles (edges are artifact requirements)
    producer_of = {a: art.get("producer") for a, art in artifacts.items()}
    edges = {n["id"]: [producer_of[r["artifact"]] for r in n.get("requires", []) if producer_of[r["artifact"]]] for n in nodes}
    color, stack = {}, []
    order = []

    def visit(nid):
        color[nid] = 1
        stack.append(nid)
        for dep in edges[nid]:
            if color.get(dep) == 1:
                die("cycle in artifact dependencies: %s -> %s" % (" -> ".join(stack[stack.index(dep):]), dep), 2)
            if color.get(dep) is None:
                visit(dep)
        stack.pop()
        color[nid] = 2
        order.append(nid)

    for nid in edges:
        if color.get(nid) is None:
            visit(nid)

    # --- write state
    root = resolve_root(args)
    gdir = root / graph["id"]
    if gdir.exists():
        if not args.force:
            die("%s already exists — pass --force to replace, or use a new graph id" % gdir, 3)
        shutil.rmtree(gdir)

    graph_state = {
        "schema": SCHEMA,
        "graph": {
            "id": graph["id"],
            "goal": graph["goal"],
            "status": "planned",
            "created": now(),
            "root": str(gdir.resolve()),
            "caps": dict(DEFAULT_CAPS, **(graph.get("caps") or {})),
            "spawns_used": 0,
            "gate": {
                "lane": (graph.get("gate") or {}).get("lane", "reversible, contained"),
                "action": (graph.get("gate") or {}).get("action", "approve the outcome"),
                "status": "not_reached",
                "approvals": [],
            },
        },
        "artifacts": {},
        "nodes": {},
        "constraints": {
            "graph": list(spec.get("constraints", [])),
            "inherited": active_constraints(args),
        },
        "failures": [],
        "decisions": [],
        "history": [],
    }
    for aid, art in artifacts.items():
        graph_state["artifacts"][aid] = {
            "type": art["type"],
            "ext": art.get("ext", "md"),
            "producer": art.get("producer"),
            "verifier": art.get("verifier"),
            "seed": bool(art.get("seed")),
            "seed_path": art.get("path"),
            "versions": [],
            "verified_version": None if not art.get("seed") else 1,
        }
        if art.get("seed"):
            p = Path(art["path"]).expanduser()
            graph_state["artifacts"][aid]["versions"].append(
                {"version": 1, "path": str(p.resolve()), "sha256": sha256_file(p) if p.exists() else None,
                 "producer": None, "attempt": 0, "at": now(), "verified": True}
            )
    for node in nodes:
        nid = node["id"]
        graph_state["nodes"][nid] = {
            "id": nid,
            "kind": node["kind"],
            "goal": node.get("goal", ""),
            "green_condition": node.get("green_condition", ""),
            "lens": node.get("lens"),
            "requires": [
                {"artifact": r["artifact"], "required": r.get("required", True)}
                for r in node.get("requires", [])
            ],
            "produces": node.get("produces"),
            "output_contract": node.get("output_contract"),
            "on_red": node.get("on_red"),
            "status": "WAITING_HUMAN" if node["kind"] == "gate" else "PENDING",
            "attempt_count": 0,
            "attempts": [],
            "artifact": None,
            "correction": None,
            "blocked_by": None,
            "human": node["kind"] == "gate",
        }
    record(graph_state, "init", graph=graph["id"], nodes=len(nodes), artifacts=len(artifacts))
    graph_state["updated"] = now()
    write_json(gdir / "state.json", graph_state)
    out(graph_state, {
        "root": str(gdir.resolve()),
        "state": str((gdir / "state.json").resolve()),
        "nodes": sorted(graph_state["nodes"]),
        "note": "state.json is written ONLY by the orchestrator. Workers never touch it.",
    })


# ------------------------------------------------------------------ readiness


def latest_version(state, aid, verified_only=False):
    art = state["artifacts"].get(aid)
    if not art or not art["versions"]:
        return None
    versions = art["versions"]
    if verified_only:
        if art.get("verified_version") is None:
            return None
        return next((v for v in versions if v["version"] == art["verified_version"]), None)
    return versions[-1]


def input_view(state, node, aid, required):
    """Resolve one requires-entry to a concrete artifact version (or a waiting reason)."""
    art = state["artifacts"][aid]
    producer = art.get("producer")
    producer_node = state["nodes"].get(producer) if producer else None
    if producer_node and producer_node["kind"] == "gate":
        # a human decision is not a version to read; it is a door that is open or shut
        if art.get("rejected"):
            return None, "gate %s was rejected — nothing downstream runs" % producer
        version = latest_version(state, aid)
        if version is None:
            return None, "gate %s has not been answered yet" % producer
        return version, None
    verifier = art.get("verifier")
    verified_only = bool(verifier) and verifier != node["id"]
    version = latest_version(state, aid, verified_only=verified_only)
    if version is None:
        if art.get("seed") and not art["versions"]:
            return None, "seed artifact %s is missing at %s" % (aid, art.get("seed_path"))
        if verified_only:
            return None, "%s@latest is not verified yet (verifier: %s)" % (aid, verifier)
        return None, "%s has no committed version yet (producer: %s)" % (aid, art.get("producer"))
    return version, None


def compute_node_state(state, nid):
    """Derive the node's effective status. PENDING/READY/BLOCKED are recomputed, never sticky."""
    node = state["nodes"][nid]
    if node["kind"] == "gate":
        return ("WAITING_HUMAN" if node["status"] in ("PENDING", "READY", "WAITING_HUMAN")
                else node["status"]), node.get("blocked_by")
    if node["status"] in ("RUNNING", "GREEN", "ESCALATED"):
        return node["status"], node.get("blocked_by")
    waiting, blocked = [], []
    for req in node["requires"]:
        version, why = input_view(state, node, req["artifact"], req["required"])
        if version is None:
            if not req["required"]:
                continue
            producer = state["artifacts"][req["artifact"]].get("producer")
            producer_status = state["nodes"][producer]["status"] if producer else None
            if producer_status in TERMINAL_BAD:
                blocked.append(why)
            else:
                waiting.append(why)
    if blocked:
        return "BLOCKED", "; ".join(blocked)
    if waiting:
        return "PENDING", "; ".join(waiting)
    caps = state["graph"]["caps"]
    if node["status"] == "RED" and node["attempt_count"] >= caps["max_attempts"]:
        return "ESCALATED", "attempt cap reached (%d)" % caps["max_attempts"]
    return "READY", None


def refresh(state) -> None:
    """Recompute every derivable status so consumers unblock when a producer recovers."""
    for nid in state["nodes"]:
        status, why = compute_node_state(state, nid)
        node = state["nodes"][nid]
        if node["status"] == "RUNNING":
            continue
        node["status"] = status
        node["blocked_by"] = why
    if any(n["status"] == "ESCALATED" for n in state["nodes"].values()):
        state["graph"]["status"] = "needs_plan_review"
    elif state["graph"]["status"] in ("planned", "running", "gated", "blocked") and state["nodes"]:
        done = [n for n in state["nodes"].values() if n["kind"] != "gate"]
        gate = state["graph"]["gate"]
        has_gate = any(n["kind"] == "gate" for n in state["nodes"].values())
        if done and all(n["status"] == "GREEN" for n in done):
            if not has_gate:
                state["graph"]["status"] = "done"
            elif gate["status"] == "approved":
                state["graph"]["status"] = "done"
            elif gate["status"] == "rejected":
                state["graph"]["status"] = "blocked"
            else:
                gate["status"] = "waiting"
                state["graph"]["status"] = "gated"
        elif gate["status"] == "rejected":
            state["graph"]["status"] = "blocked"
        elif gate["status"] in ("waiting", "not_reached") and not any(
            n["status"] in ("RUNNING", "READY") for n in state["nodes"].values()
        ) and all(
            n["kind"] == "gate" or n["status"] == "GREEN" or held_by_gate(state, n)
            for n in state["nodes"].values()
        ):
            # nothing is in flight and the only thing outstanding is the human's answer
            gate["status"] = "waiting"
            state["graph"]["status"] = "gated"
        else:
            state["graph"]["status"] = "running"


def held_by_gate(state, node, seen=None) -> bool:
    """True when this node cannot proceed without a human answer, directly or upstream.

    Transitive on purpose: in `decision → writers → checker → assembler`, the assembler is
    held by the gate even though only the writers require the decision artifact.
    """
    seen = seen if seen is not None else set()
    for req in node["requires"]:
        producer = state["artifacts"][req["artifact"]].get("producer")
        upstream = state["nodes"].get(producer) if producer else None
        if upstream is None:
            continue
        if upstream["kind"] == "gate":
            if upstream["status"] == "WAITING_HUMAN":
                return True
            continue
        if upstream["id"] in seen or upstream["status"] == "GREEN":
            continue
        seen.add(upstream["id"])
        if held_by_gate(state, upstream, seen):
            return True
    return False


def ready_nodes(state):
    refresh(state)
    return [nid for nid, n in state["nodes"].items() if n["status"] == "READY"]


# ------------------------------------------------------------------ dispatch


def envelope(state, args, nid, attempt):
    node = state["nodes"][nid]
    art = state["artifacts"][node["produces"]]
    version = len(art["versions"]) + 1
    gdir = Path(state["graph"]["root"])
    artifact_path = (gdir / "artifacts" / ("%s.v%d.%s" % (node["produces"], version, art.get("ext", "md")))).resolve()
    if artifact_path.exists():
        discard = gdir / "discarded"
        discard.mkdir(parents=True, exist_ok=True)
        os.replace(str(artifact_path), str(discard / ("%s.v%d.attempt%d.%s" % (
            node["produces"], version, attempt, art.get("ext", "md")))))
    return_file = (gdir / "results" / ("%s.a%d.json" % (nid, attempt))).resolve()
    inputs, problems = [], []
    for req in node["requires"]:
        version_row, why = input_view(state, node, req["artifact"], req["required"])
        if version_row is None:
            if req["required"]:
                problems.append(why)
            continue
        inputs.append({
            "artifact": req["artifact"],
            "version": version_row["version"],
            "type": state["artifacts"][req["artifact"]]["type"],
            "path": version_row["path"],
            "sha256": version_row.get("sha256"),
            "required": req["required"],
        })
    if problems:
        die("node %s is not ready: %s" % (nid, "; ".join(problems)), 3)
    return {
        "schema": "graph-engineer/envelope/1",
        "graph": {"id": state["graph"]["id"], "goal": state["graph"]["goal"]},
        "node": {"id": nid, "kind": node["kind"], "attempt": attempt, "lens": node["lens"]},
        "goal": node["goal"],
        "green_condition": node["green_condition"],
        "inputs": inputs,
        "constraints": list(state["constraints"]["inherited"]) + list(state["constraints"]["graph"]),
        "writer": {"artifact": node["produces"], "version": version, "path": str(artifact_path)},
        "return_file": str(return_file),
        "output_contract": node["output_contract"],
        "limits": {
            "max_attempts": state["graph"]["caps"]["max_attempts"],
            "attempt": attempt,
        },
    }


def render_context(env) -> str:
    lines = [
        "# Graph node: %s (%s, attempt %d)" % (env["node"]["id"], env["node"]["kind"], env["node"]["attempt"]),
        "",
        "## Graph goal",
        env["graph"]["goal"],
        "",
        "## Your job",
        env["goal"],
        "",
        "## Green condition — written before the work",
        env["green_condition"],
    ]
    if env["node"].get("lens"):
        lines += ["", "## Your lens", env["node"]["lens"]]
    lines += ["", "## Inputs (read these files)"]
    if env["inputs"]:
        for item in env["inputs"]:
            lines.append(
                "- %s@v%d (%s%s) — %s"
                % (
                    item["artifact"],
                    item["version"],
                    item["type"],
                    "" if item["required"] else ", optional",
                    item["path"],
                )
            )
    else:
        lines.append("- (none — this node is a root; work only from the goal and constraints)")
    if env["constraints"]:
        lines += ["", "## Constraints (binding)"]
        lines += ["- %s" % c for c in env["constraints"]]
    lines += [
        "",
        "## Write your artifact",
        "Write the artifact (%s@v%d) to exactly this path, and nothing else may write it:"
        % (env["writer"]["artifact"], env["writer"]["version"]),
        env["writer"]["path"],
        "",
        "## Return",
        "Write your final JSON to this file as well: " + env["return_file"],
        "It must validate against the attached output schema: return ONLY the JSON value, no prose, no code fence.",
        "`artifact_path` must be the exact path above, and `node` must be `%s`." % env["node"]["id"],
        "",
        "## Isolation rule",
        "You are an isolated subagent. This envelope is everything you may rely on: no other worker's",
        "conversation, findings, or reasoning is visible to you, and your work is visible to no one until",
        "the orchestrator commits it. If an input you need is missing, say so with status \"failed\" —",
        "never guess what a sibling found, and never invent a passing result.",
    ]
    return "\n".join(lines)


def cmd_dispatch(args) -> "None":
    state = load(args)
    caps = state["graph"]["caps"]
    limit = args.limit if args.limit is not None else caps["spawn_cap"]
    limit = min(limit, caps["spawn_cap"])
    ready = ready_nodes(state)
    spawnable = [n for n in ready if state["nodes"][n]["kind"] in SPAWNABLE]
    local = [n for n in ready if state["nodes"][n]["kind"] == "code"]
    budget_left = caps["spawn_budget"] - state["graph"]["spawns_used"]
    if spawnable and budget_left <= 0:
        die(
            "spawn budget exhausted (%d of %d used). Stop spawning and return to graph design."
            % (state["graph"]["spawns_used"], caps["spawn_budget"]),
            3,
        )
    chosen = spawnable[: max(0, min(limit, budget_left))]
    deferred = spawnable[len(chosen):]

    tasks, bindings, local_envelopes = [], [], []
    gdir = Path(state["graph"]["root"])
    for nid in chosen + local:
        node = state["nodes"][nid]
        attempt = node["attempt_count"] + 1
        env = envelope(state, args, nid, attempt)
        if node.get("correction"):
            env["correction"] = node["correction"]
        env_path = (gdir / "envelopes" / ("%s.a%d.json" % (nid, attempt))).resolve()
        write_json(env_path, env)
        if node["kind"] in SPAWNABLE:
            tasks.append({
                "goal": "%s — graph node %s (attempt %d). Green condition: %s"
                % (node["goal"], nid, attempt, node["green_condition"]),
                "context": render_context(env),
                "output_schema": node["output_contract"],
            })
            bindings.append({"node": nid, "attempt": attempt, "task_index": len(tasks) - 1,
                             "envelope": str(env_path)})
            state["graph"]["spawns_used"] += 1
        else:
            local_envelopes.append({"node": nid, "attempt": attempt, "envelope": str(env_path),
                                    "artifact_path": env["writer"]["path"],
                                    "return_file": env["return_file"]})
        node["status"] = "RUNNING"
        node["attempt_count"] = attempt
        node["attempts"].append({
            "attempt": attempt,
            "started": now(),
            "status": "running",
            "inputs": [{"artifact": i["artifact"], "version": i["version"]} for i in env["inputs"]],
            "artifact_target": env["writer"]["path"],
            "return_file": env["return_file"],
            "correction": node.get("correction"),
        })
        record(state, "dispatch", node=nid, attempt=attempt)

    if args.tasks_file:
        write_json(Path(args.tasks_file).resolve(), tasks)
    refresh(state)
    save(args, state)
    out(state, {
        "round_tasks": tasks,
        "bindings": bindings,
        "local_nodes": [b["node"] for b in local_envelopes],
        "local_envelopes": local_envelopes,
        "deferred_to_next_round": deferred,
        "note": (
            "Pass `round_tasks` to delegate_task(tasks=[...]) verbatim (Hermes runs them in parallel and "
            "delivers one consolidated result per call). Run every node in `local_nodes` yourself with "
            "execute_code/terminal — they are code nodes, not spawns — then `commit` each node."
        ),
    })


# -------------------------------------------------------------------- commit


def resolve_unit(state, verifier_node, unit: str):
    """Map a verifier's `unit` to (producer node id, artifact id) — deterministically.

    A verifier may only correct a unit it actually inspected, so `unit` must name one of
    its own required artifacts, or the producer of one. This is what keeps a correction
    edge pointed at the failed unit instead of the whole batch.
    """
    nid = verifier_node["id"]
    allowed = {}
    for req in verifier_node["requires"]:
        aid = req["artifact"]
        art = state["artifacts"][aid]
        if art.get("verifier") != nid or not art.get("producer"):
            continue
        allowed[aid] = art["producer"]
        allowed[art["producer"]] = art["producer"]
    on_red = verifier_node.get("on_red") or {}
    if not allowed and on_red.get("corrects"):
        return on_red["corrects"], state["nodes"][on_red["corrects"]]["produces"]
    if unit not in allowed:
        die(
            "verifier %s rejected unit %r, but it may only correct units it inspected: %s"
            % (nid, unit, ", ".join(sorted(allowed)) or "(none)"),
            2,
        )
    producer = allowed[unit]
    artifact = unit if unit in state["artifacts"] else state["nodes"][producer]["produces"]
    return producer, artifact


def consumed_by_green(state, producer_id, aid, version):
    """Nodes that already ran GREEN on an older version of this artifact.

    Rewriting something a committed node consumed is the ambiguous-overwrite case: it needs
    a stated reason, and the consumers must be flagged rather than silently invalidated.
    """
    stale = []
    for nid, node in state["nodes"].items():
        # a verifier inspects an artifact; it does not build on it. A new version re-arms it,
        # and a RED verdict is the thing that authorizes the correction in the first place.
        if nid == producer_id or node["status"] != "GREEN" or node["kind"] == "verifier":
            continue
        for attempt in node["attempts"]:
            if any(i["artifact"] == aid and i["version"] < version for i in attempt.get("inputs", [])):
                stale.append(nid)
                break
    return stale


def cmd_commit(args) -> "None":
    state = load(args)
    nid = args.node
    if nid not in state["nodes"]:
        die("no such node: %s" % nid, 4)
    node = state["nodes"][nid]
    if node["kind"] == "gate":
        die("node %s is a human gate — use `gate --status approved|rejected`" % nid, 3)
    if node["status"] != "RUNNING":
        die("node %s is %s, not RUNNING — dispatch it first" % (nid, node["status"]), 3)
    attempt = node["attempts"][-1]
    result = read_json(Path(args.result).expanduser(), "node result")
    errors = []
    validate_value(result, node["output_contract"], nid, errors)
    if errors:
        die("node %s result rejected by its own output contract:\n  - %s" % (nid, "\n  - ".join(errors)), 2)

    # a step is not green until its artifact is a real file at the declared path
    artifact_entry = None
    if node["produces"] and result.get("status") == "done":
        target = Path(attempt["artifact_target"])
        declared = Path(result["artifact_path"]).expanduser()
        if declared.resolve() != target.resolve():
            die(
                "node %s wrote artifact_path %s, but the envelope designated %s — one writer per path"
                % (nid, declared, target),
                2,
            )
        if not target.exists():
            die("node %s reported success but %s does not exist" % (nid, target), 2)
        art = state["artifacts"][node["produces"]]
        version = len(art["versions"]) + 1
        stale = consumed_by_green(state, nid, node["produces"], version)
        if stale and not args.supersedes:
            die(
                "%s@v%d is already consumed by %s. Rewriting output a committed node ran on needs "
                "--supersedes <reason>: state why the graph is changing an artifact it already used "
                "downstream. This flags those consumers instead of silently invalidating them."
                % (node["produces"], version - 1, ", ".join(sorted(stale))),
                3,
            )
        artifact_entry = {
            "version": version,
            "path": str(target.resolve()),
            "sha256": sha256_file(target),
            "type": art["type"],
            "producer": nid,
            "attempt": attempt["attempt"],
            "at": now(),
            "verified": not art.get("verifier"),
            "bytes": target.stat().st_size,
        }
        art["versions"].append(artifact_entry)
        if not art.get("verifier"):
            art["verified_version"] = version
        else:
            # a new version of a verified artifact invalidates the verdict and re-arms the verifier
            art["verified_version"] = None
            art["rejected"] = False
            verifier_node = state["nodes"][art["verifier"]]
            if verifier_node["id"] != nid and verifier_node["status"] == "GREEN":
                verifier_node["status"] = "PENDING"
            # consumers that already ran on an older version are stale, not silently wrong
            for other_id, other in state["nodes"].items():
                if other_id == nid or other["kind"] == "gate":
                    continue
                consumed = [i for a in other["attempts"] for i in a.get("inputs", [])
                            if i["artifact"] == node["produces"] and i["version"] < version]
                if consumed and other["status"] == "GREEN":
                    other["stale_input"] = "%s@v%d superseded by v%d" % (node["produces"], consumed[-1]["version"], version)
                    state["failures"].append({"node": other_id, "kind": "stale_input",
                                              "reason": other["stale_input"], "at": now()})
        record(state, "artifact_commit", node=nid, artifact=node["produces"], version=version,
               sha256=artifact_entry["sha256"], supersedes=args.supersedes,
               re_verify=bool(art.get("verifier")))

    verdict = result.get("verdict")
    node["artifact"] = artifact_entry
    attempt["status"] = "green" if result.get("status") == "done" else "failed"
    attempt["ended"] = now()
    attempt["result_file"] = str(Path(args.result).expanduser().resolve())
    attempt["summary"] = result.get("summary")
    attempt["artifact_version"] = artifact_entry["version"] if artifact_entry else None

    if node["kind"] == "verifier":
        subjects = [r["artifact"] for r in node["requires"] if state["artifacts"][r["artifact"]].get("verifier") == nid]
        if verdict == "green":
            for aid in subjects:
                subj_art = state["artifacts"][aid]
                subj_art["verified_version"] = subj_art["versions"][-1]["version"]
                subj_art["versions"][-1]["verified"] = True
                subj_art["rejected"] = False
                state["nodes"][subj_art["producer"]]["correction"] = None
                record(state, "verified", node=nid, subject=subj_art["producer"], artifact=aid,
                       version=subj_art["verified_version"])
            node["status"] = "GREEN"
        elif verdict == "red":
            subject_id, subject_art_id = resolve_unit(state, node, result["unit"])
            subject = state["nodes"][subject_id]
            subj_art = state["artifacts"][subject_art_id]
            review = {
                "unit": result["unit"],
                "reason": result["reason"],
                "evidence": result.get("evidence", []),
                "scope": result["scope"],
                "verdict_artifact": {"artifact": node["produces"],
                                     "version": artifact_entry["version"],
                                     "path": artifact_entry["path"]},
                "verified_artifact": {
                    "artifact": subject_art_id,
                    "version": subj_art["versions"][-1]["version"],
                    "path": subj_art["versions"][-1]["path"],
                },
                "at": now(),
            }
            subject["correction"] = review
            subject["status"] = "RED"
            subj_art["rejected"] = True
            subj_art["verified_version"] = None
            if subj_art["versions"]:
                subj_art["versions"][-1]["verified"] = False
                subj_art["versions"][-1]["rejected"] = True
            node["status"] = "GREEN"
            state["failures"].append({"node": subject_id, "kind": "verification",
                                      "reason": review["reason"], "unit": review["unit"], "at": now()})
            record(state, "red", node=nid, subject=subject_id, unit=review["unit"], reason=review["reason"])
        else:
            die("verifier %s returned verdict %r — must be green or red" % (nid, verdict), 2)
    elif result.get("status") == "done":
        node["status"] = "GREEN"
        node["correction"] = None
    else:
        node["status"] = "RED"
        state["failures"].append({"node": nid, "kind": "execution",
                                  "reason": result.get("summary", ""), "at": now()})
        record(state, "failed", node=nid, reason=result.get("summary", ""))

    if node["status"] == "RED":
        caps = state["graph"]["caps"]
        if node["attempt_count"] >= caps["max_attempts"]:
            node["status"] = "ESCALATED"
            node["blocked_by"] = "attempt cap reached (%d) — the plan, not the unit, is at fault" % caps["max_attempts"]
            record(state, "escalate", node=nid, reason=node["blocked_by"])
    refresh(state)
    save(args, state)
    out(state, {"node": nid, "status": node["status"],
                "artifact": node["artifact"], "graph_status": state["graph"]["status"],
                "next_ready": ready_nodes(state)})


# ------------------------------------------------------------------ control


def cmd_escalate(args) -> "None":
    state = load(args)
    nid = args.node
    if nid not in state["nodes"]:
        die("no such node: %s" % nid, 4)
    node = state["nodes"][nid]
    node["status"] = "ESCALATED"
    node["blocked_by"] = args.reason
    state["failures"].append({"node": nid, "kind": "escalation", "reason": args.reason, "at": now()})
    record(state, "escalate", node=nid, reason=args.reason)
    refresh(state)
    state["graph"]["status"] = "needs_plan_review"
    save(args, state)
    out(state, {
        "node": nid, "status": "ESCALATED", "reason": args.reason,
        "next": "Return to graph design: fix the split, the check, or the brief — do not spawn another attempt.",
    })


def commit_decision(state, gate_node, decision: dict):
    """Write the human's decision as a versioned artifact, so downstream nodes can require it.

    A gate that produces a decision artifact turns a mid-graph pause into a real data
    dependency: `dispatch` will not release its consumers until the human answers.
    """
    aid = gate_node.get("produces")
    if not aid:
        return None
    art = state["artifacts"][aid]
    version = len(art["versions"]) + 1
    path = Path(state["graph"]["root"]) / "artifacts" / ("%s.v%d.json" % (aid, version))
    write_json(path, decision)
    entry = {
        "version": version,
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "type": art.get("type", "decision"),
        "producer": gate_node["id"],
        "attempt": 0,
        "at": now(),
        "verified": True,
        "bytes": path.stat().st_size,
    }
    art["versions"].append(entry)
    art["verified_version"] = version
    art["rejected"] = decision["status"] == "rejected"
    gate_node["artifact"] = entry
    record(state, "gate_decision", node=gate_node["id"], artifact=aid, version=version,
           status=decision["status"])
    return entry


def cmd_reopen(args) -> "None":
    """Re-open committed work: the graph accepted something and a human says it is wrong.

    This is the only way a GREEN node runs again, and it is deliberately explicit: the node
    goes RED with a reason, its artifact loses verification, and every consumer that already
    ran on it is flagged stale. The graph returns to plan review — nothing is silently
    re-run, and the rewrite still needs --supersedes at commit.
    """
    state = load(args)
    nid = args.node
    if nid not in state["nodes"]:
        die("no such node: %s" % nid, 4)
    node = state["nodes"][nid]
    if node["status"] != "GREEN":
        die("node %s is %s — reopen only applies to committed (GREEN) work" % (nid, node["status"]), 3)
    aid = node.get("produces")
    art = state["artifacts"][aid]
    consumers = consumed_by_green(state, nid, aid, len(art["versions"]) + 1)
    if consumers and not args.user_approval:
        die(
            "%s is already consumed by %s — re-opening it needs --user-approval quoting the user's words"
            % (aid, ", ".join(sorted(consumers))),
            3,
        )
    art["verified_version"] = None
    art["reopened"] = {"reason": args.reason, "at": now(), "by": args.user_approval}
    if art["versions"]:
        art["versions"][-1]["verified"] = False
    node["status"] = "RED"
    node["blocked_by"] = "reopened: %s" % args.reason
    node["correction"] = {"unit": aid, "reason": args.reason, "evidence": [], "scope": args.reason,
                          "reopened": True, "at": now()}
    state["failures"].append({"node": nid, "kind": "reopened", "reason": args.reason, "at": now()})
    state["decisions"].append({"at": now(), "decision": "reopened %s" % nid, "evidence": args.user_approval,
                               "note": args.reason})
    if consumers:
        for consumer in consumers:
            state["nodes"][consumer]["stale_input"] = "%s reopened: %s" % (aid, args.reason)
    record(state, "reopen", node=nid, artifact=aid, reason=args.reason, consumers=sorted(consumers))
    refresh(state)
    if consumers:
        state["graph"]["status"] = "needs_plan_review"
    save(args, state)
    out(state, {
        "node": nid, "status": node["status"], "stale_consumers": sorted(consumers),
        "next": "dispatch %s, then commit with --supersedes <reason>" % nid,
    })


def cmd_gate(args) -> "None":
    state = load(args)
    gate = state["graph"]["gate"]
    waiting_on = []
    for nid, node in state["nodes"].items():
        if node["kind"] != "gate":
            continue
        for req in node["requires"]:
            version, why = input_view(state, node, req["artifact"], req["required"])
            if version is None and req["required"]:
                waiting_on.append(why)
    if args.status == "approved":
        if waiting_on:
            die("gate cannot open: %s" % "; ".join(waiting_on), 3)
        lane = (args.lane or gate["lane"] or "").lower()
        hard = ("hard" in lane) or ("irreversible" in lane) or ("does not open" in lane)
        if hard and not args.user_approval:
            die(
                "lane %r is hard to reverse: an explicit --user-approval quoting the user's yes is required. "
                "Never approximate approval from model confidence." % gate["lane"],
                3,
            )
        if not args.user_approval:
            die("an approved gate needs --user-approval quoting the user's yes", 3)
        gate["status"] = "approved"
        gate["approvals"].append({"at": now(), "user": args.user_approval, "note": args.note})
        state["decisions"].append({"at": now(), "decision": "gate approved", "evidence": args.user_approval,
                                   "note": args.note})
        for node in state["nodes"].values():
            if node["kind"] != "gate":
                continue
            node["status"] = "GREEN"
            node["blocked_by"] = None
            commit_decision(state, node, {
                "node": node["id"], "status": "approved", "lane": gate["lane"], "action": gate["action"],
                "user_approval": args.user_approval, "note": args.note, "at": now(),
            })
        record(state, "gate_approved", lane=gate["lane"])
    elif args.status == "rejected":
        if not args.user_approval:
            die("a rejected gate needs --user-approval quoting the user's words", 3)
        gate["status"] = "rejected"
        gate["approvals"].append({"at": now(), "user": args.user_approval, "note": args.note, "rejected": True})
        state["decisions"].append({"at": now(), "decision": "gate rejected", "evidence": args.user_approval,
                                   "note": args.note})
        for node in state["nodes"].values():
            if node["kind"] != "gate":
                continue
            node["status"] = "BLOCKED"
            node["blocked_by"] = "human gate rejected"
            commit_decision(state, node, {
                "node": node["id"], "status": "rejected", "lane": gate["lane"], "action": gate["action"],
                "user_approval": args.user_approval, "note": args.note, "at": now(),
            })
        record(state, "gate_rejected", lane=gate["lane"])
    else:
        gate["status"] = "waiting"
        record(state, "gate_waiting", lane=gate["lane"], waiting_on=waiting_on)
    refresh(state)
    if state["graph"]["status"] == "running" and gate["status"] == "approved":
        done = [n for n in state["nodes"].values() if n["kind"] != "gate"]
        if done and all(n["status"] == "GREEN" for n in done):
            state["graph"]["status"] = "done"
    save(args, state)
    out(state, {"gate": gate, "waiting_on": waiting_on, "graph_status": state["graph"]["status"]})


def cmd_learn(args) -> "None":
    root = resolve_root(args)
    path = constraints_file(args)
    data = read_json(path, "constraints store") if path.exists() else {"schema": "graph-engineer/constraints/1",
                                                                       "constraints": []}
    state = load(args)
    node = state["nodes"].get(args.node)
    if node is None:
        die("no such node: %s" % args.node, 4)
    if args.promote:
        if node["status"] != "GREEN":
            die("only an accepted (GREEN) outcome may promote a constraint; %s is %s" % (args.node, node["status"]), 3)
        if not args.user_approval:
            die("promoting a constraint to a permanent rule needs --user-approval", 3)
    entry = {
        "constraint": args.constraint,
        "status": "active" if args.promote else "proposed",
        "from": {"node": args.node, "graph": state["graph"]["id"]},
        "evidence": args.evidence,
        "at": now(),
        "approved_by": args.user_approval,
    }
    data["constraints"].append(entry)
    write_json(path, data)
    if args.promote:
        state["constraints"]["graph"].append(args.constraint)
    record(state, "learn", constraint=args.constraint, status=entry["status"], node=args.node)
    save(args, state)
    out(state, {
        "constraint": entry,
        "store": str(path.resolve()),
        "note": "active constraints are rendered into every later envelope, including future graphs under this root"
        if args.promote else
        "proposed only — it constrains nothing until a human promotes it (--promote --user-approval)",
    })


def cmd_validate(args) -> "None":
    state = load(args)
    problems = []
    if state.get("schema") != SCHEMA:
        problems.append("state schema %r != %r" % (state.get("schema"), SCHEMA))
    for nid, node in state["nodes"].items():
        if node["status"] == "RUNNING" and not node["attempts"]:
            problems.append("%s is RUNNING with no attempt record" % nid)
        if node["status"] == "GREEN" and node["produces"]:
            art = state["artifacts"][node["produces"]]
            if node["artifact"] is None or not Path(node["artifact"]["path"]).exists():
                problems.append("%s is GREEN but its artifact file is missing" % nid)
            if art.get("verifier") and art.get("verified_version") is None and node["kind"] != "verifier":
                problems.append("%s is GREEN but %s is unverified" % (nid, node["produces"]))
        for req in node["requires"]:
            if req["artifact"] not in state["artifacts"]:
                problems.append("%s requires unknown artifact %s" % (nid, req["artifact"]))
    used = []
    for nid, node in state["nodes"].items():
        for attempt in node["attempts"]:
            used.append((attempt.get("artifact_target"), nid))
    paths = [p for p, _ in used if p]
    if len(paths) != len(set(paths)) and len({n for n, _ in used}) > 1:
        dupes = sorted({p for p in paths if paths.count(p) > 1})
        problems.append("two nodes wrote the same artifact path: %s" % ", ".join(dupes))
    counts = {}
    for nid, node in state["nodes"].items():
        if node["attempt_count"] > state["graph"]["caps"]["max_attempts"]:
            problems.append("%s exceeded the attempt cap" % nid)
        counts[nid] = node["attempt_count"]
    if problems:
        out(state, {"ok": False, "problems": problems}, 2)
    out(state, {"ok": True, "nodes": len(state["nodes"]), "attempts": counts,
                "spawns_used": state["graph"]["spawns_used"]})


# --------------------------------------------------------------------- status


ORDER = ["RUNNING", "READY", "PENDING", "BLOCKED", "RED", "ESCALATED", "WAITING_HUMAN", "GREEN"]


def cmd_status(args) -> "None":
    state = load(args)
    refresh(state)
    if args.json:
        out(state, {"status": state["graph"]["status"],
                    "graph": state["graph"],
                    "nodes": {n: {"kind": v["kind"], "status": v["status"], "attempts": v["attempt_count"],
                                  "artifact": (v["artifact"] or {}).get("version"),
                                  "waiting": v.get("blocked_by"), "stale_input": v.get("stale_input")}
                              for n, v in state["nodes"].items()},
                    "artifacts": {a: {"verified_version": v.get("verified_version"),
                                      "latest": v["versions"][-1]["version"] if v["versions"] else None}
                                  for a, v in state["artifacts"].items()},
                    "gate": state["graph"]["gate"],
                    "failures": state["failures"][-5:]})
    g = state["graph"]
    lines = ["GRAPH: %s  [%s]" % (g["id"], g["status"]), "goal: %s" % g["goal"]]
    if any(n["kind"] == "gate" for n in state["nodes"].values()):
        lines.append("GATE: %s (lane: %s) — action: %s" % (g["gate"]["status"], g["gate"]["lane"],
                                                           g["gate"]["action"]))
    lines.append("caps: attempts<=%d  spawn<=%d  budget %d/%d" % (
        g["caps"]["max_attempts"], g["caps"]["spawn_cap"], g["spawns_used"], g["caps"]["spawn_budget"]))
    for status in ORDER:
        members = [(n, v) for n, v in state["nodes"].items() if v["status"] == status]
        if not members:
            continue
        lines.append("")
        lines.append(status)
        for nid, node in members:
            art = ""
            if node["produces"]:
                a = state["artifacts"][node["produces"]]
                latest = a["versions"][-1]["version"] if a["versions"] else 0
                if latest:
                    art = "  artifact: %s@v%d%s" % (node["produces"], latest,
                                                    "" if a.get("verified_version") else " (unverified)")
                else:
                    art = "  artifact: %s (not produced yet)" % node["produces"]
            if status == "RUNNING":
                art += "  attempt %d" % node["attempt_count"]
            mark = {"GREEN": "✓", "RUNNING": "→", "WAITING_HUMAN": "★"}.get(status, "○")
            lines.append("  %s %-22s%s%s" % (mark, nid, art,
                                             "" if not node.get("blocked_by") else "  — " + node["blocked_by"]))
            if node.get("stale_input"):
                lines.append("      stale input: %s" % node["stale_input"])
    if state["failures"]:
        lines += ["", "FAILURES (last 5)"]
        for f in state["failures"][-5:]:
            lines.append("  %s %s: %s" % (f["kind"], f["node"], f["reason"]))
    print("\n".join(lines))


# ------------------------------------------------------------------------ cli


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="graph_state", description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".graph", help="graph root directory (default: .graph)")
    parser.add_argument("--graph", default=None, help="graph id (needed when the root holds several)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="validate a graph spec and create state.json")
    p.add_argument("--spec", required=True)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("status", help="render committed execution state")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("dispatch", help="emit delegate_task round payloads for READY nodes")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--tasks-file", default=None)
    p.set_defaults(func=cmd_dispatch)

    p = sub.add_parser("commit", help="validate a node result and commit it to Graph State")
    p.add_argument("--node", required=True)
    p.add_argument("--result", required=True, help="the child's returned JSON (contract)")
    p.add_argument("--supersedes", default=None, help="reason for revising an already-verified artifact")
    p.set_defaults(func=cmd_commit)

    p = sub.add_parser("escalate", help="stop retrying a node and return control to graph design")
    p.add_argument("--node", required=True)
    p.add_argument("--reason", required=True)
    p.set_defaults(func=cmd_escalate)

    p = sub.add_parser("reopen", help="re-open committed work that a human says is wrong")
    p.add_argument("--node", required=True)
    p.add_argument("--reason", required=True)
    p.add_argument("--user-approval", default=None, help="required when consumers already ran on it")
    p.set_defaults(func=cmd_reopen)

    p = sub.add_parser("gate", help="record the human gate state (never opens on confidence)")
    p.add_argument("--status", choices=["waiting", "approved", "rejected"], required=True)
    p.add_argument("--lane", default=None)
    p.add_argument("--user-approval", default=None, help="quote of the user's explicit yes")
    p.add_argument("--note", default=None)
    p.set_defaults(func=cmd_gate)

    p = sub.add_parser("learn", help="propose or (with approval) promote a learning constraint")
    p.add_argument("--constraint", required=True)
    p.add_argument("--node", required=True)
    p.add_argument("--evidence", default=None)
    p.add_argument("--promote", action="store_true")
    p.add_argument("--user-approval", default=None)
    p.set_defaults(func=cmd_learn)

    p = sub.add_parser("validate", help="check state invariants")
    p.set_defaults(func=cmd_validate)

    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        # `graph_state.py status | head` closes the pipe early; exit quietly instead of
        # dumping a traceback (Windows raises this as OSError EINVAL on flush)
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        sys.exit(0)
