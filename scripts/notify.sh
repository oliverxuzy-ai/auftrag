#!/bin/sh
# Optional forwarder for background-agent notifications
# (Notification hook, matcher: agent_needs_input | agent_completed).
#
# Native phone push (Remote Control + agentPushNotifEnabled) is the primary
# channel; this script adds ntfy / Discord fan-out for people who want it.
# No-op unless AUFTRAG_NTFY_TOPIC and/or AUFTRAG_DISCORD_WEBHOOK is set.

payload=$(cat)
[ -z "$AUFTRAG_NTFY_TOPIC" ] && [ -z "$AUFTRAG_DISCORD_WEBHOOK" ] && exit 0

msg=$(printf '%s' "$payload" | python3 -c '
import json, sys
d = json.load(sys.stdin)
kind = d.get("notification_type") or "notification"
title = d.get("title") or "Claude Code"
body = d.get("message") or ""
print("[%s] %s: %s" % (kind, title, body))
' 2>/dev/null) || msg="Claude Code: background agent notification"

if [ -n "$AUFTRAG_NTFY_TOPIC" ]; then
  curl -fsS -m 5 -d "$msg" "https://ntfy.sh/$AUFTRAG_NTFY_TOPIC" >/dev/null 2>&1
fi

if [ -n "$AUFTRAG_DISCORD_WEBHOOK" ]; then
  json=$(printf '%s' "$msg" | python3 -c 'import json,sys; print(json.dumps({"content": sys.stdin.read()[:1900]}))' 2>/dev/null)
  [ -n "$json" ] && curl -fsS -m 5 -H 'Content-Type: application/json' \
    -d "$json" "$AUFTRAG_DISCORD_WEBHOOK" >/dev/null 2>&1
fi

exit 0
