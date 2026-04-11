#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GdkPixbuf
import math

class PixelEditorWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Pixel Editor")
        self.set_default_size(700, 600)
        self.canvas_w = 16; self.canvas_h = 16
        self.zoom = 20
        self.color = (0, 0, 0, 255)
        self.tool = "pencil"
        self.pixels = [[(255,255,255,255)] * self.canvas_w for _ in range(self.canvas_h)]
        self.palette = [
            (0,0,0,255), (255,255,255,255), (255,0,0,255), (0,255,0,255),
            (0,0,255,255), (255,255,0,255), (255,0,255,255), (0,255,255,255),
            (128,0,0,255), (0,128,0,255), (0,0,128,255), (128,128,0,255),
            (128,0,128,255), (0,128,128,255), (128,128,128,255), (192,192,192,255),
        ]
        self.build_ui()

    def build_ui(self):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hbox.set_margin_top(6); hbox.set_margin_start(6); hbox.set_margin_end(6); hbox.set_margin_bottom(6)
        self.set_child(hbox)

        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        sidebar.set_size_request(130, -1)

        size_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        size_box.append(Gtk.Label(label="W:"))
        self.w_spin = Gtk.SpinButton.new_with_range(4, 64, 1)
        self.w_spin.set_value(16); size_box.append(self.w_spin)
        sidebar.append(size_box)
        size_box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        size_box2.append(Gtk.Label(label="H:"))
        self.h_spin = Gtk.SpinButton.new_with_range(4, 64, 1)
        self.h_spin.set_value(16); size_box2.append(self.h_spin)
        sidebar.append(size_box2)
        resize_btn = Gtk.Button(label="Resize")
        resize_btn.connect("clicked", self.on_resize)
        sidebar.append(resize_btn)

        sidebar.append(Gtk.Label(label="Tool"))
        for tool in ["pencil", "eraser", "fill"]:
            btn = Gtk.ToggleButton(label=tool.capitalize())
            btn.set_active(tool == "pencil")
            btn.connect("toggled", self.on_tool_toggle, tool)
            sidebar.append(btn)

        sidebar.append(Gtk.Label(label="Zoom"))
        zoom_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 4, 40, 2)
        zoom_scale.set_value(self.zoom)
        zoom_scale.connect("value-changed", lambda s: setattr(self, 'zoom', int(s.get_value())) or self.canvas.queue_draw())
        sidebar.append(zoom_scale)

        sidebar.append(Gtk.Label(label="Palette"))
        pal_grid = Gtk.Grid(); pal_grid.set_column_spacing(2); pal_grid.set_row_spacing(2)
        for i, c in enumerate(self.palette):
            da = Gtk.DrawingArea(); da.set_size_request(24, 24)
            da.set_draw_func(self._draw_swatch, c)
            ctrl = Gtk.GestureClick()
            ctrl.connect("pressed", self._pick_palette, c)
            da.add_controller(ctrl)
            pal_grid.attach(da, i%4, i//4, 1, 1)
        sidebar.append(pal_grid)

        self.cur_swatch = Gtk.DrawingArea(); self.cur_swatch.set_size_request(40, 30)
        self.cur_swatch.set_draw_func(self._draw_cur_color)
        sidebar.append(self.cur_swatch)

        export_btn = Gtk.Button(label="Export PNG")
        export_btn.connect("clicked", self.on_export)
        sidebar.append(export_btn)
        clear_btn = Gtk.Button(label="Clear")
        clear_btn.connect("clicked", self.on_clear)
        sidebar.append(clear_btn)
        hbox.append(sidebar)

        self.canvas = Gtk.DrawingArea()
        cw = self.canvas_w * self.zoom
        ch = self.canvas_h * self.zoom
        self.canvas.set_size_request(cw, ch)
        self.canvas.set_draw_func(self.on_draw)
        drag = Gtk.GestureDrag()
        drag.connect("drag-begin", self.on_paint)
        drag.connect("drag-update", lambda g, dx, dy: self._paint_at(*self._get_cell(g, dx, dy)))
        self.canvas.add_controller(drag)
        hbox.append(self.canvas)

    def _draw_swatch(self, area, cr, w, h, c):
        cr.set_source_rgba(c[0]/255, c[1]/255, c[2]/255, c[3]/255)
        cr.rectangle(0,0,w,h); cr.fill()

    def _draw_cur_color(self, area, cr, w, h):
        c = self.color
        cr.set_source_rgba(c[0]/255, c[1]/255, c[2]/255, c[3]/255)
        cr.rectangle(0,0,w,h); cr.fill()

    def _pick_palette(self, ctrl, n, x, y, c):
        self.color = c
        self.cur_swatch.queue_draw()

    def on_tool_toggle(self, btn, tool):
        if btn.get_active():
            self.tool = tool

    def on_resize(self, btn):
        nw = int(self.w_spin.get_value())
        nh = int(self.h_spin.get_value())
        new_pixels = [[(255,255,255,255)] * nw for _ in range(nh)]
        for r in range(min(nh, self.canvas_h)):
            for c in range(min(nw, self.canvas_w)):
                new_pixels[r][c] = self.pixels[r][c]
        self.canvas_w = nw; self.canvas_h = nh
        self.pixels = new_pixels
        self.canvas.set_size_request(nw * self.zoom, nh * self.zoom)
        self.canvas.queue_draw()

    def _get_cell(self, gesture, dx=0, dy=0):
        sx, sy = gesture.get_start_point().x, gesture.get_start_point().y
        return int((sx+dx) / self.zoom), int((sy+dy) / self.zoom)

    def on_paint(self, gesture, sx, sy):
        c, r = int(sx / self.zoom), int(sy / self.zoom)
        self._paint_at(c, r)

    def _paint_at(self, c, r):
        if 0 <= r < self.canvas_h and 0 <= c < self.canvas_w:
            if self.tool == "eraser":
                self.pixels[r][c] = (255, 255, 255, 255)
            elif self.tool == "fill":
                self._flood_fill(c, r, self.pixels[r][c], self.color)
            else:
                self.pixels[r][c] = self.color
            self.canvas.queue_draw()

    def _flood_fill(self, c, r, old, new):
        if old == new: return
        stack = [(c, r)]
        while stack:
            cc, rr = stack.pop()
            if not (0 <= rr < self.canvas_h and 0 <= cc < self.canvas_w): continue
            if self.pixels[rr][cc] != old: continue
            self.pixels[rr][cc] = new
            stack.extend([(cc+1,rr),(cc-1,rr),(cc,rr+1),(cc,rr-1)])

    def on_clear(self, btn):
        self.pixels = [[(255,255,255,255)] * self.canvas_w for _ in range(self.canvas_h)]
        self.canvas.queue_draw()

    def on_export(self, btn):
        dialog = Gtk.FileDialog()
        dialog.save(self, None, self.on_save_file)

    def on_save_file(self, dialog, result):
        try:
            f = dialog.save_finish(result)
            if f:
                data = bytearray()
                for row in self.pixels:
                    for r, g, b, a in row:
                        data.extend([r, g, b, a])
                pb = GdkPixbuf.Pixbuf.new_from_data(bytes(data), GdkPixbuf.Colorspace.RGB, True, 8, self.canvas_w, self.canvas_h, self.canvas_w*4)
                path = f.get_path()
                if not path.endswith(".png"): path += ".png"
                pb.savev(path, "png", [], [])
        except Exception as e:
            print(e)

    def on_draw(self, area, cr, w, h):
        z = self.zoom
        for r in range(self.canvas_h):
            for c in range(self.canvas_w):
                px = self.pixels[r][c]
                cr.set_source_rgba(px[0]/255, px[1]/255, px[2]/255, px[3]/255)
                cr.rectangle(c*z, r*z, z, z); cr.fill()
        cr.set_source_rgba(0.5, 0.5, 0.5, 0.5)
        cr.set_line_width(0.5)
        for c in range(self.canvas_w+1):
            cr.move_to(c*z, 0); cr.line_to(c*z, self.canvas_h*z)
        for r in range(self.canvas_h+1):
            cr.move_to(0, r*z); cr.line_to(self.canvas_w*z, r*z)
        cr.stroke()

class PixelEditorApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.PixelEditor")
    def do_activate(self):
        win = PixelEditorWindow(self)
        win.present()

def main():
    app = PixelEditorApp()
    app.run(None)

if __name__ == "__main__":
    main()
