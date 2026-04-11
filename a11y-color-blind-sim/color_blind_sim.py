#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, GdkPixbuf
import math

# Color blindness simulation matrices (LMS space)
# Applying Brettel/Vienot simulation
CB_MATRICES = {
    "Normal": None,
    "Protanopia (no red)": [
        [0.56667, 0.43333, 0.0],
        [0.55833, 0.44167, 0.0],
        [0.0,     0.24167, 0.75833],
    ],
    "Deuteranopia (no green)": [
        [0.625,   0.375,   0.0],
        [0.7,     0.3,     0.0],
        [0.0,     0.3,     0.7],
    ],
    "Tritanopia (no blue)": [
        [0.95,    0.05,    0.0],
        [0.0,     0.43333, 0.56667],
        [0.0,     0.475,   0.525],
    ],
    "Protanomaly (weak red)": [
        [0.81667, 0.18333, 0.0],
        [0.33333, 0.66667, 0.0],
        [0.0,     0.125,   0.875],
    ],
    "Deuteranomaly (weak green)": [
        [0.8,     0.2,     0.0],
        [0.25833, 0.74167, 0.0],
        [0.0,     0.14167, 0.85833],
    ],
    "Achromatopsia (no color)": [
        [0.299,   0.587,   0.114],
        [0.299,   0.587,   0.114],
        [0.299,   0.587,   0.114],
    ],
    "Achromatomaly (weak color)": [
        [0.618,   0.32,    0.062],
        [0.163,   0.775,   0.062],
        [0.163,   0.320,   0.516],
    ],
}

def apply_cb_matrix(r, g, b, mat):
    nr = max(0, min(255, int(mat[0][0]*r + mat[0][1]*g + mat[0][2]*b)))
    ng = max(0, min(255, int(mat[1][0]*r + mat[1][1]*g + mat[1][2]*b)))
    nb = max(0, min(255, int(mat[2][0]*r + mat[2][1]*g + mat[2][2]*b)))
    return nr, ng, nb

def simulate_pixbuf(pixbuf, mat):
    if mat is None:
        return pixbuf
    has_alpha = pixbuf.get_has_alpha()
    channels = 4 if has_alpha else 3
    w = pixbuf.get_width()
    h = pixbuf.get_height()
    rs = pixbuf.get_rowstride()
    data = bytearray(pixbuf.get_pixels())
    for y in range(h):
        for x in range(w):
            idx = y * rs + x * channels
            r, g, b = data[idx], data[idx+1], data[idx+2]
            nr, ng, nb = apply_cb_matrix(r, g, b, mat)
            data[idx] = nr; data[idx+1] = ng; data[idx+2] = nb
    return GdkPixbuf.Pixbuf.new_from_bytes(
        GLib.Bytes.new(bytes(data)),
        GdkPixbuf.Colorspace.RGB, has_alpha, 8, w, h, rs)

