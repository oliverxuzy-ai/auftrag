# todoist-sync skill — Design

**Date:** 2026-05-26
**Status:** Approved (brainstorming phase complete)
**Author:** zhengyangxu + Claude Code

## Goal

Bind a Claude Code session to a single Todoist task. As work proceeds, progress is appended to that task's Todoist comment thread; when the user explicitly confirms completion, the task is marked complete in Todoist.

Bidirectional in scope means: CC → Todoist (comments + completion). Todoist → CC reads happen only at bind-time (fetch task) and on demand; no continuous polling.

## Non-Goals

- Two-way sync of Todoist label / priority / due date
- Reverse sync (Todoist UI state change pushing into CC)
- Auto-binding from natural language ("let's work on X") — slash command only
- Concurrent multi-task binding per cwd
- Auto-completion without explicit user confirmation
- Reconstruction of milestones from git history

## User-Facing Surface

Four entry points, all explicit:

| Command | Trigger | Effect |
|---------|---------|--------|
| `/start-todo <url-or-id>` | User | Fetches task, shows summary, awaits user confirmation, writes `.claude/todoist-session.json`, posts opening `🟢` comment |
| `/update-todo <note>` | User | Immediate `📝` comment, recorded in session file |
| `/done-todo` | User | Shows closing summary, awaits user confirmation, posts `🏁` comment, calls `complete-tasks`, archives session file |
| Automatic milestone | CC self-judges | Posts `✅` comment when a milestone trigger fires (§ Milestone Detection) |

CC may also **propose** `/done-todo` when conditions are met (§ Completion); the user must still confirm.

## Architecture

```
~/.claude/skills/todoist-sync/
└── SKILL.md                    # frontmatter + workflow instructions

<cwd>/.claude/
└── todoist-session.json        # active binding state (single source of truth)
└── todoist-session.json.<id>.<ts>.done   # archived completed sessions
```

**No hooks. No external scripts. No edits to settings.json.** The skill is pure instruction; CC follows it.

**Trust boundary**: the `.claude/todoist-session.json` file is the only persistent state. CC reads it before any milestone / update / completion decision. Conversation context is never the source of truth — compaction-safe.

## State File Schema

```json
{
  "task_id": "6gj8PG4mMQgwgwc7",
  "task_content": "<task title from Todoist>",
  "project_id": "6gj8P6QH3GpmXhWf",
  "task_url": "https://app.todoist.com/app/task/<task_id>",
  "started_at": "2026-05-26T10:42:00Z",
  "cwd": "/Users/zhengyangxu/Desktop/personal/Whetstone",
  "last_activity_at": "2026-05-26T11:15:00Z",
  "milestones": [
    {
      "ts": "2026-05-26T10:45:00Z",
      "type": "start",
      "summary": "Session started",
      "comment_id": "abc123"
    }
  ]
}
```

Field rationale:
- `task_content` + `task_url` cached so CC need not re-fetch from MCP just to reference the task in chat
- `cwd` recorded as a sanity-check against accidental cross-project reads
- `last_activity_at` feeds the "≥45 min since last milestone" trigger
- `milestones[].comment_id` retained for future edit / amend support
- Conversation state, CC TaskList state, model reasoning — **never** stored here

Lifecycle:
- Created on `/start-todo` (after user confirms the binding)
- Appended to on every milestone / `/update-todo`
- Renamed to `todoist-session.json.<task_id>.<ts>.done` on successful `/done-todo` (not deleted — preserves history, recoverable from misclicks)

## Milestone Detection

