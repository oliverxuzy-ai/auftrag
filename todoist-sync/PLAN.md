# todoist-sync Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `todoist-sync` skill — a markdown instruction file at `~/.claude/skills/todoist-sync/SKILL.md` that lets Claude Code bind a session to a single Todoist task, post milestone progress as comments, and complete the task on explicit user confirmation.

**Architecture:** Pure skill — no hooks, no scripts, no `settings.json` changes. State lives in `<cwd>/.claude/todoist-session.json` per project. SKILL.md instructs CC how to behave under four slash commands plus an automatic milestone check at end of each response. All Todoist I/O goes through the existing `mcp__claude_ai_todoist__*` MCP tools.

**Tech Stack:** Markdown (SKILL.md), JSON (state file), Todoist MCP tools (`fetch-object`, `add-comments`, `complete-tasks`).

**Verification approach:** Each section ships with a manual smoke test against a throwaway Todoist task. There is no automated test framework for skills — the verification is "invoke CC with the slash command, observe the actual behavior + state file + Todoist side."

**Source spec:** `~/.claude/skills/todoist-sync/DESIGN.md`

---

## File Structure

```
~/.claude/skills/todoist-sync/
├── SKILL.md       ← built incrementally, Tasks 1-8
├── DESIGN.md      ← already exists (the spec)
└── PLAN.md        ← this file
```

State file (runtime artifact, NOT part of the skill repo):
```
<cwd>/.claude/todoist-session.json                       ← active binding
<cwd>/.claude/todoist-session.json.<task_id>.<ts>.done   ← archived completed sessions
```

`SKILL.md` is the only artifact written by this plan. Everything else is verification.

---

## Pre-flight (one-time setup)

- [ ] **Pre-1: Create a throwaway Todoist task for smoke testing**

In the Todoist app or via MCP, create a task titled `[smoke] todoist-sync test`. Note its task ID and URL — you will reuse these across Tasks 2-9. Park it in a project that won't clutter your real workflow (e.g., inbox).

- [ ] **Pre-2: Confirm the working directory for smoke tests**

Decide a throwaway directory for state-file smoke tests (e.g., `/tmp/todoist-sync-smoke/`). All `.claude/todoist-session.json` artifacts in these tasks land there. Do **not** smoke-test inside Whetstone or any active project — you'll pollute its `.claude/` directory.

```bash
mkdir -p /tmp/todoist-sync-smoke
cd /tmp/todoist-sync-smoke
```

---

## Task 1: Scaffold SKILL.md skeleton

**Files:**
- Create: `~/.claude/skills/todoist-sync/SKILL.md`

- [ ] **Step 1: Write the frontmatter + section headers**

```markdown
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

(filled in by Tasks 2-6)

## Milestone auto-detection

(filled in by Task 4)

## State file schema

(filled in by Task 7)

## Error handling

(filled in by Task 8)
```

- [ ] **Step 2: Verify the file**

```bash
ls -la ~/.claude/skills/todoist-sync/SKILL.md
head -5 ~/.claude/skills/todoist-sync/SKILL.md
```

Expected: file exists, frontmatter starts with `---` then `name: todoist-sync`.

- [ ] **Step 3: Verify the skill is discoverable by CC**

Start a new CC session in `/tmp/todoist-sync-smoke/`. Send: "list all available skills containing 'todoist'". Expected: CC lists `todoist-sync` (the description from frontmatter should appear).

If it doesn't appear: confirm the file is exactly at `~/.claude/skills/todoist-sync/SKILL.md` and frontmatter is valid YAML (no tabs, correct `---` delimiters).

---

## Task 2: `/start-todo` entry point

**Files:**
- Modify: `~/.claude/skills/todoist-sync/SKILL.md` (replace `## Entry points` placeholder onward with start-todo section, plus header for next sections)

- [ ] **Step 1: Replace `## Entry points` section with the start-todo block**

Find the line `## Entry points` and replace it (and the placeholder line below it) with:

````markdown
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

8. **Write the state file** to `<cwd>/.claude/todoist-session.json`:
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
````

(Leave a trailing `## Milestone auto-detection` placeholder header for Task 4.)

- [ ] **Step 2: Verify SKILL.md still parses**

```bash
head -1 ~/.claude/skills/todoist-sync/SKILL.md
# Expected: ---
grep -c "^## " ~/.claude/skills/todoist-sync/SKILL.md
# Expected: at least 4 (Entry points, Milestone auto-detection, State file schema, Error handling)
```