# Generate a test image pixbuf (Ishihara-like color patches)
def make_test_pixbuf(w=300, h=200):
    data = bytearray(w * h * 3)
    import random
    rng = random.Random(42)
    # Background of dots
    colors_bg = [(210, 180, 140), (200, 170, 130), (220, 190, 150), (190, 160, 120)]
    colors_num = [(82, 140, 70), (90, 155, 80), (100, 165, 90), (75, 130, 65)]
    # Draw number "74" pattern area
    for y in range(h):
        for x in range(w):
            # determine if in number region (rough)
            nx = (x - w//4) / (w * 0.3)
            ny = (y - h//4) / (h * 0.5)
            in_num = ((nx*nx + ny*ny) < 0.8 and abs(nx) > 0.1 and ny > -0.5)
            c = rng.choice(colors_num if in_num else colors_bg)
            # Add noise
            noise = rng.randint(-10, 10)
            idx = (y * w + x) * 3
            data[idx] = max(0, min(255, c[0] + noise))
            data[idx+1] = max(0, min(255, c[1] + noise))
            data[idx+2] = max(0, min(255, c[2] + noise))
    return GdkPixbuf.Pixbuf.new_from_bytes(
        GLib.Bytes.new(bytes(data)),
        GdkPixbuf.Colorspace.RGB, False, 8, w, h, w*3)

class ColorBlindSimWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Color Blindness Simulator")
        self.set_default_size(800, 620)
        self.orig_pixbuf = make_test_pixbuf()
        self.sim_pixbuf = self.orig_pixbuf
        self.current_type = "Normal"
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Color Blindness Simulator", css_classes=["title"]))

        # Type selection
        type_frame = Gtk.Frame(label="Simulation Type")
        type_flow = Gtk.FlowBox()
        type_flow.set_max_children_per_line(4)
        type_flow.set_selection_mode(Gtk.SelectionMode.SINGLE)
        type_flow.set_margin_top(6); type_flow.set_margin_start(8)
        type_flow.set_margin_end(8); type_flow.set_margin_bottom(6)
        self.type_buttons = {}
        for name in CB_MATRICES:
            btn = Gtk.ToggleButton(label=name)
            btn.set_active(name == "Normal")
            btn.connect("toggled", self.on_type_toggled, name)
            type_flow.append(btn)
            self.type_buttons[name] = btn
        type_frame.set_child(type_flow)
        vbox.append(type_frame)

        # Image display
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        for title, attr in [("Original", "orig_img"), ("Simulated", "sim_img")]:
            frame = Gtk.Frame(label=title)
            img = Gtk.Image()
            img.set_size_request(300, 200)
            frame.set_child(img)
            hbox.append(frame)
            setattr(self, attr, img)
        vbox.append(hbox)

        # Load image button
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_halign(Gtk.Align.CENTER)
        load_btn = Gtk.Button(label="Load Image...")
        load_btn.connect("clicked", self.on_load)
        btn_box.append(load_btn)
        reset_btn = Gtk.Button(label="Use Test Image")
        reset_btn.connect("clicked", self.on_reset_test)
        btn_box.append(reset_btn)
        vbox.append(btn_box)

        # Color palette demo
        palette_frame = Gtk.Frame(label="Color Palette Demo")
        self.palette_area = Gtk.DrawingArea()
        self.palette_area.set_size_request(-1, 100)
        self.palette_area.set_draw_func(self.draw_palette)
        palette_frame.set_child(self.palette_area)
        vbox.append(palette_frame)

        # Info
        info_frame = Gtk.Frame(label="About Color Blindness")
        info_view = Gtk.TextView()
        info_view.set_editable(False)
        info_view.set_wrap_mode(Gtk.WrapMode.WORD)
        info_text = (
            "Color blindness (color vision deficiency) affects ~8% of males and ~0.5% of females.\n\n"
            "• Protanopia: Missing red photoreceptors. Red appears dark/black.\n"
            "• Deuteranopia: Missing green photoreceptors. Most common form (~5% of males).\n"
            "• Tritanopia: Missing blue photoreceptors. Very rare.\n"
            "• Achromatopsia: No color perception, sees only grayscale.\n\n"
            "WCAG recommends: Do not use color alone to convey information."
        )
        info_view.get_buffer().set_text(info_text)
        info_scroll = Gtk.ScrolledWindow()
        info_scroll.set_min_content_height(100)
        info_scroll.set_child(info_view)
        info_frame.set_child(info_scroll)
        vbox.append(info_frame)

        self.status_label = Gtk.Label(label=f"Showing: Normal vision", xalign=0)
        vbox.append(self.status_label)

        self.update_images()

    def on_type_toggled(self, btn, name):
        if not btn.get_active():
            return
        self.current_type = name
        for n, b in self.type_buttons.items():
            if n != name:
                b.handler_block_by_func(self.on_type_toggled)
                b.set_active(False)
                b.handler_unblock_by_func(self.on_type_toggled)
        GLib.idle_add(self.do_simulate)

    def do_simulate(self):
        mat = CB_MATRICES.get(self.current_type)
        self.sim_pixbuf = simulate_pixbuf(self.orig_pixbuf, mat)
        self.update_images()
        self.status_label.set_text(f"Showing: {self.current_type}")
        self.palette_area.queue_draw()
        return False

    def update_images(self):
        self.orig_img.set_from_pixbuf(self.orig_pixbuf)
        self.sim_img.set_from_pixbuf(self.sim_pixbuf)

    def on_load(self, btn):
        dialog = Gtk.FileDialog()
        dialog.open(self, None, self.on_file_chosen)

    def on_file_chosen(self, dialog, result):
        try:
            f = dialog.open_finish(result)
            if f:
                path = f.get_path()
                pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, 300, 200, True)
                self.orig_pixbuf = pb
                GLib.idle_add(self.do_simulate)
        except Exception as e:
            self.status_label.set_text(f"Error: {e}")

    def on_reset_test(self, btn):
        self.orig_pixbuf = make_test_pixbuf()
        GLib.idle_add(self.do_simulate)

    def draw_palette(self, area, cr, w, h):
        palette = [
            (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0),
            (1.0, 1.0, 0.0), (1.0, 0.0, 1.0), (0.0, 1.0, 1.0),
            (1.0, 0.5, 0.0), (0.5, 0.0, 1.0), (0.0, 0.5, 0.0),
            (0.8, 0.2, 0.2), (0.2, 0.8, 0.2), (0.2, 0.2, 0.8),
        ]
        mat = CB_MATRICES.get(self.current_type)
        sw = w / len(palette)
        for i, (r, g, b) in enumerate(palette):
            # Top: original
            cr.set_source_rgb(r, g, b)
            cr.rectangle(i * sw, 0, sw, h//2)
            cr.fill()
            # Bottom: simulated
            if mat:
                nr, ng, nb = apply_cb_matrix(int(r*255), int(g*255), int(b*255), mat)
                cr.set_source_rgb(nr/255, ng/255, nb/255)
            else:
                cr.set_source_rgb(r, g, b)
            cr.rectangle(i * sw, h//2, sw, h//2)
            cr.fill()
        # Labels
        cr.set_source_rgb(0, 0, 0)
        cr.set_font_size(9)
        cr.move_to(2, h//4 + 4)
        cr.show_text("Original")
        cr.move_to(2, 3*h//4 + 4)
        cr.show_text("Simulated")

class ColorBlindSimApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.ColorBlindSim")
    def do_activate(self):
        win = ColorBlindSimWindow(self); win.present()

def main():
    app = ColorBlindSimApp(); app.run(None)

if __name__ == "__main__":
    main()
