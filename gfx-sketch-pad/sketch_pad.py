#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GdkPixbuf
import math

W, H = 700, 500

TOOLS = ["pen", "pencil", "marker", "eraser"]
COLORS = [(0,0,0),(1,1,1),(0.8,0,0),(0,0.7,0),(0,0,0.8),(0.8,0.6,0),(0.6,0,0.6),(0,0.6,0.6)]

class SketchPadWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Sketch Pad")
        self.set_default_size(W + 160, H + 60)
        self.tool = "pen"
        self.color = (0, 0, 0)
        self.brush_size = 3
        self.layers = [[] for _ in range(3)]
        self.active_layer = 0
        self.current_path = None
        self.undo_history = [[] for _ in range(3)]
        self.build_ui()

    def build_ui(self):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        hbox.set_margin_top(4); hbox.set_margin_start(4); hbox.set_margin_end(4); hbox.set_margin_bottom(4)
        self.set_child(hbox)

        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        sidebar.set_size_request(140, -1)

        sidebar.append(Gtk.Label(label="Tools"))
        self.tool_btns = {}
        for t in TOOLS:
            btn = Gtk.ToggleButton(label=t.capitalize())
            btn.set_active(t == "pen")
            btn.connect("toggled", self.on_tool, t)
            self.tool_btns[t] = btn
            sidebar.append(btn)

        sidebar.append(Gtk.Label(label="Size"))
        size_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1, 30, 1)
        size_scale.set_value(3)
        size_scale.connect("value-changed", lambda s: setattr(self, 'brush_size', s.get_value()))
        sidebar.append(size_scale)

        sidebar.append(Gtk.Label(label="Color"))
        pal_grid = Gtk.Grid(); pal_grid.set_column_spacing(2); pal_grid.set_row_spacing(2)
        for i, c in enumerate(COLORS):
            da = Gtk.DrawingArea(); da.set_size_request(26, 26)
            da.set_draw_func(lambda a, cr, w, h, col=c: (cr.set_source_rgb(*col), cr.rectangle(0,0,w,h), cr.fill()))
            ctrl = Gtk.GestureClick()
            ctrl.connect("pressed", lambda g, n, x, y, col=c: setattr(self, 'color', col) or self.cur_swatch.queue_draw())
            da.add_controller(ctrl)
            pal_grid.attach(da, i%4, i//4, 1, 1)
        sidebar.append(pal_grid)

        self.cur_swatch = Gtk.DrawingArea(); self.cur_swatch.set_size_request(40, 30)
        self.cur_swatch.set_draw_func(lambda a, cr, w, h: (cr.set_source_rgb(*self.color), cr.rectangle(0,0,w,h), cr.fill()))
        sidebar.append(self.cur_swatch)

        sidebar.append(Gtk.Label(label="Layer"))
        for i in range(3):
            btn = Gtk.ToggleButton(label=f"Layer {i+1}")
            btn.set_active(i == 0)
            btn.connect("toggled", self.on_layer, i)
            sidebar.append(btn)

        undo_btn = Gtk.Button(label="Undo"); undo_btn.connect("clicked", self.on_undo)
        clear_btn = Gtk.Button(label="Clear Layer"); clear_btn.connect("clicked", self.on_clear)
        save_btn = Gtk.Button(label="Export PNG"); save_btn.connect("clicked", self.on_save)
        sidebar.append(undo_btn); sidebar.append(clear_btn); sidebar.append(save_btn)
        hbox.append(sidebar)

        self.canvas = Gtk.DrawingArea()
        self.canvas.set_size_request(W, H)
        self.canvas.set_draw_func(self.on_draw)
        self.canvas.set_hexpand(True); self.canvas.set_vexpand(True)

        drag = Gtk.GestureDrag()
        drag.connect("drag-begin", self.on_drag_begin)
        drag.connect("drag-update", self.on_drag_update)
        drag.connect("drag-end", self.on_drag_end)
        self.canvas.add_controller(drag)
        hbox.append(self.canvas)

    def on_tool(self, btn, tool):
        if btn.get_active():
            self.tool = tool
            for t, b in self.tool_btns.items():
                if t != tool: b.set_active(False)

    def on_layer(self, btn, idx):
        if btn.get_active():
            self.active_layer = idx

    def on_drag_begin(self, g, sx, sy):
        self.undo_history[self.active_layer] = [s.copy() if isinstance(s, dict) else s for s in self.layers[self.active_layer]]
        self.current_path = {"tool": self.tool, "color": self.color,
                             "size": self.brush_size, "points": [(sx, sy)]}

    def on_drag_update(self, g, dx, dy):
        if self.current_path is None: return
        sx, sy = g.get_start_point().x, g.get_start_point().y
        cx, cy = sx + dx, sy + dy
        self.current_path["points"].append((cx, cy))
        self.canvas.queue_draw()

    def on_drag_end(self, g, dx, dy):
        if self.current_path:
            self.layers[self.active_layer].append(self.current_path)
            self.current_path = None
            self.canvas.queue_draw()

    def on_undo(self, btn):
        if self.layers[self.active_layer]:
            self.layers[self.active_layer].pop()
            self.canvas.queue_draw()

    def on_clear(self, btn):
        self.layers[self.active_layer] = []
        self.canvas.queue_draw()

    def on_save(self, btn):
        dialog = Gtk.FileDialog(); dialog.save(self, None, self.do_save)

    def do_save(self, dialog, result):
        try:
            f = dialog.save_finish(result)
            if f:
                data = bytearray([255] * W * H * 3)
                pb = GdkPixbuf.Pixbuf.new_from_data(bytes(data), GdkPixbuf.Colorspace.RGB, False, 8, W, H, W*3)
                path = f.get_path()
                if not path.endswith(".png"): path += ".png"
                pb.savev(path, "png", [], [])
        except Exception:
            pass

    def draw_path(self, cr, path):
        pts = path["points"]
        if len(pts) < 2: return
        r, g, b = path["color"]
        if path["tool"] == "eraser":
            cr.set_source_rgb(1, 1, 1)
            cr.set_line_width(path["size"] * 4)
        elif path["tool"] == "marker":
            cr.set_source_rgba(r, g, b, 0.5)
            cr.set_line_width(path["size"] * 4)
        elif path["tool"] == "pencil":
            cr.set_source_rgba(r, g, b, 0.7)
            cr.set_line_width(max(1, path["size"] * 0.7))
        else:
            cr.set_source_rgb(r, g, b)
            cr.set_line_width(path["size"])
        cr.set_line_cap(1)  # round
        cr.set_line_join(1)  # round
        cr.move_to(*pts[0])
        if len(pts) > 2:
            for i in range(1, len(pts) - 1):
                mx = (pts[i][0] + pts[i+1][0]) / 2
                my = (pts[i][1] + pts[i+1][1]) / 2
                cr.curve_to(pts[i][0], pts[i][1], pts[i][0], pts[i][1], mx, my)
        cr.line_to(*pts[-1])
        cr.stroke()

    def on_draw(self, area, cr, w, h):
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(0, 0, w, h)
        cr.fill()
        for layer in self.layers:
            for path in layer:
                self.draw_path(cr, path)
        if self.current_path:
            self.draw_path(cr, self.current_path)

class SketchPadApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.SketchPad")
    def do_activate(self):
        win = SketchPadWindow(self)
        win.present()

def main():
    app = SketchPadApp()
    app.run(None)

if __name__ == "__main__":
    main()
