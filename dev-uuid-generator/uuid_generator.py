#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk
import uuid, time, os, struct, hashlib

def make_ulid():
    t = int(time.time() * 1000)
    rand = int.from_bytes(os.urandom(10), 'big')
    ENCODING = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    result = []
    for _ in range(10):
        rand, r = divmod(rand, 32)
        result.append(ENCODING[r])
    for _ in range(10):
        t, r = divmod(t, 32)
        result.append(ENCODING[r])
    return ''.join(reversed(result))

class UuidGeneratorWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("UUID Generator")
        self.set_default_size(680, 560)
        self.history = []

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        ctrl_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        ctrl_box.append(Gtk.Label(label="Version:"))
        self.version_combo = Gtk.ComboBoxText()
        for v in ["v1 (Time-based)", "v3 (MD5)", "v4 (Random)", "v5 (SHA1)", "ULID", "Nil UUID"]:
            self.version_combo.append_text(v)
        self.version_combo.set_active(2)
        self.version_combo.connect("changed", self.on_version_changed)
        ctrl_box.append(self.version_combo)

        ctrl_box.append(Gtk.Label(label="Count:"))
        self.count_spin = Gtk.SpinButton.new_with_range(1, 1000, 1)
        self.count_spin.set_value(1)
        ctrl_box.append(self.count_spin)

        gen_btn = Gtk.Button(label="Generate")
        gen_btn.connect("clicked", self.on_generate)
        ctrl_box.append(gen_btn)

        copy_btn = Gtk.Button(label="Copy All")
        copy_btn.connect("clicked", self.on_copy_all)
        ctrl_box.append(copy_btn)

        clear_btn = Gtk.Button(label="Clear History")
        clear_btn.connect("clicked", self.on_clear)
        ctrl_box.append(clear_btn)
        vbox.append(ctrl_box)

        namespace_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        namespace_box.append(Gtk.Label(label="Namespace (v3/v5):"))
        self.ns_entry = Gtk.Entry()
        self.ns_entry.set_text(str(uuid.NAMESPACE_DNS))
        self.ns_entry.set_hexpand(True)
        namespace_box.append(self.ns_entry)
        namespace_box.append(Gtk.Label(label="Name:"))
        self.name_entry = Gtk.Entry()
        self.name_entry.set_text("example.com")
        namespace_box.append(self.name_entry)
        vbox.append(namespace_box)
        self.ns_box = namespace_box
        self.ns_box.set_visible(False)

        info_text = (
            "v1: Time-based  |  v3: MD5 namespace hash  |  v4: Random  |  "
            "v5: SHA1 namespace hash  |  ULID: Sortable random  |  Nil: All zeros"
        )
        vbox.append(Gtk.Label(label=info_text))

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        self.result_view = Gtk.TextView()
        self.result_view.set_monospace(True)
        self.result_view.set_editable(False)
        scroll.set_child(self.result_view)
        vbox.append(scroll)

        self.status_label = Gtk.Label(label="Ready")
        self.status_label.set_xalign(0)
        vbox.append(self.status_label)

    def on_version_changed(self, combo):
        v = combo.get_active()
        self.ns_box.set_visible(v in [1, 3])

    def on_generate(self, btn):
        count = int(self.count_spin.get_value())
        v_idx = self.version_combo.get_active()
        results = []
        for _ in range(count):
            try:
                if v_idx == 0:
                    results.append(str(uuid.uuid1()))
                elif v_idx == 1:
                    ns = uuid.UUID(self.ns_entry.get_text())
                    results.append(str(uuid.uuid3(ns, self.name_entry.get_text())))
                elif v_idx == 2:
                    results.append(str(uuid.uuid4()))
                elif v_idx == 3:
                    ns = uuid.UUID(self.ns_entry.get_text())
                    results.append(str(uuid.uuid5(ns, self.name_entry.get_text())))
                elif v_idx == 4:
                    results.append(make_ulid())
                elif v_idx == 5:
                    results.append("00000000-0000-0000-0000-000000000000")
            except Exception as e:
                results.append(f"Error: {e}")

        self.history.extend(results)
        self.result_view.get_buffer().set_text("\n".join(self.history))
        self.status_label.set_text(f"Generated {count} UUID(s), total in history: {len(self.history)}")

    def on_copy_all(self, btn):
        buf = self.result_view.get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
        Gdk.Display.get_default().get_clipboard().set(text)
        self.status_label.set_text("Copied to clipboard")

    def on_clear(self, btn):
        self.history.clear()
        self.result_view.get_buffer().set_text("")
        self.status_label.set_text("History cleared")

class UuidGeneratorApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.UuidGenerator")
    def do_activate(self):
        win = UuidGeneratorWindow(self)
        win.present()

def main():
    app = UuidGeneratorApp()
    app.run(None)

if __name__ == "__main__":
    main()
