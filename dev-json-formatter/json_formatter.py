#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk
import json

class JsonFormatterWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("JSON Formatter")
        self.set_default_size(900, 600)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        for label, func in [("Format", self.on_format), ("Minify", self.on_minify),
                             ("Validate", self.on_validate), ("Clear", self.on_clear),
                             ("Copy Output", self.on_copy)]:
            btn = Gtk.Button(label=label)
            btn.connect("clicked", func)
            toolbar.append(btn)
        vbox.append(toolbar)

        self.status_label = Gtk.Label(label="Paste JSON and click Format")
        self.status_label.set_xalign(0)
        vbox.append(self.status_label)

        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_vexpand(True)

        in_frame = Gtk.Frame(label="Input")
        in_scroll = Gtk.ScrolledWindow()
        self.input_view = Gtk.TextView()
        self.input_view.set_monospace(True)
        self.input_view.set_wrap_mode(Gtk.WrapMode.NONE)
        in_scroll.set_child(self.input_view)
        in_frame.set_child(in_scroll)
        paned.set_start_child(in_frame)

        out_frame = Gtk.Frame(label="Output")
        out_scroll = Gtk.ScrolledWindow()
        self.output_view = Gtk.TextView()
        self.output_view.set_monospace(True)
        self.output_view.set_editable(False)
        self.output_view.set_wrap_mode(Gtk.WrapMode.NONE)
        out_scroll.set_child(self.output_view)
        out_frame.set_child(out_scroll)
        paned.set_end_child(out_frame)

        vbox.append(paned)

        # Setup text tags for syntax highlighting
        self.out_buf = self.output_view.get_buffer()
        tt = self.out_buf.get_tag_table()
        def add_tag(name, **props):
            tag = Gtk.TextTag.new(name)
            for k, v in props.items():
                tag.set_property(k, v)
            tt.add(tag)
        add_tag("key", foreground="#61afef")
        add_tag("string", foreground="#98c379")
        add_tag("number", foreground="#d19a66")
        add_tag("bool", foreground="#c678dd")
        add_tag("null", foreground="#c678dd")
        add_tag("error", foreground="#e06c75")

    def get_input(self):
        buf = self.input_view.get_buffer()
        return buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)

    def set_output(self, text, tag=None):
        self.out_buf.set_text("")
        if tag:
            end = self.out_buf.get_end_iter()
            self.out_buf.insert_with_tags_by_name(end, text, tag)
        else:
            self.highlight_json(text)

    def highlight_json(self, text):
        import re
        self.out_buf.set_text(text)
        patterns = [
            (r'"[^"\\]*(?:\\.[^"\\]*)*"\s*:', "key"),
            (r':\s*"[^"\\]*(?:\\.[^"\\]*)*"', "string"),
            (r':\s*-?\d+\.?\d*', "number"),
            (r':\s*(true|false)', "bool"),
            (r':\s*null', "null"),
        ]
        for pattern, tag_name in patterns:
            start = self.out_buf.get_start_iter()
            for m in re.finditer(pattern, text):
                s_iter = self.out_buf.get_iter_at_offset(m.start())
                e_iter = self.out_buf.get_iter_at_offset(m.end())
                self.out_buf.apply_tag_by_name(tag_name, s_iter, e_iter)

    def on_format(self, btn):
        text = self.get_input()
        try:
            parsed = json.loads(text)
            formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
            self.set_output(formatted)
            self.status_label.set_text(f"Valid JSON — {len(formatted)} chars")
        except json.JSONDecodeError as e:
            self.set_output(f"JSON Error: {e}", "error")
            self.status_label.set_text(f"Error: {e}")

    def on_minify(self, btn):
        text = self.get_input()
        try:
            parsed = json.loads(text)
            minified = json.dumps(parsed, separators=(",", ":"), ensure_ascii=False)
            self.out_buf.set_text(minified)
            self.status_label.set_text(f"Minified — {len(minified)} chars")
        except json.JSONDecodeError as e:
            self.set_output(f"JSON Error: {e}", "error")

    def on_validate(self, btn):
        text = self.get_input()
        try:
            parsed = json.loads(text)
            keys = sum(1 for _ in self.count_keys(parsed))
            self.status_label.set_text(f"Valid JSON — {keys} keys, type: {type(parsed).__name__}")
        except json.JSONDecodeError as e:
            self.status_label.set_text(f"Invalid: {e}")

    def count_keys(self, obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                yield k
                yield from self.count_keys(v)
        elif isinstance(obj, list):
            for item in obj:
                yield from self.count_keys(item)

    def on_clear(self, btn):
        self.input_view.get_buffer().set_text("")
        self.out_buf.set_text("")
        self.status_label.set_text("Cleared")

    def on_copy(self, btn):
        buf = self.out_buf
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.set(text)
        self.status_label.set_text("Copied to clipboard")

class JsonFormatterApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.JsonFormatter")
    def do_activate(self):
        win = JsonFormatterWindow(self)
        win.present()

def main():
    app = JsonFormatterApp()
    app.run(None)

if __name__ == "__main__":
    main()
