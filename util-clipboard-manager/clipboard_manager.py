#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk
import json, os, time

DATA_DIR = os.path.expanduser("~/.local/share/com.pens.ClipboardManager")
DATA_FILE = os.path.join(DATA_DIR, "history.json")
MAX_HISTORY = 100

class ClipboardManagerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Clipboard Manager")
        self.set_default_size(700, 560)
        os.makedirs(DATA_DIR, exist_ok=True)
        self.history = self.load_history()
        self.last_text = ""
        self.pinned = set()
        self.build_ui()
        GLib.timeout_add(500, self.poll_clipboard)

    def load_history(self):
        try:
            with open(DATA_FILE) as f:
                return json.load(f)
        except Exception:
            return []

    def save_history(self):
        try:
            with open(DATA_FILE, "w") as f:
                json.dump(self.history[-MAX_HISTORY:], f)
        except Exception:
            pass

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Clipboard Manager", css_classes=["title"]))

        self.current_label = Gtk.Label(label="Current: (empty)")
        self.current_label.set_xalign(0)
        self.current_label.set_ellipsize(3)
        vbox.append(self.current_label)

        filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        filter_box.append(Gtk.Label(label="Filter:"))
        self.filter_entry = Gtk.SearchEntry()
        self.filter_entry.set_hexpand(True)
        self.filter_entry.connect("search-changed", self.on_filter)
        filter_box.append(self.filter_entry)
        vbox.append(filter_box)

        hpaned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.append(hpaned)

        scroll = Gtk.ScrolledWindow(); scroll.set_size_request(320, -1); scroll.set_vexpand(True)
        self.store = Gtk.ListStore(str, str, str, int)
        self.tree = Gtk.TreeView(model=self.store)
        self.tree.get_selection().connect("changed", self.on_selection)

        for i, (title, width) in enumerate([("Time", 100), ("Type", 60), ("Preview", 200)]):
            col = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i)
            col.set_resizable(True); col.set_fixed_width(width)
            self.tree.append_column(col)

        scroll.set_child(self.tree)
        hpaned.set_start_child(scroll)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        right.set_margin_start(8)

        preview_frame = Gtk.Frame(label="Content")
        preview_scroll = Gtk.ScrolledWindow(); preview_scroll.set_vexpand(True)
        self.preview = Gtk.TextView()
        self.preview.set_editable(False); self.preview.set_wrap_mode(Gtk.WrapMode.WORD)
        preview_scroll.set_child(self.preview)
        preview_frame.set_child(preview_scroll)
        right.append(preview_frame)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        copy_btn = Gtk.Button(label="📋 Copy to Clipboard")
        copy_btn.connect("clicked", self.on_copy)
        pin_btn = Gtk.Button(label="📌 Pin")
        pin_btn.connect("clicked", self.on_pin)
        del_btn = Gtk.Button(label="✗ Delete")
        del_btn.connect("clicked", self.on_delete)
        clear_btn = Gtk.Button(label="Clear All")
        clear_btn.connect("clicked", self.on_clear)
        btn_box.append(copy_btn); btn_box.append(pin_btn); btn_box.append(del_btn); btn_box.append(clear_btn)
        right.append(btn_box)

        stats_frame = Gtk.Frame(label="Stats")
        self.stats_label = Gtk.Label(label="", xalign=0)
        self.stats_label.set_margin_start(4)
        stats_frame.set_child(self.stats_label)
        right.append(stats_frame)

        hpaned.set_end_child(right)

        self.selected_idx = None
        self.refresh_list()

    def poll_clipboard(self):
        clipboard = self.get_clipboard()
        clipboard.read_text_async(None, self.on_clipboard_read)
        return True

    def on_clipboard_read(self, clipboard, result):
        try:
            text = clipboard.read_text_finish(result)
            if text and text != self.last_text:
                self.last_text = text
                self.add_to_history(text)
        except Exception:
            pass

    def add_to_history(self, text):
        if not text.strip():
            return
        if self.history and self.history[-1].get("text") == text:
            return
        entry = {
            "text": text,
            "time": time.strftime("%H:%M:%S"),
            "type": "text",
        }
        self.history.append(entry)
        if len(self.history) > MAX_HISTORY:
            self.history = self.history[-MAX_HISTORY:]
        self.save_history()
        self.current_label.set_text(f"Current: {text[:80]}")
        self.refresh_list()

    def refresh_list(self):
        q = self.filter_entry.get_text().lower()
        self.store.clear()
        for i, entry in enumerate(reversed(self.history)):
            text = entry.get("text", "")
            if q and q not in text.lower():
                continue
            preview = text.replace("\n", " ")[:60]
            pin_marker = "📌 " if i in self.pinned else ""
            self.store.append([entry.get("time", "--"), entry.get("type", "text"), pin_marker + preview, i])
        n = len(self.history)
        total_chars = sum(len(e.get("text", "")) for e in self.history)
        self.stats_label.set_text(f"{n} items | {total_chars:,} chars total")

    def on_filter(self, entry):
        self.refresh_list()

    def on_selection(self, selection):
        model, iter_ = selection.get_selected()
        if iter_:
            idx = len(self.history) - 1 - model[iter_][3]
            if 0 <= idx < len(self.history):
                self.selected_idx = idx
                self.preview.get_buffer().set_text(self.history[idx].get("text", ""))

    def on_copy(self, btn):
        if self.selected_idx is not None:
            text = self.history[self.selected_idx].get("text", "")
            self.get_clipboard().set(text)
            self.last_text = text

    def on_pin(self, btn):
        if self.selected_idx is not None:
            if self.selected_idx in self.pinned:
                self.pinned.discard(self.selected_idx)
            else:
                self.pinned.add(self.selected_idx)
            self.refresh_list()

    def on_delete(self, btn):
        if self.selected_idx is not None and 0 <= self.selected_idx < len(self.history):
            del self.history[self.selected_idx]
            self.save_history()
            self.selected_idx = None
            self.refresh_list()

    def on_clear(self, btn):
        self.history = []
        self.save_history()
        self.refresh_list()

class ClipboardManagerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.ClipboardManager")
    def do_activate(self):
        win = ClipboardManagerWindow(self); win.present()

def main():
    app = ClipboardManagerApp(); app.run(None)

if __name__ == "__main__":
    main()
