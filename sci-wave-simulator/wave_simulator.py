#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import math

class WaveSimulatorWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Wave Simulator")
        self.set_default_size(800, 600)
        self.t = 0.0
        self.running = True
        self.waves = [
            {"amp": 1.0, "freq": 1.0, "phase": 0.0, "type": "sine", "enabled": True},
            {"amp": 0.5, "freq": 3.0, "phase": 0.0, "type": "sine", "enabled": False},
        ]
        self.build_ui()
        GLib.timeout_add(30, self.tick)

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Wave Simulator", css_classes=["title"]))

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        # Wave configuration panel
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        left.set_size_request(230, -1)

        for i, wave in enumerate(self.waves):
            frame = Gtk.Frame(label=f"Wave {i+1}")
            wbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            wbox.set_margin_top(4); wbox.set_margin_start(4); wbox.set_margin_end(4); wbox.set_margin_bottom(4)

            en_btn = Gtk.CheckButton(label="Enabled")
            en_btn.set_active(wave["enabled"])
            en_btn.connect("toggled", self.on_wave_toggle, i)
            wbox.append(en_btn)

            wtype_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            wtype_box.append(Gtk.Label(label="Type:"))
            tc = Gtk.ComboBoxText()
            for wt in ["sine", "cosine", "square", "triangle", "sawtooth"]:
                tc.append_text(wt)
            tc.set_active(0)
            tc.connect("changed", self.on_wave_type, i)
            wtype_box.append(tc)
            wbox.append(wtype_box)

            def make_wave_slider(label, key, mn, mx, val, idx=i):
                b = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
                b.append(Gtk.Label(label=f"{label}:", xalign=0))
                adj = Gtk.Adjustment(value=val, lower=mn, upper=mx, step_increment=0.1)
                s = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj)
                s.set_hexpand(True); s.set_draw_value(True); s.set_digits(2)
                s.connect("value-changed", self.on_wave_param, idx, key)
                b.append(s)
                return b

            wbox.append(make_wave_slider("Amp", "amp", 0, 2, wave["amp"]))
            wbox.append(make_wave_slider("Freq", "freq", 0.1, 10, wave["freq"]))
            wbox.append(make_wave_slider("Phase", "phase", 0, 6.28, wave["phase"]))

            frame.set_child(wbox)
            left.append(frame)

        add_btn = Gtk.Button(label="+ Add Wave")
        add_btn.connect("clicked", self.on_add_wave)
        left.append(add_btn)

        speed_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        speed_box.append(Gtk.Label(label="Speed:"))
        adj = Gtk.Adjustment(value=1.0, lower=0, upper=5, step_increment=0.1)
        self.speed_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj)
        self.speed_scale.set_hexpand(True); self.speed_scale.set_draw_value(True)
        speed_box.append(self.speed_scale)
        left.append(speed_box)

        play_btn = Gtk.Button(label="⏸/▶ Toggle")
        play_btn.connect("clicked", lambda b: setattr(self, "running", not self.running))
        left.append(play_btn)

        hbox.append(left)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        right.set_hexpand(True)

        wave_frame = Gtk.Frame(label="Individual Waves")
        self.wave_canvas = Gtk.DrawingArea()
        self.wave_canvas.set_size_request(-1, 180)
        self.wave_canvas.set_draw_func(self.draw_waves)
        wave_frame.set_child(self.wave_canvas)
        right.append(wave_frame)

        sum_frame = Gtk.Frame(label="Superposition (Sum)")
        self.sum_canvas = Gtk.DrawingArea()
        self.sum_canvas.set_vexpand(True)
        self.sum_canvas.set_draw_func(self.draw_sum)
        sum_frame.set_child(self.sum_canvas)
        right.append(sum_frame)

        info_frame = Gtk.Frame(label="Wave Info")
        self.info_label = Gtk.Label(label="", xalign=0)
        info_frame.set_child(self.info_label)
        right.append(info_frame)

        hbox.append(right)
        vbox.append(hbox)

    def wave_val(self, wave, x):
        if not wave["enabled"]:
            return 0
        a = wave["amp"]
        f = wave["freq"]
        p = wave["phase"]
        arg = 2 * math.pi * f * x + p
        wt = wave["type"]
        if wt == "sine": return a * math.sin(arg)
        if wt == "cosine": return a * math.cos(arg)
        if wt == "square": return a * (1 if math.sin(arg) >= 0 else -1)
        if wt == "triangle": return a * (2/math.pi) * math.asin(math.sin(arg))
        if wt == "sawtooth": return a * (((arg / math.pi) % 2) - 1)
        return 0

    def tick(self):
        if self.running:
            speed = self.speed_scale.get_value()
            self.t += 0.03 * speed
            self.wave_canvas.queue_draw()
            self.sum_canvas.queue_draw()
            self.update_info()
        return True

    def update_info(self):
        active = [w for w in self.waves if w["enabled"]]
        info = " | ".join(f"W{i+1}: A={w['amp']:.1f} f={w['freq']:.1f}Hz" for i,w in enumerate(self.waves) if w["enabled"])
        if active:
            dominant = max(active, key=lambda w: w["amp"])
            period = 1/dominant["freq"] if dominant["freq"] > 0 else 0
            self.info_label.set_text(f"{info}   |   Dominant period: {period:.3f}s")

    def draw_waves(self, area, cr, w, h):
        cr.set_source_rgb(0.06, 0.06, 0.1); cr.rectangle(0, 0, w, h); cr.fill()
        colors = [(0.9,0.3,0.3),(0.3,0.6,0.9),(0.3,0.8,0.4),(0.9,0.7,0.2),(0.7,0.3,0.9)]
        steps = w * 2
        for wi, wave in enumerate(self.waves):
            if not wave["enabled"]:
                continue
            cr.set_source_rgb(*colors[wi % len(colors)])
            cr.set_line_width(1.5)
            for i in range(int(steps)):
                x = i / steps
                xc = x * w
                y = self.wave_val(wave, x + self.t)
                yc = h/2 - y * (h/2 - 10) / 2
                if i == 0: cr.move_to(xc, yc)
                else: cr.line_to(xc, yc)
            cr.stroke()
        cr.set_source_rgba(0.4, 0.4, 0.5, 0.4); cr.set_line_width(1)
        cr.move_to(0, h/2); cr.line_to(w, h/2); cr.stroke()

    def draw_sum(self, area, cr, w, h):
        cr.set_source_rgb(0.06, 0.06, 0.1); cr.rectangle(0, 0, w, h); cr.fill()
        steps = w * 2
        cr.set_source_rgb(0.3, 0.8, 0.6); cr.set_line_width(2)
        for i in range(int(steps)):
            x = i / steps
            xc = x * w
            ysum = sum(self.wave_val(wave, x + self.t) for wave in self.waves)
            yc = h/2 - ysum * (h/2 - 10) / max(len(self.waves), 1) / 1.5
            if i == 0: cr.move_to(xc, yc)
            else: cr.line_to(xc, yc)
        cr.stroke()
        cr.set_source_rgba(0.4, 0.4, 0.5, 0.4); cr.set_line_width(1)
        cr.move_to(0, h/2); cr.line_to(w, h/2); cr.stroke()

    def on_wave_toggle(self, btn, idx):
        self.waves[idx]["enabled"] = btn.get_active()

    def on_wave_type(self, combo, idx):
        self.waves[idx]["type"] = combo.get_active_text()

    def on_wave_param(self, scale, idx, key):
        self.waves[idx][key] = scale.get_value()

    def on_add_wave(self, btn):
        if len(self.waves) < 5:
            self.waves.append({"amp": 0.5, "freq": 2.0, "phase": 0.0, "type": "sine", "enabled": True})

class WaveSimulatorApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.WaveSimulator")
    def do_activate(self):
        win = WaveSimulatorWindow(self); win.present()

def main():
    app = WaveSimulatorApp(); app.run(None)

if __name__ == "__main__":
    main()
