#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import re, hashlib, base64, urllib.parse, html

class TextToolsWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Text Tools")
        self.set_default_size(800, 560)
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Text Tools", css_classes=["title"]))

        hpaned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.append(hpaned)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        left.set_margin_right = 4
        left.append(Gtk.Label(label="Input:", xalign=0))
        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True); scroll.set_size_request(380, -1)
        self.input_view = Gtk.TextView()
        self.input_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.input_buf = self.input_view.get_buffer()
        self.input_buf.set_text("Hello, World! This is a sample text.\n\nEdit me and apply transformations.")
        scroll.set_child(self.input_view)
        left.append(scroll)
        stats_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.stats_label = Gtk.Label(label="", xalign=0)
        stats_box.append(self.stats_label)
        left.append(stats_box)
        self.input_buf.connect("changed", self.update_stats)
        hpaned.set_start_child(left)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        right.set_margin_start(4)
        right.append(Gtk.Label(label="Output:", xalign=0))
        scroll2 = Gtk.ScrolledWindow(); scroll2.set_vexpand(True)
        self.output_view = Gtk.TextView()
        self.output_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.output_view.set_editable(False)
        self.output_buf = self.output_view.get_buffer()
        scroll2.set_child(self.output_view)
        right.append(scroll2)
        copy_btn = Gtk.Button(label="📋 Copy Output")
        copy_btn.connect("clicked", self.on_copy)
        right.append(copy_btn)
        hpaned.set_end_child(right)

        tools_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        tools_box.set_halign(Gtk.Align.CENTER)
        tools_box.set_margin_top(4)
        tools = [
            ("UPPER", lambda t: t.upper()),
            ("lower", lambda t: t.lower()),
            ("Title", lambda t: t.title()),
            ("Capitalize", lambda t: t.capitalize()),
            ("Reverse", lambda t: t[::-1]),
            ("Strip", lambda t: t.strip()),
            ("No spaces", lambda t: t.replace(" ", "")),
            ("Trim lines", lambda t: "\n".join(l.strip() for l in t.split("\n"))),
            ("Remove blank", lambda t: "\n".join(l for l in t.split("\n") if l.strip())),
            ("Sort lines", lambda t: "\n".join(sorted(t.split("\n")))),
            ("Unique lines", lambda t: "\n".join(dict.fromkeys(t.split("\n")))),
            ("HTML escape", lambda t: html.escape(t)),
            ("HTML unescape", lambda t: html.unescape(t)),
            ("URL encode", lambda t: urllib.parse.quote(t)),
            ("URL decode", lambda t: urllib.parse.unquote(t)),
            ("Base64 enc", lambda t: base64.b64encode(t.encode()).decode()),
            ("Base64 dec", lambda t: base64.b64decode(t.encode()).decode()),
            ("MD5", lambda t: hashlib.md5(t.encode()).hexdigest()),
            ("SHA256", lambda t: hashlib.sha256(t.encode()).hexdigest()),
            ("Count words", lambda t: str(len(t.split()))),
            ("Remove punct", lambda t: re.sub(r'[^\w\s]', '', t)),
            ("CamelCase", lambda t: ''.join(w.capitalize() for w in t.split())),
            ("snake_case", lambda t: re.sub(r'\s+', '_', t.strip().lower())),
            ("kebab-case", lambda t: re.sub(r'\s+', '-', t.strip().lower())),
            ("ROT13", lambda t: t.translate(str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz', 'NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm'))),
        ]

        MAX_PER_ROW = 8
        rows = [tools[i:i+MAX_PER_ROW] for i in range(0, len(tools), MAX_PER_ROW)]
        tools_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        for row in rows:
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            row_box.set_halign(Gtk.Align.CENTER)
            for label, fn in row:
                btn = Gtk.Button(label=label)
                btn.connect("clicked", self.make_apply(fn))
                row_box.append(btn)
            tools_vbox.append(row_box)
        vbox.append(tools_vbox)

        # Find & Replace
        fr_frame = Gtk.Frame(label="Find & Replace")
        fr_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        fr_box.set_margin_top(4); fr_box.set_margin_start(4); fr_box.set_margin_end(4); fr_box.set_margin_bottom(4)
        fr_box.append(Gtk.Label(label="Find:"))
        self.find_entry = Gtk.Entry(); self.find_entry.set_hexpand(True)
        fr_box.append(self.find_entry)
        fr_box.append(Gtk.Label(label="Replace:"))
        self.replace_entry = Gtk.Entry(); self.replace_entry.set_hexpand(True)
        fr_box.append(self.replace_entry)
        self.regex_check = Gtk.CheckButton(label="Regex")
        fr_box.append(self.regex_check)
        fr_btn = Gtk.Button(label="Replace All")
        fr_btn.connect("clicked", self.on_find_replace)
        fr_box.append(fr_btn)
        fr_frame.set_child(fr_box)
        vbox.append(fr_frame)

        self.update_stats(None)

    def get_input(self):
        return self.input_buf.get_text(self.input_buf.get_start_iter(), self.input_buf.get_end_iter(), True)

    def set_output(self, text):
        self.output_buf.set_text(text)

    def make_apply(self, fn):
        def on_click(btn):
            text = self.get_input()
            try:
                result = fn(text)
                self.set_output(result)
            except Exception as e:
                self.set_output(f"Error: {e}")
        return on_click

    def on_find_replace(self, btn):
        text = self.get_input()
        find = self.find_entry.get_text()
        replace = self.replace_entry.get_text()
        if not find:
            return
        try:
            if self.regex_check.get_active():
                result = re.sub(find, replace, text)
            else:
                result = text.replace(find, replace)
            self.set_output(result)
        except Exception as e:
            self.set_output(f"Error: {e}")

    def update_stats(self, buf):
        text = self.get_input()
        words = len(text.split())
        chars = len(text)
        lines = text.count('\n') + 1
        self.stats_label.set_text(f"Words: {words}  Chars: {chars}  Lines: {lines}")

    def on_copy(self, btn):
        text = self.output_buf.get_text(self.output_buf.get_start_iter(), self.output_buf.get_end_iter(), True)
        self.get_clipboard().set(text)

class TextToolsApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.TextTools")
    def do_activate(self):
        win = TextToolsWindow(self); win.present()

def main():
    app = TextToolsApp(); app.run(None)

if __name__ == "__main__":
    main()
