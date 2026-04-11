#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Pango
import subprocess

def set_gsettings(schema, key, value):
    try:
        subprocess.run(["gsettings", "set", schema, key, str(value)],
                       capture_output=True, timeout=3)
    except Exception:
        pass

def get_gsettings(schema, key):
    try:
        out = subprocess.check_output(["gsettings", "get", schema, key],
                                       text=True, timeout=3).strip()
        return out
    except Exception:
        return ""

class FontSizeToolWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Font Size & Accessibility")
        self.set_default_size(720, 600)
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(12); vbox.set_margin_bottom(12)
        vbox.set_margin_start(16); vbox.set_margin_end(16)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Font Size & Text Accessibility", css_classes=["title"]))

        # DPI / scaling
        dpi_frame = Gtk.Frame(label="Text Scaling")
        dpi_grid = Gtk.Grid()
        dpi_grid.set_row_spacing(8); dpi_grid.set_column_spacing(12)
        dpi_grid.set_margin_top(8); dpi_grid.set_margin_start(12)
        dpi_grid.set_margin_end(12); dpi_grid.set_margin_bottom(8)

        dpi_grid.attach(Gtk.Label(label="Text scaling factor:", xalign=1), 0, 0, 1, 1)
        self.scaling_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.5, 3.0, 0.05)
        cur_scale = get_gsettings("org.gnome.desktop.interface", "text-scaling-factor")
        try:
            self.scaling_scale.set_value(float(cur_scale))
        except ValueError:
            self.scaling_scale.set_value(1.0)
        self.scaling_scale.set_hexpand(True)
        self.scaling_scale.set_draw_value(True)
        self.scaling_scale.connect("value-changed", self.on_scale_changed)
        dpi_grid.attach(self.scaling_scale, 1, 0, 1, 1)

        # Quick presets
        preset_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        for label, val in [("1x (default)", 1.0), ("1.25x", 1.25), ("1.5x", 1.5), ("2x", 2.0)]:
            btn = Gtk.Button(label=label)
            btn._scale = val
            btn.connect("clicked", lambda b: self.scaling_scale.set_value(b._scale))
            preset_box.append(btn)
        dpi_grid.attach(preset_box, 1, 1, 1, 1)
        dpi_frame.set_child(dpi_grid)
        vbox.append(dpi_frame)

        # System font
        font_frame = Gtk.Frame(label="System Font (GNOME)")
        font_grid = Gtk.Grid()
        font_grid.set_row_spacing(8); font_grid.set_column_spacing(12)
        font_grid.set_margin_top(8); font_grid.set_margin_start(12)
        font_grid.set_margin_end(12); font_grid.set_margin_bottom(8)

        font_grid.attach(Gtk.Label(label="Interface font:", xalign=1), 0, 0, 1, 1)
        self.font_btn = Gtk.FontDialogButton()
        self.font_btn.set_dialog(Gtk.FontDialog())
        cur_font = get_gsettings("org.gnome.desktop.interface", "font-name").strip("'")
        font_grid.attach(self.font_btn, 1, 0, 1, 1)

        font_grid.attach(Gtk.Label(label="Document font:", xalign=1), 0, 1, 1, 1)
        self.doc_font_btn = Gtk.FontDialogButton()
        self.doc_font_btn.set_dialog(Gtk.FontDialog())
        font_grid.attach(self.doc_font_btn, 1, 1, 1, 1)

        font_grid.attach(Gtk.Label(label="Monospace font:", xalign=1), 0, 2, 1, 1)
        self.mono_font_btn = Gtk.FontDialogButton()
        self.mono_font_btn.set_dialog(Gtk.FontDialog())
        font_grid.attach(self.mono_font_btn, 1, 2, 1, 1)

        apply_font_btn = Gtk.Button(label="Apply Fonts via GSettings")
        apply_font_btn.connect("clicked", self.on_apply_fonts)
        font_grid.attach(apply_font_btn, 1, 3, 1, 1)
        font_frame.set_child(font_grid)
        vbox.append(font_frame)

        # Preview at various sizes
        preview_frame = Gtk.Frame(label="Size Preview")
        preview_scroll = Gtk.ScrolledWindow()
        preview_scroll.set_vexpand(True)
        preview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        preview_box.set_margin_top(8); preview_box.set_margin_start(8)
        preview_box.set_margin_end(8); preview_box.set_margin_bottom(8)

        sample = "The quick brown fox jumps over the lazy dog. (0123456789)"
        self.preview_labels = {}
        for size in [8, 10, 12, 14, 16, 18, 24, 32, 48]:
            lbl = Gtk.Label(label=f"{size}pt: {sample[:50]}")
            lbl.set_halign(Gtk.Align.START)
            lbl.set_wrap(True)
            fd = Pango.FontDescription.from_string(f"Sans {size}")
            lbl.set_font(fd)
            preview_box.append(lbl)
            self.preview_labels[size] = lbl

        preview_scroll.set_child(preview_box)
        preview_frame.set_child(preview_scroll)
        vbox.append(preview_frame)

        # WCAG sizing guidelines
        wcag_frame = Gtk.Frame(label="WCAG Text Sizing Guidelines")
        wcag_view = Gtk.TextView()
        wcag_view.set_editable(False)
        wcag_view.set_wrap_mode(Gtk.WrapMode.WORD)
        wcag_view.get_buffer().set_text(
            "WCAG 2.1 Text Accessibility:\n"
            "• Normal text: minimum 4.5:1 contrast ratio (AA standard)\n"
            "• Large text (≥18pt or ≥14pt bold): minimum 3:1 contrast ratio\n"
            "• Resize text: text can be resized up to 200% without loss of content (AA 1.4.4)\n"
            "• Text spacing: line height ≥1.5x, letter spacing ≥0.12x font size (AA 1.4.12)\n"
            "• Minimum font size recommendation: 16px (12pt) for body text\n"
            "• Touch targets: minimum 44×44px (WCAG 2.5.5)"
        )
        wcag_scroll = Gtk.ScrolledWindow()
        wcag_scroll.set_min_content_height(100)
        wcag_scroll.set_child(wcag_view)
        wcag_frame.set_child(wcag_scroll)
        vbox.append(wcag_frame)

        self.status_label = Gtk.Label(label="", xalign=0)
        vbox.append(self.status_label)

    def on_scale_changed(self, scale):
        val = scale.get_value()
        set_gsettings("org.gnome.desktop.interface", "text-scaling-factor", val)
        self.status_label.set_text(f"Text scaling factor set to {val:.2f}")

    def on_apply_fonts(self, btn):
        msgs = []
        for btn_widget, key, label in [
            (self.font_btn, "font-name", "Interface font"),
            (self.doc_font_btn, "document-font-name", "Document font"),
            (self.mono_font_btn, "monospace-font-name", "Monospace font"),
        ]:
            fd = btn_widget.get_font_desc()
            if fd:
                font_str = fd.to_string()
                set_gsettings("org.gnome.desktop.interface", key, f"'{font_str}'")
                msgs.append(f"{label}: {font_str}")
        self.status_label.set_text(" | ".join(msgs) if msgs else "No fonts selected")

class FontSizeToolApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.FontSizeTool")
    def do_activate(self):
        win = FontSizeToolWindow(self); win.present()

def main():
    app = FontSizeToolApp(); app.run(None)

if __name__ == "__main__":
    main()
