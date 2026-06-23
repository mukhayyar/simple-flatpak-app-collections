#!/usr/bin/env python3
"""com.thesis.BlockApp — BLOCK-class test bundle: host filesystem, device=all, Flatpak D-Bus, EICAR test signature."""
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

class BlockApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.thesis.BlockApp")

    def do_activate(self):
        win = Gtk.ApplicationWindow(application=self, title="BlockApp")
        win.set_default_size(440, 240)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=24,
                      margin_bottom=24, margin_start=24, margin_end=24)
        lbl = Gtk.Label(label="\u26d4 Security: BLOCK")
        lbl.add_css_class("title-2")
        sub = Gtk.Label(
            label="This app requests host filesystem access,\n"
                  "all devices, Flatpak D-Bus, and includes\n"
                  "an EICAR antivirus test signature.\n"
                  "Risk score: 91 / 100"
        )
        box.append(lbl)
        box.append(sub)
        win.set_child(box)
        win.present()

BlockApp().run()
