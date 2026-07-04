---
name: board
description: The exception queue (Meldung) - one screen showing only what needs the commander, ordered by cost of delay. Use when the user asks "what needs me", "现在轮到我什么", wants a status sweep across delegated tasks, or on /board. Reads Todoist agent:* labels; never polls sessions.
---

# Board — the Meldung

One screen, exceptions only, ordered by what your delay costs. The commander never polls sessions; the pipeline reports. (Raw session view when wanted: `claude agents` — that's the fleet; this is the *exception* queue.)

## Gather

Query Todoist for open tasks by label (`find-tasks` with label filters), one call per state:
`agent:blocked` · `agent:red` · `agent:green` · `agent:running` · `lane:learn`.
For blocked/red/green items, pull the **latest comment** (staff memo / gap report / verdict) — the queue line must say *what is being asked*, not just that something is.

## Render — a fenced block, ordered by delay cost

```
MELDUNG — <date>                        WIP: <running>/3
──────────────────────────────────────────────────────────
► 等你拍板 (blocked — an agent is stalled on you)
  1. <task>  — <the decision, one line, from the memo>   [~<min> min]  <age>
► 翻车待重派 (red — gate/Abnahme rejected)
  2. <task>  — <the gap, one line>                        [redispatch]  <age>
► 待验收 (green — batch these)
  3. <task>  — <evidence: first item>          [~<min> min · <full|sample>]
──────────────────────────────────────────────────────────
在野 (running, FYI only): <n> — <names, comma-run>
串行学习队列 (lane:learn): <top item> (+<n> more)
```

Rules:
- **Order is doctrine**: blocked > red > green. A blocked item stalls an agent *and* a mission; a red item stalls a mission; a green item stalls nothing.
- Per line: task name · one clause of "what's asked" · predicted minutes (from the contract's `evidence:` recipe; guess conservatively when absent) · age since the state transition (comment timestamp).
- Green lines carry the acceptance bar from the contract's `risk:` field — `full` (irreversible, or a task type's first 5) vs `sample`. If ledger history (`~/.claude/auftrag/ledger.jsonl`) shows a recent false-green in this task's type, mark it `full` and say why.
- Empty queue → one line: "Nichts zu melden — nothing needs you. <n> in the field." Never pad.
- Running tasks are a footer, names only. They need nothing; don't make them compete for attention.

## Closing

End with the single highest-leverage next action, ready to paste: `/catchup <task>` for the top item, or `/abnahme <task>` if greens are piling up unverified. One suggestion, not a menu.
