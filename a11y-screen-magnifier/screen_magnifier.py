#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk
import math

class ScreenMagnifierWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Screen Magnifier")
        self.set_default_size(700, 560)
        self.zoom = 2.0
        self.lens_size = 200
        self.lens_x = 200.0
        self.lens_y = 200.0
        self.color_filter = "none"
        self.show_crosshair = True
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Screen Magnifier", css_classes=["title"]))

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        controls.set_halign(Gtk.Align.CENTER)

        controls.append(Gtk.Label(label="Zoom:"))
        zoom_spin = Gtk.SpinButton.new_with_range(1.0, 8.0, 0.25)
        zoom_spin.set_value(self.zoom)
        zoom_spin.connect("value-changed", lambda s: self.set_zoom(s.get_value()))
        controls.append(zoom_spin)

        controls.append(Gtk.Label(label="Lens size:"))
        size_spin = Gtk.SpinButton.new_with_range(80, 400, 10)
        size_spin.set_value(self.lens_size)
        size_spin.connect("value-changed", lambda s: self.set_lens_size(int(s.get_value())))
        controls.append(size_spin)

        ch_btn = Gtk.ToggleButton(label="Crosshair")
        ch_btn.set_active(True)
        ch_btn.connect("toggled", lambda b: self.toggle_crosshair(b.get_active()))
        controls.append(ch_btn)
        vbox.append(controls)

        filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        filter_box.set_halign(Gtk.Align.CENTER)
        filter_box.append(Gtk.Label(label="Filter:"))
        for label, key in [("None", "none"), ("Invert", "invert"), ("Grayscale", "gray"),
                           ("Red-boost", "red"), ("High Contrast", "hc")]:
            btn = Gtk.ToggleButton(label=label)
            btn.set_active(key == "none")
            btn.connect("toggled", self.on_filter, key)
            filter_box.append(btn)
            btn._filter_key = key
        self.filter_buttons = filter_box
        vbox.append(filter_box)

        demo_frame = Gtk.Frame(label="Magnifier Demo Canvas (move mouse here)")
        self.canvas = Gtk.DrawingArea()
        self.canvas.set_vexpand(True)
        self.canvas.set_draw_func(self.draw_canvas)
        demo_frame.set_child(self.canvas)
        vbox.append(demo_frame)

        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self.on_motion)
        self.canvas.add_controller(motion)

        info_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        info_box.set_halign(Gtk.Align.CENTER)
        self.pos_label = Gtk.Label(label="Position: --")
        self.zoom_label = Gtk.Label(label=f"Zoom: {self.zoom}x")
        info_box.append(self.pos_label)
        info_box.append(self.zoom_label)
        vbox.append(info_box)

        note = Gtk.Label(label="Note: Full screen capture requires platform accessibility or screenshot API.\nThis demo shows a lens simulation with generated content.", xalign=0)
        note.set_css_classes(["dim-label"])
        note.set_wrap(True)
        vbox.append(note)

        gsettings_frame = Gtk.Frame(label="GNOME Accessibility Settings")
        gs_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        gs_box.set_margin_top(6); gs_box.set_margin_start(8); gs_box.set_margin_end(8); gs_box.set_margin_bottom(6)

        for label, cmd in [
            ("Enable GNOME Magnifier (zoom factor 2)", ["gsettings", "set", "org.gnome.desktop.a11y.magnifier", "active", "true"]),
            ("Disable GNOME Magnifier", ["gsettings", "set", "org.gnome.desktop.a11y.magnifier", "active", "false"]),
        ]:
            btn = Gtk.Button(label=label)
            btn._cmd = cmd
            btn.connect("clicked", self.run_gsettings)
            gs_box.append(btn)
        gsettings_frame.set_child(gs_box)
        vbox.append(gsettings_frame)

    def set_zoom(self, val):
        self.zoom = val
        self.zoom_label.set_text(f"Zoom: {val}x")
        self.canvas.queue_draw()

    def set_lens_size(self, val):
        self.lens_size = val
        self.canvas.queue_draw()

    def toggle_crosshair(self, val):
        self.show_crosshair = val
        self.canvas.queue_draw()

    def on_filter(self, btn, key):
        if not btn.get_active():
            return
        self.color_filter = key
        child = self.filter_buttons.get_first_child()
        while child:
            if hasattr(child, '_filter_key') and child._filter_key != key:
                child.handler_block_by_func(self.on_filter)
                child.set_active(False)
                child.handler_unblock_by_func(self.on_filter)
            child = child.get_next_sibling()
        self.canvas.queue_draw()

    def on_motion(self, ctrl, x, y):
        self.lens_x = x
        self.lens_y = y
        self.pos_label.set_text(f"Position: {int(x)}, {int(y)}")
        self.canvas.queue_draw()

    def draw_canvas(self, area, cr, w, h):
        # Background with pattern (simulating desktop content)
        cr.set_source_rgb(0.15, 0.15, 0.2)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        # Draw grid as simulated content
        cr.set_line_width(0.5)
        cr.set_source_rgba(0.3, 0.3, 0.4, 0.4)
        for x in range(0, w, 40):
            cr.move_to(x, 0); cr.line_to(x, h); cr.stroke()
        for y in range(0, h, 40):
            cr.move_to(0, y); cr.line_to(w, y); cr.stroke()

        # Some demo shapes
        shapes = [
            (w*0.2, h*0.3, 0.9, 0.2, 0.2),
            (w*0.5, h*0.5, 0.2, 0.7, 0.2),
            (w*0.7, h*0.25, 0.2, 0.4, 0.9),
            (w*0.3, h*0.7, 0.9, 0.7, 0.2),
        ]
        for sx, sy, r, g, b in shapes:
            cr.set_source_rgb(r, g, b)
            cr.arc(sx, sy, 30, 0, math.tau)
            cr.fill()
            cr.set_source_rgb(1, 1, 1)
            cr.set_font_size(10)
            cr.move_to(sx - 15, sy + 4)
            cr.show_text(f"{int(sx)},{int(sy)}")

        # Draw text lines
        cr.set_source_rgb(0.9, 0.9, 0.9)
        cr.set_font_size(14)
        for i, text in enumerate(["Sample Text Line 1", "Accessibility Demo", "GTK4 Magnifier"]):
            cr.move_to(w*0.4, h*0.4 + i*25)
            cr.show_text(text)

        # Lens magnification circle
        lx, ly = self.lens_x, self.lens_y
        r = self.lens_size / 2
        zoom = self.zoom

        cr.save()
        cr.arc(lx, ly, r, 0, math.tau)
        cr.clip()

        # Draw magnified (scaled) background
        cr.translate(lx, ly)
        cr.scale(zoom, zoom)
        cr.translate(-lx, -ly)

        # Re-draw content magnified
        cr.set_source_rgb(0.12, 0.12, 0.18)
        cr.paint()
        cr.set_line_width(0.5/zoom)
        cr.set_source_rgba(0.3, 0.3, 0.4, 0.4)
        for x in range(0, w, 40):
            cr.move_to(x, 0); cr.line_to(x, h); cr.stroke()
        for y in range(0, h, 40):
            cr.move_to(0, y); cr.line_to(w, y); cr.stroke()
        for sx, sy, rv, g, b in shapes:
            cr.set_source_rgb(rv, g, b)
            cr.arc(sx, sy, 30, 0, math.tau)
            cr.fill()
        cr.set_source_rgb(0.9, 0.9, 0.9)
        cr.set_font_size(14/zoom)
        for i, text in enumerate(["Sample Text Line 1", "Accessibility Demo", "GTK4 Magnifier"]):
            cr.move_to(w*0.4, h*0.4 + i*25)
            cr.show_text(text)

        # Apply color filter
        if self.color_filter == "invert":
            cr.set_source_rgba(1, 1, 1, 1)
            cr.set_operator(1)  # DIFFERENCE
        elif self.color_filter == "gray":
            cr.set_source_rgba(0.5, 0.5, 0.5, 0.5)

        cr.restore()

        # Lens border
        cr.set_source_rgb(0.9, 0.9, 0.2)
        cr.set_line_width(2)
        cr.arc(lx, ly, r, 0, math.tau)
        cr.stroke()

        # Crosshair
        if self.show_crosshair:
            cr.set_source_rgb(1, 0.3, 0.3)
            cr.set_line_width(1)
            cr.move_to(lx - r, ly); cr.line_to(lx + r, ly); cr.stroke()
            cr.move_to(lx, ly - r); cr.line_to(lx, ly + r); cr.stroke()

        # Zoom label in lens
        cr.set_source_rgb(1, 1, 0)
        cr.set_font_size(12)
        cr.move_to(lx - r + 5, ly - r + 16)
        cr.show_text(f"{zoom}x")

    def run_gsettings(self, btn):
        import subprocess
        try:
            subprocess.run(btn._cmd, timeout=3, capture_output=True)
        except Exception:
            pass

class ScreenMagnifierApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.ScreenMagnifier")
    def do_activate(self):
        win = ScreenMagnifierWindow(self); win.present()

def main():
    app = ScreenMagnifierApp(); app.run(None)

if __name__ == "__main__":
    main()
