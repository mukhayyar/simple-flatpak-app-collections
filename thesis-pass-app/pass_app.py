#!/usr/bin/env python3
"""com.thesis.PassApp — Minimal PASS-class test bundle for AGL security scanner benchmark."""
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

class PassApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.thesis.PassApp")

    def do_activate(self):
        win = Gtk.ApplicationWindow(application=self, title="PassApp")
        win.set_default_size(400, 200)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=24,
                      margin_bottom=24, margin_start=24, margin_end=24)
        lbl = Gtk.Label(label="\u2713 Security: PASS")
        lbl.add_css_class("title-2")
        sub = Gtk.Label(label="This app uses only safe permissions.\nRisk score: 0 / 100")
        box.append(lbl)
        box.append(sub)
        win.set_child(box)
        win.present()

PassApp().run()
