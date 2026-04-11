#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, Gst, GLib

Gst.init(None)

TRACKS = [("Kick", 60), ("Snare", 200), ("Hi-Hat", 800), ("Clap", 1200)]
STEPS = 8

class DrumMachineWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Drum Machine")
        self.set_default_size(680, 380)
        self.bpm = 120
        self.step = 0
        self.running = False
        self.timeout_id = None
        self.pattern = [[False] * STEPS for _ in range(len(TRACKS))]
        self.step_labels = []

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(12); vbox.set_margin_bottom(12)
        vbox.set_margin_start(12); vbox.set_margin_end(12)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Drum Machine", css_classes=["title"]))

        bpm_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bpm_box.append(Gtk.Label(label="BPM:"))
        self.bpm_label = Gtk.Label(label="120")
        bpm_box.append(self.bpm_label)
        bpm_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 60, 200, 1)
        bpm_scale.set_value(120)
        bpm_scale.set_hexpand(True)
        bpm_scale.connect("value-changed", self.on_bpm_changed)
        bpm_box.append(bpm_scale)
        vbox.append(bpm_box)

        step_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        step_header.append(Gtk.Label(label="Track    ", width_chars=12))
        self.step_indicators = []
        for i in range(STEPS):
            lbl = Gtk.Label(label=f"{i+1}", width_chars=5)
            step_header.append(lbl)
            self.step_indicators.append(lbl)
        vbox.append(step_header)

        self.btn_grid = []
        for ti, (name, freq) in enumerate(TRACKS):
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
            lbl = Gtk.Label(label=name, width_chars=12, xalign=0)
            row.append(lbl)
            row_btns = []
            for si in range(STEPS):
                btn = Gtk.ToggleButton(label="·", width_chars=4)
                btn.connect("toggled", self.on_step_toggled, ti, si)
                row.append(btn)
                row_btns.append(btn)
            self.btn_grid.append(row_btns)
            vbox.append(row)

        ctrl = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        ctrl.set_halign(Gtk.Align.CENTER)
        self.play_btn = Gtk.Button(label="Play")
        self.play_btn.connect("clicked", self.on_toggle)
        ctrl.append(self.play_btn)
        clear_btn = Gtk.Button(label="Clear")
        clear_btn.connect("clicked", self.on_clear)
        ctrl.append(clear_btn)
        preset_btn = Gtk.Button(label="Load Preset")
        preset_btn.connect("clicked", self.on_preset)
        ctrl.append(preset_btn)
        vbox.append(ctrl)

    def on_bpm_changed(self, scale):
        self.bpm = int(scale.get_value())
        self.bpm_label.set_text(str(self.bpm))
        if self.running:
            self.stop()
            self.start()

    def on_step_toggled(self, btn, ti, si):
        self.pattern[ti][si] = btn.get_active()
        btn.set_label("X" if btn.get_active() else "·")

    def on_clear(self, btn):
        for ti in range(len(TRACKS)):
            for si in range(STEPS):
                self.pattern[ti][si] = False
                self.btn_grid[ti][si].set_active(False)
                self.btn_grid[ti][si].set_label("·")

    def on_preset(self, btn):
        preset = [
            [True, False, False, False, True, False, False, False],
            [False, False, True, False, False, False, True, False],
            [True, True, True, True, True, True, True, True],
            [False, False, False, False, True, False, False, False],
        ]
        for ti in range(len(TRACKS)):
            for si in range(STEPS):
                self.pattern[ti][si] = preset[ti][si]
                self.btn_grid[ti][si].set_active(preset[ti][si])
                self.btn_grid[ti][si].set_label("X" if preset[ti][si] else "·")

    def on_toggle(self, btn):
        if self.running:
            self.stop()
            self.play_btn.set_label("Play")
        else:
            self.start()
            self.play_btn.set_label("Stop")

    def start(self):
        self.running = True
        interval_ms = int(60000 / (self.bpm * 2))
        self.timeout_id = GLib.timeout_add(interval_ms, self.tick)

    def stop(self):
        self.running = False
        if self.timeout_id:
            GLib.source_remove(self.timeout_id)
        for lbl in self.step_indicators:
            lbl.set_css_classes([])

    def tick(self):
        for lbl in self.step_indicators:
            lbl.set_css_classes([])
        self.step_indicators[self.step].set_css_classes(["suggested-action"])

        for ti, (name, freq) in enumerate(TRACKS):
            if self.pattern[ti][self.step]:
                self.play_sound(freq)

        self.step = (self.step + 1) % STEPS
        return self.running

    def play_sound(self, freq):
        pipe = Gst.parse_launch(
            f"audiotestsrc wave=1 freq={freq} num-buffers=3 ! audioconvert ! autoaudiosink"
        )
        pipe.set_state(Gst.State.PLAYING)
        GLib.timeout_add(200, lambda p=pipe: p.set_state(Gst.State.NULL) or False)

class DrumMachineApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.DrumMachine")
    def do_activate(self):
        win = DrumMachineWindow(self)
        win.present()

def main():
    app = DrumMachineApp()
    app.run(None)

if __name__ == "__main__":
    main()
