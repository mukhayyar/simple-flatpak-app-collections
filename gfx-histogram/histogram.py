#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GdkPixbuf

class HistogramWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Image Histogram")
        self.set_default_size(900, 700)
        self.pixbuf = None
        self.hist_r = [0]*256; self.hist_g = [0]*256; self.hist_b = [0]*256
        self.stats = {}
        self.brightness = 0; self.contrast = 1.0
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(6); vbox.set_margin_bottom(6)
        vbox.set_margin_start(6); vbox.set_margin_end(6)
        self.set_child(vbox)

        ctrl = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        open_btn = Gtk.Button(label="Open Image")
        open_btn.connect("clicked", self.on_open)
        ctrl.append(open_btn)
        ctrl.append(Gtk.Label(label="Brightness:"))
        self.bright_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, -100, 100, 1)
        self.bright_scale.set_value(0); self.bright_scale.set_size_request(120, -1)
        self.bright_scale.connect("value-changed", self.on_adjust)
        ctrl.append(self.bright_scale)
        ctrl.append(Gtk.Label(label="Contrast:"))
        self.contrast_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.1, 3.0, 0.1)
        self.contrast_scale.set_value(1.0); self.contrast_scale.set_size_request(120, -1)
        self.contrast_scale.connect("value-changed", self.on_adjust)
        ctrl.append(self.contrast_scale)
        vbox.append(ctrl)

        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_vexpand(True)

        img_frame = Gtk.Frame(label="Image")
        scroll = Gtk.ScrolledWindow()
        self.picture = Gtk.Picture()
        self.picture.set_can_shrink(True)
        scroll.set_child(self.picture)
        img_frame.set_child(scroll)
        paned.set_start_child(img_frame)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

        hist_frame = Gtk.Frame(label="RGB Histogram")
        self.hist_area = Gtk.DrawingArea()
        self.hist_area.set_size_request(400, 200)
        self.hist_area.set_draw_func(self.on_draw_hist)
        hist_frame.set_child(self.hist_area)
        right.append(hist_frame)

        stats_frame = Gtk.Frame(label="Statistics")
        stats_scroll = Gtk.ScrolledWindow()
        stats_scroll.set_vexpand(True)
        self.stats_view = Gtk.TextView()
        self.stats_view.set_editable(False); self.stats_view.set_monospace(True)
        stats_scroll.set_child(self.stats_view)
        stats_frame.set_child(stats_scroll)
        right.append(stats_frame)

        paned.set_end_child(right)
        vbox.append(paned)

    def on_open(self, btn):
        dialog = Gtk.FileDialog()
        dialog.open(self, None, self.on_file_chosen)

    def on_file_chosen(self, dialog, result):
        try:
            f = dialog.open_finish(result)
            if f:
                self.pixbuf = GdkPixbuf.Pixbuf.new_from_file(f.get_path())
                self.apply_adjustments()
        except Exception as e:
            pass

    def on_adjust(self, *args):
        self.brightness = int(self.bright_scale.get_value())
        self.contrast = self.contrast_scale.get_value()
        if self.pixbuf:
            self.apply_adjustments()

    def apply_adjustments(self):
        pb = self.pixbuf
        self.picture.set_pixbuf(pb)
        self.compute_histogram(pb)
        self.hist_area.queue_draw()

    def compute_histogram(self, pb):
        n_channels = pb.get_n_channels()
        rowstride = pb.get_rowstride()
        data = pb.get_pixels()
        w, h = pb.get_width(), pb.get_height()
        self.hist_r = [0]*256; self.hist_g = [0]*256; self.hist_b = [0]*256
        for row in range(h):
            for col in range(w):
                base = row * rowstride + col * n_channels
                r = data[base]; g = data[base+1]; b = data[base+2]
                self.hist_r[r] += 1
                self.hist_g[g] += 1
                self.hist_b[b] += 1
        n = w * h
        def stats_for(channel):
            total = sum(i * v for i, v in enumerate(channel))
            mean = total / n
            var = sum((i - mean)**2 * v for i, v in enumerate(channel)) / n
            mn = next(i for i, v in enumerate(channel) if v > 0)
            mx = 255 - next(i for i, v in enumerate(reversed(channel)) if v > 0)
            return {"min": mn, "max": mx, "mean": f"{mean:.1f}", "std": f"{var**0.5:.1f}"}
        self.stats = {
            "R": stats_for(self.hist_r),
            "G": stats_for(self.hist_g),
            "B": stats_for(self.hist_b),
            "Size": f"{w}×{h}",
        }
        lines = [f"Image: {w}×{h} ({w*h} pixels)", ""]
        for ch in ["R", "G", "B"]:
            s = self.stats[ch]
            lines.append(f"Channel {ch}: min={s['min']} max={s['max']} mean={s['mean']} std={s['std']}")
        self.stats_view.get_buffer().set_text("\n".join(lines))

    def on_draw_hist(self, area, cr, w, h):
        cr.set_source_rgb(0.1, 0.1, 0.1)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        for hist, color in [(self.hist_r, (0.8,0.2,0.2,0.6)),
                             (self.hist_g, (0.2,0.8,0.2,0.6)),
                             (self.hist_b, (0.2,0.2,0.8,0.6))]:
            if not any(hist): continue
            mx = max(hist)
            cr.set_source_rgba(*color)
            bar_w = w / 256
            for i, val in enumerate(hist):
                bh = (val / mx) * (h - 20)
                cr.rectangle(i * bar_w, h - 20 - bh, bar_w, bh)
            cr.fill()

class HistogramApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.Histogram")
    def do_activate(self):
        win = HistogramWindow(self)
        win.present()

def main():
    app = HistogramApp()
    app.run(None)

if __name__ == "__main__":
    main()
