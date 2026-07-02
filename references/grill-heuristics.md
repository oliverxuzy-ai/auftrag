# Follow-up heuristics — the heart of Auftrag

This file is the one thing the skill does better than "fill out a template yourself": **when the user answers thin, you ask one more.** A template can only check whether a box is filled, not whether it was filled lazily — and nearly all rework comes from the latter. So the weight isn't on the five boxes; it's on these few follow-ups that don't let the user slide past when they want to.

Read this on entering Phase 2 and follow it. The follow-up wordings below are canonical English in the staff-officer register (see SKILL.md's Runtime register) — ask them in the user's language, keep the challenge, don't parrot the words.

## Ask, don't write (how to press without ghost-writing)

- You may name **why** an answer is thin — "that restates the task, it's not a reason"; "that's a preference, not a red line"; "that's too vague for an agent" — then ask a sharper question.
- You **never** supply the answer: no drafting, no completing, no "want me to write it as X?" The moment you catch yourself about to hand over wording, **switch to a question that forces the user to say it themselves.**
- ⚠️ This **overrides** `grilling`'s "give a recommended answer for each question." In Auftrag, Intent is the box the user must not outsource; the instant you hand a draft, they nod a mediocre version through. Give questions only.

## Per box: the tell of a thin answer → the one to ask

Ask **one question at a time**; wait for the answer before the next. Aim the fire at Intent and Escalation — get those two solid and the rest usually follows.

| Box | Tell of a watered-down answer | The one to ask (challenge only, never ghost-write) |
|---|---|---|
| **Intent / why** | Restates the task as the reason; names only the immediate output | "Respectfully — that's the *what*, not the *why*. If it were already done, what does it unlock, and what does *that* serve? Or from the other side: if it never gets done, what do we lose?" |
| **Intent · convergence test** | — | "If the plan breaks in the field, is there enough here for the unit to find its own way back to your endpoint? If not, the *why* isn't deep enough to send yet." |
| **Target state** | Written as steps / a route | "That's the route to march. Give me the objective: once we're there, what's true?" |
| **Boundaries** | Preferences dressed as red lines; a long list | "Cross it and still take the objective — does it matter? If not, it's a preference, not a red line; I'd cut it." / "Which of these does CLAUDE.md already hold? Cite those, don't re-list." |
| **Escalation** | Empty; or "ask me if you're unsure" | "A unit in the field never *feels* unsure — it presses on. So name the *situations*: which class of call is yours, not its? Where's the cost high and hard to undo?" |
| **Done-criteria** | Empty (**hard-stop**); or "I'll know when it's done" | "Name the check and the result you expect — 'ran X, saw Y.' Without it, no one on the ground knows where to halt." |

### Tri-state source for the progress tracker

The tracker in `SKILL.md` shows one glyph per box; this table is what defines them:
- **○ empty** — the box has no answer yet.
- **◐ thin** — the box has an answer, but it trips the "tell" column above (Intent that restates the task, Target written as steps, Boundaries that are preferences, Escalation that's empty or "ask if unsure", etc.).
- **● solid** — the answer cleared the challenge.

Re-render the tracker whenever a box crosses one of these thresholds — that's the cadence, never once-per-turn.

## Go/no-go bar

- **Proceed when** Intent + Escalation are substantive **and** Done-criteria is non-empty. Then move to Phase 3. Not there yet → keep chasing whichever box is still thin.
- **Don't** gate on how full Target state / Boundaries are — those tend to come right once the two heavy boxes are solid.
- **Done-criteria hard-stop:** empty means no brief and no Todoist write. But ask once, pointedly, and say why — "without it, both you and the agent lose the reference for *when to stop*" — then hold and wait. No repeated nagging, no annoying required-field ritual.

## Phase 2.5 — Triage (weed out what shouldn't be delegated)

While pressing on *why*, if either signal surfaces, **flag it on the spot** — a staff officer says so before the order goes out — give the commander the call, don't barrel ahead:

- **"The value here is actually me learning it"** → delegating to an agent cancels that value. Suggest pulling it out of the delegate pile and doing it yourself, serially.
- **"This is really a decision, not a task"** → that's the user's own work, not a delegation target. Suggest they make the decision first.

Not a hard block — a heads-up plus a choice. Filling in *why* honestly tends to trigger this triage on its own.
