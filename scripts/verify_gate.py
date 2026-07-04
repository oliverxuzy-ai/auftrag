#!/usr/bin/env python3
"""Auftrag verify gate — Stop / SubagentStop hook.

The runtime half of the Done-criteria box. When a session (or subagent) tries
to finish, this gate reads the Auftrag contract at .claude/auftrag/active.md
in the session cwd and runs every command under its `verify:` frontmatter key.

  - No contract file       -> silent pass (the gate only binds Auftrag work).
  - All commands exit 0    -> allow the stop; reset the attempt counter.
  - Any command fails      -> block the stop; feed the failure back so the
                              agent keeps working (attempt N of max_attempts).
  - max_attempts exhausted -> give up LOUDLY: allow the stop, mark the state
                              RED, and instruct the agent to raise its hand
                              (label agent:red + Todoist comment) instead of
                              claiming success. Failure must speak.

Fail-open by design: any internal error lets the session stop normally.
State lives in .claude/auftrag/state.json next to the contract; /abnahme and
/board read it. Dispatch resets it by deleting the file.
"""

import json
import os
import subprocess
import sys

TAIL_LINES = 30
TAIL_CHARS = 2000


def tail(text):
    lines = text.strip().splitlines()[-TAIL_LINES:]
    return "\n".join(lines)[-TAIL_CHARS:]


def read_frontmatter(path):
    """Minimal parser for the constrained frontmatter this plugin writes:
    scalar keys (`key: value`) and string lists (`key:` + `  - item`)."""
    fm = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    if not lines or lines[0].strip() != "---":
        return fm
    key = None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        stripped = line.strip()
        if line[:1] in (" ", "\t") or stripped.startswith("- "):
            if key and stripped.startswith("- ") and isinstance(fm.get(key), list):
                fm[key].append(stripped[2:].strip())
            continue
        if ":" in line:
            k, _, v = line.partition(":")
            key = k.strip()
            v = v.strip()
            fm[key] = v if v else []
    return fm


def load_state(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(path, state):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    if data.get("hook_event_name") not in ("Stop", "SubagentStop"):
        return

    cwd = data.get("cwd") or os.getcwd()
    contract = os.path.join(cwd, ".claude", "auftrag", "active.md")
    if not os.path.isfile(contract):
        return

    fm = read_frontmatter(contract)
    cmds = fm.get("verify")
    if not isinstance(cmds, list) or not cmds:
        return

    def as_int(value, default):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    max_attempts = as_int(fm.get("max_attempts"), 5)
    timeout = as_int(fm.get("timeout"), 300)

    state_path = os.path.join(cwd, ".claude", "auftrag", "state.json")
    state = load_state(state_path)
    if state.get("gave_up"):
        return  # already RED and reported; let the session end.

    results, failures = [], []
    for cmd in cmds:
        try:
            p = subprocess.run(
                cmd, shell=True, cwd=cwd,
                capture_output=True, text=True, timeout=timeout,
            )
            ok = p.returncode == 0
            out = ((p.stdout or "") + "\n" + (p.stderr or "")).strip()
        except subprocess.TimeoutExpired:
            ok, out = False, "verify command timed out after %ss" % timeout
        except Exception as e:  # gate must never crash the session
            ok, out = False, "gate could not run command: %s" % e
        results.append({"cmd": cmd, "ok": ok, "tail": tail(out)})
        if not ok:
            failures.append((cmd, tail(out)))

    if not failures:
        state.update({"attempts": 0, "last": "pass", "gave_up": False,
                      "results": results})
        save_state(state_path, state)
        print(json.dumps({
            "systemMessage": "Auftrag gate ✅ %d/%d verify checks passed."
                             % (len(cmds), len(cmds)),
        }))
        return

    attempts = as_int(state.get("attempts"), 0) + 1
    state.update({"attempts": attempts, "last": "fail", "results": results})

    if attempts >= max_attempts:
        state["gave_up"] = True
        save_state(state_path, state)
        print(json.dumps({
            "systemMessage": "Auftrag gate 🔴 RED — %d verify check(s) still "
                             "failing after %d attempts. Giving up loudly."
                             % (len(failures), attempts),
            "hookSpecificOutput": {
                "hookEventName": data.get("hook_event_name"),
                "additionalContext":
                    "[AUFTRAG GATE — automated, this is NOT the user] The gate "
                    "has given up after %d attempts: the task is RED. Do NOT "
                    "claim success. Do this now, then stop: (1) set the Todoist "
                    "task's label to agent:red (remove agent:running), (2) post "
                    "a Todoist comment with exactly which checks fail and the "
                    "concrete gap, (3) end your final reply starting with "
                    "'🔴 RED'. Still failing: %s"
                    % (attempts, "; ".join(c for c, _ in failures)),
            },
        }))
        return

    save_state(state_path, state)
    detail = "\n\n".join("$ %s\n%s" % (c, t) for c, t in failures)
    print(json.dumps({
        "decision": "block",
        "reason":
            "[AUFTRAG VERIFY GATE — automated contract check. This is NOT the "
            "user and NOT a permission denial; do not stop and wait.] "
            "Attempt %d/%d: %d of %d verify commands failed. Fix the work and "
            "finish again. RED LINE: never weaken, skip, or hardcode a check "
            "to make it pass — if you believe a check itself is wrong, that "
            "is an Escalation: halt and report it instead.\n\n%s"
            % (attempts, max_attempts, len(failures), len(cmds), detail),
    }))


if __name__ == "__main__":
    try:
        main()
    finally:
        sys.exit(0)
