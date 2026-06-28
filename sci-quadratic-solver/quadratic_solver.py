#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk
import random, math, re, string, secrets, datetime, cmath, os

TITLE = "Quadratic Solver"
APP_ID = "com.pens.QuadraticSolver"
FIELDS = [("a", "1"), ("b", "-3"), ("c", "2")]

def compute(vals):
    a = float(vals[0]); b = float(vals[1]); c = float(vals[2])
    if a == 0:
        if b == 0:
            return "Not an equation (a and b are both 0)."
        return "Linear: x = {:.4g}".format(-c / b)
    disc = b * b - 4 * a * c
    out = ["a={:g}  b={:g}  c={:g}".format(a, b, c), "Discriminant = {:.4g}".format(disc)]
    if disc > 0:
        r = math.sqrt(disc)
        out.append("Two real roots:")
        out.append("  x1 = {:.6g}".format((-b + r) / (2 * a)))
        out.append("  x2 = {:.6g}".format((-b - r) / (2 * a)))
    elif disc == 0:
        out.append("One real root:")
        out.append("  x = {:.6g}".format(-b / (2 * a)))
    else:
        r = cmath.sqrt(disc)
        out.append("Two complex roots:")
        out.append("  x1 = {}".format((-b + r) / (2 * a)))
        out.append("  x2 = {}".format((-b - r) / (2 * a)))
    out.append("Vertex x = {:.6g}".format(-b / (2 * a)))
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
