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

Report it in one line — *"Proposed placement: `<project>` · `<priority>` · `<due>`. Confirm, or redirect?"* — and create only on the commander's `yes`. If nothing clearly fits, fall back to the inbox and ask which project in one line. Then create:

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

## Step 3 — Ask "dispatch now, or store?"

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