- [ ] **Step 3: Smoke test `/start-todo` happy path**

In CC at `/tmp/todoist-sync-smoke/`:
```
/start-todo https://app.todoist.com/app/task/<smoke-task-id>
```

Expected:
- CC shows the task content from your smoke task
- CC asks "Confirm? (yes/no)"
- Reply `yes`
- CC reports "Bound."
- `/tmp/todoist-sync-smoke/.claude/todoist-session.json` exists with correct fields
- In the Todoist app, the smoke task has a new comment starting with `🟢 Session started`

- [ ] **Step 4: Smoke test the "already bound" branch**

In the same session, try `/start-todo` again with the same URL.
Expected: "Already bound to this task."

- [ ] **Step 5: Smoke test the "switch binding" branch**

Create a second throwaway task. Try `/start-todo <new-task-url>`.
Expected: CC asks "Currently bound to `<first task>` ... Switch? (yes/no)". Reply `no`.
Expected: No state file change, no comment posted to either task.

- [ ] **Step 6: Smoke test the "user says no to bind" branch**

Delete the state file: `rm /tmp/todoist-sync-smoke/.claude/todoist-session.json`. Try `/start-todo <smoke-task-id>`, reply `no` to the confirm prompt.
Expected: No state file created. No comment posted.

- [ ] **Step 7: Commit (n/a — `~/.claude/` is not a git repo)**

Skip commit. If you've made `~/.claude/skills/` its own repo separately, run `git add SKILL.md && git commit -m "feat(todoist-sync): /start-todo entry point"` from that repo.

---

## Task 3: `/update-todo` entry point

**Files:**
- Modify: `~/.claude/skills/todoist-sync/SKILL.md` (append a section after start-todo block)

- [ ] **Step 1: Append the update-todo block right after the `/start-todo` section**

````markdown
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
````

- [ ] **Step 2: Smoke test happy path**

In CC at `/tmp/todoist-sync-smoke/` with an active binding:
```
/update-todo testing manual update from smoke test
```

Expected:
- CC reports "Comment posted."
- Todoist task now has a comment `📝 testing manual update from smoke test`
- `cat /tmp/todoist-sync-smoke/.claude/todoist-session.json` shows `milestones[]` now has 2 entries, the new one with `type: "manual"`.

- [ ] **Step 3: Smoke test the "no binding" branch**

```bash
mv /tmp/todoist-sync-smoke/.claude/todoist-session.json /tmp/keep-it.json
```
In CC: `/update-todo this should fail`
Expected: CC reports "No active todo binding..."

Restore: `mv /tmp/keep-it.json /tmp/todoist-sync-smoke/.claude/todoist-session.json`

- [ ] **Step 4: Smoke test the "corrupted JSON" branch**

```bash
echo "{not valid json" > /tmp/todoist-sync-smoke/.claude/todoist-session.json
```
In CC: `/update-todo whatever`
Expected: CC shows the raw JSON parse error, does NOT overwrite the file.

Restore the file by re-running `/start-todo` after deleting the broken file.

---

## Task 4: Milestone auto-detection rules

**Files:**
- Modify: `~/.claude/skills/todoist-sync/SKILL.md` (replace `## Milestone auto-detection` placeholder)

- [ ] **Step 1: Write the milestone-detection section**

````markdown
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
````

- [ ] **Step 2: Smoke test trigger #1 (git commit)**

In `/tmp/todoist-sync-smoke/`:
```bash
git init && echo "hello" > readme.md && git add readme.md
```
In CC: "commit this readme with message 'feat: add readme'"
After CC commits, expect: a new `✅ Committed: feat: add readme` (or similar) comment in Todoist; `milestones[]` in state file has a new entry with `type: "milestone"`.

- [ ] **Step 3: Smoke test the per-turn cap**

In CC: "make 3 commits each with a one-line readme change". CC should commit 3 times in one turn but post only ONE milestone comment summarizing all 3.

- [ ] **Step 4: Smoke test the debounce**

