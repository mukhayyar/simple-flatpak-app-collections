#!/usr/bin/env bash
# publish.sh — submit com.pens.IVIVehicleDashboard to the AGL PENS Store
set -euo pipefail
TOKEN=""
while [[ $# -gt 0 ]]; do
  case "$1" in --token) TOKEN="$2"; shift 2 ;; *) echo "Unknown: $1"; exit 1 ;; esac
done
[[ -z "$TOKEN" ]] && { echo "Usage: ./publish.sh --token YOUR_UPLOAD_TOKEN"; exit 1; }
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PUSH_SCRIPT="$SCRIPT_DIR/../../push-to-agl.sh"
[[ ! -f "$PUSH_SCRIPT" ]] && curl -fsSL -o "$PUSH_SCRIPT" https://admin.agl-store.cyou/api/push-to-agl.sh && chmod +x "$PUSH_SCRIPT"
cd "$SCRIPT_DIR"
"$PUSH_SCRIPT" --token "$TOKEN" --app-id "com.pens.IVIVehicleDashboard" --name "IVI Vehicle Dashboard" \
  --summary "Simulated automotive instrument cluster for AGL IVI systems" \
  --category "Utility" --repo ./flatpak_repo --multi-arch
