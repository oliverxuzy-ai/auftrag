---
name: todoist-sync
description: Bind a Claude Code session to a Todoist task. Use when user runs /start-todo, /update-todo, /done-todo, or when CC needs to decide whether to post a milestone comment or propose closing a bound task. State lives in <cwd>/.claude/todoist-session.json. All Todoist I/O goes through mcp__claude_ai_todoist__* tools.
---

# todoist-sync

Bind a Claude Code session to a single Todoist task. Append progress to that task's Todoist comment thread as work proceeds; complete the task on explicit user confirmation.

State file: `<cwd>/.claude/todoist-session.json` is the **single source of truth**. Always read it before any milestone / update / completion decision. Never infer the bound task from conversation history.

MCP tool surface used:
- `mcp__claude_ai_todoist__fetch-object` (read task)
- `mcp__claude_ai_todoist__add-comments` (write comment)
- `mcp__claude_ai_todoist__complete-tasks` (close task)

## Entry points

### `/start-todo <url-or-id>`

**Trigger:** User invokes `/start-todo` with either a Todoist task URL or a bare task ID.

**Steps:**

1. **Parse the input** to extract the task ID.
   - If input is a URL like `https://app.todoist.com/app/task/popover-library-6gj8PG4mMQgwgwc7`, take the substring after the last `/`, then take the substring after the last `-`. The Todoist task ID is the trailing alphanumeric segment (16 characters of `[A-Za-z0-9]`).
   - If input is a bare 16-char alphanumeric ID, use as-is.
   - If parsing fails: abort and tell the user "Could not parse Todoist task ID from `<input>`. Pass a full Todoist URL or a 16-char ID."

2. **Check for an existing binding** by reading `<cwd>/.claude/todoist-session.json`:
   - If file exists and `task_id` matches the new input → tell the user "Already bound to this task" and stop.
   - If file exists with a different `task_id` → say "Currently bound to `<existing task_content>` (ID `<existing task_id>`). Switch to the new task? (yes/no)". Wait for explicit `yes` / `confirm` / `go` / `好` / `可以` / `搞定` / `没问题` / `done` / `ship it`. Anything else: abort, leave existing binding intact.
   - If file does not exist: continue.

3. **Fetch the task from Todoist:**
   ```
   mcp__claude_ai_todoist__fetch-object { type: "task", id: "<parsed_id>" }
   ```
   - On 404 / not-found: abort with "Task `<id>` not found in Todoist. Check the URL."
   - On other MCP failure: abort, report the error verbatim. Do NOT create a state file.

4. **If the task is already `completed` in Todoist** (`object.checked == true`): warn "This task is already completed in Todoist. Re-open a session anyway? (yes/no)". Wait for explicit `yes`. Anything else: abort.

5. **Show the user a binding preview and wait for confirmation:**
   ```
   About to bind this Claude Code session to:

     <task_content>
     Project: <project_id> · Priority: <priority>
     URL: https://app.todoist.com/app/task/<task_id>

   Confirm? (yes/no)
   ```
   Wait for explicit `yes` / `confirm` / `go` / `好` / `可以` / `搞定` / `没问题` / `done` / `ship it`. Anything else: abort, do not write state file.

6. **Create the `.claude/` directory if it doesn't exist:**
   ```bash
   mkdir -p <cwd>/.claude
   ```

7. **Post the opening comment via MCP:**
   ```
   mcp__claude_ai_todoist__add-comments {
     items: [{ taskId: "<task_id>", content: "🟢 Session started in Claude Code (cwd: `<cwd>`)" }]
   }
   ```
   Capture the returned `commentId`.

8. **Write the state file atomically** to `<cwd>/.claude/todoist-session.json` (write to `.tmp` then rename):
   ```json
   {
     "task_id": "<id>",
     "task_content": "<content from fetch>",
     "project_id": "<project_id>",
     "task_url": "https://app.todoist.com/app/task/<id>",
     "started_at": "<ISO 8601 now, UTC>",
     "cwd": "<cwd>",
     "last_activity_at": "<same as started_at>",
     "milestones": [
       {
         "ts": "<same as started_at>",
         "type": "start",
         "summary": "Session started",
         "comment_id": "<commentId from step 7>"
       }
     ]
   }
   ```

