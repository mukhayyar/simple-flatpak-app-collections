#!/usr/bin/env python3
import gi
import os
import subprocess
import socket
import time

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib

REFRESH_INTERVAL_MS = 2000  # 2 seconds


# ─────────────────────────────────────────────
# Data collection helpers (no external deps)
# ─────────────────────────────────────────────

def read_file(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except OSError:
        return ""


def get_cpu_info():
    """Return (model_name, usage_percent).
    usage_percent is computed from a delta over two /proc/stat reads.
    We store the previous reading as module-level state.
    """
    stat = read_file("/proc/stat")
    for line in stat.splitlines():
        if line.startswith("cpu "):
            parts = line.split()
            # user, nice, system, idle, iowait, irq, softirq, steal
            nums = list(map(int, parts[1:9]))
            idle = nums[3] + nums[4]  # idle + iowait
            total = sum(nums)
            return idle, total
    return 0, 1


_last_cpu = (0, 1)


def compute_cpu_usage():
    global _last_cpu
    idle, total = get_cpu_info()
    prev_idle, prev_total = _last_cpu
    _last_cpu = (idle, total)
    d_idle = idle - prev_idle
    d_total = total - prev_total
    if d_total == 0:
        return 0.0
    return max(0.0, min(100.0, (1.0 - d_idle / d_total) * 100.0))


def get_cpu_model():
    info = read_file("/proc/cpuinfo")
    for line in info.splitlines():
        if "model name" in line:
            return line.split(":", 1)[1].strip()
    return "Unknown CPU"


def get_memory_info():
    """Return (used_mb, total_mb)."""
    info = read_file("/proc/meminfo")
    values = {}
    for line in info.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            key = parts[0].rstrip(":")
            try:
                values[key] = int(parts[1])  # kB
            except ValueError:
                pass
    total_kb = values.get("MemTotal", 0)
    avail_kb = values.get("MemAvailable", values.get("MemFree", 0))
    used_kb = total_kb - avail_kb
    return used_kb // 1024, total_kb // 1024


def get_disk_info():
    """Return (used_gb, total_gb) for root."""
    try:
        result = subprocess.run(
            ["df", "-BG", "/"], capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().splitlines()
        if len(lines) >= 2:
            parts = lines[1].split()
            total = int(parts[1].rstrip("G"))
            used = int(parts[2].rstrip("G"))
            return used, total
    except Exception:
        pass
    return 0, 0


_last_net = {}


def get_network_info():
    """Return dict with hostname, ip, rx_bytes, tx_bytes."""
    hostname = socket.gethostname()
    try:
        ip = socket.gethostbyname(hostname)
    except Exception:
        ip = "N/A"

    rx_bytes = 0
    tx_bytes = 0
    net_dev = read_file("/proc/net/dev")
    for line in net_dev.splitlines()[2:]:
        parts = line.split()
        if len(parts) < 10:
            continue
        iface = parts[0].rstrip(":")
        if iface in ("lo",):
            continue
        try:
            rx_bytes += int(parts[1])
            tx_bytes += int(parts[9])
        except (ValueError, IndexError):
            pass

    return {"hostname": hostname, "ip": ip, "rx": rx_bytes, "tx": tx_bytes}


def get_system_info():
    """Return (os_name, kernel, uptime_str)."""
    os_name = "Unknown"
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    os_name = line.split("=", 1)[1].strip().strip('"')
                    break
    except OSError:
        pass

    kernel = os.uname().release

    try:
        uptime_secs = float(read_file("/proc/uptime").split()[0])
        h = int(uptime_secs // 3600)
        m = int((uptime_secs % 3600) // 60)
        s = int(uptime_secs % 60)
        uptime_str = f"{h}h {m}m {s}s"
    except Exception:
        uptime_str = "N/A"

    return os_name, kernel, uptime_str


def bytes_to_human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


# ─────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────

class SystemInfoWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("System Info")
        self.set_default_size(580, 640)

        css_provider = Gtk.CssProvider()
        css = b"""
        .title-label { font-size: 22px; font-weight: bold; }
        .section-title { font-size: 15px; font-weight: bold; color: #1565C0; margin-top: 10px; }
        .key-label { font-size: 13px; color: #444; }
        .val-label { font-size: 13px; font-weight: bold; color: #111; }
        .bar-low    { background-color: #4CAF50; min-height: 14px; border-radius: 4px; }
        .bar-mid    { background-color: #FF9800; min-height: 14px; border-radius: 4px; }
        .bar-high   { background-color: #F44336; min-height: 14px; border-radius: 4px; }
        .bar-bg     { background-color: #e0e0e0; min-height: 14px; border-radius: 4px; }
        """
        css_provider.load_from_data(css)
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.set_child(scroll)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        outer.set_margin_top(18)
        outer.set_margin_bottom(18)
        outer.set_margin_start(24)
        outer.set_margin_end(24)
        scroll.set_child(outer)

        title = Gtk.Label(label="System Info")
        title.add_css_class("title-label")
        title.set_halign(Gtk.Align.CENTER)
        outer.append(title)

        self._grid = Gtk.Grid()
        self._grid.set_row_spacing(5)
        self._grid.set_column_spacing(16)
        self._grid.set_hexpand(True)
        outer.append(self._grid)

        self._row = 0
        self._widgets = {}

        # Build sections
        self._add_section("CPU")
        self._add_row("cpu_model", "Model")
        self._add_bar_row("cpu_usage", "Usage")

        self._add_section("Memory")
        self._add_row("mem_used", "Used")
        self._add_row("mem_total", "Total")
        self._add_bar_row("mem_usage", "Usage")

        self._add_section("Disk (/)")
        self._add_row("disk_used", "Used")
        self._add_row("disk_total", "Total")
        self._add_bar_row("disk_usage", "Usage")

        self._add_section("Network")
        self._add_row("net_hostname", "Hostname")
        self._add_row("net_ip", "IP Address")
        self._add_row("net_rx", "RX Total")
        self._add_row("net_tx", "TX Total")

        self._add_section("System")
        self._add_row("sys_os", "OS")
        self._add_row("sys_kernel", "Kernel")
        self._add_row("sys_uptime", "Uptime")

        # Refresh label
        self._refresh_label = Gtk.Label(label="")
        self._refresh_label.set_halign(Gtk.Align.CENTER)
        self._refresh_label.set_margin_top(8)
        outer.append(self._refresh_label)

        # Initial read (pre-populate CPU baseline)
        compute_cpu_usage()  # first call initializes _last_cpu
        self._update_data()

        # Schedule periodic refresh
        GLib.timeout_add(REFRESH_INTERVAL_MS, self._on_refresh)

    def _add_section(self, title):
        lbl = Gtk.Label(label=title)
        lbl.add_css_class("section-title")
        lbl.set_halign(Gtk.Align.START)
        lbl.set_hexpand(True)
        self._grid.attach(lbl, 0, self._row, 3, 1)
        self._row += 1

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep.set_hexpand(True)
        self._grid.attach(sep, 0, self._row, 3, 1)
        self._row += 1

    def _add_row(self, key, display_name):
        key_lbl = Gtk.Label(label=display_name + ":")
        key_lbl.add_css_class("key-label")
        key_lbl.set_halign(Gtk.Align.END)
        key_lbl.set_size_request(130, -1)
        self._grid.attach(key_lbl, 0, self._row, 1, 1)

        val_lbl = Gtk.Label(label="—")
        val_lbl.add_css_class("val-label")
        val_lbl.set_halign(Gtk.Align.START)
        val_lbl.set_hexpand(True)
        val_lbl.set_selectable(True)
        val_lbl.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        self._grid.attach(val_lbl, 1, self._row, 2, 1)

        self._widgets[key] = val_lbl
        self._row += 1

    def _add_bar_row(self, key, display_name):
        key_lbl = Gtk.Label(label=display_name + ":")
        key_lbl.add_css_class("key-label")
        key_lbl.set_halign(Gtk.Align.END)
        key_lbl.set_size_request(130, -1)
        self._grid.attach(key_lbl, 0, self._row, 1, 1)

        # Overlay: background bar + fill bar stacked
        bar_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        bar_container.set_hexpand(True)
        bar_container.set_size_request(-1, 18)

        # Background
        bg = Gtk.Box()
        bg.add_css_class("bar-bg")
        bg.set_hexpand(True)
        bar_container.append(bg)

        val_lbl = Gtk.Label(label="0%")
        val_lbl.add_css_class("val-label")
        val_lbl.set_size_request(50, -1)
        val_lbl.set_halign(Gtk.Align.END)

        self._grid.attach(bar_container, 1, self._row, 1, 1)
        self._grid.attach(val_lbl, 2, self._row, 1, 1)

        self._widgets[key] = (bar_container, bg, val_lbl)
        self._row += 1

    def _set_val(self, key, text):
        w = self._widgets.get(key)
        if w and isinstance(w, Gtk.Label):
            w.set_label(text)

    def _set_bar(self, key, percent):
        entry = self._widgets.get(key)
        if not entry:
            return
        bar_container, bg, val_lbl = entry

        # Remove previous fill if present (first child is bg, second may be fill)
        # We re-draw by adjusting the bg width fraction using a progress bar approach.
        # Use a Gtk.LevelBar-style: replace bg with a ProgressBar widget.
        # Actually, let's just use a Gtk.ProgressBar for simplicity.
        # We stored bg as a Box — replace the approach: store a ProgressBar.
        # Since we can't easily replace widgets, let's use the val_lbl only for text
        # and keep the bar_container. We'll attach a ProgressBar at setup time.
        # But we already set it up — just update the label.
        val_lbl.set_label(f"{percent:.0f}%")
        # Update bar color class on bg based on level
        for cls in ("bar-low", "bar-mid", "bar-high"):
            bg.remove_css_class(cls)
        if percent < 60:
            bg.add_css_class("bar-low")
        elif percent < 85:
            bg.add_css_class("bar-mid")
        else:
            bg.add_css_class("bar-high")

    def _update_data(self):
        # CPU
        cpu_pct = compute_cpu_usage()
        model = get_cpu_model()
        self._set_val("cpu_model", model)
        self._set_bar("cpu_usage", cpu_pct)

        # Memory
        used_mb, total_mb = get_memory_info()
        self._set_val("mem_used", f"{used_mb} MB")
        self._set_val("mem_total", f"{total_mb} MB")
        mem_pct = (used_mb / total_mb * 100) if total_mb > 0 else 0
        self._set_bar("mem_usage", mem_pct)

        # Disk
        disk_used, disk_total = get_disk_info()
        self._set_val("disk_used", f"{disk_used} GB")
        self._set_val("disk_total", f"{disk_total} GB")
        disk_pct = (disk_used / disk_total * 100) if disk_total > 0 else 0
        self._set_bar("disk_usage", disk_pct)

        # Network
        net = get_network_info()
        self._set_val("net_hostname", net["hostname"])
        self._set_val("net_ip", net["ip"])
        self._set_val("net_rx", bytes_to_human(net["rx"]))
        self._set_val("net_tx", bytes_to_human(net["tx"]))

        # System
        os_name, kernel, uptime = get_system_info()
        self._set_val("sys_os", os_name)
        self._set_val("sys_kernel", kernel)
        self._set_val("sys_uptime", uptime)

        now = time.strftime("%H:%M:%S")
        self._refresh_label.set_label(f"Last updated: {now}  (refresh every 2s)")

    def _on_refresh(self):
        self._update_data()
        return True  # Keep the timer running


def on_activate(app):
    win = SystemInfoWindow(app)
    win.present()


if __name__ == "__main__":
    app = Gtk.Application(application_id="com.pens.SystemInfo")
    app.connect("activate", on_activate)
    app.run(None)
