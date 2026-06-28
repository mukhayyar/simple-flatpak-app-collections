#!/usr/bin/env bash
#
# auto-run.sh — build, sign, push and publish any app in this collection
#               to the AGL PENS Store, fully automated.
#
# Usage:
#   ./auto-run.sh <app-folder> [arches]
#
# Examples:
#   ./auto-run.sh util-stopwatch                    # default arches (x86_64 aarch64)
#   ./auto-run.sh util-screen-ruler aarch64         # single arch
#   ./auto-run.sh util-stopwatch "x86_64 aarch64"   # explicit set
#
# Multi-arch:
#   By default the app is published for x86_64 and aarch64 (arm64). These apps are
#   pure-Python / arch-independent, so we build ONCE natively then clone the OSTree
#   ref into each extra arch (rewriting /x86_64/ -> /aarch64/ in the ref + metadata)
#   — no QEMU or per-arch SDK needed. All arch refs land in ONE flat-manager build,
#   so a single admin approval publishes them all. Override with the 2nd positional
#   arg or ARCHES="...".
#   armv7 ("arm") is NOT included by default: Flathub has no org.gnome.Platform/arm
#   runtime, so arm builds publish but won't install. Add it only for a runtime that
#   ships 32-bit ARM.
#
# What it does:
#   1. Log in to the AGL admin API -> access token
#   2. Download + import the developer GPG signing key, find its fingerprint
#   3. flatpak-builder build (host arch) -> export to repo -> clone extra arches
#   4. Sign the repo (all arch refs)
#   5. Push to flat-manager build-repo (create -> push -> commit); all arch refs
#      go into ONE build, capturing the numeric build id so admin approval can
#      publish every arch to the main OSTree repo
#      [skipped automatically if flat-manager-client is absent]
#   6. Build one signed .flatpak bundle per arch
#   7. Upload each bundle (server imports + re-signs into the store repo)
#   8. Submit metadata (incl. flatpak_build_id) to the review queue
#
# Config via env vars (defaults shown):
#   AGL_EMAIL      developer@agl-store.cyou
#   AGL_PASSWORD   Dev@AGL2026
#   AGL_ADMIN      https://admin.agl-store.cyou
#   AGL_HUB        https://hub.agl-store.cyou/  (flat-manager URL, keep trailing slash)
#   DEVELOPER_NAME AGL Developer
#   FM_REF         stable                        (branch/repo to build/publish)
#   SKIP_FM        0                             (set 1 to skip the OSTree push)
#   FM_CA_BUNDLE   <auto>                        (CA bundle for the hub's TLS cert;
#                                                 auto-uses agl-hub-ca-bundle.pem if present)
#
# Per-app metadata overrides (optional):
#   APP_NAME APP_SUMMARY APP_DESCRIPTION APP_CATEGORY APP_TAGS APP_LICENSE APP_HOMEPAGE
#
# Requires: flatpak, flatpak-builder, gpg, curl, python3 (jq optional,
#           flat-manager-client optional — enables stage 5).

