#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Rsvg', '2.0')
from gi.repository import Gtk, Gdk, Rsvg
import os

class SvgViewerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("SVG Viewer")
        self.set_default_size(1000, 700)
        self.handle = None
        self.svg_text = ""
        self.zoom = 1.0
        self.offset_x = 0; self.offset_y = 0
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        vbox.set_margin_top(4); vbox.set_margin_bottom(4)
        vbox.set_margin_start(4); vbox.set_margin_end(4)
        self.set_child(vbox)

        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        open_btn = Gtk.Button(label="Open SVG")
        open_btn.connect("clicked", self.on_open)
        toolbar.append(open_btn)
        for label, func in [("Zoom In", self.zoom_in), ("Zoom Out", self.zoom_out), ("Reset", self.zoom_reset)]:
            btn = Gtk.Button(label=label); btn.connect("clicked", func); toolbar.append(btn)
        self.info_label = Gtk.Label(label="Open an SVG file")
        self.info_label.set_hexpand(True)
        toolbar.append(self.info_label)
        vbox.append(toolbar)

        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_vexpand(True)

        canvas_frame = Gtk.Frame(label="Preview")
        canvas_scroll = Gtk.ScrolledWindow()
        self.canvas = Gtk.DrawingArea()
        self.canvas.set_size_request(600, 500)
        self.canvas.set_draw_func(self.on_draw)
        canvas_scroll.set_child(self.canvas)
        canvas_frame.set_child(canvas_scroll)
        paned.set_start_child(canvas_frame)

        right_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        right_vbox.set_size_request(380, -1)

        src_frame = Gtk.Frame(label="SVG Source")
        src_scroll = Gtk.ScrolledWindow()
        src_scroll.set_vexpand(True)
        self.source_view = Gtk.TextView()
        self.source_view.set_monospace(True)
        self.source_view.set_wrap_mode(Gtk.WrapMode.NONE)
        src_scroll.set_child(self.source_view)
        src_frame.set_child(src_scroll)
        right_vbox.append(src_frame)

        paned.set_end_child(right_vbox)
        vbox.append(paned)

    def on_open(self, btn):
        dialog = Gtk.FileDialog(); dialog.set_title("Open SVG")
        dialog.open(self, None, self.on_file_chosen)

    def on_file_chosen(self, dialog, result):
        try:
            f = dialog.open_finish(result)
            if f:
                path = f.get_path()
                with open(path, "r", errors="replace") as fp:
                    self.svg_text = fp.read()
                self.handle = Rsvg.Handle.new_from_file(path)
                dim = self.handle.get_intrinsic_size_in_pixels()
                w = dim.out_width if hasattr(dim, 'out_width') else 400
                h = dim.out_height if hasattr(dim, 'out_height') else 400
                self.canvas.set_size_request(int(w * self.zoom), int(h * self.zoom))
                name = os.path.basename(path)
                self.info_label.set_text(f"{name} | {w:.0f}×{h:.0f}px")
                self.set_title(f"SVG Viewer — {name}")
                self.source_view.get_buffer().set_text(self.svg_text)
                self.canvas.queue_draw()
        except Exception as e:
            self.info_label.set_text(f"Error: {e}")

    def zoom_in(self, *a): self.zoom = min(10.0, self.zoom * 1.25); self.canvas.queue_draw()
    def zoom_out(self, *a): self.zoom = max(0.1, self.zoom / 1.25); self.canvas.queue_draw()
    def zoom_reset(self, *a): self.zoom = 1.0; self.canvas.queue_draw()

    def on_draw(self, area, cr, w, h):
        cr.set_source_rgb(0.9, 0.9, 0.9)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        for i in range(0, w, 20):
            for j in range(0, h, 20):
                if (i//20 + j//20) % 2 == 0:
                    cr.set_source_rgb(0.8, 0.8, 0.8)
                    cr.rectangle(i, j, 20, 20)
                    cr.fill()

        if not self.handle: return
        cr.save()
        cr.scale(self.zoom, self.zoom)
        viewport = Rsvg.Rectangle()
        viewport.x = 0; viewport.y = 0
        try:
            dim = self.handle.get_intrinsic_size_in_pixels()
            viewport.width = dim.out_width
            viewport.height = dim.out_height
        except Exception:
            viewport.width = 400; viewport.height = 400
        try:
            self.handle.render_document(cr, viewport)
        except Exception:
            try:
                self.handle.render_cairo(cr)
            except Exception:
                pass
        cr.restore()

class SvgViewerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.SvgViewer")
    def do_activate(self):
        win = SvgViewerWindow(self)
        win.present()

def main():
    app = SvgViewerApp()
    app.run(None)

if __name__ == "__main__":
    main()
