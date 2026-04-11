#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import os, subprocess

def run_gsettings(args, timeout=3):
    try:
        return subprocess.check_output(["gsettings"] + args, text=True, timeout=timeout, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""

def set_gsettings(schema, key, value):
    try:
        subprocess.run(["gsettings", "set", schema, key, value], timeout=3, capture_output=True)
        return True
    except Exception:
        return False

class ProxySettingsWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Proxy Settings")
        self.set_default_size(680, 580)
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(12); vbox.set_margin_bottom(12)
        vbox.set_margin_start(16); vbox.set_margin_end(16)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Proxy Settings", css_classes=["title"]))

        # Mode
        mode_frame = Gtk.Frame(label="Proxy Mode")
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        mode_box.set_margin_top(8); mode_box.set_margin_start(12)
        mode_box.set_margin_end(12); mode_box.set_margin_bottom(8)

        self.mode_combo = Gtk.ComboBoxText()
        for mode in ["none", "manual", "auto"]:
            self.mode_combo.append_text(mode)
        cur_mode = run_gsettings(["get", "org.gnome.system.proxy", "mode"]).strip("'") or "none"
        modes = ["none", "manual", "auto"]
        self.mode_combo.set_active(modes.index(cur_mode) if cur_mode in modes else 0)
        self.mode_combo.connect("changed", self.on_mode_changed)
        mode_box.append(Gtk.Label(label="Mode:"))
        mode_box.append(self.mode_combo)
        mode_frame.set_child(mode_box)
        vbox.append(mode_frame)

        # Auto proxy URL
        auto_frame = Gtk.Frame(label="Auto-Config URL (PAC)")
        auto_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        auto_box.set_margin_top(8); auto_box.set_margin_start(12)
        auto_box.set_margin_end(12); auto_box.set_margin_bottom(8)
        auto_box.append(Gtk.Label(label="PAC URL:"))
        self.auto_url = Gtk.Entry()
        self.auto_url.set_hexpand(True)
        pac = run_gsettings(["get", "org.gnome.system.proxy", "autoconfig-url"]).strip("'")
        self.auto_url.set_text(pac)
        auto_box.append(self.auto_url)
        auto_frame.set_child(auto_box)
        vbox.append(auto_frame)

        # Manual proxy settings
        manual_frame = Gtk.Frame(label="Manual Proxy")
        manual_grid = Gtk.Grid()
        manual_grid.set_row_spacing(8); manual_grid.set_column_spacing(10)
        manual_grid.set_margin_top(8); manual_grid.set_margin_start(12)
        manual_grid.set_margin_end(12); manual_grid.set_margin_bottom(8)

        self.proxy_fields = {}
        proxy_types = [
            ("HTTP", "org.gnome.system.proxy.http", "host", "port"),
            ("HTTPS", "org.gnome.system.proxy.https", "host", "port"),
            ("FTP", "org.gnome.system.proxy.ftp", "host", "port"),
            ("SOCKS", "org.gnome.system.proxy.socks", "host", "port"),
        ]
        for row, (label, schema, host_key, port_key) in enumerate(proxy_types):
            manual_grid.attach(Gtk.Label(label=f"{label}:", xalign=1), 0, row, 1, 1)
            host_entry = Gtk.Entry()
            host_entry.set_placeholder_text("hostname or IP")
            host_entry.set_hexpand(True)
            cur_host = run_gsettings(["get", schema, host_key]).strip("'")
            host_entry.set_text(cur_host)
            manual_grid.attach(host_entry, 1, row, 1, 1)
            manual_grid.attach(Gtk.Label(label="Port:"), 2, row, 1, 1)
            port_entry = Gtk.Entry()
            port_entry.set_max_width_chars(6)
            cur_port = run_gsettings(["get", schema, port_key]).strip("'")
            port_entry.set_text(cur_port)
            manual_grid.attach(port_entry, 3, row, 1, 1)
            self.proxy_fields[schema] = (host_entry, port_entry)

        manual_frame.set_child(manual_grid)
        vbox.append(manual_frame)

        # Ignore hosts
        ignore_frame = Gtk.Frame(label="Ignore Hosts (no-proxy list)")
        ignore_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        ignore_box.set_margin_top(8); ignore_box.set_margin_start(12)
        ignore_box.set_margin_end(12); ignore_box.set_margin_bottom(8)
        ignore_box.append(Gtk.Label(label="Comma-separated hosts to bypass proxy:", xalign=0))
        self.ignore_entry = Gtk.Entry()
        self.ignore_entry.set_hexpand(True)
        ignore_val = run_gsettings(["get", "org.gnome.system.proxy", "ignore-hosts"])
        self.ignore_entry.set_text(ignore_val)
        ignore_box.append(self.ignore_entry)
        ignore_frame.set_child(ignore_box)
        vbox.append(ignore_frame)

        # Environment proxy
        env_frame = Gtk.Frame(label="Environment Variables (read-only)")
        env_scroll = Gtk.ScrolledWindow()
        env_scroll.set_min_content_height(100)
        env_view = Gtk.TextView()
        env_view.set_editable(False)
        env_view.set_monospace(True)
        env_lines = []
        for key in ["http_proxy", "https_proxy", "ftp_proxy", "no_proxy",
                    "HTTP_PROXY", "HTTPS_PROXY", "FTP_PROXY", "NO_PROXY"]:
            val = os.environ.get(key, "")
            if val:
                env_lines.append(f"{key}={val}")
        env_view.get_buffer().set_text("\n".join(env_lines) if env_lines else "(No proxy env vars set)")
        env_scroll.set_child(env_view)
        env_frame.set_child(env_scroll)
        vbox.append(env_frame)

        # Buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_box.set_halign(Gtk.Align.CENTER)
        apply_btn = Gtk.Button(label="Apply via GSettings")
        apply_btn.connect("clicked", self.on_apply)
        apply_btn.add_css_class("suggested-action")
        btn_box.append(apply_btn)
        reset_btn = Gtk.Button(label="Reset to None")
        reset_btn.connect("clicked", self.on_reset)
        btn_box.append(reset_btn)
        vbox.append(btn_box)

        self.status_label = Gtk.Label(label="", xalign=0)
        vbox.append(self.status_label)

    def on_mode_changed(self, combo):
        pass

    def on_apply(self, btn):
        mode = self.mode_combo.get_active_text()
        set_gsettings("org.gnome.system.proxy", "mode", f"'{mode}'")

        pac_url = self.auto_url.get_text()
        set_gsettings("org.gnome.system.proxy", "autoconfig-url", f"'{pac_url}'")

        proxy_types = [
            ("org.gnome.system.proxy.http", "HTTP"),
            ("org.gnome.system.proxy.https", "HTTPS"),
            ("org.gnome.system.proxy.ftp", "FTP"),
            ("org.gnome.system.proxy.socks", "SOCKS"),
        ]
        for schema, _ in proxy_types:
            if schema in self.proxy_fields:
                host_entry, port_entry = self.proxy_fields[schema]
                host = host_entry.get_text()
                port = port_entry.get_text() or "0"
                set_gsettings(schema, "host", f"'{host}'")
                try:
                    set_gsettings(schema, "port", str(int(port)))
                except ValueError:
                    pass

        ignore = self.ignore_entry.get_text()
        set_gsettings("org.gnome.system.proxy", "ignore-hosts", ignore)

        self.status_label.set_text(f"Applied proxy settings: mode={mode}")

    def on_reset(self, btn):
        self.mode_combo.set_active(0)
        set_gsettings("org.gnome.system.proxy", "mode", "'none'")
        self.status_label.set_text("Proxy reset to 'none'")

class ProxySettingsApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.ProxySettings")
    def do_activate(self):
        win = ProxySettingsWindow(self); win.present()

def main():
    app = ProxySettingsApp(); app.run(None)

if __name__ == "__main__":
    main()
