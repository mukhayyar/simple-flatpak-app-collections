#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, GLib, Gst

Gst.init(None)

PRESETS = [("Pomodoro 25min", 25*60), ("Short Break 5min", 5*60),
           ("Long Break 15min", 15*60), ("1 Hour", 3600), ("Custom", 0)]

class AudioTimerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Audio Timer")
        self.set_default_size(400, 480)
        self.remaining = 25 * 60
        self.total = 25 * 60
        self.running = False
        self.timeout_id = None

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(16); vbox.set_margin_bottom(16)
        vbox.set_margin_start(16); vbox.set_margin_end(16)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Audio Timer", css_classes=["title"]))

        self.bg_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.bg_box.set_hexpand(True)

        css = Gtk.CssProvider()
        css.load_from_data(b"""
.timer-display { font-size: 64px; font-weight: bold; }
.timer-green { background-color: #2ecc71; border-radius: 12px; padding: 12px; }
.timer-yellow { background-color: #f39c12; border-radius: 12px; padding: 12px; }
.timer-red { background-color: #e74c3c; border-radius: 12px; padding: 12px; }
""")
        Gtk.StyleContext.add_provider_for_display(self.get_display(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.time_label = Gtk.Label(label="25:00")
        self.time_label.set_css_classes(["timer-display"])
        self.time_label.set_halign(Gtk.Align.CENTER)
        self.bg_box.set_css_classes(["timer-green"])
        self.bg_box.append(self.time_label)
        vbox.append(self.bg_box)

        self.progress = Gtk.ProgressBar()
        self.progress.set_fraction(1.0)
        vbox.append(self.progress)

        presets_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        presets_box.set_halign(Gtk.Align.CENTER)
        for name, secs in PRESETS:
            btn = Gtk.Button(label=name)
            btn.connect("clicked", self.on_preset, secs)
            presets_box.append(btn)
        vbox.append(presets_box)

        custom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        custom_box.append(Gtk.Label(label="Custom (min):"))
        self.custom_spin = Gtk.SpinButton.new_with_range(1, 999, 1)
        self.custom_spin.set_value(25)
        custom_box.append(self.custom_spin)
        set_btn = Gtk.Button(label="Set")
        set_btn.connect("clicked", self.on_set_custom)
        custom_box.append(set_btn)
        vbox.append(custom_box)

        ctrl = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        ctrl.set_halign(Gtk.Align.CENTER)
        self.start_btn = Gtk.Button(label="Start")
        self.start_btn.connect("clicked", self.on_toggle)
        ctrl.append(self.start_btn)
        reset_btn = Gtk.Button(label="Reset")
        reset_btn.connect("clicked", self.on_reset)
        ctrl.append(reset_btn)
        vbox.append(ctrl)

        self.status_label = Gtk.Label(label="Ready")
        vbox.append(self.status_label)

    def on_preset(self, btn, secs):
        if secs == 0:
            secs = int(self.custom_spin.get_value()) * 60
        self.stop()
        self.remaining = secs
        self.total = secs
        self.update_display()
        self.start_btn.set_label("Start")

    def on_set_custom(self, btn):
        secs = int(self.custom_spin.get_value()) * 60
        self.stop()
        self.remaining = secs
        self.total = secs
        self.update_display()

    def on_toggle(self, btn):
        if self.running:
            self.stop()
            self.start_btn.set_label("Resume")
        else:
            self.start()
            self.start_btn.set_label("Pause")

    def on_reset(self, btn):
        self.stop()
        self.remaining = self.total
        self.update_display()
        self.start_btn.set_label("Start")
        self.status_label.set_text("Ready")

    def start(self):
        self.running = True
        self.timeout_id = GLib.timeout_add(1000, self.tick)

    def stop(self):
        self.running = False
        if self.timeout_id:
            GLib.source_remove(self.timeout_id)

    def tick(self):
        if self.remaining > 0:
            self.remaining -= 1
            self.update_display()
            return True
        else:
            self.running = False
            self.play_chime()
            self.status_label.set_text("Time's up!")
            self.start_btn.set_label("Start")
            return False

    def update_display(self):
        mins = self.remaining // 60
        secs = self.remaining % 60
        self.time_label.set_text(f"{mins:02d}:{secs:02d}")
        if self.total > 0:
            frac = self.remaining / self.total
            self.progress.set_fraction(frac)
            if frac > 0.5:
                self.bg_box.set_css_classes(["timer-green"])
            elif frac > 0.2:
                self.bg_box.set_css_classes(["timer-yellow"])
            else:
                self.bg_box.set_css_classes(["timer-red"])

    def play_chime(self):
        for i, (freq, delay) in enumerate([(880, 0), (1100, 300), (880, 600), (1320, 900)]):
            GLib.timeout_add(delay, self.beep, freq)

    def beep(self, freq):
        pipe = Gst.parse_launch(
            f"audiotestsrc wave=0 freq={freq} num-buffers=15 ! audioconvert ! autoaudiosink"
        )
        pipe.set_state(Gst.State.PLAYING)
        GLib.timeout_add(500, lambda p=pipe: p.set_state(Gst.State.NULL) or False)
        return False

class AudioTimerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.AudioTimer")
    def do_activate(self):
        win = AudioTimerWindow(self)
        win.present()

def main():
    app = AudioTimerApp()
    app.run(None)

if __name__ == "__main__":
    main()
