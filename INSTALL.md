# Installing into local Claude Code

The skill is `SKILL.md` (`name: auftrag`) plus its `references/`. Installing it means putting those where Claude Code scans for skills.

## Option 1: Copy (simple, independent per machine)

```bash
mkdir -p ~/.claude/skills/auftrag
cp -R SKILL.md references ~/.claude/skills/auftrag/
```

Then trigger it in Claude Code with `/auftrag` or "派个活".

> Runtime needs `SKILL.md` + `references/`. `CONCEPT.md` / `docs/` / `README.md` are for humans and can be left out.

## Option 2: Symlink (tracks the git repo, edits apply live)

If you want the local skill to always equal the repo's latest (handy while iterating):

```bash
ln -s "$(pwd)" ~/.claude/skills/auftrag
```

Edits to `SKILL.md` or `references/` in the repo take effect immediately; no re-copy after `git pull`. The cost: `~/.claude/skills/auftrag/` will also contain `README.md`, `docs/`, etc. — harmless; Claude Code only reads `SKILL.md` and what it references.

## Verify

After installing, ask Claude Code to list skills, or just:

```
/auftrag
```

It should open with a single line like "tell me the whole thing you're about to delegate, in one go" — not dump a five-box table at you — and, when it reaches the follow-up phase, actually load `references/grill-heuristics.md`.

## Uninstall

```bash
rm -rf ~/.claude/skills/auftrag        # copy method
# or
rm ~/.claude/skills/auftrag            # symlink method
```
