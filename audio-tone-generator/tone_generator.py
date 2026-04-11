#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, Gst

Gst.init(None)

WAVEFORMS = {"Sine": 0, "Square": 1, "Saw": 2, "Triangle": 3}

class ToneGeneratorWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Tone Generator")
        self.set_default_size(420, 360)
        self.playing = False
        self.pipeline = None

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_top(20); vbox.set_margin_bottom(20)
        vbox.set_margin_start(20); vbox.set_margin_end(20)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Tone Generator", css_classes=["title"]))

        freq_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        freq_box.append(Gtk.Label(label="Frequency (Hz):"))
        self.freq_label = Gtk.Label(label="440")
        freq_box.append(self.freq_label)
        vbox.append(freq_box)

        self.freq_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 20, 20000, 1)
        self.freq_scale.set_value(440)
        self.freq_scale.connect("value-changed", self.on_freq_changed)
        vbox.append(self.freq_scale)

        wave_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        wave_box.append(Gtk.Label(label="Waveform:"))
        self.wave_combo = Gtk.ComboBoxText()
        for w in WAVEFORMS:
            self.wave_combo.append_text(w)
        self.wave_combo.set_active(0)
        self.wave_combo.connect("changed", self.on_wave_changed)
        wave_box.append(self.wave_combo)
        vbox.append(wave_box)

        vol_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        vol_box.append(Gtk.Label(label="Volume:"))
        self.vol_label = Gtk.Label(label="50%")
        vol_box.append(self.vol_label)
        vbox.append(vol_box)

        self.vol_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.vol_scale.set_value(50)
        self.vol_scale.connect("value-changed", self.on_vol_changed)
        vbox.append(self.vol_scale)

        self.play_btn = Gtk.Button(label="Play")
        self.play_btn.connect("clicked", self.on_toggle)
        vbox.append(self.play_btn)

        self.status_label = Gtk.Label(label="Ready")
        vbox.append(self.status_label)

        note_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        note_box.append(Gtk.Label(label="Quick note:"))
        notes = [("A4", 440), ("C4", 261), ("E4", 330), ("G4", 392), ("A5", 880)]
        for name, freq in notes:
            btn = Gtk.Button(label=name)
            btn.connect("clicked", self.on_note, freq)
            note_box.append(btn)
        vbox.append(note_box)

    def build_pipeline(self):
        freq = int(self.freq_scale.get_value())
        wave_name = self.wave_combo.get_active_text()
        wave = WAVEFORMS.get(wave_name, 0)
        vol = self.vol_scale.get_value() / 100.0
        pipeline_str = (
            f"audiotestsrc wave={wave} freq={freq} volume={vol:.2f} ! "
            "audioconvert ! autoaudiosink"
        )
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
        self.pipeline = Gst.parse_launch(pipeline_str)

    def on_freq_changed(self, scale):
        freq = int(scale.get_value())
        self.freq_label.set_text(str(freq))
        if self.playing:
            self.build_pipeline()
            self.pipeline.set_state(Gst.State.PLAYING)

    def on_wave_changed(self, combo):
        if self.playing:
            self.build_pipeline()
            self.pipeline.set_state(Gst.State.PLAYING)

    def on_vol_changed(self, scale):
        self.vol_label.set_text(f"{int(scale.get_value())}%")
        if self.playing:
            self.build_pipeline()
            self.pipeline.set_state(Gst.State.PLAYING)

    def on_note(self, btn, freq):
        self.freq_scale.set_value(freq)

    def on_toggle(self, btn):
        if self.playing:
            if self.pipeline:
                self.pipeline.set_state(Gst.State.NULL)
            self.playing = False
            self.play_btn.set_label("Play")
            self.status_label.set_text("Stopped")
        else:
            self.build_pipeline()
            self.pipeline.set_state(Gst.State.PLAYING)
            self.playing = True
            self.play_btn.set_label("Stop")
            freq = int(self.freq_scale.get_value())
            self.status_label.set_text(f"Playing {freq} Hz")

class ToneGeneratorApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.ToneGenerator")
    def do_activate(self):
        win = ToneGeneratorWindow(self)
        win.present()

def main():
    app = ToneGeneratorApp()
    app.run(None)

if __name__ == "__main__":
    main()
