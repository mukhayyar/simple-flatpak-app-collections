#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk
import subprocess

def set_gsettings(schema, key, value):
    try:
        subprocess.run(["gsettings", "set", schema, key, str(value)],
                       capture_output=True, timeout=3)
    except Exception:
        pass

def get_gsettings(schema, key):
    try:
        return subprocess.check_output(["gsettings", "get", schema, key],
                                        text=True, timeout=3).strip()
    except Exception:
        return ""

PRESET_THEMES = [
    ("HighContrast", "High Contrast (light)", "#000000", "#ffffff"),
    ("HighContrastInverse", "High Contrast Inverse (dark)", "#ffffff", "#000000"),
    ("Adwaita", "Adwaita (normal)", "#2e3436", "#f6f5f4"),
    ("Adwaita-dark", "Adwaita Dark", "#eeeeec", "#2d2d2d"),
]

CUSTOM_CSS_TEMPLATES = {
    "High Contrast Black": """
window, .view, entry { background-color: #000000; color: #ffffff; }
button { background-color: #000000; color: #ffffff; border: 2px solid #ffffff; }
button:hover { background-color: #333333; }
""",
    "High Contrast White": """
window, .view, entry { background-color: #ffffff; color: #000000; }
button { background-color: #ffffff; color: #000000; border: 2px solid #000000; }
button:hover { background-color: #eeeeee; }
""",
    "Yellow on Black": """
window, .view, entry { background-color: #000000; color: #ffff00; }
button { background-color: #111111; color: #ffff00; border: 2px solid #ffff00; }
label { color: #ffff00; }
""",
    "Green on Black": """
window, .view, entry { background-color: #000000; color: #00ff00; }
button { background-color: #001100; color: #00ff00; border: 1px solid #00ff00; }
label { color: #00ff00; }
""",
}

class HighContrastWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("High Contrast Mode")
        self.set_default_size(700, 600)
        self.css_provider = None
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(12); vbox.set_margin_bottom(12)
        vbox.set_margin_start(16); vbox.set_margin_end(16)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="High Contrast Mode", css_classes=["title"]))

        # Quick toggles
        quick_frame = Gtk.Frame(label="Quick Accessibility Toggles")
        quick_grid = Gtk.Grid()
        quick_grid.set_row_spacing(8); quick_grid.set_column_spacing(12)
        quick_grid.set_margin_top(8); quick_grid.set_margin_start(12)
        quick_grid.set_margin_end(12); quick_grid.set_margin_bottom(8)

        # High contrast
        cur_hc = get_gsettings("org.gnome.desktop.a11y.interface", "high-contrast")
        self.hc_switch = Gtk.Switch()
        self.hc_switch.set_active(cur_hc.strip() == "true")
        self.hc_switch.connect("notify::active", self.on_hc_toggle)
        quick_grid.attach(Gtk.Label(label="GNOME High Contrast:", xalign=1), 0, 0, 1, 1)
        quick_grid.attach(self.hc_switch, 1, 0, 1, 1)

        # Large text
        cur_lt = get_gsettings("org.gnome.desktop.a11y.interface", "text-scaling-factor")
        try:
            cur_scale = float(get_gsettings("org.gnome.desktop.interface", "text-scaling-factor"))
        except ValueError:
            cur_scale = 1.0
        self.lt_switch = Gtk.Switch()
        self.lt_switch.set_active(cur_scale >= 1.3)
        self.lt_switch.connect("notify::active", self.on_large_text_toggle)
        quick_grid.attach(Gtk.Label(label="Large Text (1.5x scale):", xalign=1), 0, 1, 1, 1)
        quick_grid.attach(self.lt_switch, 1, 1, 1, 1)

        # Reduce motion
        cur_anim = get_gsettings("org.gnome.desktop.interface", "enable-animations")
        self.anim_switch = Gtk.Switch()
        self.anim_switch.set_active(cur_anim.strip() != "true")
        self.anim_switch.connect("notify::active", self.on_reduce_motion)
        quick_grid.attach(Gtk.Label(label="Reduce Motion (disable animations):", xalign=1), 0, 2, 1, 1)
        quick_grid.attach(self.anim_switch, 1, 2, 1, 1)

        quick_frame.set_child(quick_grid)
        vbox.append(quick_frame)

        # Theme presets
        theme_frame = Gtk.Frame(label="Theme Presets")
        theme_flow = Gtk.FlowBox()
        theme_flow.set_max_children_per_line(2)
        theme_flow.set_selection_mode(Gtk.SelectionMode.NONE)
        theme_flow.set_margin_top(6); theme_flow.set_margin_start(8)
        theme_flow.set_margin_end(8); theme_flow.set_margin_bottom(6)

        for theme_id, label, fg, bg in PRESET_THEMES:
            btn = Gtk.Button()
            btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            color_box = Gtk.DrawingArea()
            color_box.set_size_request(30, 20)
            color_box._fg = fg
            color_box._bg = bg
            color_box.set_draw_func(self.draw_color_preview)
            btn_box.append(color_box)
            btn_box.append(Gtk.Label(label=label))
            btn.set_child(btn_box)
            btn._theme_id = theme_id
            btn.connect("clicked", self.on_theme_preset)
            theme_flow.append(btn)
        theme_frame.set_child(theme_flow)
        vbox.append(theme_frame)

        # Custom CSS
        css_frame = Gtk.Frame(label="Custom Contrast CSS")
        css_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        css_vbox.set_margin_top(6); css_vbox.set_margin_start(8)
        css_vbox.set_margin_end(8); css_vbox.set_margin_bottom(6)

        template_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        template_box.append(Gtk.Label(label="Template:"))
        self.template_combo = Gtk.ComboBoxText()
        for name in CUSTOM_CSS_TEMPLATES:
            self.template_combo.append_text(name)
        self.template_combo.set_active(0)
        self.template_combo.connect("changed", self.on_template_changed)
        template_box.append(self.template_combo)
        css_vbox.append(template_box)

        self.css_view = Gtk.TextView()
        self.css_view.set_monospace(True)
        first_template = list(CUSTOM_CSS_TEMPLATES.values())[0]
        self.css_view.get_buffer().set_text(first_template)
        css_scroll = Gtk.ScrolledWindow()
        css_scroll.set_min_content_height(100)
        css_scroll.set_child(self.css_view)
        css_vbox.append(css_scroll)

        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        apply_css_btn = Gtk.Button(label="Apply CSS to this window")
        apply_css_btn.connect("clicked", self.on_apply_css)
        btn_row.append(apply_css_btn)
        reset_css_btn = Gtk.Button(label="Reset CSS")
        reset_css_btn.connect("clicked", self.on_reset_css)
        btn_row.append(reset_css_btn)
        css_vbox.append(btn_row)
        css_frame.set_child(css_vbox)
        vbox.append(css_frame)

        # Preview
        preview_frame = Gtk.Frame(label="Widget Preview")
        preview_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        preview_box.set_margin_top(8); preview_box.set_margin_start(8)
        preview_box.set_margin_end(8); preview_box.set_margin_bottom(8)
        preview_box.append(Gtk.Label(label="Sample Label"))
        preview_box.append(Gtk.Button(label="Button"))
        e = Gtk.Entry(); e.set_placeholder_text("Input field"); e.set_hexpand(True)
        preview_box.append(e)
        preview_box.append(Gtk.Switch())
        preview_frame.set_child(preview_box)
        vbox.append(preview_frame)

        self.status_label = Gtk.Label(label="", xalign=0)
        vbox.append(self.status_label)

    def draw_color_preview(self, area, cr, w, h, *args):
        bg = area._bg.lstrip('#')
        fg = area._fg.lstrip('#')
        cr.set_source_rgb(int(bg[:2],16)/255, int(bg[2:4],16)/255, int(bg[4:6],16)/255)
        cr.rectangle(0, 0, w, h)
        cr.fill()
        cr.set_source_rgb(int(fg[:2],16)/255, int(fg[2:4],16)/255, int(fg[4:6],16)/255)
        cr.set_font_size(8)
        cr.move_to(4, h-4)
        cr.show_text("Aa")

    def on_hc_toggle(self, switch, param):
        val = str(switch.get_active()).lower()
        set_gsettings("org.gnome.desktop.a11y.interface", "high-contrast", val)
        self.status_label.set_text(f"GNOME High Contrast: {'on' if switch.get_active() else 'off'}")

    def on_large_text_toggle(self, switch, param):
        factor = 1.5 if switch.get_active() else 1.0
        set_gsettings("org.gnome.desktop.interface", "text-scaling-factor", factor)
        self.status_label.set_text(f"Text scale: {factor}x")

    def on_reduce_motion(self, switch, param):
        val = str(not switch.get_active()).lower()
        set_gsettings("org.gnome.desktop.interface", "enable-animations", val)
        self.status_label.set_text(f"Animations: {'off' if switch.get_active() else 'on'}")

    def on_theme_preset(self, btn):
        theme = btn._theme_id
        set_gsettings("org.gnome.desktop.interface", "gtk-theme", f"'{theme}'")
        self.status_label.set_text(f"Theme set to: {theme}")

    def on_template_changed(self, combo):
        name = combo.get_active_text()
        if name in CUSTOM_CSS_TEMPLATES:
            self.css_view.get_buffer().set_text(CUSTOM_CSS_TEMPLATES[name])

    def on_apply_css(self, btn):
        buf = self.css_view.get_buffer()
        css = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)
        try:
            if self.css_provider:
                Gtk.StyleContext.remove_provider_for_display(
                    self.get_display(), self.css_provider)
            self.css_provider = Gtk.CssProvider()
            self.css_provider.load_from_data(css.encode())
            Gtk.StyleContext.add_provider_for_display(
                self.get_display(), self.css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            self.status_label.set_text("CSS applied")
        except Exception as e:
            self.status_label.set_text(f"CSS error: {e}")

    def on_reset_css(self, btn):
        if self.css_provider:
            try:
                Gtk.StyleContext.remove_provider_for_display(
                    self.get_display(), self.css_provider)
                self.css_provider = None
            except Exception:
                pass
        self.status_label.set_text("CSS reset")

class HighContrastApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.HighContrast")
    def do_activate(self):
        win = HighContrastWindow(self); win.present()

def main():
    app = HighContrastApp(); app.run(None)

if __name__ == "__main__":
    main()
