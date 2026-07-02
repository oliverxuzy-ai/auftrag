# Auftrag Terminal Interactions — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add three terminal-native interactive touchpoints to the auftrag skill — a states-only five-box progress tracker, a clickable Todoist placement menu, and a dispatch/store menu with previews — without ever letting a widget author a box's contents.

**Architecture:** auftrag is a prose-instruction skill (Markdown read by an LLM at runtime), not runnable code. This plan edits three Markdown files (`SKILL.md`, `references/grill-heuristics.md`, `references/dispatch.md`) so that the runtime model renders the existing Claude Code interactive controls (`AskUserQuestion` single/multi-select with `preview`, a re-rendered monospace tracker row) at the flow's decision/navigation/confirmation seams. No new files, no hooks, no validation scripts.

**Tech Stack:** Claude Code skill authored in Markdown. Runtime control surface = the `AskUserQuestion` tool + fenced code-block rendering in the terminal. No test runner exists and none is added (the skill's own v0 red line forbids validation scripts) — verification is ad-hoc `rg`/`grep` assertions plus a scripted manual dry-run, run during implementation and **not committed**.

## Global Constraints

Every task's requirements implicitly include this section. Values copied from the existing skill red lines + the design spec (`docs/superpowers/specs/2026-07-02-auftrag-terminal-interactions-design.md`).

- **Ask, don't write** — the words in all five boxes come from the user; never draft, complete, or suggest wording for a box. This is hard rule #1.
- **The new invariant (命门):** interactive widgets go **only** on decision/navigation/confirmation seams — the tracker, the Todoist placement menu, the dispatch/store menu. **Never** put a box's candidate *answers* into a menu. Tracker = state glyphs only; Todoist menu = metadata only; dispatch preview = echoes only what's about to be sent.
- **Done-criteria hard-stop** — empty Done ⇒ no brief, no Todoist write; ask once, say why, hold.
- **Go/no-go bar** — proceed when Intent + Escalation are substantive **and** Done is non-empty. The tracker's `✔/✖` reuses exactly this criterion, no new gate.
- **Not a system / v0 minimal** — no resident agents, no messaging, no state sync, **no hooks, no validation scripts**. (This is why verification below is ad-hoc grep + manual dry-run, nothing committed.)
- **Minimize boundaries** — unchanged; anything CLAUDE.md/an existing skill already covers → one `inherits:` line.
- **Runtime language = Chinese** (user CLAUDE.md); **staff-officer register**. Skill files stay in their current voice (English canonical prose + Chinese runtime examples).
- **Commits:** no `Co-Authored-By` line (user global CLAUDE.md).

---

### Task 1: Five-box tri-state tracker + the governing invariant

**Files:**
- Modify: `SKILL.md` — add the invariant bullet to `## This skill's own red lines (eat the dog food)`; add the tracker subsection inside `## The flow` (between Phase 0 and Phase 1).
- Modify: `references/grill-heuristics.md` — add the tri-state source note after the `## Per box` table.

**Interfaces:**
- Produces: the tracker's contract that Tasks 2–3 rely on for tone — glyph set `○ ◐ ●`, the `Go/no-go: ✔/✖` line, and the invariant bullet those later tasks cite ("menu on seams, never box contents").
- Consumes: nothing (first task).

- [ ] **Step 1: Write the failing checks (they should all fail now)**

Run:
```bash
cd /Users/zhengyangxu/Desktop/side_project/auftrag
rg -n "Progress view — the five-box tracker" SKILL.md
rg -n "Interactive widgets only on the seams" SKILL.md
rg -n "Tri-state source for the progress tracker" references/grill-heuristics.md
```
Expected: all three print nothing (exit 1) — the anchors don't exist yet.

- [ ] **Step 2: Add the invariant bullet to SKILL.md's red-lines section**

In `SKILL.md`, find the `## This skill's own red lines (eat the dog food)` list and append this bullet as the **last** item in that list (after the `Don't turn the boundaries box into a big checklist` bullet):

```markdown
- **Interactive widgets only on the seams, never on the box contents** — the tracker, the Todoist placement menu, and the dispatch/store menu are the only interactive controls, and they sit on decision/navigation/confirmation seams. The instant a menu offers candidate *answers* for any of the five boxes, this skill has committed its own #1 sin (writing the commander's words). Tracker = state glyphs only; Todoist menu = metadata only; dispatch preview = echoes only what's about to be sent.
```

- [ ] **Step 3: Add the tracker subsection to SKILL.md's flow**

In `SKILL.md`, inside `## The flow`, insert this block **between** the end of the Phase 0 paragraph (`...Then wait for the dump.`) and the `**Phase 1 — Sort into boxes (don't ghost-write)**` line:

````markdown
**Progress view — the five-box tracker (Phase 1 onward)**
From Phase 1 on — once there's something sorted into boxes — keep a one-line tracker visible, re-rendered **whenever a box changes state** (each answer that lands or gets re-classified), *not* every turn. It shows **state glyphs only** — never the commander's words, never a summary of a box's content (that would make it a second ghost-writer). Phase 0 stays clean: no tracker while the commander is still dumping.

Glyphs: `○` empty (untouched) · `◐` thin (tripped a "tell" in `references/grill-heuristics.md`) · `●` solid (cleared the challenge). Render it in a fenced block so the row aligns:

```
● Intent   ◐ Target   ○ Boundaries   ○ Escalation   ○ Done
Go/no-go: ✖
```

The `Go/no-go` glyph reuses the existing go/no-go bar with **no new criterion**: `✔ 可发` when Intent + Escalation are solid **and** Done is non-empty; otherwise `✖`.

````

- [ ] **Step 4: Add the tri-state source note to grill-heuristics.md**

In `references/grill-heuristics.md`, insert this block **between** the end of the `## Per box: the tell of a thin answer → the one to ask` table and the `## Go/no-go bar` heading:

```markdown
### Tri-state source for the progress tracker

The tracker in `SKILL.md` shows one glyph per box; this table is what defines them:
- **○ empty** — the box has no answer yet.
- **◐ thin** — the box has an answer, but it trips the "tell" column above (Intent that restates the task, Target written as steps, Boundaries that are preferences, Escalation that's empty or "ask if unsure", etc.).
- **● solid** — the answer cleared the challenge.

Re-render the tracker whenever a box crosses one of these thresholds — that's the cadence, never once-per-turn.
```

- [ ] **Step 5: Run the checks to verify they now pass, and the guards hold**

Run:
```bash
cd /Users/zhengyangxu/Desktop/side_project/auftrag
rg -n "Progress view — the five-box tracker" SKILL.md
rg -n "Interactive widgets only on the seams" SKILL.md
rg -n "Tri-state source for the progress tracker" references/grill-heuristics.md
# Guard: Phase 0 must still forbid a table (tracker must not have leaked into Phase 0)
rg -n "Don't present a table" SKILL.md
# Guard: tracker must be states-only — no instruction to echo the user's words into it
rg -n "state glyphs only" SKILL.md
```
Expected: first three now print their lines (exit 0); `Don't present a table` still present (Phase 0 unchanged); `state glyphs only` present.

- [ ] **Step 6: Manual dry-run acceptance (observe, don't automate)**

In a fresh Claude Code session, run `/auftrag` and dump a one-line task. Expected observable behavior:
- Phase 0 shows **no** tracker (just the "dump it all" open line).
- After the dump is sorted (Phase 1), a tracker row appears in a fenced block, e.g. `● Intent   ○ Target   ○ Boundaries   ○ Escalation   ○ Done` with `Go/no-go: ✖`.
- The tracker row contains **none** of your actual words — glyphs + box names only.
- As you answer follow-ups, the row re-renders only when a box's glyph changes; it flips to `Go/no-go: ✔ 可发` exactly when Intent + Escalation are solid and Done is non-empty.
If the tracker paraphrases your Intent, or appears during Phase 0, the states-only / Phase-0-clean guards were violated — fix before committing.

- [ ] **Step 7: Commit**

```bash
cd /Users/zhengyangxu/Desktop/side_project/auftrag
git add SKILL.md references/grill-heuristics.md
git commit -m "feat(auftrag): add states-only five-box tracker + seam invariant"
```

---

### Task 2: Todoist placement as a clickable menu (dispatch.md Step 2)

**Files:**
- Modify: `references/dispatch.md` — replace the one-line-proposal paragraph in `## Step 2 — Land in Todoist first (always happens)` with an `AskUserQuestion` shape. Keep the `find-projects` call, the `add-tasks` code block, the URL hand-back, and the MCP-failure rule unchanged.

**Interfaces:**
- Consumes: the invariant from Task 1 ("menu = metadata only").
- Produces: nothing later tasks depend on (Step 3 is independent).

- [ ] **Step 1: Write the failing check**

Run:
```bash
cd /Users/zhengyangxu/Desktop/side_project/auftrag
rg -n "AskUserQuestion" references/dispatch.md
```
Expected: prints nothing (exit 1) — dispatch.md has no menu yet.

- [ ] **Step 2: Replace the one-line proposal with the menu**

In `references/dispatch.md`, in `## Step 2`, replace exactly this paragraph:

```markdown
Report it in one line — *"Proposed placement: `<project>` · `<priority>` · `<due>`. Confirm, or redirect?"* — and create only on the commander's `yes`. If nothing clearly fits, fall back to the inbox and ask which project in one line. Then create:
```

with:

```markdown
Put the placement in front of the commander as **one `AskUserQuestion` call** (up to two questions) — a click, not a line to read back:

- **项目 (single-select)** — the ≤3 best-matched projects from `find-projects`, best match first and labeled `(推荐)`. `Other` (auto-provided by the tool) covers any other project or the inbox.
- **优先级 (single-select)** — `p1` / `p2` / `p3` / `p4`, with the value read off the brief's urgency/ticket signals placed first; no signal → `p4` default.

Do **not** menu the due/deadline — only when the brief implies a time, ask one text line afterward (`dueString` for a soft schedule, `deadlineDate` `YYYY-MM-DD` for a hard constraint). The menu answers **are** the explicit confirmation; Esc → don't create. This is still a recommendation, never a silent auto-set — the menu just makes the recommendation clickable. If nothing matched, the recommended option is the inbox. Then create:
```

- [ ] **Step 3: Run the check to verify it passes, and the guards hold**

Run:
```bash
cd /Users/zhengyangxu/Desktop/side_project/auftrag
rg -n "AskUserQuestion" references/dispatch.md
# Guard: metadata-only — the menu must cover project/priority, never the brief body
rg -n "单选|single-select" references/dispatch.md
# Guard: recommend-not-auto-set principle preserved
rg -n "never a silent auto-set|recommendation, never a silent" references/dispatch.md
# Guard: add-tasks + MCP-failure rules untouched
rg -n "add-tasks" references/dispatch.md
rg -n "don't claim success" references/dispatch.md
```
Expected: `AskUserQuestion` present; project/priority single-selects present; the auto-set guard line present; `add-tasks` and `don't claim success` still present (unchanged).

- [ ] **Step 4: Manual dry-run acceptance**

Continue an `/auftrag` run to Phase 4 with the boxes cleared. Expected observable behavior:
- The skill reads the project list, then presents an `AskUserQuestion` with a **项目** single-select (recommended project first, `(推荐)`) and a **优先级** single-select (`p1`–`p4`).
- The menu offers **no** field that restates or edits the brief body — project + priority (+ optional due as free text) only.
- Picking options creates the task via `add-tasks`; Esc creates nothing; the task URL is handed back.
If the menu ever offers to reword the brief/Intent, the metadata-only guard was violated.

- [ ] **Step 5: Commit**

```bash
cd /Users/zhengyangxu/Desktop/side_project/auftrag
git add references/dispatch.md
git commit -m "feat(auftrag): Todoist placement as project/priority menu"
```

---

### Task 3: Dispatch/store as a single-select menu with previews (dispatch.md Step 3)

**Files:**
- Modify: `references/dispatch.md` — rewrite the ask in `## Step 3 — Ask "dispatch now, or store?"` into an `AskUserQuestion` single-select with `preview` on each option. Keep the Store bullet's `/start-todo` explanation and the Dispatch path unchanged.

**Interfaces:**
- Consumes: the invariant from Task 1 ("preview echoes only what's about to be sent"); the escalation-prepend paragraph already defined lower in `dispatch.md` under "Dispatching a subagent".
- Produces: nothing (terminal task).

- [ ] **Step 1: Write the failing check**

Run:
```bash
cd /Users/zhengyangxu/Desktop/side_project/auftrag
rg -n "preview" references/dispatch.md
```
Expected: prints nothing (exit 1) — no preview wiring yet.

- [ ] **Step 2: Rewrite the Step 3 ask as a preview menu**

In `references/dispatch.md`, replace exactly this heading + intro:

```markdown
## Step 3 — Ask "dispatch now, or store?"

- **Store** → it's in Todoist; that's the mission on file. End your report with the one command that resumes it — ready to paste, nothing to retype:
```

with:

```markdown
## Step 3 — "Dispatch now, or store?" (menu with preview)

Ask with **one `AskUserQuestion` single-select** (single-select is what enables `preview`), so the commander sees the actual artifact of each path before choosing:

- **「派发 now」** — `preview` = the exact mission prompt the Agent tool will receive: the escalation-prepend paragraph (see "Dispatching a subagent" below) + the full brief markdown.
- **「存档」** — `preview` = the resume line, verbatim: `/start-todo <task_url>`.

No third option; Esc = cancel. Then act on the choice:

- **Store** → it's in Todoist; that's the mission on file. End your report with the one command that resumes it — ready to paste, nothing to retype:
```

(The rest of the Store bullet — the `/start-todo <task_url>` code block and its "do not re-describe the task" note — and the `**Dispatch now** → below.` line stay exactly as they are.)

- [ ] **Step 3: Run the check to verify it passes, and the guards hold**

Run:
```bash
cd /Users/zhengyangxu/Desktop/side_project/auftrag
rg -n "preview" references/dispatch.md
# Guard: single-select (preview only works single-select)
rg -n "single-select" references/dispatch.md
# Guard: preview echoes only what's sent — the two artifacts must both be named
rg -n "escalation-prepend paragraph|/start-todo <task_url>" references/dispatch.md
# Guard: Store path's resume-line discipline still intact
rg -n "do not|Do \*\*not\*\* re-describe" references/dispatch.md
```
Expected: `preview` present; `single-select` present; both artifact names present; the Store resume-line discipline still present.

- [ ] **Step 4: Manual dry-run acceptance**

Run `/auftrag` through to Step 3 (task already landed in Todoist). Expected observable behavior:
- A single-select menu appears with `派发 now` and `存档`.
- Focusing `派发 now` shows a `preview` containing the escalation prefix + the full brief (i.e., exactly what the subagent would get).
- Focusing `存档` shows a `preview` of `/start-todo <the task url>`.
- Choosing `派发` dispatches via the Agent tool with the escalation prepend; choosing `存档` ends with the `/start-todo` line; Esc cancels.
If a preview shows anything other than the about-to-be-sent artifact (e.g., it drafts new brief content), the preview-echo guard was violated.

- [ ] **Step 5: Commit**

```bash
cd /Users/zhengyangxu/Desktop/side_project/auftrag
git add references/dispatch.md
git commit -m "feat(auftrag): dispatch/store menu with previews"
```

---

## Deploy note (after all tasks)

`~/.claude/skills/auftrag/` is a **copy** of this repo (not a symlink), installed per `INSTALL.md`. The edits above land in the repo only; to make them live, re-run the install/copy step from `INSTALL.md` (or copy `SKILL.md` + `references/` into `~/.claude/skills/auftrag/`). Not a task — a reminder so the live skill actually picks up the changes.

## Self-Review

- **Spec coverage:** Feature 1 (tracker) → Task 1; Feature 2 (Todoist menu) → Task 2; Feature 3 (dispatch/store preview) → Task 3; the命门 invariant → Task 1 Step 2 + cited as a guard in Tasks 2–3; tri-state source → Task 1 Step 4; non-goals (no HUD, no Phase 2.5 widget, no ExitPlanMode, no new files) → honored by construction (only three existing files touched). All four spec acceptance criteria map to the per-task dry-run steps.
- **Placeholder scan:** every edit shows the literal Markdown to insert and the exact text to replace; verification steps are runnable `rg` commands with expected exit behavior; no "TBD"/"similar to Task N".
- **Consistency:** glyph set `○ ◐ ●`, the `Go/no-go: ✔/✖` line, and the invariant wording are defined once in Task 1 and referenced (not redefined) by the guards in Tasks 2–3; `AskUserQuestion` single-select is the surface in both Task 2 and Task 3.
