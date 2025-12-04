#!/bin/bash

APP_ID="com.pens.DigitalClock"
MANIFEST_FILE="com.pens.DigitalClock.yml"
BUILD_DIR="flatpak_build"
REPO_DIR="flatpak_repo"

echo "1. Cleaning up previous builds..."
rm -rf "$BUILD_DIR" "$REPO_DIR"

echo "2. Building the Flatpak application using $MANIFEST_FILE..."
# --ccache is for faster rebuilding; --force-clean ensures a fresh build
flatpak-builder --force-clean "$BUILD_DIR" "$MANIFEST_FILE"

if [ $? -ne 0 ]; then
    echo "Flatpak build failed."
    exit 1
fi

echo "3. Creating a local repository for the application..."
flatpak build-export "$REPO_DIR" "$BUILD_DIR"

echo "4. Installing the application from the local repository..."

flatpak remote-delete --user local-repo 2> /dev/null || true
# Add the local repository (if not already added)
flatpak remote-add --user --no-gpg-verify local-repo "$REPO_DIR"

# Install the application
flatpak install --user local-repo "$APP_ID" -y

echo "5. Running the installed Flatpak application..."
flatpak run "$APP_ID"

echo "---------------------------------------"
echo "Build and run complete. To run again, use: flatpak run $APP_ID"
echo "To uninstall, use: flatpak uninstall $APP_ID"