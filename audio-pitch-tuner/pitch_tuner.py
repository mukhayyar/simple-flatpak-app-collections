#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, Gst, GLib
import math

Gst.init(None)

NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def freq_to_note(freq):
    if freq <= 0: return ("?", 0, 0)
    midi = 69 + 12 * math.log2(freq / 440.0)
    nearest = round(midi)
    cents = (midi - nearest) * 100
    note = NOTES[nearest % 12]
    octave = nearest // 12 - 1
    return (note, octave, cents)

class PitchTunerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Pitch Tuner")
        self.set_default_size(500, 440)
        self.pipeline = None
        self.running = False
        self.cents = 0.0

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(16); vbox.set_margin_bottom(16)
        vbox.set_margin_start(16); vbox.set_margin_end(16)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Pitch Tuner", css_classes=["title"]))

        self.note_label = Gtk.Label(label="--")
        css = Gtk.CssProvider()
        css.load_from_data(b".big-note { font-size: 72px; font-weight: bold; }")
        Gtk.StyleContext.add_provider_for_display(self.get_display(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.note_label.set_css_classes(["big-note"])
        vbox.append(self.note_label)

        self.freq_label = Gtk.Label(label="-- Hz")
        vbox.append(self.freq_label)

        self.cents_label = Gtk.Label(label="0 cents")
        vbox.append(self.cents_label)

        self.gauge = Gtk.DrawingArea()
        self.gauge.set_size_request(460, 100)
        self.gauge.set_draw_func(self.on_draw_gauge)
        vbox.append(self.gauge)

        self.in_tune_label = Gtk.Label(label="")
        vbox.append(self.in_tune_label)

        self.toggle_btn = Gtk.Button(label="Start Tuner")
        self.toggle_btn.connect("clicked", self.on_toggle)
        vbox.append(self.toggle_btn)

    def on_toggle(self, btn):
        if self.running:
            self.stop()
            self.toggle_btn.set_label("Start Tuner")
        else:
            self.start()
            self.toggle_btn.set_label("Stop Tuner")

    def start(self):
        self.pipeline = Gst.parse_launch(
            "pulsesrc ! audioconvert ! spectrum bands=1024 interval=100000000 ! fakesink"
        )
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message::element", self.on_spectrum)
        self.pipeline.set_state(Gst.State.PLAYING)
        self.running = True

    def stop(self):
        self.running = False
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
        self.note_label.set_text("--")
        self.freq_label.set_text("-- Hz")

    def on_spectrum(self, bus, msg):
        s = msg.get_structure()
        if not s or s.get_name() != "spectrum":
            return
        mags = s.get_value("magnitude")
        if not mags:
            return
        max_idx = max(range(len(mags)), key=lambda i: mags[i])
        sample_rate = 44100
        n_bands = len(mags)
        freq = max_idx * sample_rate / (2 * n_bands)
        if freq < 20 or mags[max_idx] < -60:
            return
        note, octave, cents = freq_to_note(freq)
        self.cents = cents
        self.note_label.set_text(f"{note}{octave}")
        self.freq_label.set_text(f"{freq:.1f} Hz")
        self.cents_label.set_text(f"{cents:+.0f} cents")
        if abs(cents) < 5:
            self.in_tune_label.set_text("IN TUNE")
        elif cents > 0:
            self.in_tune_label.set_text("Sharp ↑")
        else:
            self.in_tune_label.set_text("Flat ↓")
        self.gauge.queue_draw()

    def on_draw_gauge(self, area, cr, w, h):
        cx, cy = w / 2, h * 0.8
        r = min(w, h) * 0.7
        cr.set_source_rgb(0.15, 0.15, 0.15)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        cr.set_source_rgb(0.3, 0.3, 0.3)
        cr.arc(cx, cy, r, math.pi, 2 * math.pi)
        cr.stroke()

        for db in range(-50, 51, 10):
            angle = math.pi + (db / 50.0) * (math.pi / 2) + math.pi / 2
            x1 = cx + (r - 10) * math.cos(angle)
            y1 = cy + (r - 10) * math.sin(angle)
            x2 = cx + r * math.cos(angle)
            y2 = cy + r * math.sin(angle)
            cr.set_source_rgb(0.5, 0.5, 0.5)
            cr.move_to(x1, y1); cr.line_to(x2, y2); cr.stroke()

        needle_angle = math.pi + (max(-50, min(50, self.cents)) / 50.0) * (math.pi / 2) + math.pi / 2
        nx = cx + (r - 20) * math.cos(needle_angle)
        ny = cy + (r - 20) * math.sin(needle_angle)
        c = abs(self.cents) / 50.0
        cr.set_source_rgb(c, 1 - c, 0)
        cr.set_line_width(3)
        cr.move_to(cx, cy)
        cr.line_to(nx, ny)
        cr.stroke()
        cr.arc(cx, cy, 5, 0, 2 * math.pi)
        cr.fill()

class PitchTunerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.PitchTuner")
    def do_activate(self):
        win = PitchTunerWindow(self)
        win.present()

def main():
    app = PitchTunerApp()
    app.run(None)

if __name__ == "__main__":
    main()
