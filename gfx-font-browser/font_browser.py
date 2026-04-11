#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Pango', '1.0')
from gi.repository import Gtk, Gdk, Pango

class FontBrowserWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Font Browser")
        self.set_default_size(900, 700)
        self.all_fonts = []
        self.selected_font = None
        self.build_ui()
        self.load_fonts()

    def build_ui(self):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.set_child(hbox)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        left.set_size_request(280, -1)
        left.set_margin_top(6); left.set_margin_start(6); left.set_margin_bottom(6)

        search = Gtk.SearchEntry()
        search.set_placeholder_text("Search fonts...")
        search.connect("search-changed", self.on_search)
        left.append(search)

        self.count_label = Gtk.Label(label="Fonts: 0")
        self.count_label.set_xalign(0)
        left.append(self.count_label)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        self.font_list = Gtk.ListBox()
        self.font_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.font_list.connect("row-selected", self.on_font_selected)
        scroll.set_child(self.font_list)
        left.append(scroll)
        hbox.append(left)

        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        hbox.append(sep)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        right.set_margin_top(8); right.set_margin_start(8); right.set_margin_end(8); right.set_margin_bottom(8)
        right.set_hexpand(True)

        ctrl_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        ctrl_box.append(Gtk.Label(label="Sample text:"))
        self.sample_entry = Gtk.Entry()
        self.sample_entry.set_text("The quick brown fox jumps over the lazy dog")
        self.sample_entry.set_hexpand(True)
        self.sample_entry.connect("changed", self.on_sample_changed)
        ctrl_box.append(self.sample_entry)
        ctrl_box.append(Gtk.Label(label="Size:"))
        self.size_spin = Gtk.SpinButton.new_with_range(8, 96, 2)
        self.size_spin.set_value(18)
        self.size_spin.connect("value-changed", self.on_sample_changed)
        ctrl_box.append(self.size_spin)
        right.append(ctrl_box)

        self.font_name_label = Gtk.Label(label="Select a font")
        self.font_name_label.set_xalign(0)
        right.append(self.font_name_label)

        variants_frame = Gtk.Frame(label="Style Variants")
        self.variants_box = Gtk.FlowBox()
        self.variants_box.set_max_children_per_line(4)
        variants_frame.set_child(self.variants_box)
        right.append(variants_frame)

        sizes_frame = Gtk.Frame(label="Size Preview")
        sizes_scroll = Gtk.ScrolledWindow()
        sizes_scroll.set_min_content_height(200)
        self.sizes_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.sizes_vbox.set_margin_top(4); self.sizes_vbox.set_margin_start(4)
        sizes_scroll.set_child(self.sizes_vbox)
        sizes_frame.set_child(sizes_scroll)
        right.append(sizes_frame)
        hbox.append(right)

    def load_fonts(self):
        context = self.get_pango_context()
        families = context.list_families()
        self.all_fonts = sorted([f.get_name() for f in families])
        self.populate_list(self.all_fonts)
        self.count_label.set_text(f"Fonts: {len(self.all_fonts)}")

    def populate_list(self, fonts):
        while self.font_list.get_row_at_index(0):
            self.font_list.remove(self.font_list.get_row_at_index(0))
        for name in fonts:
            row = Gtk.ListBoxRow()
            lbl = Gtk.Label(label=name, xalign=0)
            lbl.set_margin_start(6); lbl.set_margin_top(3); lbl.set_margin_bottom(3)
            try:
                fd = Pango.FontDescription.from_string(f"{name} 11")
                lbl.set_font_desc(fd)
            except Exception:
                pass
            row.set_child(lbl)
            row._font_name = name
            self.font_list.append(row)

    def on_search(self, entry):
        q = entry.get_text().lower()
        filtered = [f for f in self.all_fonts if q in f.lower()]
        self.populate_list(filtered)
        self.count_label.set_text(f"Fonts: {len(filtered)}")

    def on_font_selected(self, listbox, row):
        if not row: return
        self.selected_font = row._font_name
        self.font_name_label.set_text(f"Font: {self.selected_font}")
        self.update_preview()

    def on_sample_changed(self, *args):
        if self.selected_font:
            self.update_preview()

    def update_preview(self):
        if not self.selected_font: return
        sample = self.sample_entry.get_text()
        size = int(self.size_spin.get_value())

        while self.variants_box.get_child_at_index(0):
            self.variants_box.remove(self.variants_box.get_child_at_index(0))
        for style in ["Regular", "Bold", "Italic", "Bold Italic"]:
            try:
                lbl = Gtk.Label(label=style)
                fd = Pango.FontDescription.from_string(f"{self.selected_font} {style} 10")
                lbl.set_font_desc(fd)
                lbl.set_margin_start(4); lbl.set_margin_top(2)
                self.variants_box.append(lbl)
            except Exception:
                pass

        while self.sizes_vbox.get_first_child():
            self.sizes_vbox.remove(self.sizes_vbox.get_first_child())
        for s in [10, 14, 18, 24, 32, size]:
            try:
                lbl = Gtk.Label(label=f"{s}pt: {sample[:40]}")
                lbl.set_xalign(0)
                fd = Pango.FontDescription.from_string(f"{self.selected_font} {s}")
                lbl.set_font_desc(fd)
                self.sizes_vbox.append(lbl)
            except Exception:
                pass

class FontBrowserApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.FontBrowser")
    def do_activate(self):
        win = FontBrowserWindow(self)
        win.present()

def main():
    app = FontBrowserApp()
    app.run(None)

if __name__ == "__main__":
    main()
