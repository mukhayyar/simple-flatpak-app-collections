#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk
import math

def hsl_to_rgb(h, s, l):
    c = (1 - abs(2*l - 1)) * s
    x = c * (1 - abs((h/60) % 2 - 1))
    m = l - c/2
    if h < 60: r,g,b = c,x,0
    elif h < 120: r,g,b = x,c,0
    elif h < 180: r,g,b = 0,c,x
    elif h < 240: r,g,b = 0,x,c
    elif h < 300: r,g,b = x,0,c
    else: r,g,b = c,0,x
    return (r+m, g+m, b+m)

def rgb_to_hex(r, g, b):
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

def rgb_to_hsl(r, g, b):
    mx = max(r,g,b); mn = min(r,g,b)
    l = (mx+mn)/2
    if mx == mn: return 0, 0, l
    d = mx - mn
    s = d/(2-mx-mn) if l > 0.5 else d/(mx+mn)
    if mx == r: h = (g-b)/d + (6 if g<b else 0)
    elif mx == g: h = (b-r)/d + 2
    else: h = (r-g)/d + 4
    return h*60, s, l

HARMONIES = {
    "Complementary": [0, 180],
    "Analogous": [0, 30, -30],
    "Triadic": [0, 120, 240],
    "Tetradic": [0, 90, 180, 270],
    "Split-Complementary": [0, 150, 210],
}

class ColorPaletteWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Color Palette Generator")
        self.set_default_size(700, 600)
        self.base_hsl = (200, 0.7, 0.5)
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(12); vbox.set_margin_bottom(12)
        vbox.set_margin_start(12); vbox.set_margin_end(12)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Color Palette Generator", css_classes=["title"]))

        pick_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        pick_btn = Gtk.Button(label="Pick Base Color")
        pick_btn.connect("clicked", self.on_pick)
        pick_box.append(pick_btn)
        self.base_swatch = Gtk.DrawingArea()
        self.base_swatch.set_size_request(60, 40)
        self.base_swatch.set_draw_func(self.draw_base_swatch)
        pick_box.append(self.base_swatch)
        self.base_hex_label = Gtk.Label(label="#3498db")
        self.base_hex_label.set_selectable(True)
        pick_box.append(self.base_hex_label)
        vbox.append(pick_box)

        harm_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        harm_box.append(Gtk.Label(label="Harmony:"))
        self.harm_combo = Gtk.ComboBoxText()
        for h in HARMONIES:
            self.harm_combo.append_text(h)
        self.harm_combo.set_active(0)
        self.harm_combo.connect("changed", self.on_generate)
        harm_box.append(self.harm_combo)
        gen_btn = Gtk.Button(label="Generate")
        gen_btn.connect("clicked", self.on_generate)
        harm_box.append(gen_btn)
        vbox.append(harm_box)

        self.swatches_area = Gtk.DrawingArea()
        self.swatches_area.set_size_request(640, 200)
        self.swatches_area.set_draw_func(self.draw_swatches)
        vbox.append(self.swatches_area)

        export_frame = Gtk.Frame(label="Export")
        export_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        export_vbox.set_margin_top(6); export_vbox.set_margin_start(6)
        export_vbox.set_margin_bottom(6); export_vbox.set_margin_end(6)
        export_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        css_btn = Gtk.Button(label="Copy CSS Variables")
        css_btn.connect("clicked", self.on_copy_css)
        hex_btn = Gtk.Button(label="Copy HEX List")
        hex_btn.connect("clicked", self.on_copy_hex)
        export_row.append(css_btn); export_row.append(hex_btn)
        export_vbox.append(export_row)
        self.export_view = Gtk.TextView()
        self.export_view.set_editable(False)
        self.export_view.set_monospace(True)
        scroll = Gtk.ScrolledWindow(); scroll.set_min_content_height(100)
        scroll.set_child(self.export_view); export_vbox.append(scroll)
        export_frame.set_child(export_vbox)
        vbox.append(export_frame)

        self.palette = []
        self.on_generate(None)

    def draw_base_swatch(self, area, cr, w, h):
        h_val, s, l = self.base_hsl
        cr.set_source_rgb(*hsl_to_rgb(h_val, s, l))
        cr.rectangle(0, 0, w, h); cr.fill()

    def draw_swatches(self, area, cr, w, h):
        n = len(self.palette)
        if not n: return
        sw = w / n
        for i, (r, g, b) in enumerate(self.palette):
            cr.set_source_rgb(r, g, b)
            cr.rectangle(i * sw, 0, sw - 2, h - 30)
            cr.fill()
            hex_c = rgb_to_hex(r, g, b)
            cr.set_source_rgb(0, 0, 0 if (0.299*r + 0.587*g + 0.114*b) > 0.5 else 1)
            cr.set_font_size(11)
            cr.move_to(i * sw + 4, h - 8)
            cr.show_text(hex_c)

    def on_pick(self, btn):
        dialog = Gtk.ColorDialog()
        rgba = Gdk.RGBA()
        h, s, l = self.base_hsl
        r, g, b = hsl_to_rgb(h, s, l)
        rgba.red, rgba.green, rgba.blue, rgba.alpha = r, g, b, 1.0
        dialog.choose_rgba(self, rgba, None, self.on_color_chosen)

    def on_color_chosen(self, dialog, result):
        try:
            rgba = dialog.choose_rgba_finish(result)
            if rgba:
                self.base_hsl = rgb_to_hsl(rgba.red, rgba.green, rgba.blue)
                self.base_swatch.queue_draw()
                h, s, l = self.base_hsl
                r, g, b = hsl_to_rgb(h, s, l)
                self.base_hex_label.set_text(rgb_to_hex(r, g, b))
                self.on_generate(None)
        except Exception:
            pass

    def on_generate(self, *a):
        harmony = self.harm_combo.get_active_text()
        offsets = HARMONIES.get(harmony, [0, 180])
        h, s, l = self.base_hsl
        self.palette = []
        for offset in offsets:
            nh = (h + offset) % 360
            r, g, b = hsl_to_rgb(nh, s, l)
            self.palette.append((r, g, b))
        for v in [0.2, 0.4, 0.6, 0.8]:
            r, g, b = hsl_to_rgb(h, s, v)
            self.palette.append((r, g, b))
        self.swatches_area.queue_draw()

    def on_copy_css(self, btn):
        lines = [":root {"]
        for i, (r, g, b) in enumerate(self.palette):
            lines.append(f"  --color-{i+1}: {rgb_to_hex(r, g, b)};")
        lines.append("}")
        text = "\n".join(lines)
        self.export_view.get_buffer().set_text(text)
        Gdk.Display.get_default().get_clipboard().set(text)

    def on_copy_hex(self, btn):
        lines = [rgb_to_hex(r, g, b) for r, g, b in self.palette]
        text = "\n".join(lines)
        self.export_view.get_buffer().set_text(text)
        Gdk.Display.get_default().get_clipboard().set(text)

class ColorPaletteApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.ColorPalette")
    def do_activate(self):
        win = ColorPaletteWindow(self)
        win.present()

def main():
    app = ColorPaletteApp()
    app.run(None)

if __name__ == "__main__":
    main()
