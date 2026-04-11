#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk
import re

class RegexTesterWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Regex Tester")
        self.set_default_size(800, 600)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        pattern_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        pattern_box.append(Gtk.Label(label="Pattern:"))
        self.pattern_entry = Gtk.Entry()
        self.pattern_entry.set_hexpand(True)
        self.pattern_entry.set_placeholder_text("Enter regex pattern...")
        self.pattern_entry.connect("changed", self.on_update)
        pattern_box.append(self.pattern_entry)
        vbox.append(pattern_box)

        flag_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        flag_box.append(Gtk.Label(label="Flags:"))
        self.flag_i = Gtk.CheckButton(label="Ignore case (i)")
        self.flag_m = Gtk.CheckButton(label="Multiline (m)")
        self.flag_s = Gtk.CheckButton(label="Dot-all (s)")
        for f in [self.flag_i, self.flag_m, self.flag_s]:
            f.connect("toggled", self.on_update)
            flag_box.append(f)
        vbox.append(flag_box)

        self.status_label = Gtk.Label(label="Enter a pattern")
        self.status_label.set_xalign(0)
        vbox.append(self.status_label)

        paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        paned.set_vexpand(True)

        test_frame = Gtk.Frame(label="Test String")
        test_scroll = Gtk.ScrolledWindow()
        test_scroll.set_min_content_height(200)
        self.test_view = Gtk.TextView()
        self.test_view.set_monospace(True)
        self.test_buf = self.test_view.get_buffer()
        self.test_buf.connect("changed", self.on_update)
        tt = self.test_buf.get_tag_table()
        self.match_tag = Gtk.TextTag.new("match")
        self.match_tag.set_property("background", "#3d5a3e")
        self.match_tag.set_property("foreground", "#a8d5a2")
        tt.add(self.match_tag)
        test_scroll.set_child(self.test_view)
        test_frame.set_child(test_scroll)
        paned.set_start_child(test_frame)

        bottom = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        matches_frame = Gtk.Frame(label="Matches")
        matches_scroll = Gtk.ScrolledWindow()
        matches_scroll.set_min_content_height(150)
        self.matches_view = Gtk.TextView()
        self.matches_view.set_editable(False)
        self.matches_view.set_monospace(True)
        matches_scroll.set_child(self.matches_view)
        matches_frame.set_child(matches_scroll)
        bottom.append(matches_frame)
        paned.set_end_child(bottom)

        vbox.append(paned)

    def on_update(self, *args):
        pattern = self.pattern_entry.get_text()
        text = self.test_buf.get_text(
            self.test_buf.get_start_iter(), self.test_buf.get_end_iter(), True
        )
        self.test_buf.remove_tag(self.match_tag,
            self.test_buf.get_start_iter(), self.test_buf.get_end_iter())

        if not pattern:
            self.status_label.set_text("Enter a pattern")
            return

        flags = 0
        if self.flag_i.get_active(): flags |= re.IGNORECASE
        if self.flag_m.get_active(): flags |= re.MULTILINE
        if self.flag_s.get_active(): flags |= re.DOTALL

        try:
            compiled = re.compile(pattern, flags)
            matches = list(compiled.finditer(text))
            self.status_label.set_markup(f'<span foreground="#2ecc71">Valid — {len(matches)} match(es)</span>')
            lines = []
            for i, m in enumerate(matches, 1):
                s = self.test_buf.get_iter_at_offset(m.start())
                e = self.test_buf.get_iter_at_offset(m.end())
                self.test_buf.apply_tag(self.match_tag, s, e)
                line = f"Match {i}: [{m.start()}:{m.end()}] = {repr(m.group())}"
                if m.groups():
                    line += f"\n  Groups: {m.groups()}"
                if m.groupdict():
                    line += f"\n  Named: {m.groupdict()}"
                lines.append(line)
            self.matches_view.get_buffer().set_text("\n".join(lines) if lines else "No matches")
        except re.error as e:
            self.status_label.set_markup(f'<span foreground="#e74c3c">Error: {e}</span>')
            self.matches_view.get_buffer().set_text("")

class RegexTesterApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.RegexTester")
    def do_activate(self):
        win = RegexTesterWindow(self)
        win.present()

def main():
    app = RegexTesterApp()
    app.run(None)

if __name__ == "__main__":
    main()
