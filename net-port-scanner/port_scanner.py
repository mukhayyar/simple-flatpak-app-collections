#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import socket, threading

COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS", 445: "SMB",
    3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 6379: "Redis",
    8080: "HTTP-Alt", 8443: "HTTPS-Alt", 27017: "MongoDB", 9200: "Elasticsearch"
}

class PortScannerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Port Scanner")
        self.set_default_size(700, 600)
        self.scanning = False
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Port Scanner", css_classes=["title"]))

        host_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        host_box.append(Gtk.Label(label="Host:"))
        self.host_entry = Gtk.Entry()
        self.host_entry.set_text("localhost")
        self.host_entry.set_hexpand(True)
        host_box.append(self.host_entry)
        vbox.append(host_box)

        range_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.mode_combo = Gtk.ComboBoxText()
        for m in ["Common Ports", "Port Range", "Single Port"]:
            self.mode_combo.append_text(m)
        self.mode_combo.set_active(0)
        range_box.append(self.mode_combo)
        range_box.append(Gtk.Label(label="From:"))
        self.from_spin = Gtk.SpinButton.new_with_range(1, 65535, 1)
        self.from_spin.set_value(1)
        range_box.append(self.from_spin)
        range_box.append(Gtk.Label(label="To:"))
        self.to_spin = Gtk.SpinButton.new_with_range(1, 65535, 1)
        self.to_spin.set_value(1024)
        range_box.append(self.to_spin)
        vbox.append(range_box)

        ctrl = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.scan_btn = Gtk.Button(label="Start Scan")
        self.scan_btn.connect("clicked", self.on_scan)
        ctrl.append(self.scan_btn)
        self.stop_btn = Gtk.Button(label="Stop")
        self.stop_btn.connect("clicked", self.on_stop)
        self.stop_btn.set_sensitive(False)
        ctrl.append(self.stop_btn)
        vbox.append(ctrl)

        self.progress = Gtk.ProgressBar()
        vbox.append(self.progress)

        self.status_label = Gtk.Label(label="Enter a host and click Scan")
        self.status_label.set_xalign(0)
        vbox.append(self.status_label)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        self.results_view = Gtk.TextView()
        self.results_view.set_monospace(True)
        self.results_view.set_editable(False)
        scroll.set_child(self.results_view)
        vbox.append(scroll)

    def on_scan(self, btn):
        if self.scanning: return
        host = self.host_entry.get_text().strip()
        mode = self.mode_combo.get_active()
        if mode == 0:
            ports = sorted(COMMON_PORTS.keys())
        elif mode == 1:
            ports = list(range(int(self.from_spin.get_value()), int(self.to_spin.get_value()) + 1))
        else:
            ports = [int(self.from_spin.get_value())]

        self.scanning = True
        self.stop_requested = False
        self.scan_btn.set_sensitive(False)
        self.stop_btn.set_sensitive(True)
        self.results_view.get_buffer().set_text("")
        self.progress.set_fraction(0)
        self.status_label.set_text(f"Scanning {host} — {len(ports)} ports...")
        threading.Thread(target=self.scan_ports, args=(host, ports), daemon=True).start()

    def on_stop(self, btn):
        self.stop_requested = True

    def scan_ports(self, host, ports):
        open_ports = []
        total = len(ports)
        for i, port in enumerate(ports):
            if self.stop_requested:
                break
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                result = sock.connect_ex((host, port))
                sock.close()
                if result == 0:
                    service = COMMON_PORTS.get(port, "unknown")
                    open_ports.append((port, service))
                    GLib.idle_add(self.add_result, port, service)
            except Exception:
                pass
            GLib.idle_add(self.update_progress, (i + 1) / total, i + 1, total)
        GLib.idle_add(self.scan_done, open_ports, host)

    def add_result(self, port, service):
        buf = self.results_view.get_buffer()
        end = buf.get_end_iter()
        buf.insert(end, f"OPEN  {port:5d}/tcp  {service}\n")
        return False

    def update_progress(self, frac, done, total):
        self.progress.set_fraction(frac)
        self.status_label.set_text(f"Scanning: {done}/{total}")
        return False

    def scan_done(self, open_ports, host):
        self.scanning = False
        self.scan_btn.set_sensitive(True)
        self.stop_btn.set_sensitive(False)
        self.progress.set_fraction(1.0)
        status = "stopped" if self.stop_requested else "complete"
        self.status_label.set_text(f"Scan {status} — {len(open_ports)} open port(s) on {host}")
        return False

class PortScannerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.PortScanner")
    def do_activate(self):
        win = PortScannerWindow(self)
        win.present()

def main():
    app = PortScannerApp()
    app.run(None)

if __name__ == "__main__":
    main()