set -euo pipefail

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load secrets/config from .env (KEY=VALUE) WITHOUT overriding anything already
# set in the environment — so per-account creds passed by publish-rotate.sh win
# over .env defaults. .env is gitignored; keep credentials there, not in the script.
load_dotenv() {
  local f="$1" line k v
  [[ -f "$f" ]] || return 0
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue
    [[ "$line" == *=* ]] || continue
    k="${line%%=*}"; v="${line#*=}"; k="${k//[[:space:]]/}"
    [[ "$k" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
    [[ -n "${!k+x}" ]] && continue                 # already set in env -> keep it
    v="${v#"${v%%[![:space:]]*}"}"                 # ltrim value
    if [[ "$v" == \"*\" ]]; then v="${v#\"}"; v="${v%\"}"
    elif [[ "$v" == \'*\' ]]; then v="${v#\'}"; v="${v%\'}"; fi
    export "$k=$v"
  done < "$f"
}
load_dotenv "$SCRIPT_DIR/.env"

AGL_EMAIL="${AGL_EMAIL:-developer@agl-store.cyou}"
AGL_PASSWORD="${AGL_PASSWORD:-Dev@AGL2026}"
AGL_ADMIN="${AGL_ADMIN:-https://admin.agl-store.cyou}"
AGL_HUB="${AGL_HUB:-https://hub.agl-store.cyou/}"
DEVELOPER_NAME="${DEVELOPER_NAME:-AGL Developer}"
FM_REF="${FM_REF:-stable}"
SKIP_FM="${SKIP_FM:-0}"

API_BASE="$AGL_ADMIN/api"

# hub.agl-store.cyou serves a Cloudflare Origin cert (untrusted on direct,
# non-proxied connections). A committed CA bundle next to this script adds the
# Cloudflare Origin Root CA so flat-manager-client's TLS still verifies — no
# --insecure needed. Override with FM_CA_BUNDLE=/path/to/ca.pem.
FM_CA_BUNDLE="${FM_CA_BUNDLE:-}"
if [[ -z "$FM_CA_BUNDLE" && -f "$SCRIPT_DIR/agl-hub-ca-bundle.pem" ]]; then
  FM_CA_BUNDLE="$SCRIPT_DIR/agl-hub-ca-bundle.pem"
fi

# ---------------------------------------------------------------------------
# Pretty logging
# ---------------------------------------------------------------------------
if [[ -t 1 ]]; then
  C_BLUE=$'\033[1;34m'; C_GREEN=$'\033[1;32m'; C_RED=$'\033[1;31m'
  C_YELLOW=$'\033[1;33m'; C_DIM=$'\033[2m'; C_RST=$'\033[0m'
else
  C_BLUE=""; C_GREEN=""; C_RED=""; C_YELLOW=""; C_DIM=""; C_RST=""
fi
step() { echo; echo "${C_BLUE}==>${C_RST} ${C_BLUE}$*${C_RST}"; }
info() { echo "    $*"; }
ok()   { echo "${C_GREEN}    ✓ $*${C_RST}"; }
warn() { echo "${C_YELLOW}    ! $*${C_RST}"; }
die()  { echo "${C_RED}    ✗ $*${C_RST}" >&2; exit 1; }

# ---------------------------------------------------------------------------
# JSON helper: use jq if present, otherwise python3
# ---------------------------------------------------------------------------
json_get() {
  local key="$1"
  if command -v jq >/dev/null 2>&1; then
    jq -r --arg k "$key" '.[$k] // empty'
  else
    python3 -c '
import sys, json
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
v = d.get(sys.argv[1], "") if isinstance(d, dict) else ""
print(v if v is not None else "")
' "$key"
  fi
}

# ---------------------------------------------------------------------------
# Args / app detection
# ---------------------------------------------------------------------------
APP_DIR="${1:-}"
# Arches to publish. 2nd positional arg overrides; else ARCHES env; else all three.
#   x86_64  = Intel/AMD 64-bit
#   aarch64 = arm64 (64-bit ARM, e.g. Pi 4/5, most AGL targets)
#   arm     = armv7 (32-bit ARM)
# NOTE: armv7 ("arm") is intentionally NOT default — Flathub has no
# org.gnome.Platform/arm/45 runtime, so an arm build publishes but won't install.
# Add "arm" only when targeting a runtime that ships for 32-bit ARM.
ARCHES="${2:-${ARCHES:-x86_64 aarch64}}"
# The single arch we actually build natively; the rest are cloned from it.
HOST_ARCH="$(flatpak --default-arch 2>/dev/null || echo x86_64)"

[[ -n "$APP_DIR" ]] || die "Usage: ./auto-run.sh <app-folder> [arches]"
APP_DIR="${APP_DIR%/}"
APP_PATH="$SCRIPT_DIR/$APP_DIR"
[[ -d "$APP_PATH" ]] || die "App folder not found: $APP_PATH"
cd "$APP_PATH"

# Find the single flatpak manifest in the folder
MANIFEST=""
for ext in yml yaml json; do
  for f in *."$ext"; do
    [[ -e "$f" ]] || continue
    if grep -qE '^(app-id|id)[[:space:]]*:' "$f" 2>/dev/null || grep -q '"app-id"' "$f" 2>/dev/null; then
      MANIFEST="$f"; break 2
    fi
  done
done
[[ -n "$MANIFEST" ]] || die "No flatpak manifest (*.yml/*.yaml/*.json) found in $APP_DIR"

# Derive APP_ID from the manifest, falling back to the filename
APP_ID="$(grep -E '^(app-id|id)[[:space:]]*:' "$MANIFEST" 2>/dev/null | head -1 | sed -E 's/^[^:]+:[[:space:]]*//; s/["'\'' ]//g')"
[[ -n "$APP_ID" ]] || APP_ID="${MANIFEST%.*}"

# Per-app metadata (override via env). Defaults derived from the app id.
LAST_SEG="${APP_ID##*.}"
APP_NAME="${APP_NAME:-$LAST_SEG}"
APP_SUMMARY="${APP_SUMMARY:-$APP_NAME for the AGL Store}"
APP_DESCRIPTION="${APP_DESCRIPTION:-$APP_SUMMARY}"
APP_CATEGORY="${APP_CATEGORY:-Utility}"
APP_TAGS="${APP_TAGS:-utility}"
APP_LICENSE="${APP_LICENSE:-}"
APP_HOMEPAGE="${APP_HOMEPAGE:-}"

BUILD_DIR="flatpak_build"
REPO_DIR="flatpak_repo"

step "App: ${C_GREEN}$APP_ID${C_RST}  ${C_DIM}(folder: $APP_DIR, manifest: $MANIFEST, arches: $ARCHES)${C_RST}"

# ---------------------------------------------------------------------------
# Helper: clone an arch-independent OSTree ref to another arch (no QEMU/cross
# build needed — these apps ship only a Python script, identical on every arch).
# Rewrites the ref path and the /src_arch/ -> /dst_arch/ token in xa.metadata.
# ---------------------------------------------------------------------------
clone_arch_ref() {
  local src_arch="$1" dst_arch="$2"
  local src_ref dst_ref tmp meta
  src_ref="$(ostree --repo="$REPO_DIR" refs 2>/dev/null | grep -E "^app/${APP_ID}/${src_arch}/" | head -1)"
  [[ -n "$src_ref" ]] || die "No $src_arch ref found to clone $dst_arch from"
  dst_ref="${src_ref/\/${src_arch}\//\/${dst_arch}\/}"
  tmp="$(mktemp -d)"
  ostree --repo="$REPO_DIR" checkout --user-mode "$src_ref" "$tmp/content" || die "checkout $src_ref failed"
  if [[ -f "$tmp/content/metadata" ]]; then
    sed -i "s|/${src_arch}/|/${dst_arch}/|g" "$tmp/content/metadata"
    meta="$(cat "$tmp/content/metadata")"
  fi
  ostree --repo="$REPO_DIR" commit --branch="$dst_ref" --tree=dir="$tmp/content" \
    ${meta:+--add-metadata-string="xa.metadata=${meta}"} >/dev/null \
    || die "commit $dst_ref failed"
  rm -rf "$tmp"
}

# ---------------------------------------------------------------------------
# 1. Login & get access token
# ---------------------------------------------------------------------------
step "1/8  Logging in as $AGL_EMAIL"
LOGIN_RESP="$(curl -s -X POST "$API_BASE/auth/login/email" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$AGL_EMAIL\",\"password\":\"$AGL_PASSWORD\"}")"
TOKEN="$(printf '%s' "$LOGIN_RESP" | json_get access_token)"
[[ -n "$TOKEN" ]] || die "Login failed: $LOGIN_RESP"
ok "Got access token"

# ---------------------------------------------------------------------------
# 2. Download & import signing key, find fingerprint
# ---------------------------------------------------------------------------
step "2/8  Fetching & importing GPG signing key"
KEYFILE="$SCRIPT_DIR/agl-signing-key.gpg"
curl -fsSL -H "Authorization: Bearer $TOKEN" \
  "$API_BASE/developer/my-gpg-key/download" -o "$KEYFILE" \
  || die "Could not download signing key"
IMPORT_OUT="$(gpg --batch --import "$KEYFILE" 2>&1)"
printf '%s\n' "$IMPORT_OUT" | sed 's/^/    /'

# Prefer the key that was JUST imported (correct when several accounts' keys —
# all uid "AGL Developer" — coexist in the keyring during account rotation).
IMPORTED_KEYID="$(printf '%s' "$IMPORT_OUT" | grep -oiE 'key [0-9A-F]{8,40}' | head -1 | awk '{print $2}')"
FP=""
if [[ -n "$IMPORTED_KEYID" ]]; then
  FP="$(gpg --list-secret-keys --with-colons "$IMPORTED_KEYID" 2>/dev/null | awk -F: '$1=="fpr"{print $10; exit}')"
fi
# Fallbacks: match by developer name, then first secret key.
[[ -n "$FP" ]] || FP="$(gpg --list-secret-keys --with-colons 2>/dev/null | awk -F: -v name="$DEVELOPER_NAME" '
  $1=="fpr" { fpr=$10 }
  $1=="uid" && index($10, name) { print fpr; exit }')"
[[ -n "$FP" ]] || FP="$(gpg --list-secret-keys --with-colons 2>/dev/null | awk -F: '$1=="fpr"{print $10; exit}')"
[[ -n "$FP" ]] || die "Could not determine signing key fingerprint"
ok "Signing key fingerprint: $FP"

# ---------------------------------------------------------------------------
# 3. Build
# ---------------------------------------------------------------------------
step "3/8  Building Flatpak"
command -v flatpak-builder >/dev/null || die "flatpak-builder not installed"
flatpak remote-add --if-not-exists --user flathub \
  https://dl.flathub.org/repo/flathub.flatpakrepo >/dev/null 2>&1 || true

info "Cleaning previous build artifacts"
rm -rf "$BUILD_DIR" "$REPO_DIR" "${APP_ID}"*.flatpak

info "Running flatpak-builder for host arch $HOST_ARCH (auto-installing runtime deps from flathub)"
flatpak-builder --user --force-clean \
  --install-deps-from=flathub \
  --arch="$HOST_ARCH" \
  --default-branch="$FM_REF" \
  --repo="$REPO_DIR" \
  "$BUILD_DIR" "$MANIFEST" \
  || die "flatpak-builder failed"
ok "Built $HOST_ARCH and exported to ./$REPO_DIR"

# Clone the host build into every other requested arch (arch-independent apps).
for a in $ARCHES; do
  [[ "$a" == "$HOST_ARCH" ]] && continue
  info "Cloning $HOST_ARCH ref -> $a"
  clone_arch_ref "$HOST_ARCH" "$a"
  ok "Created ref app/$APP_ID/$a/$FM_REF"
done

# If the host arch wasn't requested, drop its ref so we publish only $ARCHES.
if ! grep -qw "$HOST_ARCH" <<<"$ARCHES"; then
  HOST_REF="$(ostree --repo="$REPO_DIR" refs 2>/dev/null | grep -E "^app/${APP_ID}/${HOST_ARCH}/" | head -1 || true)"
  [[ -n "$HOST_REF" ]] && { ostree --repo="$REPO_DIR" refs --delete "$HOST_REF" >/dev/null 2>&1 || true; }
fi
flatpak build-update-repo "$REPO_DIR" >/dev/null 2>&1 || true
ok "Repo arches: $(ostree --repo="$REPO_DIR" refs 2>/dev/null | grep -oE "^app/${APP_ID}/[^/]+" | sed "s#app/${APP_ID}/##" | sort -u | paste -sd' ' -)"

# ---------------------------------------------------------------------------
# 4. Sign the repo
# ---------------------------------------------------------------------------
step "4/8  Signing repository"
flatpak build-sign "$REPO_DIR" --gpg-sign="$FP" || die "Repo signing failed"
flatpak build-update-repo "$REPO_DIR" --gpg-sign="$FP" >/dev/null 2>&1 || true
ok "Repo signed"

# ---------------------------------------------------------------------------
# 5. Push to flat-manager / OSTree (build-repo)
# ---------------------------------------------------------------------------
step "5/8  Pushing to flat-manager build-repo (OSTree)"
if [[ "$SKIP_FM" == "1" ]]; then
  warn "SKIP_FM=1 — skipping OSTree push"
elif ! command -v flat-manager-client >/dev/null 2>&1; then
  warn "flat-manager-client not installed — skipping OSTree push"
  warn "  (bundle upload below still works, but admin approval can't publish"
  warn "   the OSTree build without flatpak_build_id)"
else
  # Trust the hub's issuing CA (Cloudflare Origin Root) without disabling verify
  [[ -n "$FM_CA_BUNDLE" ]] && export SSL_CERT_FILE="$FM_CA_BUNDLE"

  info "Requesting flat-manager token"
  FM_RESP="$(curl -s -X POST "$API_BASE/developer/fm-token" \
    -H "Authorization: Bearer $TOKEN" \
    -H 'Content-Type: application/json' \
    -d "{\"developer_name\":\"$DEVELOPER_NAME\",\"role\":\"developer\",\"app_id\":\"$APP_ID\"}")"
  FM_TOKEN="$(printf '%s' "$FM_RESP" | json_get token)"
  [[ -n "$FM_TOKEN" ]] || die "Could not get flat-manager token: $FM_RESP"
  FM_URL="$(printf '%s' "$FM_RESP" | json_get flat_manager_url)"; FM_URL="${FM_URL:-$AGL_HUB}"
  FM_REPO="$(printf '%s' "$FM_RESP" | json_get repo)"; FM_REPO="${FM_REPO:-$FM_REF}"
  # Ensure trailing slash (flat-manager-client requires it)
  [[ "$FM_URL" == */ ]] || FM_URL="${FM_URL}/"
  ok "Got flat-manager token (url: $FM_URL, repo: $FM_REPO)"

  # flat-manager-client reads token from REPO_TOKEN env var
  export REPO_TOKEN="$FM_TOKEN"

  info "Creating build transaction"
  BUILD_URL="$(flat-manager-client create "$FM_URL" "$FM_REPO")"
  [[ -n "$BUILD_URL" ]] || die "flat-manager create failed"
  info "Build URL: $BUILD_URL"
  # Extract numeric build ID for submission metadata (needed for admin approval publish)
  FM_BUILD_ID="$(printf '%s' "$BUILD_URL" | grep -oE '[0-9]+$')"

  info "Pushing repo to build-repo"
  flat-manager-client push "$BUILD_URL" "./$REPO_DIR" || die "flat-manager push failed"

  info "Committing (waits for OSTree ingest)"
  flat-manager-client commit --wait "$BUILD_URL" || die "flat-manager commit failed"
  ok "OSTree refs live: app/$APP_ID/{$(tr ' ' ',' <<<"$ARCHES")}/$FM_REF (build #${FM_BUILD_ID})"
fi

FM_BUILD_ID="${FM_BUILD_ID:-}"

# ---------------------------------------------------------------------------
# 6+7. Build a signed bundle per arch and upload each to the store
# ---------------------------------------------------------------------------
step "6/8  Creating signed bundles (one per arch)"
declare -a BUNDLES=()
for a in $ARCHES; do
  b="${APP_ID}-${a}.flatpak"
  flatpak build-bundle "$REPO_DIR" "$b" "$APP_ID" "$FM_REF" \
    --arch="$a" --gpg-sign="$FP" \
    || die "Bundle creation failed for $a"
  ok "Bundle ($a): $b ($(du -sh "$b" | cut -f1))"
  BUNDLES+=("$a:$b")
done

# ---------------------------------------------------------------------------
# 7. Upload each arch's bundle (appstream / portal)
# ---------------------------------------------------------------------------
step "7/8  Uploading bundles to AGL store (appstream)"
# Non-fatal: the bundle upload is the supplementary appstream-import path. The
# primary publish goes through the flat-manager build (stage 5) + submit (stage 8)
# + admin approval, which carries every arch via flatpak_build_id. So if this
# endpoint is down/erroring, warn and continue — don't abort the publish.
DETECTED_ID=""
for entry in "${BUNDLES[@]}"; do
  a="${entry%%:*}"; b="${entry#*:}"
  info "Uploading $a bundle ($b)"
  UP_RESP="$(curl -s -H "Authorization: Bearer $TOKEN" \
    -F "file=@$b;type=application/octet-stream" \
    "$API_BASE/developer/upload-bundle")"
  ID="$(printf '%s' "$UP_RESP" | json_get app_id)"
  if [[ -z "$ID" ]]; then
    warn "Bundle upload failed for $a (non-fatal): $UP_RESP"
    continue
  fi
  DETECTED_ID="$ID"
  ok "Uploaded $a — detected app_id: $ID"
done

# ---------------------------------------------------------------------------
# 8. Submit metadata to the review queue
# ---------------------------------------------------------------------------
step "8/8  Submitting app metadata"
META_JSON="$(APP_ID="$APP_ID" NAME="$APP_NAME" SUMMARY="$APP_SUMMARY" \
  DESCRIPTION="$APP_DESCRIPTION" CATEGORY="$APP_CATEGORY" TAGS="$APP_TAGS" \
  LICENSE="$APP_LICENSE" HOMEPAGE="$APP_HOMEPAGE" \
  BUILD_ID="$FM_BUILD_ID" BUILD_URL="${BUILD_URL:-}" python3 -c '
import os, json
tags = [t.strip().lower() for t in os.environ.get("TAGS","").split(",") if t.strip()]
d = {
  "app_id": os.environ["APP_ID"],
  "name": os.environ["NAME"],
  "summary": os.environ["SUMMARY"],
  "description": os.environ["DESCRIPTION"],
  "app_type": "desktop-application",
  "categories": [os.environ["CATEGORY"]],
}
if tags: d["tags"] = tags
if os.environ.get("LICENSE"):    d["license"]           = os.environ["LICENSE"]
if os.environ.get("HOMEPAGE"):   d["homepage"]          = os.environ["HOMEPAGE"]
if os.environ.get("BUILD_ID"):   d["flatpak_build_id"]  = int(os.environ["BUILD_ID"])
if os.environ.get("BUILD_URL"):  d["flatpak_build_url"] = os.environ["BUILD_URL"]
print(json.dumps(d))')"

SUB_RESP="$(curl -s -w $'\n%{http_code}' -X POST "$API_BASE/developer/submit" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "$META_JSON")"
SUB_CODE="$(printf '%s' "$SUB_RESP" | tail -n1)"
SUB_BODY="$(printf '%s' "$SUB_RESP" | sed '$d')"
SUB_ID="$(printf '%s' "$SUB_BODY" | json_get id)"

case "$SUB_CODE" in
  201|200) ok "Submitted — submission #${SUB_ID:-?} (flatpak_build_id=${FM_BUILD_ID:-none})" ;;
  409)     warn "Active submission for $APP_ID already exists (build-repo push still applied)." ;;
  *)       die "Submit failed (HTTP $SUB_CODE): $SUB_BODY" ;;
esac

# Cleanup local bundles (repo kept for inspection)
rm -f "${APP_ID}"*.flatpak

echo
echo "${C_GREEN}========================================${C_RST}"
echo "${C_GREEN} Done! $APP_ID pushed to the AGL Store${C_RST}"
echo "${C_GREEN}========================================${C_RST}"
info "Submission : #${SUB_ID:-?}  (status: in review queue)"
info "Build id   : ${FM_BUILD_ID:-none}  (admin approval publishes this to main repo)"
info "Arches     : $ARCHES"
info "OSTree refs: app/$APP_ID/{$(tr ' ' ',' <<<"$ARCHES")}/$FM_REF"
info "Track at   : $AGL_ADMIN/developer/portal"
