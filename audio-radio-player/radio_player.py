#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, Gst

Gst.init(None)

STATIONS = [
    ("BBC World Service", "http://stream.live.vc.bbcmedia.co.uk/bbc_world_service"),
    ("NPR News", "https://npr-ice.streamguys1.com/live.mp3"),
    ("Classical KUSC", "https://kusc.streamguys1.com/kusc128.mp3"),
    ("Jazz 24", "https://live.wostreaming.net/manifest/ppm-jazz24aac256-ibc1.m3u8"),
    ("Radio Paradise", "http://stream.radioparadise.com/aac-320"),
    ("SomaFM Groove Salad", "http://ice2.somafm.com/groovesalad-256-mp3"),
    ("KEXP Seattle", "https://kexp-mp3-128.streamguys1.com/kexp128.mp3"),
    ("Lush (SomaFM)", "http://ice2.somafm.com/lush-256-mp3"),
    ("Deep Space One", "http://ice1.somafm.com/deepspaceone-128-mp3"),
    ("Indie Pop Rocks", "http://ice1.somafm.com/indiepop-256-mp3"),
]

class RadioPlayerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Radio Player")
        self.set_default_size(480, 500)
        self.player = None
        self.current = None

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(16); vbox.set_margin_bottom(16)
        vbox.set_margin_start(16); vbox.set_margin_end(16)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Internet Radio", css_classes=["title"]))

        self.status_label = Gtk.Label(label="Select a station")
        vbox.append(self.status_label)

        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(300)
        scroll.set_vexpand(True)

        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        listbox.connect("row-activated", self.on_station_selected)
        scroll.set_child(listbox)
        vbox.append(scroll)

        for name, url in STATIONS:
            row = Gtk.ListBoxRow()
            label = Gtk.Label(label=name, xalign=0)
            label.set_margin_start(8); label.set_margin_top(8); label.set_margin_bottom(8)
            label._url = url
            row.set_child(label)
            listbox.append(row)

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.play_btn = Gtk.Button(label="Play")
        self.play_btn.connect("clicked", self.on_play)
        self.stop_btn = Gtk.Button(label="Stop")
        self.stop_btn.connect("clicked", self.on_stop)
        controls.append(self.play_btn)
        controls.append(self.stop_btn)
        vbox.append(controls)

        vol_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        vol_box.append(Gtk.Label(label="Volume:"))
        self.vol_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.vol_scale.set_value(70)
        self.vol_scale.set_hexpand(True)
        self.vol_scale.connect("value-changed", self.on_volume)
        vol_box.append(self.vol_scale)
        vbox.append(vol_box)

        self.selected_row = None

    def on_station_selected(self, listbox, row):
        self.selected_row = row
        label = row.get_child()
        self.status_label.set_text(f"Selected: {label.get_text()}")

    def on_play(self, btn):
        if not self.selected_row:
            self.status_label.set_text("Please select a station first")
            return
        label = self.selected_row.get_child()
        name = label.get_text()
        url = label._url
        self.on_stop(None)
        self.player = Gst.parse_launch(f"playbin uri=\"{url}\"")
        vol = self.vol_scale.get_value() / 100.0
        self.player.set_property("volume", vol)
        self.player.set_state(Gst.State.PLAYING)
        self.current = name
        self.status_label.set_text(f"Playing: {name}")

    def on_stop(self, btn):
        if self.player:
            self.player.set_state(Gst.State.NULL)
            self.player = None
        self.status_label.set_text("Stopped")

    def on_volume(self, scale):
        if self.player:
            self.player.set_property("volume", scale.get_value() / 100.0)

class RadioPlayerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.RadioPlayer")
    def do_activate(self):
        win = RadioPlayerWindow(self)
        win.present()

def main():
    app = RadioPlayerApp()
    app.run(None)

if __name__ == "__main__":
    main()
