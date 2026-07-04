---
name: abnahme
description: Independent acceptance check of a completed Auftrag. Use when an executor reports its verify gate passed, when a delegated task needs a verdict before the commander reviews it, or on /abnahme. Input is a Todoist task URL/ID or a path to an Auftrag contract file. Never run it inside the session that executed the work.
argument-hint: "<todoist-task-url | task-id | path/to/active.md>"
---

# Abnahme — the second key

*Abnahme* is German for acceptance testing — the inspection that is **not** performed by whoever built the thing. That's the whole point: **the executor never grades its own work.** Self-reports are framing-dependent; a fresh, adversarial examiner is not.

Position in the pipeline: gate passed (deterministic) → **Abnahme (independent verdict)** → commander's sampled review. The gate proves the checks ran; Abnahme proves the *contract* was met and nobody gamed the checks.

## Hard rules

| Rule | Detail |
|---|---|
| **Two-key** | Never verify work produced in this same session/context. If asked to, refuse and spawn the examiner instead — that's the design, not an inconvenience. |
| **Deterministic outranks opinion** | The examiner re-runs every `verify:` command itself. A failing command = RED, whatever the diff "looks like". Pasted output is never trusted. |
| **Verdict only** | Abnahme never fixes the work. Findings go in the verdict; repair is a new dispatch (or the same executor resumed) — otherwise the second key becomes a second builder. |
| **Green is Abnahme's alone** | Only this flow sets `agent:green`. Executors may self-report failure (blocked/red), never success. |

## Flow

**1. Assemble the dossier.** From the argument, gather:
- The **contract** (five boxes + frontmatter): from the Todoist task description (`find-tasks` / `fetch-object`) or the given file path.
- The **field report**: latest Todoist comments — the executor's "gate passed" comment should carry worktree path, branch, PR link, and evidence items. Also read `.claude/auftrag/state.json` in the worktree if reachable (gate attempt history).
- The **diff**: the worktree/branch/PR named in the report.

Missing pieces (no worktree path, no diff)? Report exactly what's missing and stop — an unverifiable delivery is itself a finding.

**2. Spawn the examiner.** Use the Agent tool with the plugin's `pruefer` agent (fresh context — that's the second key). Hand it: the contract verbatim, the worktree path/branch/PR, and the dossier. It re-runs verify, audits the diff against Target state and Boundaries, hunts for check-gaming, and returns a structured verdict (schema in the agent definition).

**3. Land the verdict.**
- **GREEN** → Todoist: remove `agent:running`, add `agent:green`; comment: the verdict summary + the `evidence:` items for the commander's ≤60-second review + acceptance bar reminder (`risk: irreversible` → full review; `reversible` → sampling).
- **RED** → remove `agent:running`, add `agent:red`; comment: each blocker with file/command references, plus the examiner's `failure_class`.

**4. Append the ledger line** to `~/.claude/auftrag/ledger.jsonl` (create dir if needed):

```json
{"ts": "<ISO date>", "id": "<task-slug>", "type": "delegate", "risk": "reversible",
 "verdict": "green|red", "failure_class": "brief-gap|silent-execution-error|check-gaming|flaky-verify|null",
 "blockers": 0, "contract_gaps": 1, "escalations": 0}
```

`contract_gaps` (things the contract itself left ambiguous, even on GREEN) is the disease-1-vs-disease-2 instrument — the monthly retro reads this file to rule which disease dominates. Don't skip it on green verdicts.

**5. Report to the commander**, staff-officer register: verdict first, then what's asked of them now (accept / redispatch / decide), then the 60-second evidence. If the verdict is GREEN and `risk: reversible`, say plainly whether this one falls inside or outside the sampling window (new task types: first 5 get full review).
