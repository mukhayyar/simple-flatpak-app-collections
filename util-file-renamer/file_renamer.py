#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import os, re

class FileRenamerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Batch File Renamer")
        self.set_default_size(900, 620)
        self.files = []
        self.current_dir = os.path.expanduser("~")
        self.build_ui()
        self.load_directory(self.current_dir)

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(6); vbox.set_margin_bottom(6)
        vbox.set_margin_start(6); vbox.set_margin_end(6)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Batch File Renamer", css_classes=["title"]))

        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.path_entry = Gtk.Entry()
        self.path_entry.set_text(self.current_dir)
        self.path_entry.set_hexpand(True)
        self.path_entry.connect("activate", lambda e: self.load_directory(e.get_text()))
        nav_box.append(self.path_entry)
        browse_btn = Gtk.Button(label="📂 Browse")
        browse_btn.connect("clicked", self.on_browse)
        nav_box.append(browse_btn)
        filter_entry = Gtk.Entry(); filter_entry.set_placeholder_text("*.txt")
        filter_entry.connect("changed", lambda e: self.load_directory(self.current_dir, e.get_text()))
        nav_box.append(filter_entry)
        vbox.append(nav_box)

        rule_frame = Gtk.Frame(label="Rename Rules")
        rule_grid = Gtk.Grid()
        rule_grid.set_row_spacing(6); rule_grid.set_column_spacing(8)
        rule_grid.set_margin_top(6); rule_grid.set_margin_start(6); rule_grid.set_margin_end(6); rule_grid.set_margin_bottom(6)

        rule_grid.attach(Gtk.Label(label="Operation:", xalign=1), 0, 0, 1, 1)
        self.op_combo = Gtk.ComboBoxText()
        for op in ["Find & Replace", "Add Prefix", "Add Suffix", "Number Sequence", "Change Extension",
                   "Remove Characters", "Insert at Position", "Uppercase", "Lowercase", "Title Case",
                   "Remove Spaces", "Replace Spaces"]:
            self.op_combo.append_text(op)
        self.op_combo.set_active(0)
        self.op_combo.connect("changed", self.on_op_changed)
        rule_grid.attach(self.op_combo, 1, 0, 2, 1)

        self.param1_label = Gtk.Label(label="Find:", xalign=1)
        self.param1_entry = Gtk.Entry(); self.param1_entry.set_hexpand(True)
        rule_grid.attach(self.param1_label, 0, 1, 1, 1)
        rule_grid.attach(self.param1_entry, 1, 1, 2, 1)

        self.param2_label = Gtk.Label(label="Replace:", xalign=1)
        self.param2_entry = Gtk.Entry(); self.param2_entry.set_hexpand(True)
        rule_grid.attach(self.param2_label, 0, 2, 1, 1)
        rule_grid.attach(self.param2_entry, 1, 2, 2, 1)

        self.regex_check = Gtk.CheckButton(label="Use Regex")
        rule_grid.attach(self.regex_check, 0, 3, 1, 1)
        self.case_check = Gtk.CheckButton(label="Case sensitive")
        self.case_check.set_active(True)
        rule_grid.attach(self.case_check, 1, 3, 1, 1)

        preview_btn = Gtk.Button(label="Preview Changes")
        preview_btn.connect("clicked", self.on_preview)
        rule_grid.attach(preview_btn, 0, 4, 2, 1)
        apply_btn = Gtk.Button(label="Apply Rename")
        apply_btn.connect("clicked", self.on_apply)
        rule_grid.attach(apply_btn, 2, 4, 1, 1)

        rule_frame.set_child(rule_grid)
        vbox.append(rule_frame)

        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        self.store = Gtk.ListStore(bool, str, str, str)
        tree = Gtk.TreeView(model=self.store)

        toggle_renderer = Gtk.CellRendererToggle()
        toggle_renderer.connect("toggled", self.on_row_toggle)
        tree.append_column(Gtk.TreeViewColumn("✓", toggle_renderer, active=0))

        for i, (title, width) in enumerate([("Original Name", 280), ("New Name", 280), ("Status", 120)], 1):
            col = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i)
            col.set_resizable(True); col.set_fixed_width(width)
            tree.append_column(col)

        scroll.set_child(tree)
        vbox.append(scroll)

        self.status_label = Gtk.Label(label="", xalign=0)
        vbox.append(self.status_label)

    def load_directory(self, path, pattern=""):
        if not os.path.isdir(path):
            return
        self.current_dir = path
        self.path_entry.set_text(path)
        self.store.clear()
        self.files = []
        try:
            entries = sorted(os.listdir(path))
            for name in entries:
                if os.path.isfile(os.path.join(path, name)):
                    if pattern and not self.match_glob(name, pattern):
                        continue
                    self.files.append(name)
                    self.store.append([True, name, name, ""])
        except Exception as e:
            self.status_label.set_text(f"Error: {e}")
        self.status_label.set_text(f"{len(self.files)} files in {path}")

    def match_glob(self, name, pattern):
        import fnmatch
        return fnmatch.fnmatch(name, pattern)

    def on_browse(self, btn):
        dialog = Gtk.FileDialog()
        dialog.select_folder(self, None, self.on_folder_selected)

    def on_folder_selected(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
            if folder:
                self.load_directory(folder.get_path())
        except Exception:
            pass

    def on_op_changed(self, combo):
        op = combo.get_active_text()
        if op == "Find & Replace":
            self.param1_label.set_text("Find:")
            self.param2_label.set_text("Replace:")
        elif op == "Add Prefix":
            self.param1_label.set_text("Prefix:")
            self.param2_label.set_text("")
        elif op == "Add Suffix":
            self.param1_label.set_text("Suffix:")
            self.param2_label.set_text("")
        elif op == "Number Sequence":
            self.param1_label.set_text("Start:")
            self.param2_label.set_text("Step:")
        elif op == "Change Extension":
            self.param1_label.set_text("New ext:")
            self.param2_label.set_text("")
        elif op == "Remove Characters":
            self.param1_label.set_text("Remove:")
            self.param2_label.set_text("")
        elif op == "Insert at Position":
            self.param1_label.set_text("Text:")
            self.param2_label.set_text("Position:")
        elif op == "Replace Spaces":
            self.param1_label.set_text("Replace with:")
            self.param2_label.set_text("")

    def compute_new_name(self, original, idx):
        op = self.op_combo.get_active_text()
        p1 = self.param1_entry.get_text()
        p2 = self.param2_entry.get_text()
        name, ext = os.path.splitext(original)
        if op == "Find & Replace":
            flags = 0 if self.case_check.get_active() else re.IGNORECASE
            if self.regex_check.get_active():
                try: return re.sub(p1, p2, original, flags=flags)
                except Exception as e: return f"ERROR: {e}"
            else:
                if not self.case_check.get_active():
                    new = re.sub(re.escape(p1), p2, original, flags=re.IGNORECASE)
                else:
                    new = original.replace(p1, p2)
                return new
        elif op == "Add Prefix": return p1 + original
        elif op == "Add Suffix": return name + p1 + ext
        elif op == "Number Sequence":
            try:
                start = int(p1) if p1 else 1
                step = int(p2) if p2 else 1
                n = start + idx * step
                pad = len(str(start + len(self.files) * step))
                return f"{n:0{pad}d}_{original}"
            except Exception: return original
        elif op == "Change Extension": return name + ("." + p1.lstrip(".") if p1 else "")
        elif op == "Remove Characters": return ''.join(c for c in original if c not in p1)
        elif op == "Insert at Position":
            try:
                pos = int(p2) if p2 else 0
                return original[:pos] + p1 + original[pos:]
            except Exception: return original
        elif op == "Uppercase": return original.upper()
        elif op == "Lowercase": return original.lower()
        elif op == "Title Case": return original.title()
        elif op == "Remove Spaces": return original.replace(" ", "")
        elif op == "Replace Spaces": return original.replace(" ", p1 or "_")
        return original

    def on_preview(self, btn):
        for i in range(len(self.files)):
            iter_ = self.store.get_iter_from_string(str(i))
            if self.store[iter_][0]:
                new_name = self.compute_new_name(self.files[i], i)
                self.store[iter_][2] = new_name
                if new_name == self.files[i]:
                    self.store[iter_][3] = "No change"
                elif new_name.startswith("ERROR"):
                    self.store[iter_][3] = new_name
                else:
                    self.store[iter_][3] = "→ rename"
        self.status_label.set_text("Preview generated. Click 'Apply Rename' to execute.")

    def on_apply(self, btn):
        renamed = 0
        errors = 0
        for i in range(len(self.files)):
            iter_ = self.store.get_iter_from_string(str(i))
            if not self.store[iter_][0]:
                continue
            old_name = self.store[iter_][1]
            new_name = self.store[iter_][2]
            if old_name == new_name or new_name.startswith("ERROR"):
                continue
            old_path = os.path.join(self.current_dir, old_name)
            new_path = os.path.join(self.current_dir, new_name)
            try:
                os.rename(old_path, new_path)
                self.store[iter_][1] = new_name
                self.store[iter_][3] = "✓ Done"
                renamed += 1
            except Exception as e:
                self.store[iter_][3] = f"Error: {e}"
                errors += 1
        self.status_label.set_text(f"Renamed: {renamed}  Errors: {errors}")
        self.load_directory(self.current_dir)

    def on_row_toggle(self, renderer, path):
        iter_ = self.store.get_iter(path)
        self.store[iter_][0] = not self.store[iter_][0]

class FileRenamerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.FileRenamer")
    def do_activate(self):
        win = FileRenamerWindow(self); win.present()

def main():
    app = FileRenamerApp(); app.run(None)

if __name__ == "__main__":
    main()
