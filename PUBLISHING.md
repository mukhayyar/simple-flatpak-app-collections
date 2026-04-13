# Publishing to AGL PENS Store

Complete guide to signing and submitting a Flatpak app from this collection to the [AGL PENS Store](https://admin.agl-store.cyou).

---

## Overview

Every app submission requires:
1. A **personal GPG signing key** (issued by the platform, downloaded once)
2. A **signed `.flatpak` bundle** (the script handles this automatically)
3. An **upload token** (generated when you fill the Submit App form on the portal)

The `publish.sh` in each app folder wraps everything into a single command.

---

## Part 1 — One-Time Setup

### Step 1: Create a developer account

Go to **[admin.agl-store.cyou](https://admin.agl-store.cyou/developer/portal)** and sign in with your GitHub account or institutional email.

### Step 2: Download your signing key

1. In the Developer Portal, scroll to the **Signing Key** section
2. Click **"Download Signing Key"** — saves as `agl-signing-key-<yourname>.gpg`
3. Import it into your local GPG keyring:

```bash
gpg --import agl-signing-key-yourname.gpg
```

4. Verify it was imported:

```bash
gpg --list-secret-keys | grep "AGL Developer"
```

You should see output like:
```
uid   [ultimate] Your Name (AGL Developer) <devXX@agl-store.cyou>
```

> **Your signing key is valid for 1 year.** You'll get an email reminder before it expires. Renew it from the portal.

### Step 3: Install prerequisites

```bash
# Flatpak tools
sudo apt install flatpak flatpak-builder gpg curl  # Debian/Ubuntu
sudo dnf install flatpak flatpak-builder gnupg curl # Fedora
sudo pacman -S flatpak flatpak-builder gnupg curl   # Arch

# GNOME runtime (required by all apps in this collection)
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install flathub org.gnome.Platform//46 org.gnome.Sdk//46
```

### Step 4: Download push-to-agl.sh (once, at repo root)

```bash
# Run from the root of this repo (simple-flatpak-app-collections/)
curl -o push-to-agl.sh https://admin.agl-store.cyou/api/push-to-agl.sh
chmod +x push-to-agl.sh
```

The `publish.sh` in each app folder looks for `../../push-to-agl.sh` relative to itself — so keep it at the repo root.

---

## Part 2 — Submitting an App

### Step 1: Build the app locally (test first)

```bash
cd <app-folder>          # e.g. cd game-snake
./build_and_run.sh       # builds, installs, and runs the app locally
```

Make sure the app launches and works correctly before submitting.

### Step 2: Get an upload token from the portal

1. Go to **[admin.agl-store.cyou/developer/portal](https://admin.agl-store.cyou/developer/portal)**
2. Scroll to **"Submit App"**
3. Fill in the form:
   - **App ID** — e.g. `com.pens.Snake` (must match the manifest `app-id`)
   - **Name**, **Summary**, **Category**, etc.
4. Click **"Submit"**
5. The portal shows a **"Next Step"** panel with a ready-to-copy command including your upload token
6. Copy just the `--token` value (starts with `ey...`)

### Step 3: Publish

```bash
cd <app-folder>
./publish.sh --token YOUR_UPLOAD_TOKEN
```

That's it. The script will:
1. Build a `.flatpak` bundle from `./flatpak_repo`
2. Sign it with your AGL signing key (GPG, automatic)
3. Upload the signed bundle to the store
4. Submit the metadata
5. Clean up temporary files

Example output:
```
==> Using AGL signing key: ...A1B2C3D4E5F6
==> Building bundle from ./flatpak_repo...
==> Signing bundle with key A1B2C3D4E5F6...
    Signature: com.pens.Snake.flatpak.asc
==> Uploading bundle to AGL store...
    Upload successful. Detected app_id: com.pens.Snake
==> Submitting app metadata...

✓ Done! Submission #42 queued for review.

  App ID:    com.pens.Snake
  Track:     https://admin.agl-store.cyou/developer/portal
```

---

## Part 3 — What Happens After Submission

| Stage | Who | What |
|---|---|---|
| **Pending** | System | Bundle stored, metadata saved |
| **Security scan** | ClamAV + checksec | Automated malware + hardening check |
| **Admin review** | PENS admin | Code review, policy check |
| **Approved** | Admin | App goes live on the store |
| **Rejected** | Admin | Email sent with reason; you can appeal |

You'll receive an email at each stage. Track status at the portal.

---

## Part 4 — Understanding GPG Signing

### Why signing is required

Every bundle uploaded to AGL Store must be signed with your personal developer key. This ensures:
- The bundle wasn't tampered with between your machine and the server
- Each submission is traceable to a verified developer identity
- The store can detect if a bundle is modified after signing

### How it works (under the hood)

```
You                         AGL Store
───                         ─────────
flatpak build-bundle        
  → com.pens.Snake.flatpak  

gpg --detach-sign           
  → com.pens.Snake.flatpak.asc

POST /developer/upload-bundle
  file=bundle.flatpak       →  server verifies .asc against
  signature=<asc content>       your stored public key
                            →  if valid: imports into OSTree repo
                            →  if invalid: 400 error

POST /developer/submit      →  metadata saved, submission created
  app_id, name, summary...
```

### Manual signing (if you want to do it yourself)

```bash
# 1. Build the bundle
flatpak build-bundle flatpak_repo com.pens.Snake.flatpak com.pens.Snake

# 2. Sign it (detached, ASCII-armored)
gpg --armor --detach-sign \
    --default-key "$(gpg --list-secret-keys --with-colons | grep -A1 'AGL Developer' | grep '^fpr' | head -1 | cut -d: -f10)" \
    --output com.pens.Snake.flatpak.asc \
    com.pens.Snake.flatpak

# 3. Verify locally (optional)
gpg --verify com.pens.Snake.flatpak.asc com.pens.Snake.flatpak

# 4. Upload manually
curl -X POST https://admin.agl-store.cyou/api/developer/upload-bundle \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@com.pens.Snake.flatpak" \
  -F "signature=$(cat com.pens.Snake.flatpak.asc)"
```

### Key management tips

```bash
# List your AGL signing keys
gpg --list-secret-keys | grep -A2 "AGL Developer"

# Backup your key (store safely — password manager, encrypted USB)
gpg --armor --export-secret-keys "AGL Developer" > my-agl-key-backup.gpg

# If you lose your key: go to the portal → Signing Key → Download again
# The platform stores your private key — you can always re-download it
```

---

## Troubleshooting

### `AGL signing key not found in your GPG keyring`
You haven't imported your key yet. Go to the portal → Download Signing Key → `gpg --import`.

### `GPG signature verification failed`
You signed with a different key than what's registered. Check:
```bash
gpg --list-secret-keys | grep AGL
```
Make sure you're using the key from the portal, not a personal key.

### `Bundle import failed`
The `.flatpak` bundle has an internal error. Check the build:
```bash
flatpak-builder --force-clean build-dir *.yml && echo "Build OK"
```

### `App ID segment starts with a digit`
App IDs like `com.pens.2048` are invalid — Flatpak rejects them.
Rename to `com.pens.Game2048`.

### Token expired / invalid
Upload tokens are valid for **48 hours**. If expired, go back to the portal, click Submit again, and get a new token.

---

## Quick Reference

```bash
# One-time setup
gpg --import agl-signing-key-*.gpg
curl -o push-to-agl.sh https://admin.agl-store.cyou/api/push-to-agl.sh && chmod +x push-to-agl.sh

# Per-app publish
cd <app-folder>
./build_and_run.sh            # test locally first
./publish.sh --token TOKEN    # sign and submit

# Check your key
gpg --list-secret-keys | grep "AGL Developer"

# Renew expired key
# → portal → Signing Key → Renew Key (re-download and re-import)
```
