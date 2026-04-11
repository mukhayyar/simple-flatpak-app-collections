#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import socket, subprocess, threading

QUERY_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "PTR"]

class DnsLookupWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("DNS Lookup")
        self.set_default_size(700, 560)
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="DNS Lookup Tool", css_classes=["title"]))

        query_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        query_box.append(Gtk.Label(label="Hostname:"))
        self.hostname_entry = Gtk.Entry()
        self.hostname_entry.set_placeholder_text("e.g., google.com")
        self.hostname_entry.set_hexpand(True)
        query_box.append(self.hostname_entry)
        query_box.append(Gtk.Label(label="Type:"))
        self.type_combo = Gtk.ComboBoxText()
        for t in QUERY_TYPES:
            self.type_combo.append_text(t)
        self.type_combo.set_active(0)
        query_box.append(self.type_combo)
        lookup_btn = Gtk.Button(label="Lookup")
        lookup_btn.connect("clicked", self.on_lookup)
        query_box.append(lookup_btn)
        vbox.append(query_box)

        all_btn = Gtk.Button(label="Lookup All Types")
        all_btn.connect("clicked", self.on_lookup_all)
        vbox.append(all_btn)

        self.status_label = Gtk.Label(label="Enter a hostname and click Lookup")
        self.status_label.set_xalign(0)
        vbox.append(self.status_label)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        self.results_view = Gtk.TextView()
        self.results_view.set_monospace(True)
        self.results_view.set_editable(False)
        scroll.set_child(self.results_view)
        vbox.append(scroll)

        copy_btn = Gtk.Button(label="Copy Results")
        copy_btn.connect("clicked", self.on_copy)
        vbox.append(copy_btn)

    def on_lookup(self, btn):
        hostname = self.hostname_entry.get_text().strip()
        qtype = self.type_combo.get_active_text()
        if hostname:
            self.results_view.get_buffer().set_text("")
            self.status_label.set_text(f"Looking up {qtype} for {hostname}...")
            threading.Thread(target=self.do_lookup, args=(hostname, [qtype]), daemon=True).start()

    def on_lookup_all(self, btn):
        hostname = self.hostname_entry.get_text().strip()
        if hostname:
            self.results_view.get_buffer().set_text("")
            self.status_label.set_text(f"Looking up all record types for {hostname}...")
            threading.Thread(target=self.do_lookup, args=(hostname, QUERY_TYPES), daemon=True).start()

    def do_lookup(self, hostname, types):
        results = []
        for qtype in types:
            try:
                if qtype == "A":
                    addrs = socket.getaddrinfo(hostname, None, socket.AF_INET)
                    for a in addrs:
                        results.append(f"A     {a[4][0]}")
                elif qtype == "AAAA":
                    addrs = socket.getaddrinfo(hostname, None, socket.AF_INET6)
                    for a in addrs:
                        results.append(f"AAAA  {a[4][0]}")
                elif qtype == "PTR":
                    try:
                        name = socket.gethostbyaddr(hostname)[0]
                        results.append(f"PTR   {name}")
                    except Exception:
                        pass
                else:
                    try:
                        out = subprocess.run(
                            ["dig", "+short", "-t", qtype, hostname],
                            capture_output=True, text=True, timeout=5
                        )
                        for line in out.stdout.strip().splitlines():
                            if line:
                                results.append(f"{qtype:<6}{line}")
                    except FileNotFoundError:
                        try:
                            out = subprocess.run(
                                ["nslookup", "-type=" + qtype, hostname],
                                capture_output=True, text=True, timeout=5
                            )
                            results.append(f"--- {qtype} ---")
                            results.append(out.stdout)
                        except Exception as e:
                            results.append(f"{qtype}: {e}")
            except Exception as e:
                results.append(f"{qtype} error: {e}")

        text = "\n".join(results) if results else "No results found"
        GLib.idle_add(self.show_results, hostname, text)

    def show_results(self, hostname, text):
        self.results_view.get_buffer().set_text(text)
        self.status_label.set_text(f"Results for: {hostname}")
        return False

    def on_copy(self, btn):
        buf = self.results_view.get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
        from gi.repository import Gdk
        Gdk.Display.get_default().get_clipboard().set(text)

class DnsLookupApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.DnsLookup")
    def do_activate(self):
        win = DnsLookupWindow(self)
        win.present()

def main():
    app = DnsLookupApp()
    app.run(None)

if __name__ == "__main__":
    main()
