#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import os

class EnvViewerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Environment Variables Viewer")
        self.set_default_size(900, 620)
        self.all_vars = {}
        self.build_ui()
        self.load_env()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(6); vbox.set_margin_bottom(6)
        vbox.set_margin_start(6); vbox.set_margin_end(6)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Environment Variables Viewer", css_classes=["title"]))

        filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        filter_box.append(Gtk.Label(label="Filter:"))
        self.filter_entry = Gtk.SearchEntry()
        self.filter_entry.set_hexpand(True)
        self.filter_entry.connect("search-changed", self.on_filter)
        filter_box.append(self.filter_entry)
        cat_combo = Gtk.ComboBoxText()
        for cat in ["All", "PATH", "HOME", "SHELL", "DISPLAY", "USER/LOGIN", "LANG", "PYTHON", "DBUS"]:
            cat_combo.append_text(cat)
        cat_combo.set_active(0)
        cat_combo.connect("changed", self.on_category)
        filter_box.append(cat_combo)
        refresh_btn = Gtk.Button(label="⟳ Refresh")
        refresh_btn.connect("clicked", lambda b: self.load_env())
        filter_box.append(refresh_btn)
        vbox.append(filter_box)

        hpaned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.append(hpaned)

        scroll = Gtk.ScrolledWindow(); scroll.set_size_request(420, -1); scroll.set_vexpand(True)
        self.store = Gtk.ListStore(str, str)
        self.tree = Gtk.TreeView(model=self.store)
        self.tree.get_selection().connect("changed", self.on_selection)

        for i, (title, width) in enumerate([("Variable", 200), ("Value", 400)]):
            renderer = Gtk.CellRendererText()
            renderer.set_property("ellipsize", 3)
            col = Gtk.TreeViewColumn(title, renderer, text=i)
            col.set_resizable(True); col.set_fixed_width(width)
            col.set_sort_column_id(i)
            self.tree.append_column(col)

        scroll.set_child(self.tree)
        hpaned.set_start_child(scroll)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        right.set_margin_start(8); right.set_margin_top(4); right.set_margin_end(4)

        detail_frame = Gtk.Frame(label="Variable Details")
        detail_scroll = Gtk.ScrolledWindow(); detail_scroll.set_min_content_height(180)
        self.detail_view = Gtk.TextView()
        self.detail_view.set_editable(False); self.detail_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.detail_view.set_monospace(True)
        detail_scroll.set_child(self.detail_view)
        detail_frame.set_child(detail_scroll)
        right.append(detail_frame)

        set_frame = Gtk.Frame(label="Set/Modify Variable")
        set_grid = Gtk.Grid(); set_grid.set_row_spacing(6); set_grid.set_column_spacing(8)
        set_grid.set_margin_top(6); set_grid.set_margin_start(6); set_grid.set_margin_end(6); set_grid.set_margin_bottom(6)
        set_grid.attach(Gtk.Label(label="Name:", xalign=1), 0, 0, 1, 1)
        self.name_entry = Gtk.Entry(); self.name_entry.set_hexpand(True)
        set_grid.attach(self.name_entry, 1, 0, 1, 1)
        set_grid.attach(Gtk.Label(label="Value:", xalign=1), 0, 1, 1, 1)
        self.val_entry = Gtk.Entry(); self.val_entry.set_hexpand(True)
        set_grid.attach(self.val_entry, 1, 1, 1, 1)
        set_btn = Gtk.Button(label="Set (current session)")
        set_btn.connect("clicked", self.on_set)
        set_grid.attach(set_btn, 0, 2, 2, 1)
        set_frame.set_child(set_grid)
        right.append(set_frame)

        export_frame = Gtk.Frame(label="Export")
        export_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        export_box.set_margin_top(4); export_box.set_margin_start(4); export_box.set_margin_end(4); export_box.set_margin_bottom(4)
        copy_btn = Gtk.Button(label="Copy All (shell format)")
        copy_btn.connect("clicked", self.on_copy_all)
        copy_sel_btn = Gtk.Button(label="Copy Selected")
        copy_sel_btn.connect("clicked", self.on_copy_selected)
        export_box.append(copy_btn); export_box.append(copy_sel_btn)
        export_frame.set_child(export_box)
        right.append(export_frame)

        self.status_label = Gtk.Label(label="", xalign=0)
        right.append(self.status_label)

        hpaned.set_end_child(right)

        self.category_filter = "All"
        self.selected_var = None

    def load_env(self):
        self.all_vars = dict(os.environ)
        self.populate_store()

    def populate_store(self, q=""):
        self.store.clear()
        for key in sorted(self.all_vars.keys()):
            val = self.all_vars[key]
            if q and q.lower() not in key.lower() and q.lower() not in val.lower():
                continue
            if self.category_filter != "All":
                if self.category_filter not in key.upper():
                    continue
            self.store.append([key, val[:100]])
        self.status_label.set_text(f"{self.store.iter_n_children(None)} variables shown")

    def on_filter(self, entry):
        self.populate_store(entry.get_text())

    def on_category(self, combo):
        self.category_filter = combo.get_active_text()
        self.populate_store(self.filter_entry.get_text())

    def on_selection(self, selection):
        model, iter_ = selection.get_selected()
        if not iter_:
            return
        key = model[iter_][0]
        val = self.all_vars.get(key, "")
        self.selected_var = (key, val)
        self.name_entry.set_text(key)
        self.val_entry.set_text(val)
        if key == "PATH":
            parts = val.split(":")
            detail = f"{key}:\n" + "\n".join(f"  {p}" for p in parts)
        else:
            detail = f"{key}={val}"
        self.detail_view.get_buffer().set_text(detail)

    def on_set(self, btn):
        name = self.name_entry.get_text().strip()
        val = self.val_entry.get_text()
        if name:
            os.environ[name] = val
            self.all_vars[name] = val
            self.populate_store(self.filter_entry.get_text())
            self.status_label.set_text(f"Set {name}={val[:60]}")

    def on_copy_all(self, btn):
        lines = [f"export {k}={repr(v)}" for k, v in sorted(self.all_vars.items())]
        text = "\n".join(lines)
        self.get_clipboard().set(text)
        self.status_label.set_text(f"Copied {len(lines)} variables to clipboard")

    def on_copy_selected(self, btn):
        if self.selected_var:
            k, v = self.selected_var
            text = f"export {k}={repr(v)}"
            self.get_clipboard().set(text)
            self.status_label.set_text(f"Copied {k}")

class EnvViewerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.EnvViewer")
    def do_activate(self):
        win = EnvViewerWindow(self); win.present()

def main():
    app = EnvViewerApp(); app.run(None)

if __name__ == "__main__":
    main()