9. **Confirm to the user:**
   ```
   Bound. Working on: <task_content>
   ```

### `/update-todo <note>`

**Trigger:** User invokes `/update-todo` with a free-text note.

**Steps:**

1. **Read state file** `<cwd>/.claude/todoist-session.json`.
   - Not found: abort with "No active todo binding in this directory. Run `/start-todo <url>` first."
   - Invalid JSON: surface the raw parse error. **Do NOT auto-overwrite.**

2. **Post the comment:**
   ```
   mcp__claude_ai_todoist__add-comments {
     items: [{ taskId: state.task_id, content: "📝 <note>" }]
   }
   ```
   Capture `commentId`.

3. **On MCP failure:** Do NOT update the state file. Tell the user the error and let them retry.

4. **On success:** Append to `state.milestones`:
   ```json
   {
     "ts": "<now ISO UTC>",
     "type": "manual",
     "summary": "<note>",
     "comment_id": "<commentId>"
   }
   ```
   Update `state.last_activity_at = <now>`.

5. **Write the state file back atomically:** write to `<cwd>/.claude/todoist-session.json.tmp`, then rename to `<cwd>/.claude/todoist-session.json`. This prevents corruption if the write is interrupted.

6. **Confirm:** "Comment posted."

### `/done-todo` (Path A: user-initiated)

**Trigger:** User invokes `/done-todo`.

**Steps:**

1. **Read state file**. Not found → abort: "No active todo binding."

2. **Generate a closing summary** (≤ 1 sentence) from `state.milestones` + the current conversation. Focus on the concrete outcome (e.g., "Popover dismissal fixed via NSPanel lifecycle overrides").

3. **Compute duration:** `now - state.started_at`, formatted as `~<N>m` or `~<N>h<M>m`.

4. **Compose the closing comment template:**
   ```
   🏁 Done. <closing summary>.

   - Session: <started_at> → <now> (~<duration>)
   - Milestones: <count of state.milestones>
   - Final state: <last milestone summary, or "code change applied" / "investigation complete">
   ```

5. **Show the user a preview and wait for confirmation:**
   ```
   About to close: <task_content>

   Closing comment will be:
   <comment as composed above>

   Confirm? (yes/no)
   ```
   Wait for explicit `yes` / `confirm` / `go` / `好` / `可以` / `搞定` / `没问题` / `done` / `ship it`. Anything else: abort. Do NOT proceed silently.

6. **If `state.milestones.length == 1`** (only the start milestone): warn first: "No work milestones recorded in this session. Close anyway? (yes/no)" before showing the preview. Same confirmation rules.

7. **Post the closing comment first:**
   ```
   mcp__claude_ai_todoist__add-comments {
     items: [{ taskId: state.task_id, content: "<closing comment>" }]
   }
   ```
   **On MCP failure here: ABORT.** Never call `complete-tasks` without a closing comment.

8. **Complete the task:**
   ```
   mcp__claude_ai_todoist__complete-tasks { taskIds: [state.task_id] }
   ```
   On MCP failure: report the error. Do NOT archive the state file. User can retry `/done-todo`.

9. **Archive the state file** with a filesystem-safe timestamp (use `T11-30-00Z` not `T11:30:00Z`):
   ```bash
   mv <cwd>/.claude/todoist-session.json \
      <cwd>/.claude/todoist-session.json.<task_id>.<safe-iso-ts>.done
   ```

10. **Confirm:** "Todo closed."

### `/done-todo` (Path B: CC proposes)

**When CC may propose closing:**

At the end of any response, check ALL of the following:

