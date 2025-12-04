How to Install Flatpak Builder

To build Flatpak applications, you generally need to install flatpak-builder separately, as it is often packaged apart from the main flatpak command.

1. Install Dependencies

Ubuntu / Debian / Linux Mint

On Debian-based systems, you need to add the official PPA to get the latest version, as the default repositories can be outdated.

sudo add-apt-repository ppa:flatpak/stable
sudo apt update
sudo apt install flatpak flatpak-builder


Note: If you are on an older version of Ubuntu and add-apt-repository is missing, install software-properties-common first.

Fedora / CentOS / RHEL

Fedora embraces Flatpak natively, so you usually just need to ensure the builder is installed.

sudo dnf install flatpak flatpak-builder


Arch Linux / Manjaro

Both packages are in the official repositories.

sudo pacman -S flatpak flatpak-builder


openSUSE

sudo zypper install flatpak flatpak-builder


2. Add the Flathub Repository

Even though you are building your own app, your app depends on a "Runtime" (like org.gnome.Platform) and an "SDK" (like org.gnome.Sdk). These are downloaded from Flathub.

Run this command to add the Flathub remote to your system:

flatpak remote-add --user --if-not-exists flathub [https://dl.flathub.org/repo/flathub.flatpakrepo](https://dl.flathub.org/repo/flathub.flatpakrepo)


3. Verify Installation

To check if you are ready to build, run:

flatpak-builder --version


If it prints a version number (e.g., Flatpak Builder 1.2.3), you are ready to run the build_and_run.sh scripts from the previous steps!


4. Install the GNOME SDK (Required for these examples)

The examples provided (Calculator, Clock, etc.) use the GNOME Runtime version 45. You need to install this specifically before building, otherwise you will get an error like Unable to find sdk org.gnome.Sdk version 45.

Run this command to install both the Platform (to run apps) and the SDK (to build apps):

flatpak install flathub org.gnome.Sdk//45 org.gnome.Platform//45


Note: You may be asked to select a specific version or architecture; usually, the default option (x86_64) is correct.

5. Verify Installation

To check if you are ready to build, run:

flatpak-builder --version


If it prints a version number (e.g., Flatpak Builder 1.2.3), you are ready to run the build_and_run.sh scripts from the previous steps!