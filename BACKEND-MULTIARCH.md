# Backend handoff — accept multi-arch (x86_64 + aarch64 + arm/armv7)

Goal: let one app be **published for multiple architectures** — `x86_64`, `aarch64`
(arm64), and `arm` (armv7) — through the AGL store backend.

> Arch naming (flatpak/OSTree): `x86_64`, `aarch64` (= arm64), `arm` (= armv7,
> 32-bit). Use these exact strings; "armv7" is `arm` in refs.

---

## TL;DR — is a backend change even required?

**For publishing: NO, the happy path already works.** The developer tool pushes all
arch refs into ONE flat-manager build and submits that single `flatpak_build_id`;
approval calls flat-manager's publish, which is **arch-agnostic and publishes every
ref in the build**. flat-manager needs no changes.

**But the backend has single-arch assumptions that will cause bugs / wrong UI / broken
cleanup once arm builds flow through.** The tasks below remove those assumptions so the
backend correctly *receives, records, displays, and tears down* multi-arch apps.

Active code lives in the **top-level flat files** (`rest_api.py`, `database.py`,
`models.py`) — NOT the `app/` package (that's a partially-wired alternate structure).

---

## What the developer side now sends (already implemented in `auto-run.sh`)

For one app, in one run:

1. **flat-manager:** builds host arch once, clones the OSTree ref into each other arch
   (these apps are pure-Python / arch-independent — no QEMU, no cross-SDK), pushes
   **all** arch refs (`app/<id>/x86_64/<branch>`, `.../aarch64/...`, `.../arm/...`)
   into a **single** flat-manager build → **one `flatpak_build_id`**.
2. **upload-bundle:** uploads **one `.flatpak` bundle per arch**
   (`<id>-x86_64.flatpak`, `<id>-aarch64.flatpak`, `<id>-arm.flatpak`) — i.e.
   `POST /developer/upload-bundle` is now called **2–3 times for the same app_id**.
3. **submit:** **one** submission carrying the single `flatpak_build_id`.
4. Branch is `stable` by default (env `FM_REF`), **not** `master`.

So the backend must tolerate: multiple `upload-bundle` calls per app (different arches),
and a submission whose build contains multiple arch refs.

---

## Backend tasks

### 1. `upload-bundle`: import each arch generically; stop faking arches
File: `rest_api.py` → `upload_bundle()` @ **~1204**

- Currently imports the bundle into `/srv/flatpak-repo` via `flatpak build-import-bundle`
  (~1249-1257), then extracts arch (~1277-1278) **defaulting to `x86_64`**.
- **Problem A — the clone hack (~1276-1307):** when the imported arch is `x86_64`, it
  checks out `app/{id}/x86_64/master`, rewrites metadata `/x86_64/` → `/aarch64/`, and
  commits a synthetic `app/{id}/aarch64/master`. With real aarch64 uploads this produces
  a **fake aarch64 ref that collides with / shadows the real one**. → **Remove it**, or
  gate it behind an explicit `arch_independent=true` flag that is OFF when real per-arch
  bundles are uploaded.
- **Problem B — x86_64 default:** read the arch **from the imported ref** for *every*
  bundle (don't default to x86_64), so `aarch64` and `arm` import under their own refs
  and coexist. Verify a 2nd/3rd upload for the same `app_id` does **not** overwrite the
  earlier arch (refs are keyed `app/{id}/{arch}/{branch}` so they should coexist — just
  don't assume/rewrite arch).
- Return the **actual** arch imported (don't hardcode `arches: ["x86_64","aarch64"]`
  @ ~1317-1320).

### 2. Hardcoded branch `master` vs real `stable`
- `upload-bundle` (clone hack, revoke, expiry) assumes branch `master`. Real refs use the
  configurable branch (default `stable`). Derive the branch from the imported ref instead
  of hardcoding `master`. Affected: ~1284-1295, **2087**, **2348**.

### 3. Generalize revoke / expiry to ALL arches
Files/lines: `rest_api.py:2087` (revoke), `rest_api.py:2348` (expiry cleanup)

- Both hardcode `ref = f"app/{app_id}/x86_64/master"`. With multi-arch this **orphans**
  the `aarch64` and `arm` refs on unpublish/expiry.
- Replace with enumeration: list `ostree refs` matching `app/{app_id}/*/*` and delete
  each (all arches, correct branch).

### 4. (Recommended) Track arches in the data model + expose them
- `SubmitAppRequest` (`rest_api.py:611-624`) has no arch field. `AppSubmission`
  (`database.py:285-315`) and `App` (`database.py:40-84`) have **no arch column**.
- Add an `arches: List[str]` (store as JSON/text) to `App` (and optionally
  `AppSubmission`); **populate it from the published refs** rather than trusting client
  input.
- Display models already exist: `AppsIndex.arches` (`models.py:257`) and
  `SummaryResponse.arches` (`models.py:330`). Wire them to the new column.
- `service.py:252` has `arches=["x86_64"],  # Would get from app metadata` — replace the
  stub with the real per-app arch list.

### 5. Submission uniqueness — confirm it still fits
- `submit_app()` (`rest_api.py:1333`) rejects a new submit if a pending/approved one
  exists for the app (409, ~1356-1361). This is **fine** — multi-arch is ONE submission
  (one `flatpak_build_id` spanning all arches), not one-per-arch. No change needed, but
  don't "fix" this into per-arch submissions.

### 6. Publish path — no change needed (verify only)
- `approve_submission()` (`rest_api.py:1454`) → flat-manager publish (~1517-1538) POSTs
  `{FLAT_MANAGER_API}/api/v1/build/{build_id}/publish`, which publishes **all** refs/arches
  in the build. Confirmed arch-agnostic. Just ensure the flat-manager path runs whenever
  `flatpak_build_id` is set (it does).

---

## Acceptance criteria

1. Uploading `x86_64`, `aarch64`, and `arm` bundles for the same `app_id` results in
   three independent refs in the repo — none overwritten, none synthetic.
2. No fabricated/cloned arch refs are created server-side for real multi-arch uploads.
3. A single submission with one `flatpak_build_id` publishes all three arches on approval.
4. `App.arches` reflects the real published arches and surfaces in the index/summary API.
5. Revoking or expiring an app removes **all** arch refs (`app/{id}/*/*`), not just x86_64.
6. No code hardcodes branch `master` where the deploy branch is `stable`.

## Out of scope
- flat-manager (`/home/mukhayyar/projects/agl/flat-manager`) — already fully arch-agnostic.
- Cross-compilation / QEMU — not needed; these apps are arch-independent and cloned at the
  OSTree layer. (If a future app ships **compiled** code, real per-arch builds with
  `qemu-user-static` + per-arch SDKs would be required, and the clone trick must NOT be
  used for it.)
