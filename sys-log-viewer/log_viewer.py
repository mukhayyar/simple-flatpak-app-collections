#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import os, subprocess, threading, re

LOG_FILES = [
    ("/var/log/syslog", "Syslog"),
    ("/var/log/messages", "Messages"),
    ("/var/log/auth.log", "Auth"),
    ("/var/log/kern.log", "Kernel"),
    ("/var/log/dmesg", "Dmesg"),
    ("/var/log/apt/history.log", "APT History"),
    ("/var/log/dpkg.log", "DPKG"),
]

class LogViewerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Log Viewer")
        self.set_default_size(1000, 660)
        self.current_file = None
        self.all_lines = []
        self.build_ui()
        self.load_journalctl()

    def build_ui(self):
        hpaned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_child(hpaned)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        left.set_size_request(220, -1)
        left.set_margin_top(8); left.set_margin_start(8); left.set_margin_bottom(8)

        left.append(Gtk.Label(label="Log Sources:", xalign=0))
        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        self.source_list = Gtk.ListBox()
        self.source_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.source_list.connect("row-selected", self.on_source_selected)

        journal_row = Gtk.ListBoxRow()
        journal_row._source = "journalctl"
        journal_lbl = Gtk.Label(label="Journal (systemd)", xalign=0)
        journal_lbl.set_margin_start(6); journal_lbl.set_margin_top(4); journal_lbl.set_margin_bottom(4)
        journal_row.set_child(journal_lbl)
        self.source_list.append(journal_row)

        for path, label in LOG_FILES:
            if os.path.exists(path):
                row = Gtk.ListBoxRow()
                row._source = path
                lbl = Gtk.Label(label=label, xalign=0)
                lbl.set_margin_start(6); lbl.set_margin_top(4); lbl.set_margin_bottom(4)
                row.set_child(lbl)
                self.source_list.append(row)

        scroll.set_child(self.source_list)
        left.append(scroll)

        custom_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        custom_box.append(Gtk.Label(label="Custom file:", xalign=0))
        self.custom_entry = Gtk.Entry()
        self.custom_entry.set_placeholder_text("/path/to/log")
        self.custom_entry.connect("activate", self.on_custom_file)
        custom_box.append(self.custom_entry)
        left.append(custom_box)

        lines_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        lines_box.append(Gtk.Label(label="Lines:"))
        self.lines_spin = Gtk.SpinButton.new_with_range(50, 10000, 50)
        self.lines_spin.set_value(500)
        lines_box.append(self.lines_spin)
        left.append(lines_box)

        hpaned.set_start_child(left)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        right.set_margin_top(8); right.set_margin_end(8); right.set_margin_bottom(8); right.set_margin_start(4)

        filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        filter_box.append(Gtk.Label(label="Filter:"))
        self.filter_entry = Gtk.SearchEntry()
        self.filter_entry.set_hexpand(True)
        self.filter_entry.connect("search-changed", self.on_filter)
        filter_box.append(self.filter_entry)
        level_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        level_box.append(Gtk.Label(label="Level:"))
        self.level_combo = Gtk.ComboBoxText()
        for lvl in ["All", "ERROR", "WARN", "INFO"]:
            self.level_combo.append_text(lvl)
        self.level_combo.set_active(0)
        self.level_combo.connect("changed", self.on_filter)
        level_box.append(self.level_combo)
        filter_box.append(level_box)
        right.append(filter_box)

        self.status_label = Gtk.Label(label="Select a log source", xalign=0)
        right.append(self.status_label)

        scroll2 = Gtk.ScrolledWindow(); scroll2.set_vexpand(True)
        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_view.set_monospace(True)
        self.log_buf = self.log_view.get_buffer()
        tt = self.log_buf.get_tag_table()
        for name, color in [("error", "#e06c75"), ("warn", "#e5c07b"), ("info", "#98c379"), ("debug", "#61afef")]:
            tag = Gtk.TextTag.new(name)
            tag.set_property("foreground", color)
            tt.add(tag)
        scroll2.set_child(self.log_view)
        right.append(scroll2)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        refresh_btn = Gtk.Button(label="⟳ Refresh")
        refresh_btn.connect("clicked", lambda b: self.reload_current())
        follow_btn = Gtk.Button(label="⬇ Scroll to Bottom")
        follow_btn.connect("clicked", lambda b: self.scroll_to_bottom())
        btn_box.append(refresh_btn); btn_box.append(follow_btn)
        right.append(btn_box)

        hpaned.set_end_child(right)

    def load_journalctl(self):
        threading.Thread(target=self._load_journal, daemon=True).start()

    def _load_journal(self):
        try:
            n = int(self.lines_spin.get_value())
            result = subprocess.run(["journalctl", "-n", str(n), "--no-pager", "--output=short"],
                                    capture_output=True, text=True, timeout=10)
            lines = result.stdout.split('\n')
            GLib.idle_add(self.show_lines, lines, "journalctl")
        except Exception as e:
            GLib.idle_add(self.show_lines, [f"journalctl error: {e}"], "journalctl")

    def on_source_selected(self, listbox, row):
        if row:
            source = row._source
            self.current_file = source
            if source == "journalctl":
                self.load_journalctl()
            else:
                self.load_file(source)

    def on_custom_file(self, entry):
        path = entry.get_text().strip()
        if os.path.exists(path):
            self.current_file = path
            self.load_file(path)

    def load_file(self, path):
        threading.Thread(target=self._load_file, args=(path,), daemon=True).start()

    def _load_file(self, path):
        try:
            n = int(self.lines_spin.get_value())
            result = subprocess.run(["tail", "-n", str(n), path],
                                    capture_output=True, text=True, timeout=10)
            lines = result.stdout.split('\n')
            GLib.idle_add(self.show_lines, lines, path)
        except Exception as e:
            GLib.idle_add(self.show_lines, [f"Error: {e}"], path)

    def show_lines(self, lines, source):
        self.all_lines = lines
        q = self.filter_entry.get_text().lower()
        level = self.level_combo.get_active_text()
        self.render_lines(lines, q, level)
        self.status_label.set_text(f"{source}  |  {len(lines)} lines")
        return False

    def render_lines(self, lines, q, level):
        self.log_buf.set_text("")
        for line in lines:
            if q and q not in line.lower():
                continue
            if level != "All":
                if level.lower() not in line.lower():
                    continue
            end = self.log_buf.get_end_iter()
            line_lower = line.lower()
            if "error" in line_lower or "critical" in line_lower or "fatal" in line_lower:
                self.log_buf.insert_with_tags_by_name(end, line + "\n", "error")
            elif "warn" in line_lower:
                self.log_buf.insert_with_tags_by_name(end, line + "\n", "warn")
            elif "info" in line_lower:
                self.log_buf.insert_with_tags_by_name(end, line + "\n", "info")
            elif "debug" in line_lower:
                self.log_buf.insert_with_tags_by_name(end, line + "\n", "debug")
            else:
                self.log_buf.insert(end, line + "\n")

    def on_filter(self, widget):
        q = self.filter_entry.get_text().lower()
        level = self.level_combo.get_active_text()
        self.render_lines(self.all_lines, q, level)

    def reload_current(self):
        if self.current_file == "journalctl":
            self.load_journalctl()
        elif self.current_file:
            self.load_file(self.current_file)

    def scroll_to_bottom(self):
        end = self.log_buf.get_end_iter()
        self.log_view.scroll_to_iter(end, 0, False, 0, 1)

class LogViewerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.LogViewer")
    def do_activate(self):
        win = LogViewerWindow(self); win.present()

def main():
    app = LogViewerApp(); app.run(None)

if __name__ == "__main__":
    main()
