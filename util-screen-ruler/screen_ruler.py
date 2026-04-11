#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk
import math

class ScreenRulerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Screen Ruler")
        self.set_default_size(600, 140)
        self.set_decorated(True)
        self.ruler_width = 600
        self.ruler_height = 80
        self.orientation = "horizontal"
        self.unit = "px"
        self.dpi = 96
        self.marker = None
        self.second_marker = None
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(vbox)

        ctrl_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        ctrl_box.set_margin_top(4); ctrl_box.set_margin_start(8); ctrl_box.set_margin_end(8); ctrl_box.set_margin_bottom(4)

        orient_combo = Gtk.ComboBoxText()
        orient_combo.append_text("Horizontal")
        orient_combo.append_text("Vertical")
        orient_combo.set_active(0)
        orient_combo.connect("changed", self.on_orientation)
        ctrl_box.append(orient_combo)

        unit_combo = Gtk.ComboBoxText()
        for u in ["px", "cm", "in", "mm", "pt"]:
            unit_combo.append_text(u)
        unit_combo.set_active(0)
        unit_combo.connect("changed", self.on_unit)
        ctrl_box.append(unit_combo)

        ctrl_box.append(Gtk.Label(label="DPI:"))
        dpi_spin = Gtk.SpinButton.new_with_range(72, 300, 1)
        dpi_spin.set_value(96)
        dpi_spin.connect("value-changed", lambda s: setattr(self, "dpi", int(s.get_value())) or self.ruler.queue_draw())
        ctrl_box.append(dpi_spin)

        flip_btn = Gtk.Button(label="Flip")
        flip_btn.connect("clicked", self.on_flip)
        ctrl_box.append(flip_btn)

        self.info_label = Gtk.Label(label="Move mouse over ruler")
        self.info_label.set_hexpand(True)
        ctrl_box.append(self.info_label)

        vbox.append(ctrl_box)

        ruler_frame = Gtk.Frame()
        self.ruler = Gtk.DrawingArea()
        self.ruler.set_size_request(600, 80)
        self.ruler.set_draw_func(self.draw_ruler)

        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self.on_mouse_move)
        self.ruler.add_controller(motion)

        click = Gtk.GestureClick()
        click.connect("pressed", self.on_click)
        self.ruler.add_controller(click)

        ruler_frame.set_child(self.ruler)
        vbox.append(ruler_frame)

    def px_to_unit(self, px):
        if self.unit == "px": return px
        if self.unit == "cm": return px / self.dpi * 2.54
        if self.unit == "in": return px / self.dpi
        if self.unit == "mm": return px / self.dpi * 25.4
        if self.unit == "pt": return px / self.dpi * 72
        return px

    def unit_label(self, px):
        val = self.px_to_unit(px)
        if self.unit == "px": return f"{int(val)}"
        return f"{val:.2f}"

    def on_orientation(self, combo):
        txt = combo.get_active_text()
        self.orientation = "horizontal" if txt == "Horizontal" else "vertical"
        if self.orientation == "vertical":
            self.ruler.set_size_request(80, 600)
        else:
            self.ruler.set_size_request(600, 80)
        self.ruler.queue_draw()

    def on_unit(self, combo):
        self.unit = combo.get_active_text()
        self.ruler.queue_draw()

    def on_flip(self, btn):
        pass

    def on_mouse_move(self, ctrl, x, y):
        pos = x if self.orientation == "horizontal" else y
        val = self.px_to_unit(pos)
        txt = f"Position: {val:.2f} {self.unit} ({int(pos)} px)"
        if self.marker is not None:
            dist = abs(pos - self.marker)
            dist_val = self.px_to_unit(dist)
            txt += f"  |  Distance from marker: {dist_val:.2f} {self.unit} ({int(dist)} px)"
        if self.second_marker is not None and self.marker is not None:
            d = abs(self.second_marker - self.marker)
            txt += f"  |  M1-M2: {self.px_to_unit(d):.2f} {self.unit}"
        self.info_label.set_text(txt)
        self.ruler.queue_draw()
        self._mouse_pos = (x, y)

    def on_click(self, gesture, n_press, x, y):
        pos = x if self.orientation == "horizontal" else y
        if n_press == 1:
            self.marker = pos
        elif n_press == 2:
            self.second_marker = pos
        self.ruler.queue_draw()

    def draw_ruler(self, area, cr, w, h):
        cr.set_source_rgb(0.95, 0.95, 0.85)
        cr.rectangle(0, 0, w, h); cr.fill()

        cr.set_source_rgb(0.4, 0.4, 0.4)
        cr.set_line_width(1)

        if self.orientation == "horizontal":
            length = w
            tick_fn = lambda pos, tick_h: (cr.move_to(pos, h - tick_h), cr.line_to(pos, h), cr.stroke())
        else:
            length = h
            tick_fn = lambda pos, tick_h: (cr.move_to(w - tick_h, pos), cr.line_to(w, pos), cr.stroke())

        step = 10  # px between minor ticks
        for px in range(0, int(length), step):
            val = self.px_to_unit(px)
            is_major = (px % 100 == 0)
            is_mid = (px % 50 == 0)
            tick_h = 30 if is_major else (20 if is_mid else 10)
            tick_fn(px, tick_h)
            if is_major:
                cr.set_font_size(10)
                cr.set_source_rgb(0.2, 0.2, 0.2)
                if self.orientation == "horizontal":
                    cr.move_to(px + 2, h - 32)
                else:
                    cr.move_to(2, px - 2)
                cr.show_text(self.unit_label(px))
            cr.set_source_rgb(0.4, 0.4, 0.4)

        # Marker
        if self.marker is not None:
            cr.set_source_rgb(0.8, 0.2, 0.2); cr.set_line_width(1.5)
            if self.orientation == "horizontal":
                cr.move_to(self.marker, 0); cr.line_to(self.marker, h); cr.stroke()
                cr.set_font_size(9)
                cr.move_to(self.marker + 2, 12)
                cr.show_text(f"M1:{self.unit_label(self.marker)}{self.unit}")
            else:
                cr.move_to(0, self.marker); cr.line_to(w, self.marker); cr.stroke()

        if self.second_marker is not None:
            cr.set_source_rgb(0.2, 0.2, 0.8); cr.set_line_width(1.5)
            if self.orientation == "horizontal":
                cr.move_to(self.second_marker, 0); cr.line_to(self.second_marker, h); cr.stroke()
                cr.move_to(self.second_marker + 2, 24)
                cr.set_font_size(9); cr.show_text(f"M2:{self.unit_label(self.second_marker)}{self.unit}")
            else:
                cr.move_to(0, self.second_marker); cr.line_to(w, self.second_marker); cr.stroke()

        # Border
        cr.set_source_rgb(0.2, 0.2, 0.2); cr.set_line_width(1)
        cr.rectangle(0, 0, w, h); cr.stroke()

class ScreenRulerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.ScreenRuler")
    def do_activate(self):
        win = ScreenRulerWindow(self); win.present()

def main():
    app = ScreenRulerApp(); app.run(None)

if __name__ == "__main__":
    main()
