#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk
import base64

class BaseConverterWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Base Converter")
        self.set_default_size(600, 480)
        self.updating = False

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(16); vbox.set_margin_bottom(16)
        vbox.set_margin_start(16); vbox.set_margin_end(16)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Number Base Converter", css_classes=["title"]))

        self.entries = {}
        bases = [
            ("Binary (Base 2)", 2),
            ("Octal (Base 8)", 8),
            ("Decimal (Base 10)", 10),
            ("Hexadecimal (Base 16)", 16),
            ("Base 32", 32),
            ("Base 64", 64),
        ]

        for label, base in bases:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            lbl = Gtk.Label(label=label, width_chars=22, xalign=0)
            row.append(lbl)
            entry = Gtk.Entry()
            entry.set_hexpand(True)
            entry.set_placeholder_text(f"Enter {label}...")
            entry.connect("changed", self.on_changed, base)
            row.append(entry)
            copy_btn = Gtk.Button(label="Copy")
            copy_btn.connect("clicked", self.on_copy, entry)
            row.append(copy_btn)
            self.entries[base] = entry
            vbox.append(row)

        self.info_label = Gtk.Label(label="")
        self.info_label.set_xalign(0)
        vbox.append(self.info_label)

        binary_frame = Gtk.Frame(label="Binary Grouped (nibbles)")
        self.binary_grouped = Gtk.Label(label="")
        self.binary_grouped.set_selectable(True)
        self.binary_grouped.set_margin_top(4); self.binary_grouped.set_margin_start(8)
        binary_frame.set_child(self.binary_grouped)
        vbox.append(binary_frame)

        hex_frame = Gtk.Frame(label="Hex Grouped (bytes)")
        self.hex_grouped = Gtk.Label(label="")
        self.hex_grouped.set_selectable(True)
        self.hex_grouped.set_margin_top(4); self.hex_grouped.set_margin_start(8)
        hex_frame.set_child(self.hex_grouped)
        vbox.append(hex_frame)

    def on_changed(self, entry, base):
        if self.updating:
            return
        text = entry.get_text().strip()
        if not text:
            self.clear_all()
            return
        try:
            if base == 32:
                val = int(text, 32) if all(c in "0123456789ABCDEFGHIJKLMNOPQRSTUV" for c in text.upper()) else None
                if val is None:
                    padded = text + "=" * ((8 - len(text) % 8) % 8)
                    decoded = base64.b32decode(padded.upper().encode())
                    val = int.from_bytes(decoded, "big")
            elif base == 64:
                padded = text + "=" * ((4 - len(text) % 4) % 4)
                decoded = base64.b64decode(padded.encode())
                val = int.from_bytes(decoded, "big")
            else:
                val = int(text, base)
            self.update_all(val, base)
        except Exception as e:
            self.info_label.set_text(f"Invalid input for base {base}: {e}")

    def update_all(self, val, source_base):
        self.updating = True
        bases_map = {2: bin(val)[2:], 8: oct(val)[2:],
                     10: str(val), 16: hex(val)[2:].upper()}
        try:
            b32 = base64.b32encode(val.to_bytes((val.bit_length() + 7) // 8 or 1, "big")).decode()
            bases_map[32] = b32
        except Exception:
            bases_map[32] = "N/A"
        try:
            b64 = base64.b64encode(val.to_bytes((val.bit_length() + 7) // 8 or 1, "big")).decode()
            bases_map[64] = b64
        except Exception:
            bases_map[64] = "N/A"

        for b, entry in self.entries.items():
            if b != source_base:
                entry.set_text(bases_map.get(b, ""))

        bin_str = bases_map.get(2, "")
        padded_bin = bin_str.zfill((len(bin_str) + 3) // 4 * 4)
        grouped_bin = " ".join(padded_bin[i:i+4] for i in range(0, len(padded_bin), 4))
        self.binary_grouped.set_text(grouped_bin)

        hex_str = bases_map.get(16, "")
        padded_hex = hex_str.zfill((len(hex_str) + 1) // 2 * 2)
        grouped_hex = " ".join(padded_hex[i:i+2] for i in range(0, len(padded_hex), 2))
        self.hex_grouped.set_text(grouped_hex)

        self.info_label.set_text(f"Decimal value: {val} (bits: {val.bit_length()})")
        self.updating = False

    def clear_all(self):
        self.updating = True
        for entry in self.entries.values():
            entry.set_text("")
        self.binary_grouped.set_text("")
        self.hex_grouped.set_text("")
        self.info_label.set_text("")
        self.updating = False

    def on_copy(self, btn, entry):
        Gdk.Display.get_default().get_clipboard().set(entry.get_text())

class BaseConverterApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.BaseConverter")
    def do_activate(self):
        win = BaseConverterWindow(self)
        win.present()

def main():
    app = BaseConverterApp()
    app.run(None)

if __name__ == "__main__":
    main()
