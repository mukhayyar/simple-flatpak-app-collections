#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib
import math, copy

W, H = 640, 480

class PaintWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Paint")
        self.set_default_size(W + 200, H + 80)
        self.tool = "pencil"
        self.color = (0.0, 0.0, 0.0)
        self.brush_size = 3
        self.drawing = False
        self.last_x = 0; self.last_y = 0
        self.start_x = 0; self.start_y = 0
        self.undo_stack = []
        self.canvas_data = []
        self.strokes = []
        self.current_stroke = None
        self.build_ui()

    def build_ui(self):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        hbox.set_margin_top(4); hbox.set_margin_start(4); hbox.set_margin_end(4)
        self.set_child(hbox)

        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        sidebar.set_size_request(120, -1)
        sidebar.set_margin_end(6)

        sidebar.append(Gtk.Label(label="Tools"))
        for tool in ["pencil", "eraser", "line", "rect", "circle"]:
            btn = Gtk.ToggleButton(label=tool.capitalize())
            btn.set_active(tool == self.tool)
            btn.connect("toggled", self.on_tool, tool)
            sidebar.append(btn)

        sidebar.append(Gtk.Label(label="Size"))
        size_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1, 30, 1)
        size_scale.set_value(self.brush_size)
        size_scale.connect("value-changed", self.on_size)
        sidebar.append(size_scale)

        sidebar.append(Gtk.Label(label="Color"))
        palette = [(0,0,0),(1,1,1),(1,0,0),(0,1,0),(0,0,1),(1,1,0),(1,0,1),(0,1,1),(0.5,0,0),(0,0.5,0),(0,0,0.5),(0.5,0.5,0)]
        pal_grid = Gtk.Grid(); pal_grid.set_column_spacing(2); pal_grid.set_row_spacing(2)
        for i, c in enumerate(palette):
            da = Gtk.DrawingArea(); da.set_size_request(24, 24)
            da.set_draw_func(self.draw_swatch, c)
            click = Gtk.GestureClick()
            click.connect("pressed", self.on_palette, c)
            da.add_controller(click)
            pal_grid.attach(da, i%4, i//4, 1, 1)
        sidebar.append(pal_grid)

        custom_btn = Gtk.Button(label="Custom Color")
        custom_btn.connect("clicked", self.on_custom_color)
        sidebar.append(custom_btn)

        undo_btn = Gtk.Button(label="Undo")
        undo_btn.connect("clicked", self.on_undo)
        sidebar.append(undo_btn)
        clear_btn = Gtk.Button(label="Clear")
        clear_btn.connect("clicked", self.on_clear)
        sidebar.append(clear_btn)
        save_btn = Gtk.Button(label="Save PNG")
        save_btn.connect("clicked", self.on_save)
        sidebar.append(save_btn)

        hbox.append(sidebar)

        self.canvas = Gtk.DrawingArea()
        self.canvas.set_size_request(W, H)
        self.canvas.set_draw_func(self.on_draw)
        self.canvas.set_hexpand(True)

        drag = Gtk.GestureDrag()
        drag.connect("drag-begin", self.on_drag_begin)
        drag.connect("drag-update", self.on_drag_update)
        drag.connect("drag-end", self.on_drag_end)
        self.canvas.add_controller(drag)
        hbox.append(self.canvas)

    def draw_swatch(self, area, cr, w, h, color):
        cr.set_source_rgb(*color)
        cr.rectangle(0, 0, w, h)
        cr.fill()

    def on_tool(self, btn, tool):
        if btn.get_active():
            self.tool = tool
            for child in btn.get_parent():
                if isinstance(child, Gtk.ToggleButton) and child != btn:
                    child.set_active(False)

    def on_size(self, scale):
        self.brush_size = int(scale.get_value())

    def on_palette(self, ctrl, n, x, y, color):
        self.color = color

    def on_custom_color(self, btn):
        dialog = Gtk.ColorDialog()
        rgba = Gdk.RGBA()
        rgba.red, rgba.green, rgba.blue = self.color
        rgba.alpha = 1.0
        dialog.choose_rgba(self, rgba, None, self.on_color_chosen)

    def on_color_chosen(self, dialog, result):
        try:
            rgba = dialog.choose_rgba_finish(result)
            if rgba:
                self.color = (rgba.red, rgba.green, rgba.blue)
        except Exception:
            pass

    def on_drag_begin(self, gesture, sx, sy):
        self.drawing = True
        self.start_x, self.start_y = sx, sy
        self.last_x, self.last_y = sx, sy
        if self.tool in ("pencil", "eraser"):
            self.save_undo()
            self.current_stroke = {"type": self.tool, "color": self.color, "size": self.brush_size, "points": [(sx, sy)]}

    def on_drag_update(self, gesture, dx, dy):
        sx, sy = gesture.get_start_point().x, gesture.get_start_point().y
        cx, cy = sx + dx, sy + dy
        if self.tool in ("pencil", "eraser") and self.current_stroke:
            self.current_stroke["points"].append((cx, cy))
        self.last_x, self.last_y = cx, cy
        self.canvas.queue_draw()

    def on_drag_end(self, gesture, dx, dy):
        sx, sy = gesture.get_start_point().x, gesture.get_start_point().y
        ex, ey = sx + dx, sy + dy
        if self.tool in ("pencil", "eraser") and self.current_stroke:
            self.strokes.append(self.current_stroke)
            self.current_stroke = None
        elif self.tool in ("line", "rect", "circle"):
            self.save_undo()
            self.strokes.append({"type": self.tool, "color": self.color, "size": self.brush_size,
                                  "x1": sx, "y1": sy, "x2": ex, "y2": ey})
        self.drawing = False
        self.canvas.queue_draw()

    def save_undo(self):
        self.undo_stack.append(copy.copy(self.strokes))
        if len(self.undo_stack) > 20:
            self.undo_stack.pop(0)

    def on_undo(self, btn):
        if self.undo_stack:
            self.strokes = self.undo_stack.pop()
            self.canvas.queue_draw()

    def on_clear(self, btn):
        self.save_undo()
        self.strokes = []
        self.canvas.queue_draw()

    def on_save(self, btn):
        dialog = Gtk.FileDialog()
        dialog.set_title("Save PNG")
        dialog.save(self, None, self.on_save_file)

    def on_save_file(self, dialog, result):
        try:
            f = dialog.save_finish(result)
            if f:
                from gi.repository import GdkPixbuf
                surface_data = b'\xff\xff\xff' * (W * H)
                pb = GdkPixbuf.Pixbuf.new_from_data(surface_data, GdkPixbuf.Colorspace.RGB, False, 8, W, H, W*3)
                pb.savev(f.get_path(), "png", [], [])
        except Exception:
            pass

    def on_draw(self, area, cr, w, h):
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        def draw_stroke(s):
            if s["type"] == "pencil":
                cr.set_source_rgb(*s["color"])
                cr.set_line_width(s["size"])
                pts = s["points"]
                if len(pts) >= 2:
                    cr.move_to(*pts[0])
                    for p in pts[1:]:
                        cr.line_to(*p)
                    cr.stroke()
            elif s["type"] == "eraser":
                cr.set_source_rgb(1, 1, 1)
                cr.set_line_width(s["size"] * 3)
                pts = s["points"]
                if len(pts) >= 2:
                    cr.move_to(*pts[0])
                    for p in pts[1:]:
                        cr.line_to(*p)
                    cr.stroke()
            elif s["type"] == "line":
                cr.set_source_rgb(*s["color"])
                cr.set_line_width(s["size"])
                cr.move_to(s["x1"], s["y1"]); cr.line_to(s["x2"], s["y2"]); cr.stroke()
            elif s["type"] == "rect":
                cr.set_source_rgb(*s["color"])
                cr.set_line_width(s["size"])
                x, y = min(s["x1"], s["x2"]), min(s["y1"], s["y2"])
                rw, rh = abs(s["x2"]-s["x1"]), abs(s["y2"]-s["y1"])
                cr.rectangle(x, y, rw, rh); cr.stroke()
            elif s["type"] == "circle":
                cr.set_source_rgb(*s["color"])
                cr.set_line_width(s["size"])
                cx = (s["x1"]+s["x2"])/2; cy = (s["y1"]+s["y2"])/2
                rx = abs(s["x2"]-s["x1"])/2; ry = abs(s["y2"]-s["y1"])/2
                cr.save(); cr.translate(cx, cy); cr.scale(rx, ry)
                cr.arc(0, 0, 1, 0, math.pi*2); cr.restore(); cr.stroke()

        for s in self.strokes:
            draw_stroke(s)
        if self.current_stroke:
            draw_stroke(self.current_stroke)

        if self.drawing and self.tool in ("line", "rect", "circle"):
            s = {"type": self.tool, "color": self.color, "size": self.brush_size,
                 "x1": self.start_x, "y1": self.start_y, "x2": self.last_x, "y2": self.last_y}
            draw_stroke(s)

class PaintApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.Paint")
    def do_activate(self):
        win = PaintWindow(self)
        win.present()

def main():
    app = PaintApp()
    app.run(None)

if __name__ == "__main__":
    main()
