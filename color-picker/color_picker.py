#!/usr/bin/env python3
import gi
import colorsys

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GdkPixbuf


def rgb_to_hsv(r, g, b):
    """Convert 0-255 RGB to HSV (h: 0-360, s: 0-100, v: 0-100)."""
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    return round(h * 360), round(s * 100), round(v * 100)


class ColorPickerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Color Picker")
        self.set_default_size(500, 520)

        self._updating = False

        css_provider = Gtk.CssProvider()
        css = b"""
        .title-label { font-size: 22px; font-weight: bold; }
        .hex-label { font-size: 28px; font-weight: bold; font-family: monospace; }
        .hsv-label { font-size: 14px; color: #555; }
        .copy-btn { font-size: 14px; }
        .slider-label { font-size: 13px; min-width: 20px; }
        """
        css_provider.load_from_data(css)
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        outer.set_margin_top(20)
        outer.set_margin_bottom(20)
        outer.set_margin_start(30)
        outer.set_margin_end(30)
        self.set_child(outer)

        title = Gtk.Label(label="Color Picker")
        title.add_css_class("title-label")
        title.set_halign(Gtk.Align.CENTER)
        outer.append(title)

        # Color preview box (drawn via CSS background)
        self.preview_frame = Gtk.Frame()
        self.preview_frame.set_size_request(-1, 130)
        self.preview_frame.set_hexpand(True)
        self.preview_box = Gtk.Box()
        self.preview_box.set_hexpand(True)
        self.preview_box.set_vexpand(True)
        self.preview_frame.set_child(self.preview_box)
        outer.append(self.preview_frame)

        # Hex display
        self.hex_label = Gtk.Label(label="#FF0000")
        self.hex_label.add_css_class("hex-label")
        self.hex_label.set_halign(Gtk.Align.CENTER)
        outer.append(self.hex_label)

        # HSV display
        self.hsv_label = Gtk.Label(label="HSV: 0°, 100%, 100%")
        self.hsv_label.add_css_class("hsv-label")
        self.hsv_label.set_halign(Gtk.Align.CENTER)
        outer.append(self.hsv_label)

        # RGB sliders
        slider_grid = Gtk.Grid()
        slider_grid.set_row_spacing(8)
        slider_grid.set_column_spacing(10)
        outer.append(slider_grid)

        self.sliders = {}
        self.value_labels = {}
        colors = [("R", "Red", "#FF0000"), ("G", "Green", "#00AA00"), ("B", "Blue", "#0000FF")]

        for row, (key, name, _color) in enumerate(colors):
            lbl = Gtk.Label(label=name)
            lbl.add_css_class("slider-label")
            lbl.set_halign(Gtk.Align.START)
            lbl.set_size_request(40, -1)
            slider_grid.attach(lbl, 0, row, 1, 1)

            scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 255, 1)
            scale.set_hexpand(True)
            scale.set_draw_value(False)
            scale.connect("value-changed", self.on_slider_changed)
            slider_grid.attach(scale, 1, row, 1, 1)
            self.sliders[key] = scale

            val_lbl = Gtk.Label(label="255")
            val_lbl.set_size_request(38, -1)
            val_lbl.set_halign(Gtk.Align.END)
            slider_grid.attach(val_lbl, 2, row, 1, 1)
            self.value_labels[key] = val_lbl

        # Set initial slider values: R=255, G=0, B=0
        self.sliders["R"].set_value(255)
        self.sliders["G"].set_value(0)
        self.sliders["B"].set_value(0)

        # Copy to clipboard button
        copy_btn = Gtk.Button(label="Copy Hex to Clipboard")
        copy_btn.add_css_class("copy-btn")
        copy_btn.set_halign(Gtk.Align.CENTER)
        copy_btn.set_size_request(200, 40)
        copy_btn.connect("clicked", self.on_copy_clicked)
        outer.append(copy_btn)

        self.status_label = Gtk.Label(label="")
        self.status_label.set_halign(Gtk.Align.CENTER)
        outer.append(self.status_label)

        self._update_display()

    def _get_rgb(self):
        r = int(self.sliders["R"].get_value())
        g = int(self.sliders["G"].get_value())
        b = int(self.sliders["B"].get_value())
        return r, g, b

    def on_slider_changed(self, _scale):
        if self._updating:
            return
        self._updating = True
        r, g, b = self._get_rgb()
        for key, val in zip(["R", "G", "B"], [r, g, b]):
            self.value_labels[key].set_label(str(val))
        self._update_display()
        self._updating = False

    def _update_display(self):
        r, g, b = self._get_rgb()
        hex_str = f"#{r:02X}{g:02X}{b:02X}"
        self.hex_label.set_label(hex_str)

        h, s, v = rgb_to_hsv(r, g, b)
        self.hsv_label.set_label(f"HSV: {h}°, {s}%, {v}%")

        # Update preview background via CSS
        css_color = f"box {{ background-color: {hex_str}; }}"
        provider = Gtk.CssProvider()
        provider.load_from_data(css_color.encode())
        ctx = self.preview_box.get_style_context()
        ctx.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def on_copy_clicked(self, _btn):
        r, g, b = self._get_rgb()
        hex_str = f"#{r:02X}{g:02X}{b:02X}"
        display = Gdk.Display.get_default()
        if display:
            clipboard = display.get_clipboard()
            clipboard.set(hex_str)
            self.status_label.set_label(f"Copied {hex_str} to clipboard!")
        else:
            self.status_label.set_label("Could not access clipboard.")


def on_activate(app):
    win = ColorPickerWindow(app)
    win.present()


if __name__ == "__main__":
    app = Gtk.Application(application_id="com.pens.ColorPicker")
    app.connect("activate", on_activate)
    app.run(None)