1. `<cwd>/.claude/todoist-session.json` exists and is valid.
2. `state.milestones.length ≥ 2` (i.e., at least one milestone beyond `start`).
3. **Within the last 2 user messages**, the user used one of these positive-feedback tokens as a standalone-ish reaction (not embedded in a question or negation):
   - `好` / `可以` / `搞定` / `没问题` / `done` / `ship it`

   **Do NOT** expand this set. `还行`, `大概`, `差不多`, `挺好`, `不错`, `nice`, `great`, `perfect` — none of these count. Use only the exact tokens above. If the model is uncertain whether a token qualifies, treat it as NOT qualifying.
4. The current turn has NO failure signal: no test fail, no build error, no `but` / `however` / `actually` / `wait` from the user.

**If all four hold:** append (do NOT replace) a single line at the end of the response:

```
🎯 Looks like this todo is wrapped up. Say `yes` or run `/done-todo` to close it.
```

**Do NOT** call `complete-tasks` from Path B. Just suggest.

**If user replies with `yes` / `confirm` / `go` / `好` / `可以` / `搞定` / `没问题` / `done` / `ship it`:** enter Path A starting at step 2 (generate closing summary).

**If user replies anything else:** do nothing further. Do not re-suggest in the same turn.

**Path B is rate-limited:** if CC suggested closing in the previous response and the user did NOT confirm, do NOT suggest again in the next response. Wait at least 2 turns before another suggestion.

## Milestone auto-detection

