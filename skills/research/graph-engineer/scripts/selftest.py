#!/usr/bin/env python3
"""selftest.py — the seven execution scenarios graph-engineer must satisfy.

This is executable documentation of the state machine, not a unit-test suite. It drives
the real CLI (subprocess) with simulated isolated children: a "child" only ever sees the
envelope the orchestrator hands it, writes its artifact, and returns its contract JSON.

    python scripts/selftest.py            # run all scenarios
    python scripts/selftest.py 4          # run one

Scenario -> invariant:

  1  three independent workers -> all READY in one round; verifier gates merge; gate last
  2  A -> B                     -> B cannot be dispatched before A's artifact is committed
  3  diamond A -> {B,C} -> D    -> B and C dispatch together; D waits for both committed
  4  verifier rejects B         -> only B returns; C does not rerun; D waits for B green
  5  attempts exhausted         -> ESCALATED, no infinite retry, graph returns to design
  6  sequential but no data     -> the edge cannot even be written (init rejects it)
  7  irreversible action        -> the hard-to-reverse lane never opens on its own
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "graph_state.py"
FAILURES = []


# ------------------------------------------------------------------ harness


def run(args, root, expect=0):
    cmd = [sys.executable, str(SCRIPT), "--root", str(root)] + args
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != expect:
        raise AssertionError(
            "command failed: %s\nexit=%d (expected %d)\nstdout:\n%s\nstderr:\n%s"
            % (" ".join(args), proc.returncode, expect, proc.stdout, proc.stderr)
        )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return proc.stdout


def dispatch(root, graph=None, limit=None):
    args = ["dispatch"]
    if graph:
        args += ["--graph", graph]
    if limit is not None:
        args += ["--limit", str(limit)]
    return run(args, root)


def dispatch_one(root, node, graph=None):
    """Dispatch, assert exactly `node` came back, return the round payload."""
    payload = dispatch(root, graph)
    got = [b["node"] for b in payload["bindings"]]
    assert got == [node], "expected only %s to be READY, got %s" % (node, got)
    return payload


def commit(root, node, result, graph=None, expect=0, supersedes=None):
    path = root / ("result-%s.json" % node)
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    args = ["commit", "--node", node, "--result", str(path)]
    if supersedes:
        args += ["--supersedes", supersedes]
    if graph:
        args = ["--graph", graph] + args
    return run(args, root, expect=expect)


def run_g(root, graph, args, expect=0):
    return run(["--graph", graph] + list(args), root, expect=expect)


def envelope_of(root, node, attempt=1, graph=None):
    base = root / (graph or "") if graph else root
    for path in sorted(base.glob("*/envelopes/%s.a%d.json" % (node, attempt))):
        return json.loads(path.read_text(encoding="utf-8"))
    raise AssertionError("no envelope for %s.a%d under %s" % (node, attempt, base))


def child_ok(root, node, payload=None, attempt=1, graph=None):
    """Simulate an isolated child: read the envelope, write artifact + contract, return."""
    env = envelope_of(root, node, attempt, graph)
    target = Path(env["writer"]["path"])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# %s attempt %d\n" % (node, attempt), encoding="utf-8")
    result = {
        "node": node,
        "status": "done",
        "summary": "wrote %s" % target.name,
        "artifact_path": str(target),
        "evidence": ["selftest"],
    }
    result.update(payload or {})
    Path(env["return_file"]).parent.mkdir(parents=True, exist_ok=True)
    Path(env["return_file"]).write_text(json.dumps(result), encoding="utf-8")
    return result


def write_spec(root, spec, name="spec.json"):
    path = root / name
    path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    return str(path)


def base_contract(extra_required=(), extra_props=None, kind="worker"):
    props = {
        "node": {"type": "string"},
        "status": {"type": "string", "enum": ["done", "failed"]},
        "summary": {"type": "string", "minLength": 1},
        "artifact_path": {"type": "string"},
        "evidence": {"type": "array", "items": {"type": "string"}},
    }
    required = ["node", "status", "summary", "artifact_path"] + list(extra_required)
    if kind == "verifier":
        props.update({
            "verdict": {"type": "string", "enum": ["green", "red"]},
            "unit": {"type": "string"},
            "reason": {"type": "string"},
            "scope": {"type": "string"},
        })
        required += ["verdict", "unit", "reason", "scope"]
    props.update(extra_props or {})
    return {"type": "object", "properties": props, "required": required}


def node(nid, kind, requires, produces, goal=None, green=None, lens=None, on_red=None):
    entry = {
        "id": nid,
        "kind": kind,
        "goal": goal or ("do %s" % nid),
        "green_condition": green or ("%s produces its artifact and reports done" % nid),
        "requires": [{"artifact": a} for a in requires],
        "produces": produces,
        "output_contract": base_contract(kind=kind),
    }
    if lens:
        entry["lens"] = lens
    if on_red:
        entry["on_red"] = on_red
    return entry


def scenario(number, title):
    def wrap(fn):
        def inner(tmp):
            try:
                fn(tmp)
                print("  PASS  %d. %s" % (number, title))
            except AssertionError as exc:
                FAILURES.append("%d. %s -> %s" % (number, title, exc))
                print("  FAIL  %d. %s\n        %s" % (number, title, exc))
        inner.__name__ = fn.__name__
        return inner
    return wrap


# ---------------------------------------------------------------- scenarios


@scenario(1, "three independent workers run in one round, verifier gates merge, gate last")
def s1(root):
    findings = ["findings-a", "findings-b", "findings-c"]
    spec = {
        "graph": {"id": "s1", "goal": "audit three subsystems",
                  "gate": {"lane": "reversible, wide", "action": "publish report"}},
        "artifacts": {
            "seed-notes": {"type": "source", "seed": True, "path": str(root / "seed.md")},
            **{f: {"type": "findings", "producer": "w" + f[-1], "verifier": "verify"} for f in findings},
            "verdict": {"type": "verdict", "producer": "verify"},
            "report": {"type": "report", "producer": "merge"},
        },
        "nodes": [
            node("w" + f[-1], "worker", ["seed-notes"], f, lens="subsystem %s" % f[-1]) for f in findings
        ] + [
            node("verify", "verifier", findings, "verdict", lens="reproducible evidence"),
            node("merge", "code", findings, "report", green="one report exists"),
            {"id": "gate-1", "kind": "gate", "requires": [{"artifact": "report"}],
             "goal": "approve publish", "green_condition": "human says yes"},
        ],
    }
    (root / "seed.md").write_text("seed", encoding="utf-8")
    run(["init", "--spec", write_spec(root, spec)], root)

    round1 = dispatch(root)
    assert len(round1["round_tasks"]) == 3, "expected 3 workers in round 1, got %d" % len(round1["round_tasks"])
    assert {b["node"] for b in round1["bindings"]} == {"wa", "wb", "wc"}, round1["bindings"]
    for nid in ("wa", "wb", "wc"):
        commit(root, nid, child_ok(root, nid))
    st = run(["status", "--json"], root)
    assert st["nodes"]["verify"]["status"] == "READY", st["nodes"]["verify"]
    assert st["nodes"]["merge"]["status"] == "PENDING", "merge must wait for verification: %s" % st["nodes"]["merge"]

    d2 = dispatch(root)
    assert [b["node"] for b in d2["bindings"]] == ["verify"], d2["bindings"]
    commit(root, "verify", child_ok(root, "verify", {"verdict": "green", "unit": "findings-a",
                                                     "reason": "all accepted", "scope": "none"}))
    st = run(["status", "--json"], root)
    assert st["nodes"]["merge"]["status"] == "READY", "merge must unlock after verification"
    d3 = dispatch(root)
    assert d3["local_nodes"] == ["merge"], "merge is a code node: the orchestrator runs it, not a spawn"
    commit(root, "merge", child_ok(root, "merge"))
    st = run(["status", "--json"], root)
    assert st["graph"]["status"] == "gated", st["graph"]["status"]
    assert st["nodes"]["gate-1"]["status"] == "WAITING_HUMAN"

    # the learning edge: an accepted outcome may propose a constraint, a human promotes it,
    # and every later envelope under this root receives it
    run_g(root, "s1", ["learn", "--constraint", "findings cite file:line",
                       "--node", "verify", "--promote", "--user-approval", "\"yes, make it a rule\""])
    assert run_g(root, "s1", ["validate"])["ok"] is True
    spec2 = {
        "graph": {"id": "s1b", "goal": "a later run"},
        "artifacts": {"z": {"type": "report", "producer": "only"}},
        "nodes": [node("only", "worker", [], "z")],
    }
    run(["init", "--spec", write_spec(root, spec2, "spec2.json")], root)
    run_g(root, "s1b", ["dispatch"])
    env = json.loads((root / "s1b" / "envelopes" / "only.a1.json").read_text(encoding="utf-8"))
    assert "findings cite file:line" in env["constraints"], env["constraints"]


@scenario(2, "A -> B: B is not dispatchable before A's artifact is committed")
def s2(root):
    spec = {
        "graph": {"id": "s2", "goal": "two stage"},
        "artifacts": {
            "x": {"type": "findings", "producer": "a"},
            "y": {"type": "report", "producer": "b"},
        },
        "nodes": [node("a", "worker", [], "x"), node("b", "worker", ["x"], "y")],
    }
    run(["init", "--spec", write_spec(root, spec)], root)
    first = dispatch(root)
    assert [b["node"] for b in first["bindings"]] == ["a"], first["bindings"]
    st = run(["status", "--json"], root)
    assert st["nodes"]["b"]["status"] == "PENDING", st["nodes"]["b"]
    assert "no committed version yet" in st["nodes"]["b"]["waiting"], st["nodes"]["b"]["waiting"]
    commit(root, "a", child_ok(root, "a"))
    second = dispatch(root)
    assert [b["node"] for b in second["bindings"]] == ["b"], second["bindings"]


@scenario(3, "diamond: B and C run together, D waits for both committed artifacts")
def s3(root):
    spec = {
        "graph": {"id": "s3", "goal": "diamond"},
        "artifacts": {
            "a": {"type": "plan", "producer": "split"},
            "b": {"type": "findings", "producer": "wa"},
            "c": {"type": "findings", "producer": "wc"},
            "d": {"type": "report", "producer": "merge"},
        },
        "nodes": [node("split", "splitter", [], "a"), node("wa", "worker", ["a"], "b"),
                  node("wc", "worker", ["a"], "c"), node("merge", "code", ["b", "c"], "d")],
    }
    run(["init", "--spec", write_spec(root, spec)], root)
    dispatch_one(root, "split")
    commit(root, "split", child_ok(root, "split"))
    r2 = dispatch(root, limit=1)
    assert [b["node"] for b in r2["bindings"]] == ["wa"], r2["bindings"]
    assert r2["deferred_to_next_round"] == ["wc"], "spawn cap must defer, not oversubscribe: %s" % r2
    assert [b["node"] for b in dispatch(root)["bindings"]] == ["wc"], "the deferred node runs next round"
    commit(root, "wa", child_ok(root, "wa"))
    st = run(["status", "--json"], root)
    assert st["nodes"]["merge"]["status"] == "PENDING", "D must wait for C: %s" % st["nodes"]["merge"]
    commit(root, "wc", child_ok(root, "wc"))
    r3 = dispatch(root)
    assert r3["local_nodes"] == ["merge"], r3
    env = envelope_of(root, "merge")
    assert {i["artifact"] for i in env["inputs"]} == {"b", "c"}, "D must receive both committed artifacts"
    assert all(i["version"] == 1 for i in env["inputs"])
    commit(root, "merge", child_ok(root, "merge"))

    # reopening committed work is the only way a GREEN node runs again, and it may not be
    # silent: the reason is recorded, the consumers are flagged, and the rewrite needs --supersedes
    run_g(root, "s3", ["reopen", "--node", "wa", "--reason", "evidence was wrong",
                       "--user-approval", "\"re-open it\""])
    st = run(["status", "--json"], root)
    assert st["graph"]["status"] == "needs_plan_review", st["graph"]["status"]
    assert st["nodes"]["merge"]["stale_input"], "the consumer of the reopened artifact must be flagged"
    dispatch_one(root, "wa")
    commit(root, "wa", child_ok(root, "wa", attempt=2), graph="s3", expect=3)   # refused: no reason given
    st = run(["status", "--json"], root)
    assert st["nodes"]["wa"]["status"] == "RUNNING", "a refused commit must change nothing"
    commit(root, "wa", child_ok(root, "wa", attempt=2), graph="s3", supersedes="evidence was wrong")
    st = run(["status", "--json"], root)
    assert st["artifacts"]["b"]["latest"] == 2, st["artifacts"]["b"]
    # no verifier is declared on `b`, so a fresh commit is trusted again — but the consumer
    # that ran on v1 is still flagged, and the graph stays in plan review
    assert st["nodes"]["merge"]["stale_input"], st["nodes"]["merge"]
    assert st["graph"]["status"] == "needs_plan_review", st["graph"]["status"]


@scenario(4, "verifier rejects B: only B returns, C does not rerun, D waits for B green")
def s4(root):
    findings = ["findings-b", "findings-c"]
    spec = {
        "graph": {"id": "s4", "goal": "correct one unit"},
        "artifacts": {
            **{f: {"type": "findings", "producer": "w" + f[-1], "verifier": "verify"} for f in findings},
            "verdict": {"type": "verdict", "producer": "verify"},
            "report": {"type": "report", "producer": "merge"},
        },
        "nodes": [node("wb", "worker", [], "findings-b"), node("wc", "worker", [], "findings-c"),
                  node("verify", "verifier", findings, "verdict", lens="kill weak findings"),
                  node("merge", "code", findings, "report")],
    }
    run(["init", "--spec", write_spec(root, spec)], root)
    first = dispatch(root)
    assert {b["node"] for b in first["bindings"]} == {"wb", "wc"}, first["bindings"]
    commit(root, "wb", child_ok(root, "wb"))
    commit(root, "wc", child_ok(root, "wc"))
    dispatch_one(root, "verify")
    commit(root, "verify", child_ok(root, "verify", {
        "verdict": "red", "unit": "findings-b", "reason": "no reproducible evidence",
        "scope": "fix findings-b only", "evidence": ["claim without source: line 3"]}))
    st = run(["status", "--json"], root)
    assert st["nodes"]["wb"]["status"] == "READY", "B must return for correction: %s" % st["nodes"]["wb"]
    assert st["nodes"]["wc"]["status"] == "GREEN", "C must not rerun"
    assert st["nodes"]["merge"]["status"] == "PENDING", st["nodes"]["merge"]
    d = dispatch(root)
    assert [b["node"] for b in d["bindings"]] == ["wb"], "only the failed unit returns: %s" % d["bindings"]
    env = envelope_of(root, "wb", attempt=2)
    assert env["correction"]["unit"] == "findings-b", "correction envelope must carry the verdict"
    assert env["correction"]["evidence"] == ["claim without source: line 3"]
    assert env["correction"]["verified_artifact"]["version"] == 1
    commit(root, "wb", child_ok(root, "wb", attempt=2))
    st = run(["status", "--json"], root)
    assert st["nodes"]["verify"]["status"] == "READY", "the verifier re-arms on a new version"
    dispatch_one(root, "verify")
    commit(root, "verify", child_ok(root, "verify", {"verdict": "green", "unit": "findings-b",
                                                     "reason": "fixed", "scope": "none"}, attempt=2))
    st = run(["status", "--json"], root)
    assert st["nodes"]["merge"]["status"] == "READY", "D unlocks only after corrected B is GREEN"
    assert st["artifacts"]["findings-b"]["latest"] == 2, st["artifacts"]["findings-b"]


@scenario(5, "a node that fails past the cap escalates to graph design instead of retrying")
def s5(root):
    spec = {
        "graph": {"id": "s5", "goal": "cap", "caps": {"max_attempts": 2}},
        "artifacts": {"x": {"type": "findings", "producer": "a"},
                      "y": {"type": "report", "producer": "b"}},
        "nodes": [node("a", "worker", [], "x"), node("b", "code", ["x"], "y")],
    }
    run(["init", "--spec", write_spec(root, spec)], root)
    for attempt in (1, 2):
        dispatch(root)
        commit(root, "a", {"node": "a", "status": "failed", "summary": "tool failure",
                           "artifact_path": "", "evidence": []})
    st = run(["status", "--json"], root)
    assert st["nodes"]["a"]["status"] == "ESCALATED", st["nodes"]["a"]
    assert st["graph"]["status"] == "needs_plan_review", st["graph"]["status"]
    assert st["nodes"]["b"]["status"] == "BLOCKED", "downstream of a dead dependency must block: %s" % st["nodes"]["b"]
    d = dispatch(root)
    assert d["bindings"] == [], "no further spawns after escalation"
    run(["escalate", "--node", "a", "--reason", "split is wrong"], root)


@scenario(6, "a sequential-looking pair with no data crossing cannot be written down")
def s6(root):
    spec = {
        "graph": {"id": "s6", "goal": "fake edge"},
        "artifacts": {"x": {"type": "findings", "producer": "a"},
                      "y": {"type": "report", "producer": "b"}},
        "nodes": [node("a", "worker", [], "x"),
                  dict(node("b", "worker", [], "y"), depends_on=["a"])],
    }
    spec_path = write_spec(root, spec)
    proc = subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), "init", "--spec", spec_path],
                          capture_output=True, text=True)
    assert proc.returncode == 2, "init must reject an ordering-only edge, got %d" % proc.returncode
    assert "unknown key" in proc.stderr and "depends_on" in proc.stderr, proc.stderr

    spec["nodes"][1] = node("b", "worker", ["missing-artifact"], "y")
    proc = subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), "init", "--spec",
                           write_spec(root, spec, "spec2.json")], capture_output=True, text=True)
    assert proc.returncode == 2 and "undeclared artifact" in proc.stderr, proc.stderr

    spec["artifacts"]["z"] = {"type": "findings", "producer": "a"}
    spec["nodes"][1] = node("b", "worker", ["z"], "y")
    proc = subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), "init", "--spec",
                           write_spec(root, spec, "spec3.json")], capture_output=True, text=True)
    assert proc.returncode == 2 and "producer" in proc.stderr, proc.stderr


@scenario(7, "an irreversible action stops at the gate, and nothing downstream runs on confidence")
def s7(root):
    spec = {
        "graph": {"id": "s7", "goal": "ship it",
                  "gate": {"lane": "hard to reverse", "action": "publish to production"}},
        "artifacts": {
            "x": {"type": "report", "producer": "a"},
            "decision": {"type": "decision", "ext": "json", "producer": "gate-1"},
            "shipped": {"type": "report", "producer": "publish"},
        },
        "nodes": [node("a", "worker", [], "x"),
                  {"id": "gate-1", "kind": "gate", "goal": "approve publish",
                   "green_condition": "explicit user yes",
                   "requires": [{"artifact": "x"}], "produces": "decision"},
                  node("publish", "code", ["decision"], "shipped")],
    }
    run(["init", "--spec", write_spec(root, spec)], root)
    dispatch_one(root, "a")
    commit(root, "a", child_ok(root, "a"))
    st = run(["status", "--json"], root)
    assert st["graph"]["status"] == "gated", st["graph"]["status"]
    assert st["graph"]["gate"]["lane"] == "hard to reverse"
    assert st["nodes"]["publish"]["status"] == "PENDING", "the gate must hold downstream work"
    assert "has not been answered yet" in st["nodes"]["publish"]["waiting"], st["nodes"]["publish"]["waiting"]
    assert dispatch(root)["bindings"] == [] and dispatch(root)["local_nodes"] == [], "nothing runs past an open gate"

    proc = subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), "gate", "--status", "approved"],
                          capture_output=True, text=True)
    assert proc.returncode == 3, "hard-to-reverse lane must not open on its own"
    assert "explicit --user-approval" in proc.stderr, proc.stderr

    run(["gate", "--status", "rejected", "--user-approval", "\"no, not like this\""], root)
    st = run(["status", "--json"], root)
    assert st["nodes"]["publish"]["status"] == "BLOCKED", st["nodes"]["publish"]

    run(["gate", "--status", "approved", "--user-approval", "\"yes, publish it\""], root)
    st = run(["status", "--json"], root)
    assert st["nodes"]["publish"]["status"] == "READY", "an explicit yes releases the graph"
    assert dispatch(root)["local_nodes"] == ["publish"], "the released node is dispatched"
    commit(root, "publish", child_ok(root, "publish"))
    st = run(["status", "--json"], root)
    assert st["graph"]["status"] == "done", st["graph"]["status"]


# --------------------------------------------------------------------- main


SCENARIOS = [s1, s2, s3, s4, s5, s6, s7]


def main(argv):
    wanted = [int(a) for a in argv[1:]] or list(range(1, len(SCENARIOS) + 1))
    print("graph-engineer execution scenarios (isolated workers, committed graph)")
    for number in wanted:
        tmp = Path(tempfile.mkdtemp(prefix="graph-selftest-%d-" % number))
        try:
            SCENARIOS[number - 1](tmp)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    if FAILURES:
        print("\n%d scenario(s) failed:" % len(FAILURES))
        for failure in FAILURES:
            print("  - %s" % failure)
        return 1
    print("\nall %d scenarios passed" % len(wanted))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
