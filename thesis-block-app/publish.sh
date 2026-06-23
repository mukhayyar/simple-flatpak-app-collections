#!/usr/bin/env bash
# publish.sh — submit com.thesis.BlockApp to the AGL PENS Store
set -euo pipefail
TOKEN=""
while [[ $# -gt 0 ]]; do
  case "$1" in --token) TOKEN="$2"; shift 2 ;; *) echo "Unknown: $1"; exit 1 ;; esac
done
[[ -z "$TOKEN" ]] && { echo "Usage: ./publish.sh --token TOKEN"; exit 1; }
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PUSH_SCRIPT="$SCRIPT_DIR/../../push-to-agl.sh"
if [[ ! -f "$PUSH_SCRIPT" ]]; then
  curl -fsSL -o "$PUSH_SCRIPT" https://admin.agl-store.cyou/api/push-to-agl.sh
  chmod +x "$PUSH_SCRIPT"
fi
cd "$SCRIPT_DIR"
"$PUSH_SCRIPT" --token "$TOKEN" --app-id "com.thesis.BlockApp" --name "BlockApp" \
  --summary "BLOCK-class benchmark bundle (malware test, overprivileged)" --category "Utility" \
  --repo ./flatpak_repo
