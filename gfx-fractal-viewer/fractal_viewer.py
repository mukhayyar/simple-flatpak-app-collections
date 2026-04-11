#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib
import threading

W, H = 600, 480

def mandelbrot(cx, cy, max_iter):
    zx, zy = 0.0, 0.0
    for i in range(max_iter):
        if zx*zx + zy*zy > 4.0:
            return i
        zx, zy = zx*zx - zy*zy + cx, 2*zx*zy + cy
    return max_iter

def julia(zx, zy, cx, cy, max_iter):
    for i in range(max_iter):
        if zx*zx + zy*zy > 4.0:
            return i
        zx, zy = zx*zx - zy*zy + cx, 2*zx*zy + cy
    return max_iter

SCHEMES = ["Fire", "Cool", "Pastel", "Rainbow"]

def colorize(val, max_iter, scheme):
    if val == max_iter: return (0, 0, 0)
    t = val / max_iter
    if scheme == "Fire":
        return (int(255*min(1,3*t)), int(255*max(0,min(1,3*t-1))), int(255*max(0,3*t-2)))
    elif scheme == "Cool":
        return (int(255*t), int(255*(1-t)), int(255*0.8))
    elif scheme == "Pastel":
        import math
        return (int(200+55*math.sin(t*6)), int(200+55*math.sin(t*6+2)), int(200+55*math.sin(t*6+4)))
    else:
        import colorsys
        r,g,b = colorsys.hsv_to_rgb(t, 0.8, 1.0)
        return (int(r*255), int(g*255), int(b*255))

class FractalViewerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Fractal Viewer")
        self.set_default_size(W + 40, H + 120)
        self.x_min, self.x_max = -2.5, 1.0
        self.y_min, self.y_max = -1.4, 1.4
        self.max_iter = 100
        self.mode = "mandelbrot"
        self.julia_c = (-0.7, 0.27)
        self.scheme = "Fire"
        self.pixel_data = None
        self.rendering = False
        self.build_ui()
        GLib.idle_add(self.render)

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(6); vbox.set_margin_bottom(6)
        vbox.set_margin_start(6); vbox.set_margin_end(6)
        self.set_child(vbox)

        ctrl = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.mode_combo = Gtk.ComboBoxText()
        self.mode_combo.append_text("Mandelbrot")
        self.mode_combo.append_text("Julia")
        self.mode_combo.set_active(0)
        self.mode_combo.connect("changed", self.on_mode_changed)
        ctrl.append(self.mode_combo)

        ctrl.append(Gtk.Label(label="Iterations:"))
        self.iter_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 20, 500, 10)
        self.iter_scale.set_value(100)
        self.iter_scale.set_size_request(120, -1)
        self.iter_scale.connect("value-changed", self.on_iter_changed)
        ctrl.append(self.iter_scale)

        self.scheme_combo = Gtk.ComboBoxText()
        for s in SCHEMES:
            self.scheme_combo.append_text(s)
        self.scheme_combo.set_active(0)
        self.scheme_combo.connect("changed", self.on_scheme_changed)
        ctrl.append(self.scheme_combo)

        reset_btn = Gtk.Button(label="Reset View")
        reset_btn.connect("clicked", self.on_reset)
        ctrl.append(reset_btn)
        vbox.append(ctrl)

        self.info_label = Gtk.Label(label="Click to zoom, right-click for Julia set (in Mandelbrot mode)")
        vbox.append(self.info_label)

        self.canvas = Gtk.DrawingArea()
        self.canvas.set_size_request(W, H)
        self.canvas.set_draw_func(self.on_draw)

        click = Gtk.GestureClick()
        click.set_button(0)
        click.connect("pressed", self.on_click)
        self.canvas.add_controller(click)
        vbox.append(self.canvas)

    def on_mode_changed(self, combo):
        self.mode = "julia" if combo.get_active() == 1 else "mandelbrot"
        self.on_reset(None)

    def on_iter_changed(self, scale):
        self.max_iter = int(scale.get_value())
        GLib.idle_add(self.render)

    def on_scheme_changed(self, combo):
        self.scheme = combo.get_active_text()
        GLib.idle_add(self.render)

    def on_reset(self, btn):
        self.x_min, self.x_max = -2.5, 1.0
        self.y_min, self.y_max = -1.4, 1.4
        GLib.idle_add(self.render)

    def on_click(self, gesture, n, px, py):
        button = gesture.get_current_button()
        cx = self.x_min + (px / W) * (self.x_max - self.x_min)
        cy = self.y_min + (py / H) * (self.y_max - self.y_min)
        if button == 3 and self.mode == "mandelbrot":
            self.julia_c = (cx, cy)
            self.mode_combo.set_active(1)
            return
        dx = (self.x_max - self.x_min) / 4
        dy = (self.y_max - self.y_min) / 4
        self.x_min, self.x_max = cx - dx, cx + dx
        self.y_min, self.y_max = cy - dy, cy + dy
        GLib.idle_add(self.render)

    def render(self):
        if self.rendering:
            return False
        self.rendering = True
        self.info_label.set_text("Rendering...")
        threading.Thread(target=self._render_thread, daemon=True).start()
        return False

    def _render_thread(self):
        scale = 2
        sw, sh = W // scale, H // scale
        data = bytearray(sw * sh * 3)
        xr = (self.x_max - self.x_min) / sw
        yr = (self.y_max - self.y_min) / sh
        mi = self.max_iter
        scheme = self.scheme
        jc = self.julia_c
        mode = self.mode
        for py in range(sh):
            for px in range(sw):
                cx = self.x_min + px * xr
                cy = self.y_min + py * yr
                if mode == "mandelbrot":
                    val = mandelbrot(cx, cy, mi)
                else:
                    val = julia(cx, cy, jc[0], jc[1], mi)
                r, g, b = colorize(val, mi, scheme)
                idx = (py * sw + px) * 3
                data[idx] = r; data[idx+1] = g; data[idx+2] = b
        self.pixel_data = (bytes(data), sw, sh, scale)
        GLib.idle_add(self._render_done)

    def _render_done(self):
        self.rendering = False
        self.info_label.set_text(f"Mode: {self.mode.capitalize()} | Iter: {self.max_iter} | Click to zoom")
        self.canvas.queue_draw()
        return False

    def on_draw(self, area, cr, w, h):
        cr.set_source_rgb(0, 0, 0)
        cr.rectangle(0, 0, w, h)
        cr.fill()
        if not self.pixel_data:
            return
        data, sw, sh, scale = self.pixel_data
        from gi.repository import GdkPixbuf
        pb = GdkPixbuf.Pixbuf.new_from_data(data, GdkPixbuf.Colorspace.RGB, False, 8, sw, sh, sw*3)
        scaled = pb.scale_simple(W, H, GdkPixbuf.InterpType.NEAREST)
        from gi.repository import Gdk
        Gdk.cairo_set_source_pixbuf(cr, scaled, 0, 0)
        cr.paint()

class FractalViewerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.FractalViewer")
    def do_activate(self):
        win = FractalViewerWindow(self)
        win.present()

def main():
    app = FractalViewerApp()
    app.run(None)

if __name__ == "__main__":
    main()
