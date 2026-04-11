#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, Gdk, GLib, Gst

Gst.init(None)

TIME_CONTROLS = {
    "Blitz 3+2": (180, 2),
    "Blitz 5+0": (300, 0),
    "Rapid 10+0": (600, 0),
    "Rapid 10+5": (600, 5),
    "Classical 90": (5400, 0),
    "Custom": (None, None),
}

class ChessClockWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Chess Clock")
        self.set_default_size(480, 560)
        self.white_time = 300
        self.black_time = 300
        self.increment = 0
        self.active = None
        self.running = False
        self.move_count = [0, 0]
        self.log = []
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        css = Gtk.CssProvider()
        css.load_from_data(b"""
.clock-active { background-color: #2ecc71; color: #000; font-size: 64px; font-weight: bold; border-radius: 12px; padding: 20px; }
.clock-inactive { background-color: #2c3e50; color: #aaa; font-size: 64px; font-weight: bold; border-radius: 12px; padding: 20px; }
.clock-low { background-color: #e74c3c; color: white; font-size: 64px; font-weight: bold; border-radius: 12px; padding: 20px; }
""")
        Gtk.StyleContext.add_provider_for_display(self.get_display(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        tc_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        tc_box.set_halign(Gtk.Align.CENTER)
        for tc in TIME_CONTROLS:
            btn = Gtk.Button(label=tc)
            btn.connect("clicked", self.on_time_control, tc)
            tc_box.append(btn)
        vbox.append(tc_box)

        self.white_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.white_time_label = Gtk.Label(label=self.fmt(self.white_time))
        self.white_time_label.set_css_classes(["clock-inactive"])
        self.white_time_label.set_halign(Gtk.Align.FILL)
        self.white_box.append(self.white_time_label)
        self.white_label = Gtk.Label(label="WHITE")
        self.white_box.append(self.white_label)
        white_btn = Gtk.Button(label="White's Move Done")
        white_btn.connect("clicked", self.on_white_done)
        self.white_box.append(white_btn)
        vbox.append(self.white_box)

        self.black_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.black_time_label = Gtk.Label(label=self.fmt(self.black_time))
        self.black_time_label.set_css_classes(["clock-inactive"])
        self.black_time_label.set_halign(Gtk.Align.FILL)
        self.black_box.append(self.black_time_label)
        self.black_label = Gtk.Label(label="BLACK")
        self.black_box.append(self.black_label)
        black_btn = Gtk.Button(label="Black's Move Done")
        black_btn.connect("clicked", self.on_black_done)
        self.black_box.append(black_btn)
        vbox.append(self.black_box)

        ctrl = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        ctrl.set_halign(Gtk.Align.CENTER)
        self.start_btn = Gtk.Button(label="Start (White moves first)")
        self.start_btn.connect("clicked", self.on_start)
        ctrl.append(self.start_btn)
        reset_btn = Gtk.Button(label="Reset")
        reset_btn.connect("clicked", self.on_reset)
        ctrl.append(reset_btn)
        vbox.append(ctrl)

        space_ctrl = Gtk.EventControllerKey()
        space_ctrl.connect("key-pressed", self.on_key)
        self.add_controller(space_ctrl)

        self.log_view = Gtk.TextView()
        self.log_view.set_editable(False)
        self.log_view.set_size_request(-1, 100)
        scroll = Gtk.ScrolledWindow()
        scroll.set_child(self.log_view)
        vbox.append(scroll)

    def fmt(self, secs):
        m, s = divmod(max(0, int(secs)), 60)
        return f"{m:02d}:{s:02d}"

    def on_time_control(self, btn, tc):
        mins, inc = TIME_CONTROLS[tc]
        if mins is None:
            return
        self.white_time = self.black_time = mins
        self.increment = inc
        self.active = None
        self.running = False
        if hasattr(self, 'timeout_id'):
            GLib.source_remove(self.timeout_id)
        self.update_display()

    def on_start(self, btn):
        if not self.running:
            self.active = "white"
            self.running = True
            self.timeout_id = GLib.timeout_add(100, self.tick)
            self.update_display()

    def on_reset(self, btn):
        self.running = False
        if hasattr(self, 'timeout_id'):
            GLib.source_remove(self.timeout_id)
        self.active = None
        self.move_count = [0, 0]
        self.log = []
        self.log_view.get_buffer().set_text("")
        self.update_display()

    def on_key(self, ctrl, keyval, keycode, state):
        if keyval == Gdk.KEY_space:
            if self.active == "white":
                self.on_white_done(None)
            elif self.active == "black":
                self.on_black_done(None)
        return True

    def on_white_done(self, btn):
        if self.active == "white" and self.running:
            self.white_time += self.increment
            self.move_count[0] += 1
            self.log.append(f"W move {self.move_count[0]}: {self.fmt(self.white_time)}")
            self.active = "black"
            self.beep()
            self.update_display()

    def on_black_done(self, btn):
        if self.active == "black" and self.running:
            self.black_time += self.increment
            self.move_count[1] += 1
            self.log.append(f"B move {self.move_count[1]}: {self.fmt(self.black_time)}")
            self.active = "white"
            self.beep()
            self.update_display()

    def tick(self):
        if not self.running:
            return False
        if self.active == "white":
            self.white_time -= 0.1
            if self.white_time <= 0:
                self.white_time = 0
                self.running = False
                self.set_title("Chess Clock — Black wins on time!")
        elif self.active == "black":
            self.black_time -= 0.1
            if self.black_time <= 0:
                self.black_time = 0
                self.running = False
                self.set_title("Chess Clock — White wins on time!")
        self.update_display()
        return self.running

    def update_display(self):
        self.white_time_label.set_text(self.fmt(self.white_time))
        self.black_time_label.set_text(self.fmt(self.black_time))
        w_class = "clock-active" if self.active == "white" else ("clock-low" if self.white_time < 30 else "clock-inactive")
        b_class = "clock-active" if self.active == "black" else ("clock-low" if self.black_time < 30 else "clock-inactive")
        self.white_time_label.set_css_classes([w_class])
        self.black_time_label.set_css_classes([b_class])
        log_text = "\n".join(self.log[-20:])
        self.log_view.get_buffer().set_text(log_text)

    def beep(self):
        pipe = Gst.parse_launch("audiotestsrc wave=0 freq=880 num-buffers=3 ! audioconvert ! autoaudiosink")
        pipe.set_state(Gst.State.PLAYING)
        GLib.timeout_add(300, lambda p=pipe: p.set_state(Gst.State.NULL) or False)

class ChessClockApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.ChessClock")
    def do_activate(self):
        win = ChessClockWindow(self)
        win.present()

def main():
    app = ChessClockApp()
    app.run(None)

if __name__ == "__main__":
    main()
