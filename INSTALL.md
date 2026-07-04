# Installing the auftragstaktik plugin

The repo **is** the plugin (and its own marketplace). Everything installs together: the skills (`auftrag`, `abnahme`, `board`, `catchup`, `todoist-sync`), the `pruefer` examiner agent, and the verify-gate hooks.

## Install (persistent)

Inside any Claude Code session:

```
/plugin marketplace add /Users/zhengyangxu/Desktop/side_project/auftrag
/plugin install auftragstaktik@auftragstaktik
```

Then restart or `/reload-plugins`.

> **Remove old standalone copies first.** If `~/.claude/skills/auftrag` or `~/.claude/skills/todoist-sync` still exist from the pre-plugin era, delete them — standalone skills shadow the plugin versions, so you'd silently keep running the stale ones.

## Skill names after install

Plugin skills are namespaced: `/auftragstaktik:auftrag`, `/auftragstaktik:abnahme`, `/auftragstaktik:board`, `/auftragstaktik:catchup`, `/auftragstaktik:start-todo`-style commands come from `todoist-sync`. Typing the short form (e.g. `/auftrag`) still finds them via fuzzy match, and trigger phrases ("认真派个活", "what needs me") invoke them model-side as before.

## Updating after you edit the repo

Installed plugins are **cached copies** — repo edits don't apply live. After changing anything:

```
/plugin marketplace update auftragstaktik
```

(or reinstall). For a live-editing dev loop instead, run a session with the repo mounted directly:

```bash
claude --plugin-dir /Users/zhengyangxu/Desktop/side_project/auftrag
```

then `/reload-plugins` picks up edits without restarting.

## One-time environment setup (Phase 0 of the workflow design)

1. **Phone push**: `"agentPushNotifEnabled": true` in `~/.claude/settings.json`, and pair once with `claude remote-control` — BLOCKED/RED raises its hand on your phone, with presence detection so it stays quiet while you're at the keyboard.
2. **Optional extra channels**: export `AUFTRAG_NTFY_TOPIC=<topic>` and/or `AUFTRAG_DISCORD_WEBHOOK=<url>` to fan background-agent notifications out through `scripts/notify.sh`. Unset = no-op.
3. **Todoist labels**: created on first dispatch automatically (`auftrag`, `agent:running`, `agent:blocked`, `agent:red`, `agent:green`, `lane:learn`).

## Verify the install

```
/auftragstaktik:auftrag       → opens with "give me the whole thing, in one go"
/auftragstaktik:board         → renders a MELDUNG block (empty queue is fine)
```

Gate smoke test: in any scratch repo, create `.claude/auftrag/active.md` with frontmatter `verify:` containing `- false`, ask the session to finish something — it should get bounced by `[AUFTRAG VERIFY GATE]`; change to `- true` and it should pass with "Auftrag gate ✅". Delete the file afterward.

## Uninstall

```
/plugin uninstall auftragstaktik@auftragstaktik
/plugin marketplace remove auftragstaktik
```
