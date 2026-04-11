#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk
import hashlib, os

ALGOS = ["md5", "sha1", "sha224", "sha256", "sha384", "sha512", "sha3_256", "sha3_512"]

class HashToolWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Hash Tool")
        self.set_default_size(700, 560)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        input_frame = Gtk.Frame(label="Input")
        input_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        input_box.set_margin_top(4); input_box.set_margin_start(4)
        input_box.set_margin_bottom(4); input_box.set_margin_end(4)

        self.text_radio = Gtk.CheckButton(label="Text input")
        self.text_radio.set_active(True)
        self.file_radio = Gtk.CheckButton(label="File input")
        self.file_radio.set_group(self.text_radio)
        rb_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        rb_box.append(self.text_radio)
        rb_box.append(self.file_radio)
        input_box.append(rb_box)

        self.text_entry = Gtk.Entry()
        self.text_entry.set_placeholder_text("Enter text to hash...")
        self.text_entry.connect("changed", self.on_compute)
        input_box.append(self.text_entry)

        file_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.file_entry = Gtk.Entry()
        self.file_entry.set_placeholder_text("Select a file...")
        self.file_entry.set_hexpand(True)
        file_box.append(self.file_entry)
        browse_btn = Gtk.Button(label="Browse")
        browse_btn.connect("clicked", self.on_browse)
        file_box.append(browse_btn)
        input_box.append(file_box)

        compute_btn = Gtk.Button(label="Compute Hashes")
        compute_btn.connect("clicked", self.on_compute)
        input_box.append(compute_btn)
        input_frame.set_child(input_box)
        vbox.append(input_frame)

        results_frame = Gtk.Frame(label="Results")
        grid = Gtk.Grid()
        grid.set_column_spacing(8); grid.set_row_spacing(4)
        grid.set_margin_top(8); grid.set_margin_start(8)
        grid.set_margin_bottom(8); grid.set_margin_end(8)
        self.hash_entries = {}
        for i, algo in enumerate(ALGOS):
            lbl = Gtk.Label(label=algo.upper() + ":", xalign=1)
            entry = Gtk.Entry()
            entry.set_editable(False)
            entry.set_hexpand(True)
            entry.set_width_chars(50)
            copy_btn = Gtk.Button(label="Copy")
            copy_btn.connect("clicked", self.on_copy, algo)
            grid.attach(lbl, 0, i, 1, 1)
            grid.attach(entry, 1, i, 1, 1)
            grid.attach(copy_btn, 2, i, 1, 1)
            self.hash_entries[algo] = entry
        results_frame.set_child(grid)
        scroll = Gtk.ScrolledWindow()
        scroll.set_child(results_frame)
        scroll.set_vexpand(True)
        vbox.append(scroll)

        compare_frame = Gtk.Frame(label="Compare Hashes")
        cmp_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        cmp_box.set_margin_top(4); cmp_box.set_margin_start(4)
        cmp_box.set_margin_bottom(4); cmp_box.set_margin_end(4)
        self.cmp1 = Gtk.Entry(); self.cmp1.set_placeholder_text("Hash 1"); self.cmp1.set_hexpand(True)
        self.cmp2 = Gtk.Entry(); self.cmp2.set_placeholder_text("Hash 2"); self.cmp2.set_hexpand(True)
        self.cmp_result = Gtk.Label(label="")
        cmp_btn = Gtk.Button(label="Compare")
        cmp_btn.connect("clicked", self.on_compare)
        cmp_box.append(self.cmp1); cmp_box.append(self.cmp2)
        cmp_box.append(cmp_btn); cmp_box.append(self.cmp_result)
        compare_frame.set_child(cmp_box)
        vbox.append(compare_frame)

    def on_browse(self, btn):
        dialog = Gtk.FileDialog()
        dialog.open(self, None, self.on_file_chosen)

    def on_file_chosen(self, dialog, result):
        try:
            f = dialog.open_finish(result)
            if f:
                self.file_entry.set_text(f.get_path())
                self.file_radio.set_active(True)
                self.on_compute(None)
        except Exception:
            pass

    def on_compute(self, *args):
        if self.file_radio.get_active():
            path = self.file_entry.get_text()
            if not os.path.isfile(path):
                return
            with open(path, "rb") as f:
                data = f.read()
        else:
            data = self.text_entry.get_text().encode("utf-8")

        for algo in ALGOS:
            try:
                h = hashlib.new(algo, data).hexdigest()
                self.hash_entries[algo].set_text(h)
            except Exception:
                self.hash_entries[algo].set_text("N/A")

    def on_copy(self, btn, algo):
        text = self.hash_entries[algo].get_text()
        Gdk.Display.get_default().get_clipboard().set(text)

    def on_compare(self, btn):
        h1 = self.cmp1.get_text().strip().lower()
        h2 = self.cmp2.get_text().strip().lower()
        if h1 == h2:
            self.cmp_result.set_markup('<span foreground="#2ecc71">MATCH</span>')
        else:
            self.cmp_result.set_markup('<span foreground="#e74c3c">NO MATCH</span>')

class HashToolApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.HashTool")
    def do_activate(self):
        win = HashToolWindow(self)
        win.present()

def main():
    app = HashToolApp()
    app.run(None)

if __name__ == "__main__":
    main()
