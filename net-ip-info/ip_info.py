#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import socket, subprocess, threading, urllib.request, json

class IpInfoWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("IP Info")
        self.set_default_size(600, 560)
        self.build_ui()
        GLib.idle_add(self.refresh)

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(12); vbox.set_margin_bottom(12)
        vbox.set_margin_start(12); vbox.set_margin_end(12)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="IP Information", css_classes=["title"]))

        refresh_btn = Gtk.Button(label="Refresh")
        refresh_btn.connect("clicked", lambda b: self.refresh())
        vbox.append(refresh_btn)

        self.info_view = Gtk.TextView()
        self.info_view.set_editable(False)
        self.info_view.set_monospace(True)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_child(self.info_view)
        vbox.append(scroll)

    def refresh(self):
        self.info_view.get_buffer().set_text("Loading...")
        threading.Thread(target=self.gather_info, daemon=True).start()
        return False

    def gather_info(self):
        lines = []
        hostname = socket.gethostname()
        lines.append(f"Hostname: {hostname}")

        try:
            local_ip = socket.gethostbyname(hostname)
            lines.append(f"Local IP: {local_ip}")
        except Exception as e:
            lines.append(f"Local IP: Error - {e}")

        try:
            result = subprocess.run(["ip", "addr"], capture_output=True, text=True, timeout=5)
            lines.append("\n--- Network Interfaces ---")
            current_iface = None
            for line in result.stdout.splitlines():
                line = line.strip()
                if line and line[0].isdigit():
                    parts = line.split(":")
                    if len(parts) >= 2:
                        current_iface = parts[1].strip().split("@")[0]
                        lines.append(f"\nInterface: {current_iface}")
                elif "inet " in line and current_iface:
                    parts = line.split()
                    if len(parts) >= 2:
                        lines.append(f"  IPv4: {parts[1]}")
                elif "inet6" in line and current_iface:
                    parts = line.split()
                    if len(parts) >= 2:
                        lines.append(f"  IPv6: {parts[1]}")
                elif "link/ether" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        lines.append(f"  MAC:  {parts[1]}")
        except Exception as e:
            lines.append(f"\nNetwork interfaces error: {e}")

        try:
            result = subprocess.run(["ip", "route", "show", "default"], capture_output=True, text=True, timeout=5)
            lines.append("\n--- Gateway ---")
            for line in result.stdout.splitlines():
                if "default via" in line:
                    gw = line.split("via")[1].split()[0]
                    lines.append(f"Default Gateway: {gw}")
        except Exception:
            pass

        try:
            lines.append("\n--- Public IP ---")
            with urllib.request.urlopen("https://api.ipify.org?format=json", timeout=5) as resp:
                data = json.loads(resp.read())
                lines.append(f"Public IP: {data.get('ip', 'unknown')}")
        except Exception as e:
            lines.append(f"Public IP: Could not fetch ({e})")

        try:
            with open("/etc/resolv.conf") as f:
                lines.append("\n--- DNS Servers ---")
                for line in f:
                    if line.startswith("nameserver"):
                        lines.append(f"  {line.strip()}")
        except Exception:
            pass

        GLib.idle_add(self.show_info, "\n".join(lines))

    def show_info(self, text):
        self.info_view.get_buffer().set_text(text)
        return False

class IpInfoApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.IpInfo")
    def do_activate(self):
        win = IpInfoWindow(self)
        win.present()

def main():
    app = IpInfoApp()
    app.run(None)

if __name__ == "__main__":
    main()