At the **end** of each response (after fulfilling the user's request), if `<cwd>/.claude/todoist-session.json` exists and is valid:

1. **Check triggers (any one fires → propose milestone):**
   - A successful `git commit` was invoked this turn (no hook failure).
   - A batch of CC TaskList items all transitioned to `completed` this turn.
   - Tests / lint / build went from red → green within this session (the most recent prior run was failing; the run this turn passed).
   - Complete bug-investigation loop: root cause located AND fix proposed AND user acknowledged this turn.
   - `ExitPlanMode` was invoked this turn.
   - At least 45 minutes since `last_activity_at` AND this turn produced substantive output.

2. **Apply anti-triggers (any one matches → do NOT comment):**
   - Pure exploration / file reading / grep with no concrete output.
   - Pure explanatory answer to a user question (no artifact produced).
   - The turn ended with an unresolved error / test failure.
   - Less than 5 minutes since `last_activity_at` (debounce — wait for next turn).
   - The only thing that changed is CC's internal TaskList status without any real-world output.

3. **Per-turn cap:** At most **one** milestone comment per response. If multiple triggers fire, pick the most informative and post just one.

4. **If a milestone fires:**
   - Compose a comment:
     ```
     ✅ <one-line summary, < 100 chars>

     - <optional detail 1>
     - <optional detail 2>
     - <optional detail 3>
     ```
   - Post via `mcp__claude_ai_todoist__add-comments`.
   - On success: append to `state.milestones`:
     ```json
     {
       "ts": "<now>",
       "type": "milestone",
       "summary": "<one-line summary>",
       "comment_id": "<commentId>"
     }
     ```
     Update `state.last_activity_at = <now>`.
   - On MCP failure: append the same entry locally but with `comment_id: null, sync_failed: true`. Do NOT update `last_activity_at`. On the next milestone tick, before composing a new milestone, first retry the failed ones in order; on retry success, update their entries in place.

5. **Order:** Milestone check runs LAST in a turn. Never let it pollute the actual answer to the user.

## State file schema

Path: `<cwd>/.claude/todoist-session.json`

Treat this file as the **single source of truth** for which Todoist task is bound. Never trust conversation history over this file.

Complete shape:

```json
{
  "task_id": "string, Todoist task ID (16 alphanumeric chars)",
  "task_content": "string, task title from Todoist (cached so we don't refetch)",
  "project_id": "string, Todoist project ID",
  "task_url": "string, https://app.todoist.com/app/task/<task_id>",
  "started_at": "ISO 8601 UTC, set on /start-todo",
  "cwd": "absolute path of working directory at /start-todo time",
  "last_activity_at": "ISO 8601 UTC, updated on every successful milestone or /update-todo",
  "milestones": [
    {
      "ts": "ISO 8601 UTC",
      "type": "one of: start | milestone | manual | done",
      "summary": "string, ≤ 100 chars",
      "comment_id": "string (Todoist comment ID), or null if sync_failed",
      "sync_failed": "bool, optional; true if MCP add-comments failed and this entry awaits retry"
    }
  ]
}
```

**Write pattern (always atomic):**
1. Write JSON to `<cwd>/.claude/todoist-session.json.tmp`
2. Rename `.tmp` → `todoist-session.json`

This guarantees no half-written file is ever observed.

**Archive on completion:** Rename `todoist-session.json` to `todoist-session.json.<task_id>.<safe-ts>.done` where safe-ts uses `T11-30-00Z` not `T11:30:00Z` (avoiding `:` for filesystem portability).

**Multi-window same cwd:** If two CC windows write to the same file concurrently, the atomic-rename pattern means one wins cleanly. To minimize lost writes: always read → modify → write fresh, never hold the JSON in memory across multiple turns.

## Error handling

### State file issues

| Situation | Behavior |
|-----------|----------|
| File missing on `/update-todo` or `/done-todo` | Abort with: "No active todo binding in this directory. Run `/start-todo <url>` first." |
| File present but invalid JSON | Surface the raw parse error verbatim. Do NOT auto-overwrite or delete. User decides whether to repair or run `/start-todo` again (which requires manually removing the broken file). |
| File present, `task_id` looks malformed | Treat as invalid JSON (above). |
| File `cwd` does not match current `cwd` | Print a one-line warning ("session file was created in `<old cwd>`; you are in `<current cwd>`") but proceed. This handles symlinks and renamed directories. |

### Todoist-side issues

| Situation | Behavior |
|-----------|----------|
| `fetch-object` returns 404 / not-found on `/start-todo` | Abort. Do NOT create state file. |
| `fetch-object` succeeds and `object.checked == true` on `/start-todo` | Warn "task is already completed" and require explicit `yes` to bind. |
| `fetch-object` returns 404 on `/update-todo` or `/done-todo` | Prompt: "Bound task `<task_id>` is missing from Todoist. Clear session? (yes/no)". On `yes`: archive the session file as `.cleared` instead of `.done`. |
| `add-comments` fails on `/update-todo` | Tell the user the error verbatim. Do NOT modify state file. Let them retry. |
| `add-comments` fails on automatic milestone | Append milestone locally with `comment_id: null, sync_failed: true`. On next milestone tick, retry failed entries first. |
| `add-comments` fails inside `/done-todo` (closing comment) | **Abort.** Do NOT call `complete-tasks`. Surface error. |
| `complete-tasks` fails after closing comment succeeded | Keep session file active. Tell user "Closing comment posted but `complete-tasks` failed: `<error>`. Run `/done-todo` again to retry completion. (The closing comment will be re-posted; this is expected duplicate.)" |

### Concurrency

| Situation | Behavior |
|-----------|----------|
| Two CC windows, same cwd, both `/start-todo` same task | Atomic-rename write pattern handles it; both succeed. `started_at` retains earliest only if read-before-write is followed; otherwise the later one wins on that field. `milestones[]` appended to whoever read most recently. Acceptable. |
| Two CC windows, same cwd, different tasks via `/start-todo` | Second one detects existing binding, prompts to switch. |
| Same cwd, one window holds stale binding in memory while the other rewrites the file | Each window must read state file fresh at each operation. Never cache across turns. |

### Anti-patterns (explicitly DO NOT do)

- Do NOT auto-bind from a Todoist URL pasted in conversation. Slash command only.
- Do NOT migrate an in-progress conversation onto a newly-bound task retroactively.
- Do NOT infer milestones from `git log` history.
- Do NOT support concurrent active bindings per cwd.
- Do NOT write Todoist label / priority / due-date.
- Do NOT poll Todoist for external state changes.
- Do NOT call `complete-tasks` without an in-turn explicit user `yes`.
- Do NOT treat ambiguous user replies (`还行`, `大概可以`, `差不多`) as positive feedback.
