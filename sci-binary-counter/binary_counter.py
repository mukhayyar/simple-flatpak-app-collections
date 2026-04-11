#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

class BinaryCounterWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Binary Counter")
        self.set_default_size(700, 560)
        self.count = 0
        self.bits = 8
        self.running = False
        self.speed = 500
        self.build_ui()
        self.update_display()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(16); vbox.set_margin_bottom(16)
        vbox.set_margin_start(20); vbox.set_margin_end(20)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Binary Counter", css_classes=["title"]))

        cfg_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        cfg_box.set_halign(Gtk.Align.CENTER)
        cfg_box.append(Gtk.Label(label="Bits:"))
        self.bits_combo = Gtk.ComboBoxText()
        for b in ["4", "8", "16"]:
            self.bits_combo.append_text(b)
        self.bits_combo.set_active(1)
        self.bits_combo.connect("changed", self.on_bits_changed)
        cfg_box.append(self.bits_combo)
        cfg_box.append(Gtk.Label(label="Speed (ms):"))
        self.speed_spin = Gtk.SpinButton.new_with_range(50, 2000, 50)
        self.speed_spin.set_value(500)
        self.speed_spin.connect("value-changed", lambda s: setattr(self, "speed", int(s.get_value())))
        cfg_box.append(self.speed_spin)
        vbox.append(cfg_box)

        # Bit LEDs
        led_frame = Gtk.Frame(label="Binary Display")
        self.led_area = Gtk.DrawingArea()
        self.led_area.set_size_request(-1, 100)
        self.led_area.set_draw_func(self.draw_leds)
        led_frame.set_child(self.led_area)
        vbox.append(led_frame)

        # Value display
        values_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        values_box.set_halign(Gtk.Align.CENTER)
        self.dec_label = Gtk.Label(label="DEC: 0")
        self.hex_label = Gtk.Label(label="HEX: 0x00")
        self.oct_label = Gtk.Label(label="OCT: 00")
        for lbl in [self.dec_label, self.hex_label, self.oct_label]:
            lbl.set_css_classes(["heading"])
            values_box.append(lbl)
        vbox.append(values_box)

        # Manual bit toggle
        tog_frame = Gtk.Frame(label="Toggle Bits Manually")
        self.toggle_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.toggle_box.set_halign(Gtk.Align.CENTER)
        self.toggle_box.set_margin_top(6); self.toggle_box.set_margin_bottom(6)
        self.bit_btns = []
        tog_frame.set_child(self.toggle_box)
        vbox.append(tog_frame)

        ctrl_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        ctrl_box.set_halign(Gtk.Align.CENTER)
        self.play_btn = Gtk.Button(label="▶ Auto Count")
        self.play_btn.connect("clicked", self.on_play)
        step_up_btn = Gtk.Button(label="+1")
        step_up_btn.connect("clicked", lambda b: self.step(1))
        step_dn_btn = Gtk.Button(label="-1")
        step_dn_btn.connect("clicked", lambda b: self.step(-1))
        reset_btn = Gtk.Button(label="Reset")
        reset_btn.connect("clicked", lambda b: self.set_count(0))
        ctrl_box.append(self.play_btn); ctrl_box.append(step_up_btn)
        ctrl_box.append(step_dn_btn); ctrl_box.append(reset_btn)
        vbox.append(ctrl_box)

        # Set value
        set_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        set_box.set_halign(Gtk.Align.CENTER)
        set_box.append(Gtk.Label(label="Set value (dec):"))
        self.set_entry = Gtk.Entry()
        self.set_entry.set_placeholder_text("0-255")
        set_box.append(self.set_entry)
        set_btn = Gtk.Button(label="Set")
        set_btn.connect("clicked", self.on_set)
        set_box.append(set_btn)
        set_box.append(Gtk.Label(label="Hex:"))
        self.hex_entry = Gtk.Entry()
        self.hex_entry.set_placeholder_text("0x00")
        set_box.append(self.hex_entry)
        hex_btn = Gtk.Button(label="Set Hex")
        hex_btn.connect("clicked", self.on_set_hex)
        set_box.append(hex_btn)
        vbox.append(set_box)

        # Arithmetic
        arith_frame = Gtk.Frame(label="Bitwise Operations")
        arith_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        arith_box.set_margin_top(4); arith_box.set_margin_start(4); arith_box.set_margin_end(4); arith_box.set_margin_bottom(4)
        arith_box.append(Gtk.Label(label="Operand:"))
        self.op_entry = Gtk.Entry(); self.op_entry.set_text("15"); self.op_entry.set_size_request(60, -1)
        arith_box.append(self.op_entry)
        for op_name, op_fn in [("AND", lambda a,b: a&b), ("OR", lambda a,b: a|b),
                                ("XOR", lambda a,b: a^b), ("NOT", lambda a,b: (~a)&self.max_val()),
                                ("<<1", lambda a,b: (a<<1)&self.max_val()), (">>1", lambda a,b: a>>1)]:
            btn = Gtk.Button(label=op_name)
            btn.connect("clicked", self.on_bitwise, op_fn)
            arith_box.append(btn)
        arith_frame.set_child(arith_box)
        vbox.append(arith_frame)

        self.rebuild_toggles()

    def max_val(self):
        return (1 << self.bits) - 1

    def on_bits_changed(self, combo):
        self.bits = int(combo.get_active_text())
        self.count = self.count & self.max_val()
        self.rebuild_toggles()
        self.update_display()

    def rebuild_toggles(self):
        while self.toggle_box.get_first_child():
            self.toggle_box.remove(self.toggle_box.get_first_child())
        self.bit_btns = []
        for i in range(self.bits - 1, -1, -1):
            btn = Gtk.Button(label=f"b{i}")
            btn.set_size_request(44, 36)
            btn.connect("clicked", self.on_toggle_bit, i)
            self.toggle_box.append(btn)
            self.bit_btns.append((i, btn))

    def on_toggle_bit(self, btn, bit):
        self.count ^= (1 << bit)
        self.count &= self.max_val()
        self.update_display()

    def set_count(self, v):
        self.count = v & self.max_val()
        self.update_display()

    def step(self, delta):
        self.count = (self.count + delta) & self.max_val()
        self.update_display()

    def on_play(self, btn):
        self.running = not self.running
        self.play_btn.set_label("⏸ Pause" if self.running else "▶ Auto Count")
        if self.running:
            GLib.timeout_add(self.speed, self.auto_step)

    def auto_step(self):
        if self.running:
            self.step(1)
            GLib.timeout_add(self.speed, self.auto_step)
        return False

    def on_set(self, btn):
        try:
            v = int(self.set_entry.get_text())
            self.set_count(v)
        except ValueError:
            pass

    def on_set_hex(self, btn):
        try:
            v = int(self.hex_entry.get_text(), 16)
            self.set_count(v)
        except ValueError:
            pass

    def on_bitwise(self, btn, op_fn):
        try:
            operand = int(self.op_entry.get_text())
        except ValueError:
            operand = 0
        self.set_count(op_fn(self.count, operand))

    def update_display(self):
        n = self.count
        b = self.bits
        self.dec_label.set_text(f"DEC: {n}")
        self.hex_label.set_text(f"HEX: 0x{n:0{b//4}X}")
        self.oct_label.set_text(f"OCT: {oct(n)}")
        self.led_area.queue_draw()

        for i, btn in self.bit_btns:
            bit_val = (n >> i) & 1
            css = Gtk.CssProvider()
            if bit_val:
                css.load_from_data(b"button { background: #2a7a2a; color: white; font-weight: bold; }")
            else:
                css.load_from_data(b"button { background: #333; color: #888; }")
            btn.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def draw_leds(self, area, cr, w, h):
        cr.set_source_rgb(0.08, 0.08, 0.12); cr.rectangle(0, 0, w, h); cr.fill()
        n = self.count
        b = self.bits
        cell_w = w / b
        for i in range(b):
            bit_pos = b - 1 - i
            bit_val = (n >> bit_pos) & 1
            x = i * cell_w
            cr.set_source_rgb(0.9, 0.7, 0.2) if bit_val else cr.set_source_rgb(0.2, 0.2, 0.2)
            cr.arc(x + cell_w/2, h/2, min(cell_w/2 - 4, h/2 - 8), 0, 3.14159*2)
            cr.fill()
            cr.set_source_rgb(0.9, 0.9, 0.9); cr.set_font_size(11)
            cr.move_to(x + cell_w/2 - 3, h - 6)
            cr.show_text(str(bit_val))
            cr.set_font_size(8)
            cr.move_to(x + cell_w/2 - 5, 14)
            cr.show_text(str(bit_pos))

class BinaryCounterApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.BinaryCounter")
    def do_activate(self):
        win = BinaryCounterWindow(self); win.present()

def main():
    app = BinaryCounterApp(); app.run(None)

if __name__ == "__main__":
    main()
