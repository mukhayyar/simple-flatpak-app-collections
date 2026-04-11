#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, GLib, Gst

Gst.init(None)

class MetronomeWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Metronome")
        self.set_default_size(400, 450)
        self.bpm = 120
        self.beat = 0
        self.beats_per_measure = 4
        self.subdivision = 1
        self.running = False
        self.timeout_id = None
        self.tap_times = []

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_top(20)
        vbox.set_margin_bottom(20)
        vbox.set_margin_start(20)
        vbox.set_margin_end(20)
        self.set_child(vbox)

        self.flash_label = Gtk.Label(label="●")
        self.flash_label.set_css_classes(["beat-flash"])
        css = Gtk.CssProvider()
        css.load_from_data(b".beat-flash { font-size: 60px; color: #888; } .beat-accent { color: #e74c3c; } .beat-on { color: #2ecc71; }")
        Gtk.StyleContext.add_provider_for_display(self.get_display(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        vbox.append(self.flash_label)

        self.bpm_label = Gtk.Label(label=f"BPM: {self.bpm}")
        self.bpm_label.set_css_classes(["title"])
        vbox.append(self.bpm_label)

        self.bpm_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 40, 240, 1)
        self.bpm_scale.set_value(self.bpm)
        self.bpm_scale.connect("value-changed", self.on_bpm_changed)
        vbox.append(self.bpm_scale)

        beat_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        beat_box.append(Gtk.Label(label="Beats/Measure:"))
        self.beats_spin = Gtk.SpinButton.new_with_range(1, 12, 1)
        self.beats_spin.set_value(4)
        self.beats_spin.connect("value-changed", self.on_beats_changed)
        beat_box.append(self.beats_spin)
        vbox.append(beat_box)

        sub_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        sub_box.append(Gtk.Label(label="Subdivision:"))
        for label, val in [("Quarter", 1), ("8th", 2), ("16th", 4)]:
            btn = Gtk.Button(label=label)
            btn.connect("clicked", self.on_subdivision, val)
            sub_box.append(btn)
        vbox.append(sub_box)

        tap_btn = Gtk.Button(label="Tap Tempo")
        tap_btn.connect("clicked", self.on_tap)
        vbox.append(tap_btn)

        self.start_btn = Gtk.Button(label="Start")
        self.start_btn.connect("clicked", self.on_toggle)
        vbox.append(self.start_btn)

        self.beat_indicators = []
        beat_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        beat_row.set_halign(Gtk.Align.CENTER)
        for i in range(4):
            lbl = Gtk.Label(label="○")
            self.beat_indicators.append(lbl)
            beat_row.append(lbl)
        vbox.append(beat_row)
        self.update_indicators()

        self.pipeline = Gst.parse_launch(
            "audiotestsrc name=src ! audioconvert ! autoaudiosink"
        )
        self.src = self.pipeline.get_by_name("src")

    def update_indicators(self):
        while len(self.beat_indicators) < self.beats_per_measure:
            lbl = Gtk.Label(label="○")
            self.beat_indicators.append(lbl)
        while len(self.beat_indicators) > self.beats_per_measure:
            self.beat_indicators.pop()

    def on_beats_changed(self, spin):
        self.beats_per_measure = int(spin.get_value())
        self.beat = 0

    def on_subdivision(self, btn, val):
        self.subdivision = val
        if self.running:
            self.stop_metronome()
            self.start_metronome()

    def on_bpm_changed(self, scale):
        self.bpm = int(scale.get_value())
        self.bpm_label.set_text(f"BPM: {self.bpm}")
        if self.running:
            self.stop_metronome()
            self.start_metronome()

    def on_tap(self, btn):
        import time
        now = time.time()
        self.tap_times.append(now)
        self.tap_times = [t for t in self.tap_times if now - t < 3]
        if len(self.tap_times) >= 2:
            intervals = [self.tap_times[i+1] - self.tap_times[i] for i in range(len(self.tap_times)-1)]
            avg = sum(intervals) / len(intervals)
            self.bpm = max(40, min(240, int(60 / avg)))
            self.bpm_scale.set_value(self.bpm)

    def on_toggle(self, btn):
        if self.running:
            self.stop_metronome()
            self.start_btn.set_label("Start")
        else:
            self.start_metronome()
            self.start_btn.set_label("Stop")

    def start_metronome(self):
        self.running = True
        interval_ms = int(60000 / (self.bpm * self.subdivision))
        self.timeout_id = GLib.timeout_add(interval_ms, self.tick)

    def stop_metronome(self):
        self.running = False
        if self.timeout_id:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None
        self.pipeline.set_state(Gst.State.NULL)
        self.flash_label.set_css_classes(["beat-flash"])

    def tick(self):
        actual_beat = self.beat % (self.beats_per_measure * self.subdivision)
        is_accent = (actual_beat == 0)
        if is_accent:
            freq = 1000
            self.flash_label.set_css_classes(["beat-flash", "beat-accent"])
        else:
            freq = 600
            self.flash_label.set_css_classes(["beat-flash", "beat-on"])
        self.src.set_property("freq", freq)
        self.src.set_property("wave", 0)
        self.pipeline.set_state(Gst.State.PLAYING)
        GLib.timeout_add(50, self.silence)
        self.beat = (self.beat + 1) % (self.beats_per_measure * self.subdivision)
        GLib.timeout_add(100, self.reset_flash)
        return self.running

    def silence(self):
        self.pipeline.set_state(Gst.State.NULL)
        return False

    def reset_flash(self):
        self.flash_label.set_css_classes(["beat-flash"])
        return False

class MetronomeApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.Metronome")

    def do_activate(self):
        win = MetronomeWindow(self)
        win.present()

def main():
    app = MetronomeApp()
    app.run(None)

if __name__ == "__main__":
    main()
