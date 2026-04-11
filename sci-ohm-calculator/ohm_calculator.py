#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import math

class OhmCalculatorWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Ohm's Law Calculator")
        self.set_default_size(660, 580)
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(16); vbox.set_margin_bottom(16)
        vbox.set_margin_start(20); vbox.set_margin_end(20)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Ohm's Law Calculator", css_classes=["title"]))
        vbox.append(Gtk.Label(label="V = I × R    P = V × I = I² × R = V²/R", xalign=0.5))

        grid = Gtk.Grid()
        grid.set_row_spacing(8); grid.set_column_spacing(12)

        fields = [
            ("Voltage (V):", "V", "volts"),
            ("Current (I):", "A", "amperes"),
            ("Resistance (R):", "Ω", "ohms"),
            ("Power (P):", "W", "watts"),
        ]
        self.entries = {}
        for row, (label, unit, name) in enumerate(fields):
            lbl = Gtk.Label(label=label, xalign=1)
            entry = Gtk.Entry()
            entry.set_hexpand(True)
            entry.set_placeholder_text(f"Enter {name}...")
            entry._field = unit
            unit_lbl = Gtk.Label(label=unit)
            grid.attach(lbl, 0, row, 1, 1)
            grid.attach(entry, 1, row, 1, 1)
            grid.attach(unit_lbl, 2, row, 1, 1)
            self.entries[unit] = entry
        vbox.append(grid)

        note = Gtk.Label(label="Enter any 2 values and click Calculate (leave others blank)")
        note.set_xalign(0)
        vbox.append(note)

        calc_btn = Gtk.Button(label="Calculate")
        calc_btn.set_halign(Gtk.Align.CENTER)
        calc_btn.connect("clicked", self.on_calculate)
        vbox.append(calc_btn)

        clear_btn = Gtk.Button(label="Clear All")
        clear_btn.set_halign(Gtk.Align.CENTER)
        clear_btn.connect("clicked", self.on_clear)
        vbox.append(clear_btn)

        self.result_label = Gtk.Label(label="")
        self.result_label.set_wrap(True)
        self.result_label.set_selectable(True)
        vbox.append(self.result_label)

        diagram_frame = Gtk.Frame(label="Circuit Diagram")
        self.diagram = Gtk.DrawingArea()
        self.diagram.set_size_request(-1, 160)
        self.diagram.set_draw_func(self.draw_diagram)
        diagram_frame.set_child(self.diagram)
        vbox.append(diagram_frame)

        resistor_frame = Gtk.Frame(label="Resistor Color Code")
        r_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        r_box.set_margin_top(4); r_box.set_margin_start(4); r_box.set_margin_end(4); r_box.set_margin_bottom(4)
        r_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        r_row.append(Gtk.Label(label="Resistance (Ω):"))
        self.res_entry = Gtk.Entry(); self.res_entry.set_placeholder_text("e.g. 4700")
        r_row.append(self.res_entry)
        decode_btn = Gtk.Button(label="Decode Color Bands")
        decode_btn.connect("clicked", self.on_decode_resistor)
        r_row.append(decode_btn)
        r_box.append(r_row)
        self.color_label = Gtk.Label(label="")
        self.color_label.set_selectable(True)
        r_box.append(self.color_label)
        resistor_frame.set_child(r_box)
        vbox.append(resistor_frame)

        self.V = None; self.I = None; self.R = None; self.P = None

    def on_clear(self, btn):
        for e in self.entries.values():
            e.set_text("")
        self.result_label.set_text("")
        self.V = self.I = self.R = self.P = None
        self.diagram.queue_draw()

    def get_val(self, field):
        txt = self.entries[field].get_text().strip()
        if not txt:
            return None
        try:
            return float(txt)
        except ValueError:
            return None

    def on_calculate(self, btn):
        V = self.get_val("V"); I = self.get_val("A")
        R = self.get_val("Ω"); P = self.get_val("W")
        known = sum(1 for x in [V, I, R, P] if x is not None)
        if known < 2:
            self.result_label.set_text("Please enter at least 2 values")
            return

        # Solve for unknowns
        if V is None and I is not None and R is not None: V = I * R
        if V is None and P is not None and I is not None: V = P / I
        if V is None and P is not None and R is not None: V = math.sqrt(P * R)
        if I is None and V is not None and R is not None: I = V / R
        if I is None and P is not None and V is not None: I = P / V
        if I is None and P is not None and R is not None: I = math.sqrt(P / R)
        if R is None and V is not None and I is not None: R = V / I if I != 0 else None
        if R is None and V is not None and P is not None: R = V**2 / P if P != 0 else None
        if R is None and I is not None and P is not None: R = P / I**2 if I != 0 else None
        if P is None and V is not None and I is not None: P = V * I
        if P is None and V is not None and R is not None: P = V**2 / R if R != 0 else None
        if P is None and I is not None and R is not None: P = I**2 * R

        for field, val in [("V", V), ("A", I), ("Ω", R), ("W", P)]:
            if val is not None:
                self.entries[field].set_text(f"{val:.4g}")

        self.V = V; self.I = I; self.R = R; self.P = P

        lines = []
        if all(x is not None for x in [V, I, R, P]):
            lines = [f"Voltage:    {V:.4g} V", f"Current:    {I:.4g} A",
                     f"Resistance: {R:.4g} Ω", f"Power:      {P:.4g} W"]
            if P:
                t = P * 3600
                lines.append(f"Energy/hr:  {t:.4g} J = {t/1000:.4g} kJ")
        self.result_label.set_text("\n".join(lines))
        self.diagram.queue_draw()

    def draw_diagram(self, area, cr, w, h):
        cr.set_source_rgb(0.08, 0.08, 0.12); cr.rectangle(0, 0, w, h); cr.fill()
        cx, cy = w // 2, h // 2
        cr.set_source_rgb(0.7, 0.7, 0.9); cr.set_line_width(2)
        margin = 40
        cr.rectangle(margin, cy - 30, w - 2 * margin, 60); cr.stroke()

        # Battery (left)
        bx = margin + 20
        cr.set_line_width(3)
        for i, thick in [(0, True), (1, False), (2, True), (3, False)]:
            x = bx + i * 8
            ht = 16 if thick else 10
            cr.move_to(x, cy - ht); cr.line_to(x, cy + ht); cr.stroke()
            cr.set_line_width(2) if thick else cr.set_line_width(1.5)
        cr.set_source_rgb(0.7, 0.9, 0.7)
        cr.set_font_size(10)
        if self.V: cr.move_to(bx - 10, cy - 35); cr.show_text(f"V={self.V:.3g}V")

        # Resistor (right)
        rx = w - margin - 60
        cr.set_source_rgb(0.9, 0.7, 0.3); cr.set_line_width(2)
        cr.rectangle(rx, cy - 12, 40, 24); cr.stroke()
        cr.set_source_rgb(0.7, 0.7, 0.7)
        if self.R: cr.move_to(rx + 2, cy - 18); cr.show_text(f"R={self.R:.3g}Ω")

        # Arrows for current
        if self.I and self.I > 0:
            cr.set_source_rgb(0.9, 0.5, 0.3)
            arrow_y = cy - 30
            cr.move_to(w // 2 - 20, arrow_y); cr.line_to(w // 2 + 20, arrow_y); cr.stroke()
            cr.move_to(w // 2 + 15, arrow_y - 5); cr.line_to(w // 2 + 20, arrow_y); cr.line_to(w // 2 + 15, arrow_y + 5); cr.stroke()
            cr.move_to(w // 2, arrow_y - 15); cr.show_text(f"I={self.I:.3g}A")

        if self.P:
            cr.set_source_rgb(0.9, 0.9, 0.3)
            cr.move_to(w // 2 - 30, cy + 45); cr.show_text(f"P={self.P:.3g}W")

    COLORS = ["black","brown","red","orange","yellow","green","blue","violet","gray","white","gold","silver"]
    CVALS = [0,1,2,3,4,5,6,7,8,9,0.1,0.01]

    def on_decode_resistor(self, btn):
        txt = self.res_entry.get_text().strip()
        if not txt:
            return
        try:
            val = float(txt)
        except ValueError:
            self.color_label.set_text("Invalid value")
            return
        if val <= 0:
            self.color_label.set_text("Value must be positive")
            return
        sig = f"{val:.2e}"
        mantissa, exp = sig.split("e")
        d1 = int(mantissa[0])
        d2 = int(mantissa[2])
        mult = int(exp)
        multiplier = mult - 1
        bands = [self.COLORS[d1], self.COLORS[d2]]
        if multiplier >= 0:
            bands.append(self.COLORS[multiplier] if multiplier < 10 else "?")
        else:
            bands.append("gold" if multiplier == -1 else "silver")
        self.color_label.set_text(f"Color Bands: {bands[0]} | {bands[1]} | {bands[2]} | gold (±5%)")

class OhmCalculatorApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.OhmCalculator")
    def do_activate(self):
        win = OhmCalculatorWindow(self); win.present()

def main():
    app = OhmCalculatorApp(); app.run(None)

if __name__ == "__main__":
    main()