CC runs the milestone check at the **end** of each response (after fulfilling the user's request), reading `.claude/todoist-session.json` to know the active binding and `last_activity_at`.

### Triggers (any one fires)

1. A successful `git commit` invoked by CC (no hook failure)
2. A batch of CC's TaskList items all transitioning to `completed`
3. Tests / lint / build going from red → green in the current session
4. Complete bug investigation loop: root cause located + fix proposed + user acknowledged
5. ExitPlanMode invocation (plan locked in)
6. ≥ 45 min since last milestone AND substantive output this turn

### Anti-triggers (explicitly **not** milestones)

- Pure exploration / file reading / grep
- Pure explanatory answers to user questions
- Unresolved errors / failures
- < 5 min since last milestone (debounce)
- CC's internal TaskList status churn alone (without real-world output)

### Comment format

```
✅ <one-line summary, < 100 chars>

- <optional detail 1>
- <optional detail 2>
- <optional detail 3>
```

### Constraints

- **At most one** milestone comment per CC response (no fan-out)
- The `add-comments` MCP call must succeed before `last_activity_at` is updated and the milestone is appended to `milestones[]` (no partial writes)
- On MCP failure: append the milestone locally with `comment_id: null, sync_failed: true`; retry on next milestone tick before writing the new one

## Update Flow (`/update-todo`)

1. Read session file; abort with clear error if no binding
2. Call `add-comments` with content `📝 <user-supplied note>`
3. On success: append `{type: "manual", summary: "<note>", comment_id: <id>, ts: <now>}` to `milestones[]`
4. Update `last_activity_at`

## Completion Flow (`/done-todo`)

### Path A — User runs `/done-todo`

1. Read session file; abort if no binding
2. Generate closing summary from `milestones[]` + current conversation context
3. Show preview to user:
   ```
   About to close todo: <task_content>

   Closing comment:
   🏁 Done. <summary>. Worked through <N> milestones over <duration>.

   Confirm? (yes/no)
   ```
4. Wait for explicit confirmation (yes / confirm / go / 好 / 可以 / 搞定 / 没问题 / done / ship it). **No** other reply proceeds.
5. Call `add-comments` (closing comment). On failure: **abort** — never leave a "closed task with no closing comment" inconsistency.
6. Call `complete-tasks {taskIds: [task_id]}`. On failure: keep session file as-is, report error, allow retry.
7. Rename session file to `todoist-session.json.<task_id>.<ts>.done`

### Path B — CC proposes completion

CC may suggest `/done-todo` at the end of a response **only if all** these hold:
- At least one milestone in `milestones[]` (not a freshly started session)
- Within the last 2 user turns, user used one of the closed-set positive-feedback words: **好 / 可以 / 搞定 / 没问题 / done / ship it** (no synonyms, no inferred sentiment)
- No failure signal this turn (no test fail, no build error, no "but...", no "actually...")

When CC proposes, it appends a brief line:
```
🎯 Looks like this todo is wrapped up. Say 'yes' or run /done-todo to close it.
```

User confirmation by `yes / confirm / go / 好 / 可以 / 搞定 / 没问题 / done / ship it` advances into Path A step 5. Anything else: do nothing.

## Closing Comment Format

```
🏁 Done. <one-line summary of what was accomplished>.

- Session: <start_ts> → <end_ts> (~<duration>)
- Milestones: <count>
- Final state: <last milestone summary, or "code change applied" / "investigation complete">
```

## Error Handling & Edge Cases

| Situation | Behavior |
|-----------|----------|
| `session.json` exists but isn't valid JSON | Surface the raw error; do **not** auto-overwrite or delete. User decides. |
| Bound task no longer exists in Todoist (`fetch-object` 404) | Prompt: "Bound task missing — clear session?" Awaits `yes`. |
| `/start-todo` on a task already `completed` in Todoist | Warn: "Task already completed. Re-open session anyway?" Awaits `yes`. |
| `/done-todo` with empty `milestones[]` | Warn: "No milestones recorded. Close anyway?" Awaits `yes`. |
| Two CC windows, same cwd, same task | Both write to same file. Append-only `milestones[]` merges; `started_at` keeps earliest, `last_activity_at` updates on each write. |
| Two CC windows, same cwd, different `/start-todo` | Second one prompts: "Currently bound to X — switch to Y?" Awaits `yes`. |
| Different cwd, different tasks | Fully isolated (separate session files). |
| `add-comments` network failure | Local milestone gets `sync_failed: true`. Retry queue flushed on next milestone tick. |
| `complete-tasks` failure mid-`/done-todo` | Session file stays active. Error surfaced. User can retry `/done-todo`. |
| Pre-completion `add-comments` failure | Abort. Do not call `complete-tasks`. Surfaces inconsistency risk to user. |
| Compaction / session resume next day | Skill reads `.claude/todoist-session.json` cold. No reliance on chat history. |

## Explicit Anti-Patterns

- ❌ Auto-binding from pasted Todoist URLs (slash command only)
- ❌ Migrating an in-flight conversation onto a newly-bound task retroactively
- ❌ Inferring milestones from `git log` history
- ❌ Concurrent active bindings per cwd
- ❌ Writing Todoist label / priority / due-date
- ❌ Polling Todoist for external state changes
- ❌ Auto-completion without an in-turn explicit user `yes`
- ❌ Treating ambiguous user replies ("还行", "大概可以") as positive feedback

## Open Questions

None at design phase. All decisions explicit above.

## Out of Scope (future work, do not build now)

- Stop hook reminder for missed milestones (would require `~/.claude/settings.json` edit and a wrapper script)
- Batch flush mode (local milestone log → single comment on `/done-todo`)
- Subtask-aware binding (a Todoist task with subtasks → multi-binding)
- Cross-device session sync (sync file is local only)
