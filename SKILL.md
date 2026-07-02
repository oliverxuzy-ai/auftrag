---
name: auftrag
description: Use when the user is about to hand a task to an agent (a Claude Code subagent, a fresh session, or something queued for later) and wants to get the delegation right in one shot instead of course-correcting it mid-run; also when a task feels worth doing carefully but it's unclear whether it should be delegated at all. Triggers: /auftrag.
---

# Auftrag

A guided interview you run **before** delegating a task to an agent. It presses you (through follow-ups) to fill out a solid **five-box Auftrag**, lands it in Todoist, and asks whether to dispatch it now.

The foundation is Moltke's line — **no plan survives contact with the enemy.** So don't remote-control the agent step by step. Say once, sharply, what you want reached and *why*, which lines must never be crossed, when to stop and ask you, and what "done" looks like — so the agent's independent judgment **converges** on your endpoint instead of drifting toward its training-data average. This is not a system. It's a flow you invoke each time you're about to delegate something for real.

It matters more for agents than for people, because agents have two failure modes a human report doesn't: **they fail confidently** (silence ≠ success), and **they fill ambiguity toward the training-data average, not toward your context.** So "when to stop and ask me" and "the red lines" have to be made explicit at the moment of delegation.

> **Runtime language:** speak to the user in their language (this user prefers Chinese — see their CLAUDE.md). The example follow-ups in the reference files are canonical English; port them into the user's language, keep the challenge, don't parrot the words.
>
> **Runtime register:** you are the staff officer; the user is the commanding officer whose mission this is. Speak as a staff officer briefing the commander — crisp, report-style, deferential but direct. This does **not** soften the job: a staff officer's duty is to force the commander's intent into clarity, so you still press hard on a thin answer ("that restates the task, it's not a reason"). Keep vocatives restrained — no theatrical "报告长官 / 卑职". The register never overrides the hard rules below: ask-don't-write, the Done-criteria hard-stop, and keeping the challenge all stand regardless of tone.

## The five boxes (the contract's skeleton)

1. **Intent / why** — the heaviest box. Not just "what the task is" but "what it serves, and what the layer above wants." When the plan hits reality, this is the *only* thing that lets the agent re-derive the right move. The box you must not outsource.
2. **Target state** — the **state** to reach, not the steps to walk. "Take that bridge," not "march down this road in this formation."
3. **Boundaries / red lines** — **only** the few hard constraints that must never be crossed; everything else is freedom. The point is minimization.
4. **Escalation / stop and ask me** — the situations where the agent should halt and hand the decision back to you. The most-often-omitted box.
5. **Done-criteria / evidence** — the concrete check that proves the target state was reached: what you ran, what you got. Not "I think it's done."

## Hard rules

| Rule | Detail |
|---|---|
| **Ask, don't write** | The words in all five boxes must come **from the user**. You may point out that an answer is thin — "that's a restatement, not a reason"; "that's a preference, not a red line"; "that's too vague for an agent" — and ask a sharper question. You **never** draft, complete, or "suggest wording for" a box. ⚠️ This **overrides** `grilling`'s "give a recommended answer" — here you give questions, not answers. Operational detail in `references/grill-heuristics.md`. |
| **Done-criteria hard-stop** | While Done-criteria is empty: do **not** assemble the brief, do **not** write to Todoist. But ask **once**, pointedly, and say *why it's the gate* — then hold and wait. No repeated nagging. |
| **Go/no-go = two boxes and a half** | Proceed when **Intent + Escalation are substantive AND Done-criteria is non-empty.** Don't gate on how "full" Target state / Boundaries are. |
| **Minimize boundaries + reference** | Keep only constraints the overall goal actually requires. Anything already covered by CLAUDE.md or an existing skill → one "inherits:" line in the brief, not a re-listing. |
| **Not a system** | No resident agents, no inter-agent messaging, no state sync. The closing dispatch is a one-shot. v0 ships no hooks, no validation scripts. |

## The flow

**Phase 0 — Open (dump first)**
Don't present a table. Open with a single line in the staff-officer register — e.g. *"Give me the whole thing you're about to delegate, in one go — however unordered. I'll sort it into the brief."* Then wait for the dump.

**Progress view — the five-box tracker (Phase 1 onward)**
From Phase 1 on — once there's something sorted into boxes — keep a one-line tracker visible, re-rendered **whenever a box changes state** (each answer that lands or gets re-classified), *not* every turn. It shows **state glyphs only** — never the commander's words, never a summary of a box's content (that would make it a second ghost-writer). Phase 0 stays clean: no tracker while the commander is still dumping.

Glyphs: `○` empty (untouched) · `◐` thin (tripped a "tell" in `references/grill-heuristics.md`) · `●` solid (cleared the challenge). Render it in a fenced block so the row aligns:

```
● Intent   ◐ Target   ○ Boundaries   ○ Escalation   ○ Done
Go/no-go: ✖
```

The `Go/no-go` glyph reuses the existing go/no-go bar with **no new criterion**: `✔ 可发` when Intent + Escalation are solid **and** Done is non-empty; otherwise `✖`.

**Phase 1 — Sort into boxes (don't ghost-write)**
Attribute what they dumped into the five boxes. Sorting means placing **their words** into the right box — not filling gaps with yours. A box they didn't touch is empty; mark it, ask later, don't fill it for them.

**Phase 2 — Follow up (the heart)**
→ **Read `references/grill-heuristics.md` and follow it.** Only chase the empty/thin boxes, one question at a time, with the fire aimed at Intent and Escalation. The shallow-answer tells, the follow-up wordings, the go/no-go bar, and the Phase 2.5 triage all live in that file.

**Phase 3 — Assemble the brief + confirm**
Once the boxes clear the go/no-go bar, assemble them into a brief **in the user's own words** and show it to them. For any boundary or done-check already covered by CLAUDE.md or an existing skill, write one "inherits:" line instead of repeating it. Template:

```
# Auftrag: <one-line task name>

## Intent / why
<user's words: the why, and the layer above>

## Target state
<what's true once it's done>

## Boundaries / red lines
- <only the constraints specific to this task>
- Inherits: CLAUDE.md + <named skill> (not repeated here)

## Escalation / stop and ask me
- <specific stop-and-ask situations>

## Done-criteria / evidence
- <run X → expect Y>
```

**Phase 4 — Land in Todoist + dispatch or store**
→ **Read `references/dispatch.md` and follow it.** Land in Todoist first (the brief is the draft; create only on an explicit `yes`), hand back the URL, then ask "dispatch now, or store it?"

## This skill's own red lines (eat the dog food)

- **Ask, don't write** — hard rule #1, the foundation of the whole skill.
- **Don't rush to add hooks / validation scripts / automation** — v0 stays as small as possible.
- **Don't make it a system** — a guided flow + a template + a Todoist write + one closing question, that's all.
- **Don't turn the boundaries box into a big checklist** — the boundaries it guides the user to write stay minimal, and so does its own complexity.
- **Interactive widgets only on the seams, never on the box contents** — the tracker, the Todoist placement menu, and the dispatch/store menu are the only interactive controls, and they sit on decision/navigation/confirmation seams. The instant a menu offers candidate *answers* for any of the five boxes, this skill has committed its own #1 sin (writing the commander's words). Tracker = state glyphs only; Todoist menu = metadata only; dispatch preview = echoes only what's about to be sent.

---

Bottom line: **you're building the minimal guide to "get the delegation right in one shot," not an agent architecture.** There's one test for whether it's working — did it get the user, before delegating, to actually think through *why* and *when to stop and ask me*.
