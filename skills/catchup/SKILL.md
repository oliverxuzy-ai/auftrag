---
name: catchup
description: O(1) re-entry into one delegated task - answers "why did I dispatch this, where is it now, what do you need from me" in 30 seconds. Use when the user switches back to a task and has lost the thread, asks "这个任务到哪了 / 我刚才要干嘛", or on /catchup. Input: Todoist task URL/ID; with no argument, take the top item of /board.
argument-hint: "<todoist-task-url | task-id>"
---

# Catchup — re-entry in 30 seconds

Context-switch amnesia isn't a memory problem; it's state living in the head instead of the system. This skill reads the state back. Budget: **≤15 lines**, three sections, hard order. No argument → run the board's gather step and take its top item.

Sources: the Todoist task (description = the contract, comments = the history, labels = the state), plus `.claude/auftrag/state.json` in the worktree when a comment names one.

## Output — exactly three sections

**1. 当初为什么派 (2–3 lines).** The contract's Intent box, quoted in the commander's own words — not summarized into new words (re-entry works by recognition). Plus one line of Target state.

**2. 现在到哪了 (3–5 lines).** Current state label, plainly: 在野 / 等你拍板 / 翻车 / 待验收 / 存档未派. The last meaningful event with its timestamp (gate passed, memo posted, verdict landed, attempts count from state.json). Worktree/branch/PR if in play.

**3. 此刻要你做什么 (1–3 lines).** Exactly one action, imperative, with its handle ready to paste:
- blocked → the memo's question + "拍板后回给执行者" (reply / redispatch with the decision)
- red → the gap, one line + `/auftrag` to re-brief or resume the executor
- green → the first `evidence:` item to look at + accept or `/abnahme` if no verdict yet
- running → "不需要你。回去做别的。" — that is a valid and common answer; don't invent involvement.

## Rules

- Never re-open the interview, never edit the contract, never message the executor unprompted — this skill only *reads*.
- If the trail is broken (no contract in the description, no comments), say which piece is missing and point at the fix (`/auftrag` to re-brief), don't reconstruct from guesswork.
