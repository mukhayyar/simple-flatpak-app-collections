#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, Gst, GLib
import math

Gst.init(None)

NUM_BANDS = 32

class SpectrumAnalyzerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Spectrum Analyzer")
        self.set_default_size(640, 360)
        self.magnitudes = [-80.0] * NUM_BANDS
        self.running = False
        self.pipeline = None

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Spectrum Analyzer"))

        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_draw_func(self.on_draw)
        self.drawing_area.set_hexpand(True)
        self.drawing_area.set_vexpand(True)
        vbox.append(self.drawing_area)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.start_btn = Gtk.Button(label="Start")
        self.start_btn.connect("clicked", self.on_toggle)
        btn_box.append(self.start_btn)
        vbox.append(btn_box)

    def on_toggle(self, btn):
        if self.running:
            self.stop()
            self.start_btn.set_label("Start")
        else:
            self.start()
            self.start_btn.set_label("Stop")

    def start(self):
        self.pipeline = Gst.parse_launch(
            "pulsesrc ! audioconvert ! spectrum bands=32 interval=33000000 ! fakesink"
        )
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message::element", self.on_spectrum_message)
        self.pipeline.set_state(Gst.State.PLAYING)
        self.running = True
        GLib.timeout_add(33, self.refresh)

    def stop(self):
        self.running = False
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)

    def on_spectrum_message(self, bus, message):
        s = message.get_structure()
        if s and s.get_name() == "spectrum":
            mags = s.get_value("magnitude")
            if mags:
                self.magnitudes = list(mags[:NUM_BANDS])

    def refresh(self):
        self.drawing_area.queue_draw()
        return self.running

    def on_draw(self, area, cr, w, h):
        cr.set_source_rgb(0.1, 0.1, 0.1)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        bar_w = w / NUM_BANDS
        for i, mag in enumerate(self.magnitudes):
            normalized = max(0, (mag + 80) / 80.0)
            bar_h = normalized * h
            r = normalized
            g = 0.5 * (1 - normalized)
            b = 1 - normalized
            cr.set_source_rgb(r, g, b)
            cr.rectangle(i * bar_w + 1, h - bar_h, bar_w - 2, bar_h)
            cr.fill()

        cr.set_source_rgb(0.3, 0.3, 0.3)
        for db in [-60, -40, -20, 0]:
            y = h * (1 - (db + 80) / 80.0)
            cr.move_to(0, y)
            cr.line_to(w, y)
            cr.stroke()
            cr.set_source_rgb(0.6, 0.6, 0.6)
            cr.move_to(2, y - 2)
            cr.show_text(f"{db}dB")
            cr.set_source_rgb(0.3, 0.3, 0.3)

class SpectrumAnalyzerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.SpectrumAnalyzer")
    def do_activate(self):
        win = SpectrumAnalyzerWindow(self)
        win.present()

def main():
    app = SpectrumAnalyzerApp()
    app.run(None)

if __name__ == "__main__":
    main()
