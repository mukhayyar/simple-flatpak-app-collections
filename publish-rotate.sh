#!/usr/bin/env bash
#
# publish-rotate.sh — publish many apps, rotating the developer account per app.
#
# Round-robins a pool of developer accounts across the given app folders so the
# store shows varied authorship. Each app is published by the next account in the
# pool via auto-run.sh (which honours AGL_EMAIL / AGL_PASSWORD env vars).
#
# Usage:
#   ./publish-rotate.sh <app-folder> [<app-folder> ...]
#   ./publish-rotate.sh --all                 # every app folder with a manifest
#   START_AT=2 ./publish-rotate.sh --all      # start rotation at the 3rd account
#
# Notes:
#   * The "active submission already exists" rule is keyed on app_id, NOT account.
#     Apps already submitted by ANY account will return 409 — this script reports
#     them as SKIPPED and moves on (it does not treat 409 as failure).
#   * Each account signs with its OWN downloaded key (auto-run.sh now picks the
#     just-imported key), so signatures match the publishing developer.
#
# Override the pool with ACCOUNTS="email:pass email:pass ...".

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load the account pool (and any creds) from .env without overriding existing env.
load_dotenv() {
  local f="$1" line k v
  [[ -f "$f" ]] || return 0
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue
    [[ "$line" == *=* ]] || continue
    k="${line%%=*}"; v="${line#*=}"; k="${k//[[:space:]]/}"
    [[ "$k" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
    [[ -n "${!k+x}" ]] && continue
    v="${v#"${v%%[![:space:]]*}"}"
    if [[ "$v" == \"*\" ]]; then v="${v#\"}"; v="${v%\"}"
    elif [[ "$v" == \'*\' ]]; then v="${v#\'}"; v="${v%\'}"; fi
    export "$k=$v"
  done < "$f"
}
load_dotenv "$SCRIPT_DIR/.env"

# Account pool: space-separated "email:password" entries (from .env / ACCOUNTS env).
[[ -n "${ACCOUNTS:-}" ]] || { echo "No ACCOUNTS set. Create .env (see .env.example) or export ACCOUNTS=..."; exit 1; }
read -ra POOL <<<"$ACCOUNTS"
N=${#POOL[@]}

# Resolve app list
if [[ "${1:-}" == "--all" ]]; then
  mapfile -t APPS < <(
    for d in "$SCRIPT_DIR"/*/; do
      d="${d%/}"; b="$(basename "$d")"
      compgen -G "$d/*.yml" >/dev/null 2>&1 || compgen -G "$d/*.yaml" >/dev/null 2>&1 || compgen -G "$d/*.json" >/dev/null 2>&1 || continue
      echo "$b"
    done | sort)
else
  APPS=("$@")
fi
[[ ${#APPS[@]} -gt 0 ]] || { echo "Usage: ./publish-rotate.sh <app-folder> [...] | --all"; exit 1; }

i="${START_AT:-0}"
declare -a SUMMARY=()
for app in "${APPS[@]}"; do
  acct="${POOL[$((i % N))]}"
  email="${acct%%:*}"; pass="${acct#*:}"
  echo
  echo "################################################################"
  echo "# [$((i+1))/${#APPS[@]}] $app   →   $email"
  echo "################################################################"

  out="$(AGL_EMAIL="$email" AGL_PASSWORD="$pass" "$SCRIPT_DIR/auto-run.sh" "$app" 2>&1)"
  rc=$?
  echo "$out"

  if grep -q "already exists" <<<"$out"; then
    SUMMARY+=("SKIP(409)  $app  ($email)")
  elif grep -qE "Submitted — submission|Done!" <<<"$out" && [[ $rc -eq 0 ]]; then
    sid="$(grep -oE 'submission #[0-9?]+' <<<"$out" | head -1)"
    SUMMARY+=("OK         $app  ($email)  $sid")
  else
    fail="$(grep -oE '✗ .*' <<<"$out" | head -1)"
    SUMMARY+=("FAIL       $app  ($email)  ${fail:-rc=$rc}")
  fi
  i=$((i+1))
done

echo
echo "================ ROTATION SUMMARY ================"
printf '%s\n' "${SUMMARY[@]}"
