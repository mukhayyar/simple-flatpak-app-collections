#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk
import math

def parse_hex(s):
    s = s.strip().lstrip('#')
    if len(s) == 3:
        s = ''.join(c*2 for c in s)
    if len(s) != 6:
        return None
    try:
        r = int(s[0:2], 16) / 255
        g = int(s[2:4], 16) / 255
        b = int(s[4:6], 16) / 255
        return (r, g, b)
    except ValueError:
        return None

def srgb_to_linear(c):
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4

def relative_luminance(r, g, b):
    rl = srgb_to_linear(r)
    gl = srgb_to_linear(g)
    bl = srgb_to_linear(b)
    return 0.2126 * rl + 0.7152 * gl + 0.0722 * bl

def contrast_ratio(lum1, lum2):
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)

def wcag_grade(ratio, large=False):
    if large:
        if ratio >= 4.5: return "AAA", True
        if ratio >= 3.0: return "AA", True
        return "FAIL", False
    else:
        if ratio >= 7.0: return "AAA", True
        if ratio >= 4.5: return "AA", True
        if ratio >= 3.0: return "AA Large", True
        return "FAIL", False

PRESET_COMBOS = [
    ("Black on White", "#000000", "#ffffff"),
    ("White on Black", "#ffffff", "#000000"),
    ("White on Blue", "#ffffff", "#0000cc"),
    ("Black on Yellow", "#000000", "#ffff00"),
    ("Dark on Light Gray", "#333333", "#cccccc"),
    ("GNOME Dark text", "#eeeeec", "#2e3436"),
    ("Red on White", "#cc0000", "#ffffff"),
    ("Green on Black", "#00cc00", "#000000"),
    ("Gray on Gray", "#888888", "#aaaaaa"),
]

class ContrastCheckerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("WCAG Contrast Checker")
        self.set_default_size(700, 620)
        self.fg = (0, 0, 0)
        self.bg = (1, 1, 1)
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(12); vbox.set_margin_bottom(12)
        vbox.set_margin_start(16); vbox.set_margin_end(16)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="WCAG Contrast Checker", css_classes=["title"]))

        # Color inputs
        input_frame = Gtk.Frame(label="Colors")
        input_grid = Gtk.Grid()
        input_grid.set_row_spacing(8); input_grid.set_column_spacing(12)
        input_grid.set_margin_top(8); input_grid.set_margin_start(12)
        input_grid.set_margin_end(12); input_grid.set_margin_bottom(8)

        for row, (label, attr, default) in enumerate([("Foreground (text):", "fg_entry", "#000000"),
                                                       ("Background:", "bg_entry", "#ffffff")]):
            input_grid.attach(Gtk.Label(label=label, xalign=1), 0, row, 1, 1)
            entry = Gtk.Entry()
            entry.set_text(default)
            entry.set_max_width_chars(10)
            entry.connect("changed", self.on_color_changed)
            input_grid.attach(entry, 1, row, 1, 1)

            swatch = Gtk.DrawingArea()
            swatch.set_size_request(60, 30)
            swatch.set_draw_func(self.draw_swatch, attr)
            input_grid.attach(swatch, 2, row, 1, 1)
            setattr(self, attr, entry)
            setattr(self, attr + "_swatch", swatch)

        swap_btn = Gtk.Button(label="⇄ Swap")
        swap_btn.connect("clicked", self.on_swap)
        input_grid.attach(swap_btn, 3, 0, 1, 2)
        input_frame.set_child(input_grid)
        vbox.append(input_frame)

        # Results
        result_frame = Gtk.Frame(label="Contrast Analysis")
        result_grid = Gtk.Grid()
        result_grid.set_row_spacing(8); result_grid.set_column_spacing(16)
        result_grid.set_margin_top(8); result_grid.set_margin_start(12)
        result_grid.set_margin_end(12); result_grid.set_margin_bottom(8)

        labels = ["Contrast Ratio:", "WCAG AA (normal text):", "WCAG AA (large text):",
                  "WCAG AAA (normal):", "WCAG AAA (large):", "Luminance FG:", "Luminance BG:"]
        self.result_labels = {}
        for i, lbl in enumerate(labels):
            key = Gtk.Label(label=lbl, xalign=1)
            key.set_css_classes(["dim-label"])
            val = Gtk.Label(label="—", xalign=0)
            result_grid.attach(key, 0, i, 1, 1)
            result_grid.attach(val, 1, i, 1, 1)
            self.result_labels[lbl] = val
        result_frame.set_child(result_grid)
        vbox.append(result_frame)

        # Preview
        preview_frame = Gtk.Frame(label="Preview")
        self.preview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.preview_box.set_margin_top(12); self.preview_box.set_margin_bottom(12)
        self.preview_box.set_margin_start(12); self.preview_box.set_margin_end(12)
        self.small_label = Gtk.Label(label="Small text (14px): The quick brown fox")
        self.large_label = Gtk.Label(label="Large text (18pt+): Header Text")
        self.bold_label = Gtk.Label(label="Bold text (14pt bold): Bold Sample")
        for lbl in [self.small_label, self.large_label, self.bold_label]:
            self.preview_box.append(lbl)
        preview_frame.set_child(self.preview_box)
        vbox.append(preview_frame)

        # Presets
        preset_frame = Gtk.Frame(label="Preset Combinations")
        preset_scroll = Gtk.ScrolledWindow()
        preset_scroll.set_min_content_height(120)
        preset_store = Gtk.ListStore(str, str, str, str)
        for name, fg_hex, bg_hex in PRESET_COMBOS:
            fg = parse_hex(fg_hex)
            bg = parse_hex(bg_hex)
            if fg and bg:
                lum_fg = relative_luminance(*fg)
                lum_bg = relative_luminance(*bg)
                ratio = contrast_ratio(lum_fg, lum_bg)
                grade, _ = wcag_grade(ratio)
                preset_store.append([name, fg_hex, bg_hex, f"{ratio:.2f} ({grade})"])
        preset_view = Gtk.TreeView(model=preset_store)
        for i, title in enumerate(["Name", "FG", "BG", "Result"]):
            col = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i)
            col.set_resizable(True)
            preset_view.append_column(col)
        preset_view.get_selection().connect("changed", self.on_preset_selected)
        self.preset_store = preset_store
        preset_scroll.set_child(preset_view)
        preset_frame.set_child(preset_scroll)
        vbox.append(preset_frame)

        self.update_contrast()

    def draw_swatch(self, area, cr, w, h, attr):
        entry = getattr(self, attr, None)
        if entry:
            rgb = parse_hex(entry.get_text())
            if rgb:
                cr.set_source_rgb(*rgb)
                cr.rectangle(0, 0, w, h)
                cr.fill()

    def on_color_changed(self, entry):
        self.update_contrast()

    def update_contrast(self):
        fg_hex = self.fg_entry.get_text()
        bg_hex = self.bg_entry.get_text()
        fg = parse_hex(fg_hex)
        bg = parse_hex(bg_hex)

        self.fg_entry_swatch.queue_draw()
        self.bg_entry_swatch.queue_draw()

        if not fg or not bg:
            for lbl in self.result_labels.values():
                lbl.set_text("Invalid color")
            return

        self.fg = fg
        self.bg = bg
        lum_fg = relative_luminance(*fg)
        lum_bg = relative_luminance(*bg)
        ratio = contrast_ratio(lum_fg, lum_bg)

        grade_normal, pass_normal = wcag_grade(ratio, large=False)
        grade_large, pass_large = wcag_grade(ratio, large=True)
        grade_aaa, pass_aaa = (("AAA", True) if ratio >= 7.0 else ("FAIL", False))
        grade_aaa_large, pass_aaa_large = (("AAA", True) if ratio >= 4.5 else ("FAIL", False))

        def make_result(grade, passed):
            return f"{'✓' if passed else '✗'} {grade}"

        self.result_labels["Contrast Ratio:"].set_text(f"{ratio:.2f}:1")
        self.result_labels["WCAG AA (normal text):"].set_text(make_result(grade_normal, pass_normal))
        self.result_labels["WCAG AA (large text):"].set_text(make_result(grade_large, pass_large))
        self.result_labels["WCAG AAA (normal):"].set_text(make_result(grade_aaa, pass_aaa))
        self.result_labels["WCAG AAA (large):"].set_text(make_result(grade_aaa_large, pass_aaa_large))
        self.result_labels["Luminance FG:"].set_text(f"{lum_fg:.4f}")
        self.result_labels["Luminance BG:"].set_text(f"{lum_bg:.4f}")

        # Update preview
        fr, fg_v, fb = fg
        br, bg_v, bb = bg
        css = f"* {{ color: rgb({int(fr*255)},{int(fg_v*255)},{int(fb*255)}); background-color: rgb({int(br*255)},{int(bg_v*255)},{int(bb*255)}); }}"
        try:
            provider = Gtk.CssProvider()
            provider.load_from_data(css.encode())
            for lbl in [self.small_label, self.large_label, self.bold_label]:
                lbl.get_style_context().add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        except Exception:
            pass

    def on_swap(self, btn):
        fg_val = self.fg_entry.get_text()
        bg_val = self.bg_entry.get_text()
        self.fg_entry.set_text(bg_val)
        self.bg_entry.set_text(fg_val)

    def on_preset_selected(self, selection):
        model, iter_ = selection.get_selected()
        if not iter_:
            return
        fg_hex = model.get_value(iter_, 1)
        bg_hex = model.get_value(iter_, 2)
        self.fg_entry.set_text(fg_hex)
        self.bg_entry.set_text(bg_hex)

class ContrastCheckerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.ContrastChecker")
    def do_activate(self):
        win = ContrastCheckerWindow(self); win.present()

def main():
    app = ContrastCheckerApp(); app.run(None)

if __name__ == "__main__":
    main()
