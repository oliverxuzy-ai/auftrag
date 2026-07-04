# Lanes — what "dispatch" means when the outcome isn't an artifact

Read this from Phase 4 when the brief's `type` is `learn` or `decide`. These lanes exist because the operative axis of delegability is **"can acceptance be mechanized × can errors be cheaply undone"** — not "is there a task". A learn or decide task still gets an Auftrag and a Todoist entry; what changes is *which part* gets delegated and *who* owns done.

## Learn lane (`type: learn`) — delegate the prep, never the eating

The value of the task lives in the commander's head afterward; an agent finishing it would cancel the value. So the agent only **sets the table**:

- **Dispatchable artifact:** a study pack — an annotated code walkthrough, a distilled explainer with sources, exercises **with answers**, a runnable environment. Scope it in the brief's Target state.
- **Anti-hallucination verify (still required):** the pack must survive minimal machine checks — every referenced file:line actually exists (`test -f` / grep), every exercise or snippet actually runs. A study pack that lies is worse than none. These go in `verify:` like any contract.
- **After the pack lands:** the task leaves the agent pipeline entirely — no `agent:*` labels, no board presence, no notifications. It joins the commander's **serial queue** (Todoist label `lane:learn`). One at a time; learning does not parallelize.
- **Done belongs to the commander:** the `evidence:` track is a self-test in their own words ("I can explain X without the notes", "I can re-solve Y cold"). The agent's completion is never the task's completion.

## Decide lane (`type: decide`) — delegate the staff work, never the call

The outcome lives in the commander's judgment. The agent prepares the ground:

- **Dispatchable artifact: the staff memo**, fixed template — the same one escalating executors use, so every item in the decision queue reads identically and the commander's decision cost is minimal:

  ```
  ## Staff memo: <the decision>
  1. Options (≥2 real ones — no strawmen)
     - <option A>: cost, effort, blast radius
     - <option B>: …
  2. Irreversibility — which options can be undone cheaply, which cannot
  3. Recommendation + confidence (low / medium / high)
  4. What new information would flip this recommendation
  ```

  Line 4 is the signature of honest staff work — it tells the commander what to watch instead of pretending certainty.
- **Verify (still required):** claims in the memo must be sourced — every cited number/behavior traceable to a file, doc, or command output the memo links. Spot-checkable, listed in `verify:` where mechanizable.
- **Landing:** memo goes up as a Todoist comment on the task; label `agent:blocked` — because that state *means* "waiting on the commander", which is exactly what a ready decision is. It surfaces at the top of `/board`.
- **Done belongs to the commander:** the decision, stated. A made decision frequently becomes the next `/auftrag` — that hand-off is the natural seam between the two skills.

## The one rule shared by both lanes

The agent's output is **input to the commander's work**, not a substitute for it. If a lane task keeps getting "why isn't this done in one shot" feelings, the type field was wrong — re-triage, don't push harder.
