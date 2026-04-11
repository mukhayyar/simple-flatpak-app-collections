#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Pango', '1.0')
from gi.repository import Gtk, GLib, Pango, PangoCairo
import os, subprocess

def get_system_fonts():
    fonts = []
    try:
        out = subprocess.check_output(["fc-list", "--format=%{family}\n"], text=True, timeout=10)
        seen = set()
        for line in out.strip().split('\n'):
            for name in line.split(','):
                n = name.strip()
                if n and n not in seen:
                    seen.add(n)
                    fonts.append(n)
    except Exception:
        pass
    if not fonts:
        fonts = ["Sans", "Serif", "Monospace", "DejaVu Sans", "Liberation Sans"]
    return sorted(fonts)

class FontManagerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Font Manager")
        self.set_default_size(900, 620)
        self.all_fonts = get_system_fonts()
        self.preview_text = "The quick brown fox jumps over the lazy dog"
        self.build_ui()

    def build_ui(self):
        hpaned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_child(hpaned)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        left.set_margin_top(8); left.set_margin_bottom(8)
        left.set_margin_start(8); left.set_margin_end(4)
        left.set_size_request(280, -1)

        left.append(Gtk.Label(label="Font Manager", css_classes=["title"]))

        search = Gtk.SearchEntry()
        search.set_placeholder_text("Search fonts...")
        search.connect("search-changed", self.on_search)
        left.append(search)

        self.count_label = Gtk.Label(label=f"{len(self.all_fonts)} fonts", xalign=0)
        self.count_label.set_css_classes(["dim-label"])
        left.append(self.count_label)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        self.font_store = Gtk.ListStore(str)
        for f in self.all_fonts:
            self.font_store.append([f])

        self.font_filter = self.font_store.filter_new()
        self.search_text = ""
        self.font_filter.set_visible_func(self.font_visible)

        self.font_list = Gtk.TreeView(model=self.font_filter)
        self.font_list.set_headers_visible(False)
        col = Gtk.TreeViewColumn("Font", Gtk.CellRendererText(), text=0)
        self.font_list.append_column(col)
        self.font_list.get_selection().connect("changed", self.on_font_selected)
        scroll.set_child(self.font_list)
        left.append(scroll)

        hpaned.set_start_child(left)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        right.set_margin_top(8); right.set_margin_bottom(8)
        right.set_margin_start(4); right.set_margin_end(8)

        self.font_title = Gtk.Label(label="Select a font", css_classes=["title"])
        self.font_title.set_halign(Gtk.Align.START)
        right.append(self.font_title)

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        controls.append(Gtk.Label(label="Size:"))
        self.size_spin = Gtk.SpinButton.new_with_range(6, 96, 1)
        self.size_spin.set_value(24)
        self.size_spin.connect("value-changed", self.update_preview)
        controls.append(self.size_spin)

        self.bold_btn = Gtk.ToggleButton(label="Bold")
        self.bold_btn.connect("toggled", self.update_preview)
        self.italic_btn = Gtk.ToggleButton(label="Italic")
        self.italic_btn.connect("toggled", self.update_preview)
        controls.append(self.bold_btn)
        controls.append(self.italic_btn)
        right.append(controls)

        preview_frame = Gtk.Frame(label="Preview")
        preview_scroll = Gtk.ScrolledWindow()
        preview_scroll.set_min_content_height(120)
        self.preview_label = Gtk.Label(label=self.preview_text)
        self.preview_label.set_wrap(True)
        self.preview_label.set_margin_top(12); self.preview_label.set_margin_bottom(12)
        self.preview_label.set_margin_start(12); self.preview_label.set_margin_end(12)
        preview_scroll.set_child(self.preview_label)
        preview_frame.set_child(preview_scroll)
        right.append(preview_frame)

        # All sizes preview
        sizes_frame = Gtk.Frame(label="Size Samples")
        sizes_scroll = Gtk.ScrolledWindow()
        sizes_scroll.set_min_content_height(180)
        sizes_scroll.set_vexpand(True)
        self.sizes_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.sizes_box.set_margin_top(6); self.sizes_box.set_margin_start(8)
        sizes_scroll.set_child(self.sizes_box)
        sizes_frame.set_child(sizes_scroll)
        right.append(sizes_frame)

        # Custom preview text entry
        custom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        custom_box.append(Gtk.Label(label="Custom text:"))
        self.custom_entry = Gtk.Entry()
        self.custom_entry.set_text(self.preview_text)
        self.custom_entry.set_hexpand(True)
        self.custom_entry.connect("changed", self.on_custom_text)
        custom_box.append(self.custom_entry)
        right.append(custom_box)

        # Font info
        self.info_label = Gtk.Label(label="", xalign=0)
        self.info_label.set_css_classes(["dim-label"])
        right.append(self.info_label)

        hpaned.set_end_child(right)

        # Select first font
        if self.all_fonts:
            self.font_list.get_selection().select_path(Gtk.TreePath.new_first())

    def font_visible(self, model, iter_, data):
        if not self.search_text:
            return True
        val = model.get_value(iter_, 0) or ""
        return self.search_text.lower() in val.lower()

    def on_search(self, entry):
        self.search_text = entry.get_text()
        self.font_filter.refilter()
        n = self.font_filter.iter_n_children(None)
        self.count_label.set_text(f"{n} fonts")

    def on_font_selected(self, selection):
        model, iter_ = selection.get_selected()
        if not iter_:
            return
        font_name = model.get_value(iter_, 0)
        self.font_title.set_label(font_name)
        self.update_preview()

    def get_selected_font(self):
        model, iter_ = self.font_list.get_selection().get_selected()
        if iter_:
            return model.get_value(iter_, 0)
        return None

    def update_preview(self, *args):
        font_name = self.get_selected_font()
        if not font_name:
            return
        size = int(self.size_spin.get_value())
        bold = self.bold_btn.get_active()
        italic = self.italic_btn.get_active()
        style = ""
        if bold: style += " Bold"
        if italic: style += " Italic"
        fd = Pango.FontDescription.from_string(f"{font_name}{style} {size}")
        self.preview_label.set_font(fd)
        self.preview_label.set_label(self.preview_text)

        # Rebuild size samples
        while True:
            child = self.sizes_box.get_first_child()
            if not child:
                break
            self.sizes_box.remove(child)

        for sz in [8, 10, 12, 14, 18, 24, 36, 48]:
            lbl = Gtk.Label(label=f"{sz}pt: {self.preview_text[:40]}")
            lbl.set_halign(Gtk.Align.START)
            fd2 = Pango.FontDescription.from_string(f"{font_name} {sz}")
            lbl.set_font(fd2)
            self.sizes_box.append(lbl)

        self.info_label.set_text(f"Font: {font_name} | Style:{style or ' Regular'} | Size: {size}pt")

    def on_custom_text(self, entry):
        self.preview_text = entry.get_text() or "Abc"
        self.update_preview()

class FontManagerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.FontManager")
    def do_activate(self):
        win = FontManagerWindow(self); win.present()

def main():
    app = FontManagerApp(); app.run(None)

if __name__ == "__main__":
    main()
