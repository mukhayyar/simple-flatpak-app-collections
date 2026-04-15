#!/usr/bin/env bash
# publish.sh — submit com.pens.PeriodicTable to the AGL PENS Store
# Run from this directory.
#
# First-time setup (one time only):
#   1. Log in to https://admin.agl-store.cyou/developer/portal
#   2. Go to "Signing Key" → "Download Signing Key"
#   3. gpg --import agl-signing-key-*.gpg
#   4. Download push-to-agl.sh once:
#      curl -o ../../push-to-agl.sh https://admin.agl-store.cyou/api/push-to-agl.sh
#      chmod +x ../../push-to-agl.sh
#
# Usage:
#   ./publish.sh --token YOUR_UPLOAD_TOKEN
#   (Get the token from the portal after filling the Submit App form)

set -euo pipefail

TOKEN=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --token) TOKEN="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

[[ -z "$TOKEN" ]] && { echo "Usage: ./publish.sh --token YOUR_UPLOAD_TOKEN"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PUSH_SCRIPT="$SCRIPT_DIR/../../push-to-agl.sh"

if [[ ! -f "$PUSH_SCRIPT" ]]; then
  echo "==> Downloading push-to-agl.sh..."
  curl -fsSL -o "$PUSH_SCRIPT" https://admin.agl-store.cyou/api/push-to-agl.sh
  chmod +x "$PUSH_SCRIPT"
fi

cd "$SCRIPT_DIR"

"$PUSH_SCRIPT" \
  --token    "$TOKEN" \
  --app-id   "com.pens.PeriodicTable" \
  --name     "Periodic Table" \
  --summary  "Periodic Table application for AGL Store" \
  --category "Education" \
  --repo     ./flatpak_repo \
  --multi-arch
