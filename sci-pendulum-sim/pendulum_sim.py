#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import math

class PendulumSimWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Pendulum Simulator")
        self.set_default_size(700, 580)
        self.running = False
        self.theta = math.pi / 4
        self.omega = 0.0
        self.g = 9.81
        self.length = 1.5
        self.damping = 0.01
        self.dt = 0.02
        self.time = 0.0
        self.trail = []
        self.max_trail = 80
        self.build_ui()
        GLib.timeout_add(20, self.simulation_step)

    def build_ui(self):
        hpaned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_child(hpaned)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        left.set_size_request(220, -1)
        left.set_margin_top(10); left.set_margin_start(10); left.set_margin_bottom(10)

        left.append(Gtk.Label(label="Pendulum Simulator", css_classes=["heading"]))

        def make_slider(label, mn, mx, val, step=0.1):
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            box.append(Gtk.Label(label=label, xalign=0))
            adj = Gtk.Adjustment(value=val, lower=mn, upper=mx, step_increment=step)
            scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj)
            scale.set_draw_value(True); scale.set_value_pos(Gtk.PositionType.RIGHT)
            box.append(scale)
            return box, scale

        g_box, self.g_scale = make_slider("Gravity (m/s²)", 0.5, 25, 9.81, 0.1)
        self.g_scale.connect("value-changed", lambda s: setattr(self, "g", s.get_value()))
        left.append(g_box)

        l_box, self.l_scale = make_slider("Length (m)", 0.2, 5, 1.5, 0.1)
        self.l_scale.connect("value-changed", lambda s: setattr(self, "length", s.get_value()))
        left.append(l_box)

        d_box, self.d_scale = make_slider("Damping", 0.0, 0.2, 0.01, 0.005)
        self.d_scale.connect("value-changed", lambda s: setattr(self, "damping", s.get_value()))
        left.append(d_box)

        a_box, self.a_scale = make_slider("Init Angle (deg)", 0, 175, 45, 1)
        left.append(a_box)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.play_btn = Gtk.Button(label="▶ Start")
        self.play_btn.connect("clicked", self.on_play)
        reset_btn = Gtk.Button(label="⟳ Reset")
        reset_btn.connect("clicked", self.on_reset)
        btn_box.append(self.play_btn); btn_box.append(reset_btn)
        left.append(btn_box)

        self.info_label = Gtk.Label(label="", xalign=0)
        self.info_label.set_wrap(True)
        left.append(self.info_label)

        period_lbl = Gtk.Label(label="", xalign=0)
        period_lbl.set_markup("<b>Theory (small angle):</b>")
        left.append(period_lbl)
        self.period_label = Gtk.Label(label="", xalign=0)
        left.append(self.period_label)

        hpaned.set_start_child(left)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.canvas = Gtk.DrawingArea()
        self.canvas.set_vexpand(True)
        self.canvas.set_draw_func(self.draw_pendulum)
        right.append(self.canvas)

        chart_frame = Gtk.Frame(label="Angle over Time")
        self.chart = Gtk.DrawingArea()
        self.chart.set_size_request(-1, 120)
        self.chart.set_draw_func(self.draw_chart)
        chart_frame.set_child(self.chart)
        right.append(chart_frame)
        hpaned.set_end_child(right)

        self.angle_history = []
        self.time_history = []
        self.update_theory()

    def on_play(self, btn):
        self.running = not self.running
        self.play_btn.set_label("⏸ Pause" if self.running else "▶ Resume")

    def on_reset(self, btn):
        self.theta = math.radians(self.a_scale.get_value())
        self.omega = 0.0
        self.time = 0.0
        self.trail = []
        self.angle_history = []
        self.time_history = []
        self.running = False
        self.play_btn.set_label("▶ Start")

    def simulation_step(self):
        if self.running:
            # Runge-Kutta 4 for pendulum
            def derivatives(theta, omega):
                alpha = -(self.g / self.length) * math.sin(theta) - self.damping * omega
                return omega, alpha

            k1_t, k1_w = derivatives(self.theta, self.omega)
            k2_t, k2_w = derivatives(self.theta + 0.5*self.dt*k1_t, self.omega + 0.5*self.dt*k1_w)
            k3_t, k3_w = derivatives(self.theta + 0.5*self.dt*k2_t, self.omega + 0.5*self.dt*k2_w)
            k4_t, k4_w = derivatives(self.theta + self.dt*k3_t, self.omega + self.dt*k3_w)

            self.theta += self.dt/6 * (k1_t + 2*k2_t + 2*k3_t + k4_t)
            self.omega += self.dt/6 * (k1_w + 2*k2_w + 2*k3_w + k4_w)
            self.time += self.dt

            self.angle_history.append(math.degrees(self.theta))
            self.time_history.append(self.time)
            if len(self.angle_history) > 500:
                self.angle_history = self.angle_history[-500:]
                self.time_history = self.time_history[-500:]

            lx = math.sin(self.theta)
            ly = math.cos(self.theta)
            self.trail.append((lx, ly))
            if len(self.trail) > self.max_trail:
                self.trail = self.trail[-self.max_trail:]

            ke = 0.5 * (self.length * self.omega)**2
            pe = self.g * self.length * (1 - math.cos(self.theta))
            te = ke + pe
            self.info_label.set_text(
                f"t = {self.time:.2f}s\nθ = {math.degrees(self.theta):.1f}°\nω = {self.omega:.2f} rad/s\n"
                f"KE = {ke:.3f} J\nPE = {pe:.3f} J\nTE = {te:.3f} J"
            )
            self.update_theory()
            self.canvas.queue_draw()
            self.chart.queue_draw()
        return True

    def update_theory(self):
        period = 2 * math.pi * math.sqrt(self.length / self.g)
        freq = 1 / period if period > 0 else 0
        self.period_label.set_text(f"T = {period:.3f} s\nf = {freq:.3f} Hz")

    def draw_pendulum(self, area, cr, w, h):
        cr.set_source_rgb(0.06, 0.06, 0.1); cr.rectangle(0, 0, w, h); cr.fill()
        pivot_x, pivot_y = w // 2, h // 4
        scale = min(w, h) * 0.35
        bob_x = pivot_x + math.sin(self.theta) * scale
        bob_y = pivot_y + math.cos(self.theta) * scale

        # Trail
        for i, (lx, ly) in enumerate(self.trail):
            alpha = i / len(self.trail) * 0.6
            cr.set_source_rgba(0.3, 0.6, 0.9, alpha)
            tx = pivot_x + lx * scale
            ty = pivot_y + ly * scale
            cr.arc(tx, ty, 3, 0, math.tau); cr.fill()

        # Rod
        cr.set_source_rgb(0.6, 0.6, 0.7); cr.set_line_width(2)
        cr.move_to(pivot_x, pivot_y); cr.line_to(bob_x, bob_y); cr.stroke()

        # Pivot
        cr.set_source_rgb(0.8, 0.8, 0.8)
        cr.arc(pivot_x, pivot_y, 6, 0, math.tau); cr.fill()

        # Bob
        r = 18
        cr.set_source_rgb(0.3, 0.6, 0.9)
        cr.arc(bob_x, bob_y, r, 0, math.tau); cr.fill()
        cr.set_source_rgb(0.5, 0.8, 1.0); cr.set_line_width(2)
        cr.arc(bob_x, bob_y, r, 0, math.tau); cr.stroke()

        # Velocity arrow
        vx = math.cos(self.theta) * self.omega * 20
        vy = -math.sin(self.theta) * self.omega * 20
        cr.set_source_rgb(0.9, 0.5, 0.2); cr.set_line_width(2)
        cr.move_to(bob_x, bob_y); cr.line_to(bob_x + vx, bob_y + vy); cr.stroke()

        # Ground line
        cr.set_source_rgba(0.4, 0.4, 0.5, 0.5); cr.set_line_width(1)
        cr.move_to(0, pivot_y); cr.line_to(w, pivot_y); cr.stroke()

    def draw_chart(self, area, cr, w, h):
        cr.set_source_rgb(0.08, 0.08, 0.12); cr.rectangle(0, 0, w, h); cr.fill()
        if len(self.angle_history) < 2:
            return
        data = self.angle_history[-300:]
        mn, mx = min(data), max(data)
        if mx == mn:
            return
        cr.set_source_rgb(0.3, 0.7, 0.9); cr.set_line_width(1.5)
        for i, v in enumerate(data):
            x = i / len(data) * w
            y = h - (v - mn) / (mx - mn) * (h - 10) - 5
            if i == 0:
                cr.move_to(x, y)
            else:
                cr.line_to(x, y)
        cr.stroke()
        cr.set_source_rgb(0.7, 0.7, 0.7); cr.set_font_size(9)
        cr.move_to(2, h - 2); cr.show_text(f"{mn:.1f}°")
        cr.move_to(2, 12); cr.show_text(f"{mx:.1f}°")
        # Zero line
        if mn <= 0 <= mx:
            yz = h - (0 - mn) / (mx - mn) * (h - 10) - 5
            cr.set_source_rgba(0.5, 0.5, 0.5, 0.5)
            cr.move_to(0, yz); cr.line_to(w, yz); cr.stroke()

class PendulumSimApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.PendulumSim")
    def do_activate(self):
        win = PendulumSimWindow(self); win.present()

def main():
    app = PendulumSimApp(); app.run(None)

if __name__ == "__main__":
    main()
