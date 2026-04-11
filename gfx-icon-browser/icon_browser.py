#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

SIZES = [16, 24, 32, 48, 64, 128]

class IconBrowserWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Icon Browser")
        self.set_default_size(900, 700)
        self.icon_size = 32
        self.all_icons = []
        self.filtered_icons = []
        self.build_ui()
        self.load_icons()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(6); vbox.set_margin_bottom(6)
        vbox.set_margin_start(6); vbox.set_margin_end(6)
        self.set_child(vbox)

        ctrl = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search icons...")
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("search-changed", self.on_search)
        ctrl.append(self.search_entry)

        ctrl.append(Gtk.Label(label="Size:"))
        self.size_combo = Gtk.ComboBoxText()
        for s in SIZES:
            self.size_combo.append_text(str(s))
        self.size_combo.set_active(2)
        self.size_combo.connect("changed", self.on_size_changed)
        ctrl.append(self.size_combo)

        self.count_label = Gtk.Label(label="Icons: 0")
        ctrl.append(self.count_label)
        vbox.append(ctrl)

        self.selected_label = Gtk.Label(label="Click an icon to see its name")
        self.selected_label.set_xalign(0)
        vbox.append(self.selected_label)

        copy_btn = Gtk.Button(label="Copy Selected Name")
        copy_btn.connect("clicked", self.on_copy)
        vbox.append(copy_btn)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        self.flow = Gtk.FlowBox()
        self.flow.set_max_children_per_line(12)
        self.flow.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.flow.connect("child-activated", self.on_icon_selected)
        scroll.set_child(self.flow)
        vbox.append(scroll)
        self.selected_name = None

    def load_icons(self):
        theme = Gtk.IconTheme.get_for_display(self.get_display())
        self.all_icons = sorted(theme.get_icon_names())
        self.filtered_icons = self.all_icons[:]
        self.populate()
        self.count_label.set_text(f"Icons: {len(self.all_icons)}")

    def populate(self):
        while self.flow.get_child_at_index(0):
            child = self.flow.get_child_at_index(0)
            self.flow.remove(child)
        for name in self.filtered_icons[:500]:
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            img = Gtk.Image.new_from_icon_name(name)
            img.set_pixel_size(self.icon_size)
            lbl = Gtk.Label(label=name[:12])
            lbl.set_max_width_chars(12)
            lbl.set_ellipsize(3)
            vbox.append(img); vbox.append(lbl)
            vbox._icon_name = name
            self.flow.append(vbox)

    def on_search(self, entry):
        q = entry.get_text().lower()
        self.filtered_icons = [n for n in self.all_icons if q in n.lower()]
        self.count_label.set_text(f"Icons: {len(self.filtered_icons)} (showing {min(500,len(self.filtered_icons))})")
        self.populate()

    def on_size_changed(self, combo):
        self.icon_size = SIZES[combo.get_active()]
        self.populate()

    def on_icon_selected(self, flow, child):
        widget = child.get_child()
        self.selected_name = widget._icon_name
        self.selected_label.set_text(f"Selected: {self.selected_name}")

    def on_copy(self, btn):
        if self.selected_name:
            Gdk.Display.get_default().get_clipboard().set(self.selected_name)
            self.selected_label.set_text(f"Copied: {self.selected_name}")

class IconBrowserApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.IconBrowser")
    def do_activate(self):
        win = IconBrowserWindow(self)
        win.present()

def main():
    app = IconBrowserApp()
    app.run(None)

if __name__ == "__main__":
    main()
