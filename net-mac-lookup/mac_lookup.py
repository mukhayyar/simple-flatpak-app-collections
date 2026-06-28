#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk
import random, math, re, string, secrets, datetime, cmath, os

TITLE = "MAC Address Inspector"
APP_ID = "com.pens.MacLookup"
FIELDS = [("MAC address", "00:1A:2B:3C:4D:5E")]
_OUI = {"001A2B": "Ayecom Technology", "FCFBFB": "Cisco Systems", "001B63": "Apple",
        "B827EB": "Raspberry Pi Foundation", "DCA632": "Raspberry Pi Trading",
        "001C42": "Parallels", "080027": "VirtualBox (Oracle)", "525400": "QEMU/KVM"}

def compute(vals):
    raw = re.sub(r"[^0-9A-Fa-f]", "", vals[0]).upper()
    if len(raw) != 12:
        return "A MAC address has 12 hex digits, e.g. 00:1A:2B:3C:4D:5E"
    pairs = [raw[i:i+2] for i in range(0, 12, 2)]
    colon = ":".join(pairs)
    oui = raw[:6]
    first = int(pairs[0], 16)
    multicast = bool(first & 1)
    local = bool(first & 2)
    return "\n".join([
        "Normalized : " + colon,
        "Dash form  : " + "-".join(pairs),
        "Cisco form : " + ".".join([raw[i:i+4] for i in range(0, 12, 4)]),
        "OUI prefix : " + oui,
        "Vendor     : " + _OUI.get(oui, "(unknown / not in local table)"),
        "Cast       : " + ("Multicast" if multicast else "Unicast"),
        "Admin      : " + ("Locally administered" if local else "Globally unique (OUI)"),
    ])

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
