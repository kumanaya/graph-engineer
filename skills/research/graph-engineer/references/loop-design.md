# The Loop: Produce, Check, Correct, Repeat

A loop makes **one unit of work** correct without you. Four parts:

```text
produce → check → correct → repeat until green
```

The check is the whole thing. Without something that can fail the work while you are out of the room, you do not have a loop. You have a scheduler.

## Write the check first

Almost nobody does. The usual order is: build the work, bolt a review onto the end, and make the review another model looking at the output. Two optimists agreeing.

Write the condition before the work, and write it so a program could evaluate it:

| GREEN — a program can settle it | NOT A CHECK |
|--------------------------------|-------------|
| the test suite exits 0 | the output looks good |
| every claim carries a source line | the model says it is confident |
| the diff touches only the files listed in the plan | no errors were raised |
| every export present before the change still resolves after it | it seems complete |

**Absence of an error is not evidence of correctness.** Build a loop on “no errors were raised” and you get a system that confidently repeats a mistake until the budget runs out, with a clean log the whole way.

## Where the loop lives

The loop lives **inside** a box. The graph lives **between** boxes.

| Inside one box | Between boxes |
|----------------|---------------|
| produce, check, correct, repeat until green | split, fan out, verify, merge, gate, send back |

None of the right column is expressible from inside a single box. So you do not choose between loop and graph:

- A graph without loops in its boxes produces **unverified work in parallel** — worse than serially, because there is more of it.
- A loop without a graph around it is one very good step in a queue nobody designed.

## The ceiling

A loop makes one unit of work better. That is its entire job, and it is good at it.

It cannot decide which units exist, their order, or notice that two of the five steps never needed to wait for each other. So you get a very good agent running the wrong three steps, in the wrong order, one at a time: every step correct, the result still slow and still wrong-shaped. Tuning the loop will not fix it, because the fault is not inside any unit. That is the moment the graph layer starts paying for itself.

## Cap, then escalate to the plan

- **Max rounds** (default 3) **and a seen list.** Both. Without them, agents loop and burn budget.
- **When the cap hits, stop correcting.** A unit that fails three corrections is not failing; the plan that produced it is. The loop cannot see the plan. Escalate with the verdict, the reason and the evidence — then fix the split, the check, or the brief, not the unit.
- **A flaky check is not a verdict.** If a red is random or ambiguous, fix the check before spending another round on the work.

See `references/return-paths.md` for what travels back, and `references/node-types.md` for which nodes are model, code, or human.
