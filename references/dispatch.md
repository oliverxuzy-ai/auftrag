# Phase 4 — Land in Todoist + dispatch or store

Read this on entering Phase 4 and follow it. Precondition: the brief was assembled from the **user's own words** in Phase 3 and shown to them.

## Step 2 — Land in Todoist first (always happens)

Follow the user's CLAUDE.md task-creation discipline: **the brief is the draft — show it, create only on an explicit `yes`.** It was already shown in Phase 3, so one confirmation here is enough.

**Recommend a placement — don't just drop it in the inbox.** First read the project list:

```
mcp__claude_ai_todoist__find-projects { limit: 50 }
```

Then put a proposed placement in front of the commander for sign-off. It is a **recommendation, never a silent auto-set**:

- **Project** — matched from the brief's content (a work / Jira-ticket task → the work project; a personal one → its project).
- **Priority** — read off the urgency / ticket signals already in the brief, as todoist's `p1`–`p4` (`p1` highest, `p4` the default). No signal → `p4`.
- **Due / deadline** — only if the brief implies a time: `dueString` (natural language) for a soft schedule, `deadlineDate` (ISO `YYYY-MM-DD`) for a hard constraint. No signal → leave unset.

Put the placement in front of the commander as **one `AskUserQuestion` call** (up to two questions) — a click, not a line to read back:

- **项目 (single-select)** — the ≤3 best-matched projects from `find-projects`, best match first and labeled `(推荐)`. `Other` (auto-provided by the tool) covers any other project or the inbox.
- **优先级 (single-select)** — `p1` / `p2` / `p3` / `p4`, with the value read off the brief's urgency/ticket signals placed first; no signal → `p4` default.

Do **not** menu the due/deadline — only when the brief implies a time, ask one text line afterward (`dueString` for a soft schedule, `deadlineDate` `YYYY-MM-DD` for a hard constraint). The menu answers **are** the explicit confirmation; Esc → don't create. This is still a recommendation, never a silent auto-set — the menu just makes the recommendation clickable. If nothing matched, the recommended option is the inbox. Then create:

```
mcp__claude_ai_todoist__add-tasks {
  tasks: [{
    content: "<one-line task name>",
    description: "<the full brief markdown>",
    projectId: "<confirmed project, or inbox>",
    priority: "<p1..p4>"
    // dueString / deadlineDate only when the brief set one
  }]
}
```

- Hand the task URL back.
- On MCP failure: report it, don't claim success, and don't dispatch an agent on top of a failed write.

## Step 3 — "Dispatch now, or store?" (menu with preview)

Ask with **one `AskUserQuestion` single-select** (single-select is what enables `preview`), so the commander sees the actual artifact of each path before choosing:

- **「派发 now」** — `preview` = the exact mission prompt the Agent tool will receive: the escalation-prepend paragraph (see "Dispatching a subagent" below) + the full brief markdown.
- **「存档」** — `preview` = the resume line, verbatim: `/start-todo <task_url>`.

No third option; Esc = cancel. Then act on the choice:

- **Store** → it's in Todoist; that's the mission on file. End your report with the one command that resumes it — ready to paste, nothing to retype:

  ```
  /start-todo <task_url>
  ```

  Say it plainly: to take this up later — same machine or another — paste that line. Do **not** re-describe the task or open a fresh todo; that spawns a duplicate cut off from this one.
- **Dispatch now** → below.

## Dispatching a subagent (one-shot)

In the current session, use the **Agent tool** with the brief as the mission prompt. Default to `general-purpose`; if the user names a different agent type (e.g. `Explore`, `code-reviewer`), use that.

**Key translation — turn "stop and ask me" into halt-and-return.** A subagent runs to completion and returns; it can't actually pause to ask you mid-run. So when you hand it the brief, prepend this:

> "This is your Auftrag; execute against it — the *how* is yours. **If you hit any situation listed under Escalation, do not improvise: halt, report what you've found, and return with the decision the commander must make.** When the objective is met, verify against Done-criteria and return the evidence — not 'I think it's done.'"

That preserves the escalation semantics within the constraints of a one-shot dispatch.

## Boundaries

- No resident agents, no inter-agent messaging, no state sync. This is one Agent-tool call: it runs, it returns, it's over.
- No polling, no daemon, no auto-redispatch.
