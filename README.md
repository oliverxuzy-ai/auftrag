# auftragstaktik

A Claude Code skill named **`auftrag`**. It presses you to think a delegation through *before* you hand a task to an agent.

## Where it comes from

**Auftragstaktik** (mission command) is the command doctrine the Prussian army beat into shape in the 19th century. Its foundation is Moltke's line:

> No plan survives contact with the enemy.

The conclusion: stop remote-controlling the front line. Say clearly what must be achieved and *why*, and which few lines must never be crossed — then hand the freedom of *how* to whoever has the freshest information.

Delegating to an agent is exactly this. And it matters more for agents, because they have two failures a human report doesn't: **they fail confidently** (silence ≠ success), and **they fill ambiguity toward the training-data average, not toward your context.** So "when to stop and ask me" and "the red lines" have to be spelled out at the moment you delegate.

## What the skill does

It guides you to fill out a **five-box Auftrag**, lands it in Todoist, then asks whether to dispatch it:

1. **Intent / why** — the heaviest box; the only thing that lets the agent recover when the plan hits reality
2. **Target state** — the state to reach, not the steps to walk
3. **Boundaries / red lines** — only the few hard constraints that must never be crossed
4. **Escalation / stop and ask me** — the most-often-omitted box
5. **Done-criteria / evidence** — empty means you can't proceed

Its real value isn't the table — it's that **when you answer thin, it asks one more**, with the fire aimed at the two boxes that get watered down: *why* and *escalation*. And it **asks, never writes**: Intent is the part you must not outsource, and the moment it drafts for you, you'll nod a mediocre version through.

## Using it

Trigger: `/auftrag`, `/派活`, or a phrase like "认真派个活". Then:

```
you dump the task in one go → it sorts your words into the five boxes, chases only the thin ones
→ boxes clear the bar (why + escalation solid, done-criteria non-empty) → it assembles a brief for review
→ lands in Todoist → asks "dispatch now, or store?"
```

## Repo layout

| Path | What it is |
|---|---|
| `SKILL.md` | **The deliverable** — the skill itself (`name: auftrag`), a thin orchestrator |
| `references/grill-heuristics.md` | The follow-up heuristics (the crown jewel; iterated most) |
| `references/dispatch.md` | Phase 4 plumbing: Todoist write + subagent dispatch |
| `CONCEPT.md` | The original concept doc (in Chinese), kept as provenance |
| `docs/DESIGN.md` | Design decisions and trade-offs |
| `INSTALL.md` | How to install into `~/.claude/skills/` |

## Status

v0. Deliberately small: pure prompt — no hooks, no validation scripts, no resident agents. Tighten precisely once it's been used a dozen times and the leaks show.
