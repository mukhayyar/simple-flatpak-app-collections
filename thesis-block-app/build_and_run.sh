#!/bin/bash
APP_ID="com.thesis.BlockApp"
MANIFEST_FILE="com.thesis.BlockApp.yml"
BUILD_DIR="flatpak_build"
REPO_DIR="flatpak_repo"
rm -rf "$BUILD_DIR" "$REPO_DIR"
flatpak-builder --force-clean "$BUILD_DIR" "$MANIFEST_FILE" || exit 1
flatpak build-export "$REPO_DIR" "$BUILD_DIR"
flatpak remote-delete --user local-repo-block 2>/dev/null || true
flatpak remote-add --user --no-gpg-verify local-repo-block "$REPO_DIR"
flatpak install --user local-repo-block "$APP_ID" -y
flatpak run "$APP_ID"
