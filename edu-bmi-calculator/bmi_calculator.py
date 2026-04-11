#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import math

class BMICalculatorWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("BMI Calculator")
        self.set_default_size(500, 560)
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(16); vbox.set_margin_bottom(16)
        vbox.set_margin_start(20); vbox.set_margin_end(20)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="BMI Calculator", css_classes=["title"]))

        unit_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        unit_box.set_halign(Gtk.Align.CENTER)
        self.metric_radio = Gtk.CheckButton(label="Metric (cm/kg)")
        self.metric_radio.set_active(True)
        self.imperial_radio = Gtk.CheckButton(label="Imperial (ft/in/lbs)")
        self.imperial_radio.set_group(self.metric_radio)
        self.metric_radio.connect("toggled", self.on_unit_changed)
        unit_box.append(self.metric_radio); unit_box.append(self.imperial_radio)
        vbox.append(unit_box)

        self.metric_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        h_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        h_box.append(Gtk.Label(label="Height (cm):"))
        self.height_spin = Gtk.SpinButton.new_with_range(50, 250, 0.5)
        self.height_spin.set_value(170); self.height_spin.set_hexpand(True)
        self.height_spin.connect("value-changed", self.on_calc)
        h_box.append(self.height_spin)
        self.metric_box.append(h_box)
        w_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        w_box.append(Gtk.Label(label="Weight (kg):"))
        self.weight_spin = Gtk.SpinButton.new_with_range(10, 300, 0.5)
        self.weight_spin.set_value(70); self.weight_spin.set_hexpand(True)
        self.weight_spin.connect("value-changed", self.on_calc)
        w_box.append(self.weight_spin)
        self.metric_box.append(w_box)
        vbox.append(self.metric_box)

        self.imperial_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        ft_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        ft_box.append(Gtk.Label(label="Height (ft):"))
        self.ft_spin = Gtk.SpinButton.new_with_range(1, 8, 1)
        self.ft_spin.set_value(5); self.ft_spin.connect("value-changed", self.on_calc)
        ft_box.append(self.ft_spin)
        ft_box.append(Gtk.Label(label="in:"))
        self.in_spin = Gtk.SpinButton.new_with_range(0, 11, 1)
        self.in_spin.set_value(7); self.in_spin.connect("value-changed", self.on_calc)
        ft_box.append(self.in_spin)
        self.imperial_box.append(ft_box)
        lbs_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lbs_box.append(Gtk.Label(label="Weight (lbs):"))
        self.lbs_spin = Gtk.SpinButton.new_with_range(20, 700, 1)
        self.lbs_spin.set_value(154); self.lbs_spin.set_hexpand(True)
        self.lbs_spin.connect("value-changed", self.on_calc)
        lbs_box.append(self.lbs_spin)
        self.imperial_box.append(lbs_box)
        self.imperial_box.set_visible(False)
        vbox.append(self.imperial_box)

        age_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        age_box.append(Gtk.Label(label="Age:"))
        self.age_spin = Gtk.SpinButton.new_with_range(2, 120, 1)
        self.age_spin.set_value(30); self.age_spin.connect("value-changed", self.on_calc)
        age_box.append(self.age_spin)
        age_box.append(Gtk.Label(label="Gender:"))
        self.gender_combo = Gtk.ComboBoxText()
        self.gender_combo.append_text("Male")
        self.gender_combo.append_text("Female")
        self.gender_combo.set_active(0)
        self.gender_combo.connect("changed", self.on_calc)
        age_box.append(self.gender_combo)
        vbox.append(age_box)

        self.bmi_label = Gtk.Label(label="BMI: --")
        self.bmi_label.set_markup("<span font='28' weight='bold'>BMI: --</span>")
        vbox.append(self.bmi_label)

        self.category_label = Gtk.Label(label="")
        self.category_label.set_markup("<span font='16'>Category: --</span>")
        vbox.append(self.category_label)

        self.gauge = Gtk.DrawingArea()
        self.gauge.set_size_request(-1, 80)
        self.gauge.set_draw_func(self.draw_gauge)
        vbox.append(self.gauge)

        self.info_label = Gtk.Label(label="")
        self.info_label.set_wrap(True)
        self.info_label.set_xalign(0)
        vbox.append(self.info_label)

        self.bmi_value = 0
        self.on_calc(None)

    def on_unit_changed(self, btn):
        metric = self.metric_radio.get_active()
        self.metric_box.set_visible(metric)
        self.imperial_box.set_visible(not metric)
        self.on_calc(None)

    def on_calc(self, widget):
        if self.metric_radio.get_active():
            h = self.height_spin.get_value() / 100
            w = self.weight_spin.get_value()
        else:
            ft = self.ft_spin.get_value()
            inch = self.in_spin.get_value()
            total_inches = ft * 12 + inch
            h = total_inches * 0.0254
            w = self.lbs_spin.get_value() * 0.453592

        if h <= 0:
            return
        bmi = w / (h * h)
        self.bmi_value = bmi

        if bmi < 18.5:
            cat, color = "Underweight", "#61afef"
        elif bmi < 25:
            cat, color = "Normal weight", "#98c379"
        elif bmi < 30:
            cat, color = "Overweight", "#e5c07b"
        else:
            cat, color = "Obese", "#e06c75"

        self.bmi_label.set_markup(f"<span font='28' weight='bold'>BMI: {bmi:.1f}</span>")
        self.category_label.set_markup(f"<span font='16' foreground='{color}'>{cat}</span>")

        ideal_low = 18.5 * h * h
        ideal_high = 24.9 * h * h
        unit = "kg" if self.metric_radio.get_active() else "lbs"
        mult = 1 if self.metric_radio.get_active() else 2.205
        info = (f"Ideal weight range: {ideal_low*mult:.1f} – {ideal_high*mult:.1f} {unit}\n"
                f"BMR (est.): {self.calc_bmr(w, h):.0f} kcal/day")
        self.info_label.set_text(info)
        self.gauge.queue_draw()

    def calc_bmr(self, w_kg, h_m):
        age = self.age_spin.get_value()
        h_cm = h_m * 100
        if self.gender_combo.get_active() == 0:
            return 88.362 + (13.397 * w_kg) + (4.799 * h_cm) - (5.677 * age)
        else:
            return 447.593 + (9.247 * w_kg) + (3.098 * h_cm) - (4.330 * age)

    def draw_gauge(self, area, cr, w, h):
        cr.set_source_rgb(0.15, 0.15, 0.2); cr.rectangle(0, 0, w, h); cr.fill()
        segments = [(0, 18.5, (0.38, 0.69, 0.94)), (18.5, 25, (0.6, 0.76, 0.48)),
                    (25, 30, (0.9, 0.75, 0.48)), (30, 40, (0.88, 0.38, 0.46))]
        total_range = 40
        bar_h = 24
        y = (h - bar_h) // 2
        for start, end, color in segments:
            x1 = int(start / total_range * w)
            x2 = int(end / total_range * w)
            cr.set_source_rgb(*color); cr.rectangle(x1, y, x2 - x1, bar_h); cr.fill()
        if self.bmi_value > 0:
            bmi_x = min(int(self.bmi_value / total_range * w), w - 4)
            cr.set_source_rgb(1, 1, 1)
            cr.rectangle(bmi_x - 2, y - 6, 4, bar_h + 12)
            cr.fill()
        cr.set_source_rgb(0.8, 0.8, 0.8); cr.set_font_size(10)
        for val in [0, 18.5, 25, 30, 40]:
            xv = int(val / total_range * w)
            cr.move_to(xv + 2, y + bar_h + 14); cr.show_text(str(val))

class BMICalculatorApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.BMICalculator")
    def do_activate(self):
        win = BMICalculatorWindow(self); win.present()

def main():
    app = BMICalculatorApp(); app.run(None)

if __name__ == "__main__":
    main()
