# Auftrag skill — design doc

> Records **why it's shaped this way**, which decisions were made, and what v0 deliberately skips.
> Operational detail (follow-up wordings, flow, template) is in `../SKILL.md` and `../references/`; the original intent is in `../CONCEPT.md`.
> This doc doesn't repeat SKILL.md's content — it records the trade-offs.

Date: 2026-07-01 · Status: v0 design confirmed, building

---

## 1. The problem, in one line

When delegating to an agent, nearly all rework comes from **the "why" and the "when to stop and ask me" boxes being answered lazily** — not omitted, just filled with a correct-sounding nothing. The one thing this skill does better than "fill out a template yourself" is: **you answer thin, it asks one more.** So the design weight isn't the five boxes; it's those few follow-ups.

There's one test for whether the skill is right: **did it get the user, before delegating, to actually think through *why* and *escalation*.**

## 2. Three confirmed key decisions

| Decision | Choice | Rationale / what was rejected |
|---|---|---|
| **Task backend** | **Todoist** | Specified by the concept doc; the `todoist-sync` skill already exists; the MCP tools are wired. Rejected Linear — although the current CLAUDE.md names Linear, its MCP isn't authorized yet, and both the concept and the existing tooling point at Todoist. ⚠️ See "Tension with CLAUDE.md" (§8). |
| **Interview shape** | **Dump-then-grill** | User dumps freely; the skill sorts into the five boxes and chases only the empty/thin ones. Fast, and it surfaces the "this shouldn't be delegated" triage early. Rejected box-by-box (slow, questionnaire-feeling, more likely to elicit lazy fill-in). |
| **What "dispatch now" does** | **Spawn a subagent via the Agent tool** | The user's explicit choice. A one-shot dispatch; doesn't violate "don't build a resident system." Rejected "just produce the brief and let the user launch it" (more minimal, but the user wanted it in one step). |

## 3. Structure decisions

- **A thin `SKILL.md` orchestrator + two on-demand reference files, pure prompt.** No hooks, no validation scripts. The seams follow **rate of change**, not chapters:
  - `references/grill-heuristics.md` — the follow-up heuristics (the crown jewel, iterated most; loaded only on entering Phase 2).
  - `references/dispatch.md` — the Phase 4 Todoist + subagent-dispatch plumbing (a backend swap touches only this).
  - `SKILL.md` keeps the near-static parts: the five-box definitions, the hard rules, the five-phase skeleton, and the brief template (short, kept inline).
  Cutting on rate-of-change — separating the fastest-changing part (the follow-up table) from the near-static doctrine — is the one real smell in the original monolith; the split fixes it. It's still **one skill, one continuous interview**, not multiple skills / a system (which would hit concept boundary #3).
- **The description field states only *when to use*, no workflow summary.** Per the `writing-skills` lesson: a description that summarizes the flow makes agents take a shortcut and skip the skill body — worse after the split, because they'd skip the references. So the description is trimmed to pure triggering conditions.
- **English source; runtime speaks the user's language.** The skill text is English (skills are shareable artifacts). The example follow-ups are canonical English that the running agent ports into the user's language (Chinese, per CLAUDE.md). A one-line runtime-language note in SKILL.md carries this.
- **Repo name `auftragstaktik` (the doctrine); skill name `auftrag` (one concrete order / mission).** The command is `/auftrag` — short, easy to type.
- **It's a specialization of `grilling`**, but with grilling's "give a recommended answer" turned off — see §4.

## 4. The single most important rule: ask, don't write (overrides grilling)

Concept boundary #1 is the foundation of the whole skill: the skill only **asks**; the user **answers**.

This directly conflicts with the user's existing `grilling` skill, which says "for each question, provide your recommended answer." Auftrag **overrides it here**: no recommended answers, only sharper questions.

Why: the instant the skill drafts a "why," the user nods a mediocre version through — and Intent is precisely the box the user should never outsource. So SKILL.md makes this hard rule #1, and `references/grill-heuristics.md` spells out the operational discipline: "the moment you catch yourself about to hand over wording, switch to a question that forces the user to say it themselves."

This is the *entire* difference between this skill and "a prettier template."

## 5. Go/no-go bar and hard-stop (without an annoying required-field ritual)

- **Go/no-go = two boxes and a half**: Intent + Escalation substantive, Done-criteria non-empty → proceed. Do **not** gate on how full Target state / Boundaries are. Straight from the concept: "get those two solid and the rest follows."
- **Done-criteria hard-stop**: empty means no brief, no Todoist write. Implemented as a **behavioral rule** (v0 ships no validation script): ask once, pointedly, say *why it's the gate* (without it, both user and agent lose the reference for "when to stop"), then hold and wait. The concept explicitly asks for this to be "natural, not annoying."

## 6. "Reference, don't repeat" for boundaries / done-criteria

The concept requires the brief's boundaries and done-criteria to **reference** CLAUDE.md and existing skills (the shared premises) rather than re-list them.

Implementation: when assembling the brief, any constraint already covered by CLAUDE.md or an existing skill (commit discipline, test rules, plan-mode gates, etc.) becomes one "inherits: CLAUDE.md + <skill>" line; only the task-specific parts are enumerated. This also serves "minimize boundaries."

## 7. A semantic translation for the subagent dispatch

A subagent spawned via the Agent tool **runs to completion and returns** — it can't pause mid-run to ask you, like a person would. That leaves the "escalation" box at risk of being a no-op in the subagent model.

Fix: when handing the brief to the subagent, prepend an instruction — "if you hit any escalation condition, don't guess; halt and **return** what you found plus the decision you need; when done, self-check against done-criteria and attach evidence." This translates "stop and ask me" into halt-and-return, preserving escalation semantics within a one-shot dispatch.

## 8. Tension with CLAUDE.md (worth watching)

The user's current global CLAUDE.md says "I use Linear MCP as my TODO tool," but this skill lands in Todoist. The practical reason for the mismatch: Todoist is wired and has `todoist-sync`; the Linear MCP isn't authorized yet.

**Handling**: v0 lands in Todoist. If the user later switches to Linear, the change is localized to SKILL.md's Phase 4 / `references/dispatch.md` (swap the MCP tool + go through CLAUDE.md's draft→confirm→create flow); nothing else moves. When creating the Todoist task, still follow CLAUDE.md's task-creation discipline: the brief is the draft — show it, create only on an explicit `yes`.

## 9. What v0 deliberately skips

- No hooks / validation scripts / automated enforcement (concept boundary #2).
- Not a system: no resident agents, no inter-agent messaging, no state sync (concept boundary #3). The closing dispatch is one-shot.
- No ghost-writing any box (concept boundary #1).
- No big-checklist boundaries box (concept boundary #4).
- No self-set project / priority / due — land in the inbox; the user adjusts later.

## 10. Possible later additions (not in v0)

- If Done-criteria keeps getting fudged → consider a harder gate.
- If a task type's follow-ups keep repeating → distill a per-type follow-up template.
- If Linear becomes the primary backend → add a backend choice in Phase 4.
- Whether to also store the brief as a local file (currently it only hangs on the Todoist description) — revisit if a need shows up.
