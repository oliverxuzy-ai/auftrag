# auftragstaktik

A Claude Code **plugin** for mission-command delegation: it presses you to think a delegation through *before* you hand it to an agent, then makes sure the agent **cannot silently fail** after you do.

## Where it comes from

**Auftragstaktik** (mission command) is the command doctrine the Prussian army beat into shape in the 19th century. Its foundation is Moltke's line:

> No plan survives contact with the enemy.

The conclusion: stop remote-controlling the front line. Say clearly what must be achieved and *why*, and which few lines must never be crossed — then hand the freedom of *how* to whoever has the freshest information.

Delegating to an agent is exactly this, and it matters more for agents: **they fail confidently** (silence ≠ success), and **they fill ambiguity toward the training-data average, not toward your context.** So the contract must be explicit at dispatch time — and, because no brief survives contact either, the contract must also be **enforced at runtime** by machinery the executor can't sweet-talk.

## The pipeline

```
/auftrag   contract-first briefing (five boxes; verify + evidence dual-track Done)
    │            └─ type routing: delegate / learn (prep only) / decide (staff memo only)
    ▼
dispatch   Todoist landing + WIP cap (3) + background worktree executor
    ▼
verify gate   Stop-hook runs the contract's verify commands — can't declare
    │         victory against a red check; gives up LOUDLY (RED) after N tries
    ▼
/abnahme   independent acceptance: fresh-context adversarial examiner (pruefer),
    │      re-runs checks, hunts check-gaming; only Abnahme may grant green
    ▼
/board     exception queue: blocked > red > green; you never poll
/catchup   O(1) re-entry into any one task
```

State machine, carried as Todoist labels: `agent:running → agent:blocked | agent:red | agent:green → done`. Executors may confess (blocked/red) but never self-certify (green).

## Repo layout

| Path | What it is |
|---|---|
| `.claude-plugin/` | Plugin + marketplace manifests |
| `skills/auftrag/` | The briefing interview (the original skill) + `references/` (grill heuristics, dispatch, lanes) |
| `skills/abnahme/` | Independent acceptance flow (the second key) |
| `skills/board/`, `skills/catchup/` | Exception queue + re-entry |
| `skills/todoist-sync/` | Bind a session to a Todoist task (`/start-todo` etc.) |
| `agents/pruefer.md` | The adversarial examiner subagent Abnahme spawns |
| `hooks/hooks.json`, `scripts/` | Stop/SubagentStop verify gate + optional notification fan-out |
| `CONCEPT.md` | Original concept doc (Chinese), kept as provenance |
| `docs/DESIGN.md` | v0 design decisions (the interview) |
| `docs/workflow-design.md` | The full pipeline design: pain-point critique, evidence, phased rollout |
| `INSTALL.md` | Plugin installation |

## Status

v0.2 — Phase 0+1 of `docs/workflow-design.md`: authoring (v0, battle-tested shape) + runtime enforcement (gate, Abnahme, board, catchup — new, expects its first dozen real missions). The interview itself remains pure prompt; all enforcement lives after dispatch. Ledger-driven retro (`/retro`) is Phase 2, deliberately not built until ~20 missions of data exist.
