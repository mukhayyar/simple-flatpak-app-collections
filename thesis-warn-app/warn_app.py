#!/usr/bin/env python3
"""com.thesis.WarnApp — WARN-class test bundle: X11, network, home-filesystem permissions."""
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

class WarnApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.thesis.WarnApp")

    def do_activate(self):
        win = Gtk.ApplicationWindow(application=self, title="WarnApp")
        win.set_default_size(420, 220)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=24,
                      margin_bottom=24, margin_start=24, margin_end=24)
        lbl = Gtk.Label(label="\u26a0 Security: WARN")
        lbl.add_css_class("title-2")
        sub = Gtk.Label(
            label="This app requests X11 display, network access,\n"
                  "and home directory write access.\n"
                  "Risk score: 16 / 100"
        )
        box.append(lbl)
        box.append(sub)
        win.set_child(box)
        win.present()

WarnApp().run()
