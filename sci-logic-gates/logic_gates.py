#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import math

GATES = {
    "AND":  lambda a, b: a and b,
    "OR":   lambda a, b: a or b,
    "NOT":  lambda a, b: not a,
    "NAND": lambda a, b: not (a and b),
    "NOR":  lambda a, b: not (a or b),
    "XOR":  lambda a, b: a != b,
    "XNOR": lambda a, b: a == b,
    "BUFFER": lambda a, b: a,
}

class LogicGatesWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Logic Gates Simulator")
        self.set_default_size(800, 580)
        self.a_val = False
        self.b_val = False
        self.gate = "AND"
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(12); vbox.set_margin_bottom(12)
        vbox.set_margin_start(16); vbox.set_margin_end(16)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Logic Gates Simulator", css_classes=["title"]))

        gate_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        gate_box.set_halign(Gtk.Align.CENTER)
        gate_box.append(Gtk.Label(label="Gate:"))
        self.gate_combo = Gtk.ComboBoxText()
        for g in GATES:
            self.gate_combo.append_text(g)
        self.gate_combo.set_active(0)
        self.gate_combo.connect("changed", self.on_gate_changed)
        gate_box.append(self.gate_combo)
        vbox.append(gate_box)

        inputs_frame = Gtk.Frame(label="Inputs")
        inputs_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=30)
        inputs_box.set_halign(Gtk.Align.CENTER)
        inputs_box.set_margin_top(10); inputs_box.set_margin_bottom(10)

        a_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        a_vbox.set_halign(Gtk.Align.CENTER)
        a_vbox.append(Gtk.Label(label="Input A"))
        self.a_btn = Gtk.Button(label="0")
        self.a_btn.set_size_request(80, 60)
        self.a_btn.connect("clicked", lambda b: self.toggle_input("a"))
        a_vbox.append(self.a_btn)
        inputs_box.append(a_vbox)

        b_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        b_vbox.set_halign(Gtk.Align.CENTER)
        b_vbox.append(Gtk.Label(label="Input B"))
        self.b_btn = Gtk.Button(label="0")
        self.b_btn.set_size_request(80, 60)
        self.b_btn.connect("clicked", lambda b: self.toggle_input("b"))
        b_vbox.append(self.b_btn)
        inputs_box.append(b_vbox)

        inputs_frame.set_child(inputs_box)
        vbox.append(inputs_frame)

        diagram_frame = Gtk.Frame(label="Gate Diagram")
        self.diagram = Gtk.DrawingArea()
        self.diagram.set_size_request(-1, 140)
        self.diagram.set_draw_func(self.draw_diagram)
        diagram_frame.set_child(self.diagram)
        vbox.append(diagram_frame)

        result_frame = Gtk.Frame(label="Output")
        result_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        result_box.set_halign(Gtk.Align.CENTER)
        result_box.set_margin_top(10); result_box.set_margin_bottom(10)
        self.output_label = Gtk.Label(label="0")
        self.output_label.set_markup("<span font='48' weight='bold'>0</span>")
        result_box.append(self.output_label)
        self.result_text = Gtk.Label(label="FALSE")
        self.result_text.set_markup("<span font='20'>FALSE</span>")
        result_box.append(self.result_text)
        result_frame.set_child(result_box)
        vbox.append(result_frame)

        truth_frame = Gtk.Frame(label="Truth Table")
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(120)
        self.truth_view = Gtk.TextView()
        self.truth_view.set_editable(False)
        self.truth_view.set_monospace(True)
        scroll.set_child(self.truth_view)
        truth_frame.set_child(scroll)
        vbox.append(truth_frame)

        boolean_frame = Gtk.Frame(label="Boolean Expression Builder")
        bool_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bool_box.set_margin_top(4); bool_box.set_margin_start(4); bool_box.set_margin_end(4); bool_box.set_margin_bottom(4)
        self.bool_entry = Gtk.Entry()
        self.bool_entry.set_placeholder_text("e.g. (A AND B) OR (NOT A)")
        self.bool_entry.set_hexpand(True)
        bool_box.append(self.bool_entry)
        eval_btn = Gtk.Button(label="Evaluate")
        eval_btn.connect("clicked", self.on_eval_expr)
        bool_box.append(eval_btn)
        self.bool_result = Gtk.Label(label="")
        bool_box.append(self.bool_result)
        boolean_frame.set_child(bool_box)
        vbox.append(boolean_frame)

        self.update_all()

    def toggle_input(self, which):
        if which == "a":
            self.a_val = not self.a_val
        else:
            self.b_val = not self.b_val
        self.update_all()

    def on_gate_changed(self, combo):
        self.gate = combo.get_active_text()
        self.update_all()

    def update_all(self):
        a, b = self.a_val, self.b_val
        result = GATES[self.gate](a, b)

        def style_btn(btn, val):
            css = Gtk.CssProvider()
            if val:
                css.load_from_data(b"button { background: #2d7a2d; color: white; font-size: 24px; font-weight: bold; }")
            else:
                css.load_from_data(b"button { background: #3a3a3a; color: #aaa; font-size: 24px; }")
            btn.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            btn.set_label("1" if val else "0")

        style_btn(self.a_btn, a)
        style_btn(self.b_btn, b)

        color = "#98c379" if result else "#e06c75"
        self.output_label.set_markup(f"<span font='48' weight='bold' foreground='{color}'>{'1' if result else '0'}</span>")
        self.result_text.set_markup(f"<span font='20' foreground='{color}'>{'TRUE' if result else 'FALSE'}</span>")
        self.diagram.queue_draw()
        self.refresh_truth_table()

    def refresh_truth_table(self):
        gate_fn = GATES[self.gate]
        lines = [f"Truth Table: {self.gate}\n"]
        if self.gate in ("NOT", "BUFFER"):
            lines.append(f"{'A':<6} | {'Out':<6}")
            lines.append("-" * 15)
            for a in [False, True]:
                r = gate_fn(a, False)
                lines.append(f"{'1' if a else '0':<6} | {'1' if r else '0':<6}")
        else:
            lines.append(f"{'A':<6} | {'B':<6} | {'Out':<6}")
            lines.append("-" * 22)
            for a in [False, True]:
                for b in [False, True]:
                    r = gate_fn(a, b)
                    marker = " ←" if (a == self.a_val and b == self.b_val) else ""
                    lines.append(f"{'1' if a else '0':<6} | {'1' if b else '0':<6} | {'1' if r else '0':<6}{marker}")
        self.truth_view.get_buffer().set_text("\n".join(lines))

    def draw_diagram(self, area, cr, w, h):
        cr.set_source_rgb(0.08, 0.08, 0.12); cr.rectangle(0, 0, w, h); cr.fill()
        cx, cy = w // 2, h // 2
        cr.set_line_width(2)

        a_color = (0.2, 0.8, 0.2) if self.a_val else (0.5, 0.5, 0.5)
        b_color = (0.2, 0.8, 0.2) if self.b_val else (0.5, 0.5, 0.5)
        result = GATES[self.gate](self.a_val, self.b_val)
        r_color = (0.2, 0.8, 0.2) if result else (0.8, 0.2, 0.2)

        # Input lines
        cr.set_source_rgb(*a_color)
        cr.move_to(50, cy - 20); cr.line_to(cx - 40, cy - 20); cr.stroke()
        cr.set_source_rgb(*b_color)
        if self.gate not in ("NOT", "BUFFER"):
            cr.move_to(50, cy + 20); cr.line_to(cx - 40, cy + 20); cr.stroke()

        # Gate body
        cr.set_source_rgb(0.4, 0.5, 0.7)
        cr.rectangle(cx - 40, cy - 30, 80, 60); cr.stroke()
        cr.set_source_rgb(0.2, 0.3, 0.5)
        cr.rectangle(cx - 40, cy - 30, 80, 60); cr.fill()

        cr.set_source_rgb(0.9, 0.9, 0.9); cr.set_font_size(14)
        gate_str = self.gate
        cr.move_to(cx - len(gate_str) * 4, cy + 5)
        cr.show_text(gate_str)

        # Output line
        cr.set_source_rgb(*r_color)
        cr.move_to(cx + 40, cy); cr.line_to(w - 50, cy); cr.stroke()

        # Labels
        cr.set_source_rgb(0.8, 0.8, 0.8); cr.set_font_size(11)
        cr.move_to(10, cy - 15); cr.show_text(f"A={'1' if self.a_val else '0'}")
        if self.gate not in ("NOT", "BUFFER"):
            cr.move_to(10, cy + 25); cr.show_text(f"B={'1' if self.b_val else '0'}")
        cr.set_source_rgb(*r_color)
        cr.move_to(w - 45, cy - 8); cr.show_text(f"Q={'1' if result else '0'}")

    def on_eval_expr(self, btn):
        expr = self.bool_entry.get_text().upper()
        A, B = self.a_val, self.b_val
        try:
            result = eval(
                expr.replace("AND", " and ").replace("OR", " or ").replace("NOT", " not ").replace("XOR", "!="),
                {"A": A, "B": B, "__builtins__": {}}
            )
            color = "#98c379" if result else "#e06c75"
            self.bool_result.set_markup(f"<span foreground='{color}'> = {'1' if result else '0'} ({'TRUE' if result else 'FALSE'})</span>")
        except Exception as e:
            self.bool_result.set_text(f"Error: {e}")

class LogicGatesApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.LogicGates")
    def do_activate(self):
        win = LogicGatesWindow(self); win.present()

def main():
    app = LogicGatesApp(); app.run(None)

if __name__ == "__main__":
    main()
