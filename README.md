# 📦 Simple Flatpak App Collections

A curated collection of **130 real, functional GTK4 Python applications** packaged as Flatpaks — built as a test suite for the **[PENS AGL Store](https://agl.automotivelinux.org/)** (Politeknik Elektronika Negeri Surabaya — Automotive Grade Linux App Store for IVI/embedded systems).

Each app is a standalone, installable Flatpak with:

- A real GTK4 Python UI (no stubs or placeholders)
- A pixel-art icon at `<folder>/icon.png`
- A complete Flatpak manifest (`<folder>/<app-id>.json`)
- All runtime dependencies declared

---

## 🚀 Quick Start

### Prerequisites

```bash
# Install Flatpak and flatpak-builder
sudo apt install flatpak flatpak-builder   # Debian/Ubuntu
sudo dnf install flatpak flatpak-builder   # Fedora
sudo pacman -S flatpak flatpak-builder     # Arch

# Add GNOME runtime remote
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

# Install required runtime
flatpak install flathub org.gnome.Platform//46 org.gnome.Sdk//46
```

### Build & Install a Single App

```bash
cd <app-folder>
flatpak-builder --user --install --force-clean build-dir *.json
```

### Run

```bash
flatpak run <app-id>
# e.g.:
flatpak run io.github.mukhayyar.HelloWorld
```

### Build All Apps (batch)

```bash
for dir in */; do
  manifest=$(find "$dir" -maxdepth 1 -name '*.json' | head -1)
  [ -z "$manifest" ] && continue
  echo "Building $dir..."
  flatpak-builder --user --install --force-clean "$dir/build-dir" "$manifest"
done
```

---

## 🗂️ App Manifest Structure

Each app folder follows a consistent layout:

```
<app-folder>/
├── icon.png                  # Pixel-art app icon (48×48 or 64×64)
├── <app-id>.json             # Flatpak manifest
├── <app-id>.desktop          # Desktop entry
├── <app-id>.metainfo.xml     # AppStream metadata
└── src/
    └── main.py               # GTK4 Python entry point
```

### Example Manifest (`hello-world/io.github.mukhayyar.HelloWorld.json`)

```json
{
  "app-id": "io.github.mukhayyar.HelloWorld",
  "runtime": "org.gnome.Platform",
  "runtime-version": "46",
  "sdk": "org.gnome.Sdk",
  "command": "hello-world",
  "finish-args": [
    "--share=ipc",
    "--socket=fallback-x11",
    "--socket=wayland"
  ],
  "modules": [
    {
      "name": "hello-world",
      "buildsystem": "simple",
      "build-commands": [
        "install -Dm755 main.py /app/bin/hello-world"
      ],
      "sources": [
        { "type": "file", "path": "main.py" }
      ]
    }
  ]
}
```

---

## 📋 Full App Catalog (130 Apps)

### 🌱 Original Collection (10 apps)

| Folder | Description |
|--------|-------------|
| `hello-world` | Classic Hello World GTK4 window — the simplest possible Flatpak |
| `calculator` | Arithmetic calculator with history and keyboard support |
| `digital-clock` | Real-time digital clock with date display and timezone selector |
| `todo-list` | Task manager with add, complete, and delete functionality |
| `pomodoro` | Pomodoro technique timer with work/break cycle tracking |
| `unit-converter` | Multi-category unit converter (length, weight, temperature, etc.) |
| `color-picker` | Screen color picker with hex/RGB/HSL output and palette history |
| `weather-viewer` | Weather forecast viewer using an open weather API |
| `text-editor` | Minimal plain-text editor with open, edit, and save support |
| `system-info` | Displays CPU, memory, OS, and hardware information |

---

### 🎵 AudioVideo (10 apps)

| Folder | Description |
|--------|-------------|
| `audio-audio-timer` | Interval timer that plays audio alerts at set intervals |
| `audio-chord-finder` | Guitar/piano chord finder with visual fingering diagrams |
| `audio-drum-machine` | Step-sequencer drum machine with BPM control and pattern editor |
| `audio-metronome` | Adjustable-BPM metronome with visual beat indicator |
| `audio-music-theory` | Music theory reference: scales, intervals, and chord formulas |
| `audio-pitch-tuner` | Chromatic pitch tuner using the microphone input |
| `audio-radio-player` | Internet radio player with stream URL input and station list |
| `audio-recorder` | Simple audio recorder with waveform preview and export to WAV |
| `audio-spectrum-analyzer` | Real-time audio spectrum analyzer visualizing frequency bands |
| `audio-tone-generator` | Sine/square/sawtooth tone generator with frequency and volume control |

---

### 🛠️ Development (10 apps)

| Folder | Description |
|--------|-------------|
| `dev-ascii-art` | Converts text to ASCII art using various font styles |
| `dev-base-converter` | Converts numbers between binary, octal, decimal, and hexadecimal |
| `dev-diff-viewer` | Side-by-side text diff viewer with highlighted changes |
| `dev-hash-tool` | Computes MD5, SHA-1, SHA-256, and SHA-512 hashes of text or files |
| `dev-http-tester` | Lightweight HTTP client for testing GET/POST API endpoints |
| `dev-json-formatter` | JSON formatter, validator, and pretty-printer with syntax highlighting |
| `dev-jwt-decoder` | Decodes and inspects JWT tokens (header, payload, signature) |
| `dev-regex-tester` | Interactive regular expression tester with live match highlighting |
| `dev-timestamp-tool` | Converts Unix timestamps to human-readable dates and vice versa |
| `dev-uuid-generator` | Generates UUID v1/v4 identifiers in bulk with clipboard copy |

---

### 🎮 Games (10 apps)

| Folder | Description |
|--------|-------------|
| `game-2048` | Classic 2048 sliding tile puzzle game |
| `game-breakout` | Breakout/Arkanoid brick-breaker arcade game |
| `game-chess-clock` | Two-player chess clock with configurable time controls |
| `game-fifteen-puzzle` | 15-tile sliding puzzle game with move counter |
| `game-memory-match` | Card memory matching game with flip animations |
| `game-minesweeper` | Classic Minesweeper with beginner/intermediate/expert modes |
| `game-paint` | Simple pixel painting canvas with brush, fill, and eraser tools |
| `game-snake` | Classic Snake game with score tracking and speed levels |
| `game-sudoku` | Sudoku puzzle game with hint and validation features |
| `game-word-guess` | Word-guessing game (Wordle-style) with colored feedback |

---

### 🎨 Graphics (10 apps)

| Folder | Description |
|--------|-------------|
| `gfx-color-palette` | Color palette builder and swatch organizer with export support |
| `gfx-font-browser` | Browse all installed system fonts with live preview |
| `gfx-fractal-viewer` | Mandelbrot and Julia set fractal viewer with zoom support |
| `gfx-histogram` | Displays RGB and luminance histograms from an image file |
| `gfx-icon-browser` | Browse and search all installed icon themes in the system |
| `gfx-image-viewer` | Lightweight image viewer supporting JPEG, PNG, WebP, and GIF |
| `gfx-pixel-editor` | Grid-based pixel art editor with palette and export to PNG |
| `gfx-qr-generator` | Generates QR codes from text or URLs with download support |
| `gfx-sketch-pad` | Freehand drawing canvas with pen, shapes, and color picker |
| `gfx-svg-viewer` | Renders and inspects SVG files with zoom and pan controls |

---

### 🌐 Network (10 apps)

| Folder | Description |
|--------|-------------|
| `net-dns-lookup` | DNS record lookup tool supporting A, AAAA, MX, TXT, and CNAME |
| `net-ip-info` | Displays public and local IP information with geolocation data |
| `net-network-monitor` | Monitors real-time network interface throughput (RX/TX) |
| `net-ping-monitor` | Continuous ping monitor with latency graph and packet-loss stats |
| `net-port-scanner` | TCP port scanner for scanning open ports on a host |
| `net-socket-tester` | Simple TCP/UDP socket send/receive tester for debugging |
| `net-speed-test` | Internet speed test measuring download and upload throughput |
| `net-traceroute-viewer` | Visualizes traceroute hops to a destination with latency data |
| `net-url-checker` | Checks URL reachability and displays HTTP status/response headers |
| `net-wifi-info` | Displays connected Wi-Fi SSID, signal strength, and interface details |

---

### 📋 Office (10 apps)

| Folder | Description |
|--------|-------------|
| `office-calendar-app` | Monthly calendar with event creation and reminder support |
| `office-contact-book` | Personal address book with search, add, edit, and delete |
| `office-expense-tracker` | Daily expense tracker with category breakdown and totals |
| `office-flashcards` | Flashcard study tool with flip animation and progress tracking |
| `office-habit-tracker` | Habit tracker with streak counters and daily check-ins |
| `office-invoice-maker` | Simple invoice generator with PDF export |
| `office-notes` | Quick-note app with markdown preview and persistent storage |
| `office-password-manager` | Local encrypted password vault with master password protection |
| `office-time-tracker` | Work time logger with project tagging and session summaries |
| `office-word-counter` | Text word/character/sentence/paragraph counter with readability score |

---

### 🎓 Education (10 apps)

| Folder | Description |
|--------|-------------|
| `edu-bmi-calculator` | Body Mass Index calculator with weight category classification |
| `edu-currency-converter` | Real-time currency converter using exchange rate API |
| `edu-grammar-checker` | Basic grammar and spelling checker for English text |
| `edu-language-flash` | Language learning flashcard app with vocabulary sets |
| `edu-math-quiz` | Arithmetic quiz generator for practicing mental math |
| `edu-morse-code` | Morse code encoder/decoder with audio playback |
| `edu-number-systems` | Interactive explorer for binary, octal, decimal, and hex number systems |
| `edu-periodic-table` | Interactive periodic table with element detail panel |
| `edu-timezone-world` | World clock displaying times across multiple configurable timezones |
| `edu-typing-tutor` | Touch-typing practice tool with WPM and accuracy metrics |

---

### 🔬 Science (10 apps)

| Folder | Description |
|--------|-------------|
| `sci-binary-counter` | Animated binary counter with bit-level visualization |
| `sci-function-plotter` | 2D mathematical function plotter supporting custom expressions |
| `sci-logic-gates` | Logic gate simulator with AND, OR, NOT, XOR, NAND, NOR |
| `sci-matrix-calc` | Matrix calculator for addition, multiplication, transpose, and inverse |
| `sci-ohm-calculator` | Ohm's law calculator for voltage, current, and resistance |
| `sci-pendulum-sim` | Simple pendulum physics simulator with adjustable length and gravity |
| `sci-prime-sieve` | Visualizes the Sieve of Eratosthenes for finding prime numbers |
| `sci-statistics-calc` | Descriptive statistics calculator: mean, median, mode, std dev |
| `sci-unit-science` | Scientific unit converter covering force, energy, pressure, etc. |
| `sci-wave-simulator` | Sine wave simulator with frequency, amplitude, and phase controls |

---

### 🖥️ System (10 apps)

| Folder | Description |
|--------|-------------|
| `sys-boot-analyzer` | Analyzes systemd boot time and shows slowest units |
| `sys-cpu-benchmark` | Simple CPU benchmark measuring single-threaded computation speed |
| `sys-disk-usage` | Disk usage visualizer with directory tree and bar chart |
| `sys-env-viewer` | Displays all environment variables with search and copy |
| `sys-file-permissions` | File permission viewer and chmod helper with octal display |
| `sys-log-viewer` | Real-time system log viewer with filter and search support |
| `sys-memory-map` | Visual memory map showing RAM usage by category |
| `sys-process-viewer` | Process list viewer with CPU/memory usage per process |
| `sys-service-monitor` | systemd service status monitor with start/stop/restart controls |
| `sys-startup-manager` | Lists and toggles systemd user services at login |

---

### 🔧 Utility (10 apps)

| Folder | Description |
|--------|-------------|
| `util-alarm-clock` | Alarm clock with multiple alarms and custom notification sounds |
| `util-archive-viewer` | Browse ZIP and TAR archive contents without extraction |
| `util-barcode-gen` | Generates barcodes in Code128, EAN-13, QR, and DataMatrix formats |
| `util-clipboard-manager` | Clipboard history manager with search and re-paste support |
| `util-date-calculator` | Date arithmetic: days between dates, add/subtract durations |
| `util-file-renamer` | Batch file renamer with pattern substitution and preview |
| `util-random-tools` | Random number, UUID, password, and dice-roll generator |
| `util-screen-ruler` | On-screen pixel ruler for measuring UI element dimensions |
| `util-stopwatch` | Stopwatch with lap recording and split time history |
| `util-text-tools` | Text transformation toolkit: case, trim, encode, decode, sort |

---

### ⚙️ Settings (10 apps)

| Folder | Description |
|--------|-------------|
| `set-display-info` | Displays monitor resolution, refresh rate, and scaling info |
| `set-font-manager` | Preview and compare installed fonts with size controls |
| `set-gtk-inspector` | Shortcut launcher for the built-in GTK4 Inspector debug tool |
| `set-keyboard-tester` | Visual keyboard tester showing key codes and modifier states |
| `set-locale-info` | Displays current locale, language, and encoding settings |
| `set-mouse-tester` | Mouse button, scroll, and pointer precision tester |
| `set-power-profiles` | Switches between power-saver, balanced, and performance profiles |
| `set-proxy-settings` | Configures and tests system HTTP/HTTPS proxy settings |
| `set-shortcut-ref` | Quick-reference card for common GNOME keyboard shortcuts |
| `set-theme-switcher` | Toggles between light and dark GTK4 themes system-wide |

---

### ♿ Accessibility (10 apps)

| Folder | Description |
|--------|-------------|
| `a11y-click-assist` | Dwell clicking assistant for users with limited motor control |
| `a11y-color-blind-sim` | Simulates color blindness types (deuteranopia, protanopia, etc.) |
| `a11y-contrast-checker` | WCAG contrast ratio checker for foreground/background color pairs |
| `a11y-font-size-tool` | System-wide font size adjuster for accessibility preferences |
| `a11y-high-contrast` | Toggles high-contrast GTK theme for visual impairment support |
| `a11y-on-screen-keyboard` | On-screen virtual keyboard for touchscreen or mouse input |
| `a11y-reading-guide` | Reading guide overlay to aid line tracking on screen |
| `a11y-screen-magnifier` | Screen magnifier with configurable zoom level and follow-cursor |
| `a11y-text-to-speech` | Text-to-speech reader using espeak/festival for selected text |
| `a11y-voice-notes` | Voice note recorder and transcriber using speech recognition |

---

## 🐛 Troubleshooting

### `flatpak-builder` not found

```bash
sudo apt install flatpak-builder   # Debian/Ubuntu
sudo dnf install flatpak-builder   # Fedora
```

### Runtime not installed

```bash
flatpak install flathub org.gnome.Platform//46 org.gnome.Sdk//46
```

### App launches but shows no window (Wayland)

Some apps may need X11 fallback. Run with:

```bash
flatpak run --socket=fallback-x11 <app-id>
```

### Permission errors during build

Make sure the user Flatpak installation is initialized:

```bash
flatpak --user remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
```

### Python module not found inside sandbox

Check that the required Python package is declared as a module in the manifest's `modules` array, either bundled or sourced from PyPI via `pip`.

### Build cache issues

Force a clean rebuild:

```bash
flatpak-builder --force-clean build-dir *.json
```

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.

---

## 🏫 About PENS AGL Store

This collection serves as a real-world test dataset for the **PENS AGL Store** — an Automotive Grade Linux application store developed at [Politeknik Elektronika Negeri Surabaya (PENS)](https://www.pens.ac.id/). The store targets IVI (In-Vehicle Infotainment) and embedded Linux systems running AGL, providing a curated app distribution mechanism similar to a traditional app store but optimized for automotive environments.

All 130 apps in this repository are used to validate app ingestion, metadata parsing, icon rendering, and Flatpak distribution pipelines on AGL-compatible targets.
