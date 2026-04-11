#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import math

class FunctionPlotterWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Function Plotter")
        self.set_default_size(800, 580)
        self.functions = []
        self.x_min = -10; self.x_max = 10
        self.y_min = -10; self.y_max = 10
        self.colors = [(0.9,0.3,0.3),(0.3,0.6,0.9),(0.3,0.8,0.4),(0.9,0.7,0.2),(0.7,0.3,0.9)]
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        input_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.func_entry = Gtk.Entry()
        self.func_entry.set_placeholder_text("f(x) = e.g. sin(x)*x, x**2-4, cos(x)+sin(2*x)")
        self.func_entry.set_hexpand(True)
        self.func_entry.connect("activate", self.on_add)
        input_box.append(Gtk.Label(label="f(x) ="))
        input_box.append(self.func_entry)
        add_btn = Gtk.Button(label="Add")
        add_btn.connect("clicked", self.on_add)
        clear_btn = Gtk.Button(label="Clear All")
        clear_btn.connect("clicked", self.on_clear)
        input_box.append(add_btn); input_box.append(clear_btn)
        vbox.append(input_box)

        range_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        range_box.set_halign(Gtk.Align.CENTER)
        range_box.append(Gtk.Label(label="X:"))
        self.xmin_spin = Gtk.SpinButton.new_with_range(-1000, 0, 1); self.xmin_spin.set_value(-10)
        self.xmax_spin = Gtk.SpinButton.new_with_range(0, 1000, 1); self.xmax_spin.set_value(10)
        range_box.append(self.xmin_spin); range_box.append(Gtk.Label(label="to")); range_box.append(self.xmax_spin)
        range_box.append(Gtk.Label(label="Y:"))
        self.ymin_spin = Gtk.SpinButton.new_with_range(-1000, 0, 1); self.ymin_spin.set_value(-10)
        self.ymax_spin = Gtk.SpinButton.new_with_range(0, 1000, 1); self.ymax_spin.set_value(10)
        range_box.append(self.ymin_spin); range_box.append(Gtk.Label(label="to")); range_box.append(self.ymax_spin)
        plot_btn = Gtk.Button(label="Apply Range")
        plot_btn.connect("clicked", self.on_apply_range)
        range_box.append(plot_btn)
        vbox.append(range_box)

        self.func_list_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.func_list_box.set_wrap_mode = None
        vbox.append(self.func_list_box)

        self.canvas = Gtk.DrawingArea()
        self.canvas.set_vexpand(True)
        self.canvas.set_draw_func(self.draw_plot)
        vbox.append(self.canvas)

        self.status_label = Gtk.Label(label="Add a function to plot")
        self.status_label.set_xalign(0)
        vbox.append(self.status_label)

        self.functions.append(("sin(x)", self.colors[0]))
        self.functions.append(("cos(x)", self.colors[1]))
        self.refresh_func_list()

    def on_add(self, widget):
        expr = self.func_entry.get_text().strip()
        if not expr:
            return
        color = self.colors[len(self.functions) % len(self.colors)]
        self.functions.append((expr, color))
        self.func_entry.set_text("")
        self.refresh_func_list()
        self.canvas.queue_draw()

    def on_clear(self, btn):
        self.functions.clear()
        self.refresh_func_list()
        self.canvas.queue_draw()

    def on_apply_range(self, btn):
        self.x_min = self.xmin_spin.get_value()
        self.x_max = self.xmax_spin.get_value()
        self.y_min = self.ymin_spin.get_value()
        self.y_max = self.ymax_spin.get_value()
        self.canvas.queue_draw()

    def refresh_func_list(self):
        while self.func_list_box.get_first_child():
            self.func_list_box.remove(self.func_list_box.get_first_child())
        for i, (expr, color) in enumerate(self.functions):
            r, g, b = color
            badge = Gtk.Label(label=f" f{i+1}(x)={expr} ")
            css = Gtk.CssProvider()
            css.load_from_data(f"label {{ color: rgb({int(r*255)},{int(g*255)},{int(b*255)}); font-weight: bold; }}".encode())
            badge.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            self.func_list_box.append(badge)

    def safe_eval(self, expr, x):
        ns = {k: getattr(math, k) for k in dir(math) if not k.startswith('_')}
        ns['x'] = x
        try:
            return float(eval(expr, {"__builtins__": {}}, ns))
        except Exception:
            return float('nan')

    def draw_plot(self, area, cr, w, h):
        cr.set_source_rgb(0.07, 0.07, 0.12)
        cr.rectangle(0, 0, w, h); cr.fill()

        def tx(x): return (x - self.x_min) / (self.x_max - self.x_min) * w
        def ty(y): return h - (y - self.y_min) / (self.y_max - self.y_min) * h

        # Grid
        cr.set_source_rgba(0.3, 0.3, 0.4, 0.4)
        cr.set_line_width(0.5)
        x_step = (self.x_max - self.x_min) / 10
        for xi in range(11):
            xv = self.x_min + xi * x_step
            xp = tx(xv)
            cr.move_to(xp, 0); cr.line_to(xp, h); cr.stroke()
        y_step = (self.y_max - self.y_min) / 10
        for yi in range(11):
            yv = self.y_min + yi * y_step
            yp = ty(yv)
            cr.move_to(0, yp); cr.line_to(w, yp); cr.stroke()

        # Axes
        cr.set_source_rgb(0.6, 0.6, 0.7)
        cr.set_line_width(1.5)
        if self.x_min <= 0 <= self.x_max:
            xp = tx(0); cr.move_to(xp, 0); cr.line_to(xp, h); cr.stroke()
        if self.y_min <= 0 <= self.y_max:
            yp = ty(0); cr.move_to(0, yp); cr.line_to(w, yp); cr.stroke()

        # Axis labels
        cr.set_source_rgb(0.7, 0.7, 0.7)
        cr.set_font_size(9)
        for xi in range(11):
            xv = self.x_min + xi * x_step
            xp = tx(xv)
            yp = ty(0) if self.y_min <= 0 <= self.y_max else h - 12
            cr.move_to(xp + 2, min(yp + 12, h - 2))
            cr.show_text(f"{xv:.1f}")

        # Functions
        steps = w * 2
        for expr, color in self.functions:
            cr.set_source_rgb(*color)
            cr.set_line_width(2)
            started = False
            for i in range(int(steps)):
                x = self.x_min + (self.x_max - self.x_min) * i / steps
                y = self.safe_eval(expr, x)
                if math.isnan(y) or math.isinf(y):
                    started = False
                    continue
                xp = tx(x); yp = ty(y)
                if not started:
                    cr.move_to(xp, yp)
                    started = True
                else:
                    cr.line_to(xp, yp)
            cr.stroke()

class FunctionPlotterApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.FunctionPlotter")
    def do_activate(self):
        win = FunctionPlotterWindow(self); win.present()

def main():
    app = FunctionPlotterApp(); app.run(None)

if __name__ == "__main__":
    main()
