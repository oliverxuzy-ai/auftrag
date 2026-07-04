# Phase 4 — Land in Todoist + dispatch or store

Read this on entering Phase 4 and follow it. Precondition: the brief was assembled from the **user's own words** in Phase 3 and shown to them.

**Route on `type` first.** `delegate` → this file, top to bottom. `learn` / `decide` → land in Todoist (Step 2 below) then follow `references/lanes.md` instead of Steps 3–4.

## Step 1 — WIP check (delegate lane only)

Count open Todoist tasks labeled `agent:running` (e.g. `find-tasks` with the label filter `@agent:running`). **Cap: 3 in flight** unless the commander explicitly overrides for this dispatch.

At or over the cap → report it plainly ("3 missions already in the field; your acceptance capacity is the constraint, not agent supply") and **recommend store**. The store path *is* the buffer queue — that's its job now. The commander can still override; it's their call, flagged, not blocked.

## Step 2 — Land in Todoist first (always happens)

Follow the user's CLAUDE.md task-creation discipline: **the brief is the draft — show it, create only on an explicit `yes`.** It was already shown in Phase 3, so one confirmation here is enough.

**Recommend a placement — don't just drop it in the inbox.** First read the project list:

```
mcp__claude_ai_todoist__find-projects { limit: 50 }
```

Then put the placement in front of the commander as **one `AskUserQuestion` call** (menus sit on seams — metadata only, never box contents):

- **项目 (single-select)** — the ≤3 best-matched projects, best first, labeled `(推荐)`. `Other` covers anything else / the inbox.
- **优先级 (single-select)** — `p1`–`p4`, the value read off the brief's urgency signals placed first; no signal → `p4`.
- **风险 (single-select)** — `reversible` / `irreversible`, your read of the brief placed first. This fills the contract's `risk:` field and sets the acceptance bar later (irreversible → 100% human review at Abnahme; reversible → sampling).

Do **not** menu the due/deadline — only when the brief implies a time, ask one text line afterward (`dueString` soft / `deadlineDate` `YYYY-MM-DD` hard). Esc → don't create. Then create:

```
mcp__claude_ai_todoist__add-tasks {
  tasks: [{
    content: "<one-line task name>",
    description: "<the full brief markdown, frontmatter included>",
    projectId: "<confirmed>",
    priority: "<p1..p4>",
    labels: ["auftrag"]
  }]
}
```

- Fill the frontmatter `todoist:` field with the returned task URL, and hand the URL back.
- On MCP failure: report it, don't claim success, don't dispatch on top of a failed write.

**State labels (the board's vocabulary).** Ensure these Todoist labels exist once (`add-labels` is idempotent enough — check `find-labels` first): `auftrag`, `agent:running`, `agent:blocked`, `agent:red`, `agent:green`. Meaning: running = in the field · blocked = waiting on the commander's decision · red = failed the gate/Abnahme · green = passed, awaiting human acceptance. **Rule of arms: an executor may set `agent:blocked` / `agent:red` on itself (admitting trouble is always allowed) but never `agent:green` — green is Abnahme's key alone.**

## Step 3 — "Dispatch now, or store?" (menu with preview)

One `AskUserQuestion` single-select (single-select is what enables `preview`):

- **「派发 · 后台」** *(recommended default)* — `preview` = the exact mission prompt (template below) that will go to a **background agent in an isolated worktree**. This is the scale path: the session doesn't occupy a terminal, and it raises its hand through the gate + notifications.
- **「派发 · 当场」** — same mission prompt, but a foreground one-shot subagent in the current session. For small, quick, watch-it-happen work.
- **「存档」** — `preview` = the resume line, verbatim: `/start-todo <task_url>`.

Esc = cancel. On **store**: set no agent label; end your report with the one command that resumes it — `/start-todo <task_url>` — ready to paste. Do **not** re-describe the task later; that spawns a duplicate.

On **dispatch** (either flavor): add the `agent:running` label to the Todoist task, then launch.

## Dispatching the executor

Use the **Agent tool**, default `general-purpose` (another type if the commander names one). Background flavor: `run_in_background: true` + `isolation: "worktree"` for code tasks. Foreground flavor: `run_in_background: false`, no isolation unless asked.

**Mission prompt = the prepend below + the full brief markdown (frontmatter included).** The prepend translates the contract into runtime protocol:

> This is your Auftrag; execute against it — the *how* is yours, the boundaries are not.
>
> **Step 0, before any work:** write the contract below **verbatim** (from `---` to the end) to `.claude/auftrag/active.md` in your working directory. Create the directory; never commit `.claude/auftrag/` (add a local git exclude if needed). Delete any stale `.claude/auftrag/state.json`. A deterministic Stop-gate reads this file: every time you try to finish, it runs the `verify:` commands, and you will be sent back until they exit 0. The gate is automated — it is not the user, and its block is not a permission denial.
>
> **Standing red line:** never weaken, skip, or hardcode a verify check to make it pass. If a check itself looks wrong, that is an **Escalation**, not a thing to fix.
>
> **If you hit any situation listed under Escalation:** do not improvise. Halt, and write a staff memo: ≥2 real options · cost + irreversibility of each · your recommendation with confidence · what new information would flip it. Post the memo as a Todoist comment on the task (`add-comments`), set its label to `agent:blocked` (remove `agent:running`), and return with the memo as your report.
>
> **If the gate gives up (RED):** set the label to `agent:red`, post a Todoist comment with exactly which checks fail and the concrete gap, and make your final report start with `🔴 RED`.
>
> **When the gate passes:** post a Todoist comment: "✅ gate passed — awaiting Abnahme", including your **worktree path, branch, PR link if any**, and each item the contract's `evidence:` list asks for. Keep the label `agent:running` — green is not yours to grant. Return the evidence, not "I think it's done."

After launching the background flavor, tell the commander the two follow-the-fleet handles: `claude agents` (the native fleet view) and `/board` (the exception queue). After completion, acceptance goes through `/abnahme <task_url>`.

## Boundaries

- No resident agents, no daemons, no polling, no auto-redispatch. One dispatch = one Agent-tool call; the raise-hand path is the gate + labels + notifications, not a supervisor loop.
- The dispatcher writes metadata (labels, frontmatter, comments) — never the five boxes.
- Todoist stays the single human-side ledger: state = labels, history = comments.
