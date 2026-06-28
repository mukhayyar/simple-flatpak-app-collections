#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk
import random, math, re, string, secrets, datetime, cmath, os

TITLE = "Uptime & Load Viewer"
APP_ID = "com.pens.UptimeViewer"
FIELDS = []

def _read(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except Exception:
        return ""

def compute(vals):
    out = []
    up = _read("/proc/uptime")
    if up:
        secs = float(up.split()[0])
        d = int(secs // 86400); h = int(secs % 86400 // 3600); m = int(secs % 3600 // 60)
        out.append("Uptime : {}d {}h {}m  ({:.0f} s)".format(d, h, m, secs))
    load = _read("/proc/loadavg")
    if load:
        p = load.split()
        out.append("Load   : 1m={} 5m={} 15m={}".format(p[0], p[1], p[2]))
        if len(p) > 3:
            out.append("Procs  : " + p[3])
    mem = _read("/proc/meminfo")
    if mem:
        d = {}
        for line in mem.splitlines():
            k, _, rest = line.partition(":")
            d[k] = rest.strip()
        if "MemTotal" in d and "MemAvailable" in d:
            tot = int(d["MemTotal"].split()[0]) / 1024
            avail = int(d["MemAvailable"].split()[0]) / 1024
            out.append("Memory : {:.0f} MB total, {:.0f} MB available, {:.0f} MB used".format(tot, avail, tot - avail))
    return "\n".join(out) if out else "Could not read /proc (sandbox?)."

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
