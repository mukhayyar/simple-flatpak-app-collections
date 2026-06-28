#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk
import random, math, re, string, secrets, datetime, cmath, os

TITLE = "Markdown to Text"
APP_ID = "com.pens.MarkdownPreview"
FIELDS = [("Markdown (use \\n for new lines)", "# Title\\n- one\\n- two\\n**bold** and *italic*")]

def compute(vals):
    text = vals[0].replace("\\n", "\n")
    out = []
    for line in text.split("\n"):
        s = line.rstrip()
        h = re.match(r"^(#{1,6})\s+(.*)$", s)
        if h:
            level = len(h.group(1))
            title = h.group(2)
            out.append(title.upper() if level == 1 else title)
            if level == 1:
                out.append("=" * len(title))
            continue
        s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
        s = re.sub(r"\*(.+?)\*", r"\1", s)
        s = re.sub(r"`(.+?)`", r"\1", s)
        s = re.sub(r"^\s*[-*+]\s+", "  \u2022 ", s)
        out.append(s)
    return "\n".join(out)

class AppWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title(TITLE)
        self.set_default_size(660, 560)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        for m in ("top", "bottom", "start", "end"):
            getattr(vbox, "set_margin_" + m)(10)
        self.set_child(vbox)
        head = Gtk.Label()
        head.set_markup("<big><b>" + GLib_escape(TITLE) + "</b></big>")
        head.set_xalign(0)
        vbox.append(head)
        self.entries = []
        grid = Gtk.Grid()
        grid.set_row_spacing(6)
        grid.set_column_spacing(8)
        for i, (lbl, default) in enumerate(FIELDS):
            l = Gtk.Label(label=lbl)
            l.set_xalign(0)
            e = Gtk.Entry()
            e.set_text(str(default))
            e.set_hexpand(True)
            e.connect("activate", self.on_run)
            grid.attach(l, 0, i, 1, 1)
            grid.attach(e, 1, i, 1, 1)
            self.entries.append(e)
        if FIELDS:
            vbox.append(grid)
        btn = Gtk.Button(label="Run")
        btn.connect("clicked", self.on_run)
        vbox.append(btn)
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        self.out = Gtk.TextView()
        self.out.set_monospace(True)
        self.out.set_editable(False)
        self.out.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        scroll.set_child(self.out)
        vbox.append(scroll)
        self.on_run(None)

    def on_run(self, _btn):
        vals = [e.get_text() for e in self.entries]
        try:
            text = compute(vals)
        except Exception as ex:
            text = "Error: " + str(ex)
        self.out.get_buffer().set_text(text)


def GLib_escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)

    def do_activate(self):
        AppWindow(self).present()


def main():
    App().run(None)


if __name__ == "__main__":
    main()
