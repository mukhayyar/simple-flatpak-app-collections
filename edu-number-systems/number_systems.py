#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import re

class NumberSystemsWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Number Systems")
        self.set_default_size(700, 540)
        self._updating = False
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(16); vbox.set_margin_bottom(16)
        vbox.set_margin_start(20); vbox.set_margin_end(20)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Number Systems Converter", css_classes=["title"]))

        grid = Gtk.Grid()
        grid.set_row_spacing(8); grid.set_column_spacing(10)

        systems = [
            ("Binary (Base 2):", "bin_entry", 2),
            ("Octal (Base 8):", "oct_entry", 8),
            ("Decimal (Base 10):", "dec_entry", 10),
            ("Hexadecimal (Base 16):", "hex_entry", 16),
        ]
        self.entries = {}
        for row, (label, attr, base) in enumerate(systems):
            lbl = Gtk.Label(label=label, xalign=1)
            entry = Gtk.Entry()
            entry.set_hexpand(True)
            entry._base = base
            entry.connect("changed", self.on_changed)
            grid.attach(lbl, 0, row, 1, 1)
            grid.attach(entry, 1, row, 1, 1)
            self.entries[base] = entry
            setattr(self, attr, entry)

        self.entries[10].set_text("42")
        vbox.append(grid)

        custom_frame = Gtk.Frame(label="Custom Base")
        custom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        custom_box.set_margin_top(6); custom_box.set_margin_start(6); custom_box.set_margin_end(6); custom_box.set_margin_bottom(6)
        custom_box.append(Gtk.Label(label="Base:"))
        self.custom_base_spin = Gtk.SpinButton.new_with_range(2, 36, 1)
        self.custom_base_spin.set_value(32)
        custom_box.append(self.custom_base_spin)
        custom_box.append(Gtk.Label(label="Value:"))
        self.custom_result = Gtk.Entry()
        self.custom_result.set_editable(False)
        self.custom_result.set_hexpand(True)
        custom_box.append(self.custom_result)
        convert_btn = Gtk.Button(label="Convert")
        convert_btn.connect("clicked", self.on_custom_convert)
        custom_box.append(convert_btn)
        custom_frame.set_child(custom_box)
        vbox.append(custom_frame)

        ops_frame = Gtk.Frame(label="Binary Arithmetic")
        ops_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        ops_box.set_margin_top(6); ops_box.set_margin_start(6); ops_box.set_margin_end(6); ops_box.set_margin_bottom(6)
        row1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row1.append(Gtk.Label(label="A (dec):"))
        self.arith_a = Gtk.SpinButton.new_with_range(0, 255, 1)
        self.arith_a.set_value(42); self.arith_a.connect("value-changed", self.on_arith)
        row1.append(self.arith_a)
        row1.append(Gtk.Label(label="Op:"))
        self.op_combo = Gtk.ComboBoxText()
        for op in ["AND", "OR", "XOR", "NOT A", "Left Shift", "Right Shift"]:
            self.op_combo.append_text(op)
        self.op_combo.set_active(0)
        self.op_combo.connect("changed", self.on_arith)
        row1.append(self.op_combo)
        row1.append(Gtk.Label(label="B (dec):"))
        self.arith_b = Gtk.SpinButton.new_with_range(0, 255, 1)
        self.arith_b.set_value(15); self.arith_b.connect("value-changed", self.on_arith)
        row1.append(self.arith_b)
        ops_box.append(row1)
        self.arith_result = Gtk.Label(label="Result: --", xalign=0)
        self.arith_result.set_selectable(True)
        ops_box.append(self.arith_result)
        ops_frame.set_child(ops_box)
        vbox.append(ops_frame)

        info_frame = Gtk.Frame(label="Bit Pattern (8-bit)")
        self.bit_area = Gtk.DrawingArea()
        self.bit_area.set_size_request(-1, 60)
        self.bit_area.set_draw_func(self.draw_bits)
        info_frame.set_child(self.bit_area)
        vbox.append(info_frame)

        self.current_value = 42
        self.on_arith(None)

    def on_changed(self, entry):
        if self._updating:
            return
        self._updating = True
        text = entry.get_text().strip()
        if not text:
            self._updating = False
            return
        base = entry._base
        try:
            value = int(text, base)
            self.current_value = value
            for b, e in self.entries.items():
                if e is not entry:
                    e.set_text(self.to_base(value, b))
            self.bit_area.queue_draw()
            self.on_custom_convert(None)
        except ValueError:
            pass
        self._updating = False

    def to_base(self, n, base):
        if n == 0:
            return "0"
        digits = "0123456789abcdefghijklmnopqrstuvwxyz"
        result = ""
        while n > 0:
            result = digits[n % base] + result
            n //= base
        return result.upper() if base == 16 else result

    def on_custom_convert(self, widget):
        base = int(self.custom_base_spin.get_value())
        result = self.to_base(self.current_value, base)
        self.custom_result.set_text(result.upper())

    def on_arith(self, widget):
        a = int(self.arith_a.get_value())
        b = int(self.arith_b.get_value())
        op = self.op_combo.get_active_text()
        if op == "AND":
            r = a & b
        elif op == "OR":
            r = a | b
        elif op == "XOR":
            r = a ^ b
        elif op == "NOT A":
            r = ~a & 0xFF
        elif op == "Left Shift":
            r = (a << 1) & 0xFF
        elif op == "Right Shift":
            r = (a >> 1)
        else:
            r = 0
        a_bin = f"{a:08b}"
        b_bin = f"{b:08b}"
        r_bin = f"{r & 0xFF:08b}"
        self.arith_result.set_text(
            f"{a_bin} {op} {b_bin} = {r_bin} (dec: {r & 0xFF}, hex: {r & 0xFF:02X})"
        )
        self.current_value = r & 0xFF
        self.bit_area.queue_draw()

    def draw_bits(self, area, cr, w, h):
        cr.set_source_rgb(0.1, 0.1, 0.15)
        cr.rectangle(0, 0, w, h)
        cr.fill()
        val = self.current_value & 0xFF
        bits = 8
        cell_w = w // bits
        for i in range(bits):
            bit = (val >> (7 - i)) & 1
            x = i * cell_w
            if bit:
                cr.set_source_rgb(0.3, 0.7, 0.3)
            else:
                cr.set_source_rgb(0.2, 0.2, 0.3)
            cr.rectangle(x + 2, 4, cell_w - 4, h - 20)
            cr.fill()
            cr.set_source_rgb(0.9, 0.9, 0.9)
            cr.set_font_size(14)
            cr.move_to(x + cell_w // 2 - 5, h - 16)
            cr.show_text(str(bit))
            cr.set_font_size(8)
            cr.move_to(x + 4, h - 4)
            cr.show_text(str(7 - i))

class NumberSystemsApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.NumberSystems")
    def do_activate(self):
        win = NumberSystemsWindow(self); win.present()

def main():
    app = NumberSystemsApp(); app.run(None)

if __name__ == "__main__":
    main()
