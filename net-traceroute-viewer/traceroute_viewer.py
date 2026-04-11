#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import subprocess, threading

class TracerouteViewerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Traceroute Viewer")
        self.set_default_size(780, 560)
        self.process = None
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Traceroute Viewer", css_classes=["title"]))

        ctrl = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.host_entry = Gtk.Entry()
        self.host_entry.set_placeholder_text("e.g., google.com or 8.8.8.8")
        self.host_entry.set_hexpand(True)
        ctrl.append(self.host_entry)
        self.trace_btn = Gtk.Button(label="Trace")
        self.trace_btn.connect("clicked", self.on_trace)
        ctrl.append(self.trace_btn)
        self.stop_btn = Gtk.Button(label="Stop")
        self.stop_btn.connect("clicked", self.on_stop)
        self.stop_btn.set_sensitive(False)
        ctrl.append(self.stop_btn)
        vbox.append(ctrl)

        self.status_label = Gtk.Label(label="Enter a host and click Trace")
        self.status_label.set_xalign(0)
        vbox.append(self.status_label)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        self.result_view = Gtk.TextView()
        self.result_view.set_monospace(True)
        self.result_view.set_editable(False)
        self.result_buf = self.result_view.get_buffer()
        tt = self.result_buf.get_tag_table()
        for name, color in [("hop", "#61afef"), ("timeout", "#e06c75"), ("header", "#c678dd")]:
            tag = Gtk.TextTag.new(name)
            tag.set_property("foreground", color)
            tt.add(tag)
        scroll.set_child(self.result_view)
        vbox.append(scroll)

    def on_trace(self, btn):
        host = self.host_entry.get_text().strip()
        if not host: return
        self.result_buf.set_text("")
        self.trace_btn.set_sensitive(False)
        self.stop_btn.set_sensitive(True)
        self.status_label.set_text(f"Tracing route to {host}...")
        threading.Thread(target=self.run_traceroute, args=(host,), daemon=True).start()

    def on_stop(self, btn):
        if self.process:
            self.process.terminate()

    def run_traceroute(self, host):
        try:
            self.process = subprocess.Popen(
                ["traceroute", "-n", "-w", "2", "-m", "30", host],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1
            )
            GLib.idle_add(self.add_line, f"Traceroute to {host}\n", "header")
            for line in self.process.stdout:
                line = line.rstrip()
                if not line: continue
                if "* * *" in line:
                    GLib.idle_add(self.add_line, line + "\n", "timeout")
                elif line[0].isdigit() or (line and line.split()[0].isdigit()):
                    GLib.idle_add(self.add_line, line + "\n", "hop")
                else:
                    GLib.idle_add(self.add_line, line + "\n", "header")
            self.process.wait()
            rc = self.process.returncode
        except FileNotFoundError:
            GLib.idle_add(self.add_line, "traceroute not found, trying tracepath...\n", "header")
            try:
                self.process = subprocess.Popen(
                    ["tracepath", host],
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1
                )
                for line in self.process.stdout:
                    GLib.idle_add(self.add_line, line, "hop")
                self.process.wait()
            except Exception as e:
                GLib.idle_add(self.add_line, f"Error: {e}\n", "timeout")
        except Exception as e:
            GLib.idle_add(self.add_line, f"Error: {e}\n", "timeout")
        GLib.idle_add(self.trace_done)

    def add_line(self, line, tag_name):
        end = self.result_buf.get_end_iter()
        self.result_buf.insert_with_tags_by_name(end, line, tag_name)
        self.result_view.scroll_to_iter(self.result_buf.get_end_iter(), 0.0, False, 0, 1)
        return False

    def trace_done(self):
        self.trace_btn.set_sensitive(True)
        self.stop_btn.set_sensitive(False)
        self.status_label.set_text("Traceroute complete")
        return False

class TracerouteViewerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.TracerouteViewer")
    def do_activate(self):
        win = TracerouteViewerWindow(self)
        win.present()

def main():
    app = TracerouteViewerApp()
    app.run(None)

if __name__ == "__main__":
    main()