Immediately after Step 2, in CC: "commit another readme update".
Expected: comment posted (it's >5 min from `start` milestone but the next test does back-to-back). If <5 min from last milestone: no new milestone comment, just a normal response. Inspect state file `last_activity_at` to confirm.

- [ ] **Step 5: Smoke test the anti-trigger (pure exploration)**

In CC: "show me what's in this directory" — pure ls / cat.
Expected: NO new milestone comment.

---

## Task 5: `/done-todo` — Path A (user-initiated)

**Files:**
- Modify: `~/.claude/skills/todoist-sync/SKILL.md` (append a section after milestone-detection)

- [ ] **Step 1: Append the done-todo Path A block**

````markdown
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

9. **Archive the state file:**
   ```bash
   mv <cwd>/.claude/todoist-session.json \
      <cwd>/.claude/todoist-session.json.<task_id>.<ISO ts no colons>.done
   ```
   Note: the timestamp in the archive filename uses safe chars (e.g., `2026-05-26T11-30-00Z`), since `:` is filesystem-hostile.

10. **Confirm:** "Todo closed."
````

- [ ] **Step 2: Smoke test the happy path**

In CC at `/tmp/todoist-sync-smoke/` with active binding (and at least one milestone):
```
/done-todo
```

Expected:
- CC composes a closing summary and shows preview with `Confirm? (yes/no)`.
- Reply `yes`.
- Todoist task gets a `🏁 Done.` comment.
- Todoist task is marked completed (check via the Todoist app or `find-tasks`).
- `/tmp/todoist-sync-smoke/.claude/todoist-session.json` is gone.
- `/tmp/todoist-sync-smoke/.claude/todoist-session.json.<id>.<ts>.done` exists.

- [ ] **Step 3: Smoke test the "no binding" branch**

`/done-todo` with no state file → "No active todo binding."

- [ ] **Step 4: Smoke test the "empty milestones" warning**

```bash
# Manually craft a session with only start milestone (or use /start-todo and immediately /done-todo)
```
Run `/done-todo`. Expected: extra "No work milestones recorded... Close anyway?" prompt before the normal preview.

- [ ] **Step 5: Smoke test user `no` to confirmation**

In a fresh binding: `/done-todo` → reply `no`.
Expected: state file untouched. No comment posted. No completion.

---

## Task 6: `/done-todo` — Path B (CC-proposed)

**Files:**
- Modify: `~/.claude/skills/todoist-sync/SKILL.md` (append a section after Path A)

- [ ] **Step 1: Append the Path B block**

````markdown
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
````

- [ ] **Step 2: Smoke test the trigger**

In CC with active binding, ≥2 milestones, then say literally: "搞定"
Expected: CC's next response ends with the 🎯 suggestion line.

- [ ] **Step 3: Smoke test the confirm-after-propose flow**

After Step 2, reply `yes`.
Expected: CC enters Path A from step 2 (preview comment, ask confirm again). Reply `yes` → task closes.

- [ ] **Step 4: Smoke test the "don't expand" rule**

Reset binding. Say "还行" (NOT in the closed set).
Expected: CC does NOT suggest closing.

Say "perfect" (also NOT in the closed set).
Expected: CC does NOT suggest closing.

- [ ] **Step 5: Smoke test failure-signal blocking**

Reset binding, achieve 2 milestones, then say "搞定，but the tests are still failing"
Expected: CC does NOT suggest closing (the `but` + `failing` signal blocks).

- [ ] **Step 6: Smoke test rate-limiting**

Reset binding, achieve 2 milestones, say "搞定" → CC suggests. Reply "let me check one more thing" (not a confirm).
Expected: CC does NOT suggest again in the immediate next turn even if you say "搞定" again.

---

## Task 7: State file schema reference

**Files:**
- Modify: `~/.claude/skills/todoist-sync/SKILL.md` (replace `## State file schema` placeholder)

- [ ] **Step 1: Write the state-file schema section**

````markdown
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
````

- [ ] **Step 2: Smoke test cross-restart recovery**

In CC at `/tmp/todoist-sync-smoke/` with active binding and 2+ milestones, close the CC session entirely. Start a new CC session in the same cwd. Run `/update-todo cross-restart test`.

Expected:
- New CC session reads the existing state file correctly.
- Comment posted to the original task.
- `milestones[]` now has +1 entry.

- [ ] **Step 3: Smoke test compaction recovery (manual proxy)**

Real compaction is hard to trigger on demand. As a proxy: open a fresh CC session in the same cwd with no conversation history. Without typing `/start-todo`, run `/update-todo proxy compaction recovery`.

Expected: works — CC reads the state file fresh.

---

## Task 8: Error handling and edge cases

**Files:**
- Modify: `~/.claude/skills/todoist-sync/SKILL.md` (replace `## Error handling` placeholder)

- [ ] **Step 1: Write the error-handling section**

````markdown
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
````

- [ ] **Step 2: Smoke test corrupted JSON branch**

```bash
echo "{broken" > /tmp/todoist-sync-smoke/.claude/todoist-session.json
```
In CC: `/update-todo whatever`
Expected: raw parse error surfaced, file untouched.

- [ ] **Step 3: Smoke test missing-task branch**

Bind to a fresh throwaway task. Then in the Todoist app, **delete** that task. In CC: `/update-todo test missing task`.
Expected: "Bound task is missing from Todoist. Clear session?" prompt.

- [ ] **Step 4: Smoke test cwd-mismatch warning**

```bash
mv /tmp/todoist-sync-smoke /tmp/todoist-sync-smoke-renamed
cd /tmp/todoist-sync-smoke-renamed
```
In CC: `/update-todo cwd renamed`
Expected: warning line about cwd mismatch, then comment posted normally.

---

## Task 9: End-to-end smoke test on a fresh task

**Files:** None (verification only).

- [ ] **Step 1: Fresh throwaway task**

Create a new Todoist task: `[smoke-e2e] todoist-sync end-to-end`. Note its URL.

- [ ] **Step 2: Fresh empty cwd**

```bash
rm -rf /tmp/todoist-sync-e2e
mkdir -p /tmp/todoist-sync-e2e && cd /tmp/todoist-sync-e2e
git init
```

- [ ] **Step 3: Walk the full happy path in CC**

Sequence:
1. `/start-todo <url>` → reply `yes` to confirm binding
2. CC: "create a file called notes.md with 3 bullet points about anything"
3. After CC creates and commits → milestone comment should fire
4. `/update-todo finished outline`
5. CC: "now expand bullet 1 into a paragraph"
6. After CC commits → another milestone
7. Say `搞定` → CC should propose closing
8. Reply `yes` → CC enters Path A preview
9. Reply `yes` to closing confirm → task closes

- [ ] **Step 4: Verify final state**

In Todoist app, the smoke task should show:
- 🟢 Session started ...
- ✅ <first commit milestone>
- 📝 finished outline
- ✅ <second commit milestone>
- 🏁 Done. <summary>. ...

And the task itself is marked completed.

In `/tmp/todoist-sync-e2e/.claude/`:
- `todoist-session.json` is gone
- `todoist-session.json.<task_id>.<ts>.done` exists

- [ ] **Step 5: Clean up smoke tasks**

Delete the throwaway tasks from Todoist trash (or leave them — they're closed).

---

## Self-review (for the plan author, not the executor)

After writing the plan above, the author runs this checklist before handoff:

- [x] **Spec coverage:**
  - `/start-todo` → Task 2 ✓
  - `/update-todo` → Task 3 ✓
  - Milestone auto-detection (6 triggers, 4 anti-triggers, debounce, per-turn cap, retry queue) → Task 4 ✓
  - `/done-todo` Path A → Task 5 ✓
  - `/done-todo` Path B (CC proposes) → Task 6 ✓
  - State schema + atomic write + archive → Task 7 ✓
  - Error handling + edge cases → Task 8 ✓
  - End-to-end happy path → Task 9 ✓

- [x] **Placeholder scan:** No TBD / TODO / "handle appropriately" — every step has either concrete instruction text to embed in SKILL.md or a concrete smoke-test command.

- [x] **Type consistency:** `task_id`, `task_content`, `last_activity_at`, `milestones[].type`, `comment_id`, `sync_failed` — all spelled consistently across Tasks 2-8.

- [x] **Positive-feedback closed set used identically** in Tasks 2 (binding confirm), 5 (closing confirm), 6 (Path B confirm): `yes / confirm / go / 好 / 可以 / 搞定 / 没问题 / done / ship it`. Path B *trigger* (turn-classification) uses a smaller set: `好 / 可以 / 搞定 / 没问题 / done / ship it` only — no `yes/confirm/go`. This is correct: confirmation words like `yes` don't indicate "I think this work is done", they indicate "I confirm a question".

- [x] **No automated tests:** acknowledged at the top. All verification is manual smoke tests.

---

## Execution Note

Because every task involves real MCP calls to a live Todoist account and real Claude Code sessions, this plan is **not safe to dispatch to a fresh subagent without a human in the loop** — the smoke tests need someone to (a) create throwaway tasks, (b) read the Todoist UI to verify comment ordering, (c) decide when to type `yes`. Inline execution with you driving each verification step is the realistic mode here.
