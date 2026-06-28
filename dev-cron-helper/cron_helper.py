#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk
import random, math, re, string, secrets, datetime, cmath, os

TITLE = "Cron Expression Helper"
APP_ID = "com.pens.CronHelper"
FIELDS = [("Cron expression (min hr dom mon dow)", "*/15 9-17 * * 1-5")]
_NAMES = ["minute", "hour", "day-of-month", "month", "day-of-week"]
_DOW = {"0": "Sun", "1": "Mon", "2": "Tue", "3": "Wed", "4": "Thu", "5": "Fri", "6": "Sat", "7": "Sun"}
_MON = {str(i): m for i, m in enumerate(["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}

def _describe(field, name):
    if field == "*":
        return "every " + name
    if field.startswith("*/"):
        return "every " + field[2:] + " " + name + "s"
    if "-" in field:
        a, b = field.split("-", 1)
        return name + "s " + a + " through " + b
    if "," in field:
        return name + "s " + ", ".join(field.split(","))
    return name + " " + field

def compute(vals):
    parts = vals[0].split()
    if len(parts) != 5:
        return "A cron expression needs exactly 5 fields:\n  minute hour day-of-month month day-of-week"
    out = ["Expression: " + vals[0], ""]
    for f, n in zip(parts, _NAMES):
        out.append("  " + n.ljust(13) + " = " + _describe(f, n))
    out.append("")
    out.append("Reads as: run at " + _describe(parts[0], "minute") + ", " + _describe(parts[1], "hour") +
               ", on " + _describe(parts[2], "day-of-month") + ", in " + _describe(parts[3], "month") +
               ", on " + _describe(parts[4], "day-of-week") + ".")
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
