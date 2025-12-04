# Simple Flatpak App Collections

A collection of simple Python applications packaged as Flatpak applications. This project demonstrates how to containerize and distribute desktop applications using Flatpak technology. This project is helping to test PENS Automotive Grade Linux Store using meta-flatpak and flatpak-manager(FlatHub alike).

## 📋 Project Overview

This repository contains multiple sample applications, each packaged as a Flatpak with their own build and run scripts. The applications are built on top of GNOME Runtime 45 and provide a practical starting point for Flatpak packaging.

## 🎯 Available Applications

### 1. **Hello World** (`hello-world/`)
   - A simple introductory application
   - Perfect for learning Flatpak basics
   - Minimal dependencies and configuration

### 2. **Calculator** (`calculator/`)
   - A basic calculator application
   - Demonstrates windowing system integration
   - Audio socket configuration (PulseAudio support)

### 3. **Digital Clock** (`digital-clock/`)
   - Displays current time with digital clock interface
   - Shows UI framework integration
   - Real-time updates example

### 4. **Todo List** (`todo-list/`)
   - A task management application
   - Demonstrates persistent data handling
   - File system access configuration

### 5. **Pomodoro** (`pomodoro/`)
   - A Pomodoro timer application
   - Time-based task management
   - Notification system integration

## 🚀 Quick Start

### Prerequisites

Before you can build any Flatpak application, ensure you have the following installed:

- **Flatpak**: The containerization technology
- **Flatpak Builder**: Tool for building Flatpak applications
- **GNOME SDK 45**: Runtime environment for building (required for these examples)

### Installation Instructions

For detailed installation instructions for your Linux distribution, see [BUILDER.md](BUILDER.md).

**Quick install (Ubuntu/Debian):**
```bash
sudo add-apt-repository ppa:flatpak/stable
sudo apt update
sudo apt install flatpak flatpak-builder
flatpak install flathub org.gnome.Sdk//45 org.gnome.Platform//45
```

### Building and Running an Application

Each application folder contains a `build_and_run.sh` script that automates the build process:

```bash
cd <app-folder>
./build_and_run.sh
```

**Example:**
```bash
cd calculator
./build_and_run.sh
```

The script will:
1. Clean up previous builds
2. Build the Flatpak application using the manifest file
3. Create a local repository
4. Install the application
5. Launch the application

## 📁 Project Structure

```
simple-flatpak-app-collections/
├── README.md                    # This file
├── BUILDER.md                   # Detailed installation guide
├── calculator/
│   ├── calculator.py            # Application source code
│   ├── com.pens.Calculator.yml  # Flatpak manifest
│   ├── build_and_run.sh         # Build and run script
│   ├── flatpak_build/           # Build output directory
│   └── flatpak_repo/            # Local repository
├── digital-clock/
│   ├── digital_clock.py
│   ├── com.pens.DigitalClock.yml
│   ├── build_and_run.sh
│   └── ...
├── hello-world/
│   ├── hello.py
│   ├── com.pens.HelloWorld.yml
│   ├── build_and_run.sh
│   └── ...
├── pomodoro/
│   ├── pomodoro.py
│   ├── com.pens.Pomodoro.yml
│   ├── build_and_run.sh
│   └── ...
└── todo-list/
    ├── todo-list.py
    ├── com.pens.TodoList.yml
    ├── build_and_run.sh
    └── ...
```

## 📝 Understanding Flatpak Manifests

Each application includes a `.yml` manifest file (e.g., `com.pens.Calculator.yml`) that defines:

- **App ID**: Unique identifier (reverse domain notation)
- **Runtime**: Base OS environment (org.gnome.Platform 45)
- **SDK**: Development kit for building (org.gnome.Sdk)
- **Command**: Entry point for the application
- **Finish Args**: Permissions and system access
  - `--socket=wayland`: Wayland display server access
  - `--socket=fallback-x11`: X11 fallback for older systems
  - `--socket=pulseaudio`: Audio system access
- **Modules**: Build configuration and source files

## 🔧 Common Tasks

### Clean Build
To force a complete rebuild without cache:
```bash
cd <app-folder>
rm -rf flatpak_build flatpak_repo
./build_and_run.sh
```

### View Build Output
```bash
flatpak-builder --show-manifest <app-folder>/com.pens.*.yml
```

### List Installed Flatpak Applications
```bash
flatpak list --app
```

### Uninstall an Application
```bash
flatpak uninstall com.pens.<AppName>
```

## 📚 Resources

- [Flatpak Official Documentation](https://docs.flatpak.org)
- [GNOME Platform Runtime](https://docs.flatpak.org/en/latest/available-runtimes.html)
- [Flatpak Manifest Reference](https://docs.flatpak.org/en/latest/manifests.html)
- [Flathub Repository](https://flathub.org)

## 🛠️ Troubleshooting

### "Unable to find sdk org.gnome.Sdk version 45"
Make sure you have installed the GNOME SDK 45:
```bash
flatpak install flathub org.gnome.Sdk//45 org.gnome.Platform//45
```

### Build fails with permission issues
Ensure you have the necessary permissions and that flatpak-builder is correctly installed:
```bash
flatpak-builder --version
```

### Application doesn't launch
Check the application logs:
```bash
flatpak run --command=sh com.pens.<AppName>
```

## 📄 License

Specify your project license here.

## 👥 Contributing

To add a new application to this collection:

1. Create a new directory: `mkdir new-app`
2. Add your Python application file
3. Create a Flatpak manifest (`.yml` file) based on existing examples
4. Create a `build_and_run.sh` script
5. Test the build and run process
6. Submit a pull request

## 📞 Support

For issues, questions, or improvements, please open an issue or discussion in the repository.
