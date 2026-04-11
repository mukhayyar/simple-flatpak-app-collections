#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

CONVERSIONS = {
    "Length": {
        "meters": 1.0,
        "kilometers": 1000.0,
        "centimeters": 0.01,
        "millimeters": 0.001,
        "micrometers": 1e-6,
        "nanometers": 1e-9,
        "miles": 1609.344,
        "yards": 0.9144,
        "feet": 0.3048,
        "inches": 0.0254,
        "nautical miles": 1852.0,
        "light years": 9.461e15,
        "astronomical units": 1.496e11,
    },
    "Mass": {
        "kilograms": 1.0,
        "grams": 0.001,
        "milligrams": 1e-6,
        "micrograms": 1e-9,
        "metric tons": 1000.0,
        "pounds": 0.453592,
        "ounces": 0.0283495,
        "stone": 6.35029,
        "atomic mass units": 1.66054e-27,
    },
    "Time": {
        "seconds": 1.0,
        "milliseconds": 0.001,
        "microseconds": 1e-6,
        "nanoseconds": 1e-9,
        "minutes": 60.0,
        "hours": 3600.0,
        "days": 86400.0,
        "weeks": 604800.0,
        "years": 31557600.0,
        "centuries": 3.15576e9,
    },
    "Temperature": {
        "Celsius": None, "Fahrenheit": None, "Kelvin": None, "Rankine": None,
    },
    "Speed": {
        "m/s": 1.0,
        "km/h": 1/3.6,
        "mph": 0.44704,
        "knots": 0.514444,
        "ft/s": 0.3048,
        "speed of light": 2.998e8,
        "mach (sea level)": 340.29,
    },
    "Energy": {
        "joules": 1.0,
        "kilojoules": 1000.0,
        "calories": 4.184,
        "kilocalories": 4184.0,
        "watt-hours": 3600.0,
        "kilowatt-hours": 3.6e6,
        "electron volts": 1.602e-19,
        "BTU": 1055.06,
        "ergs": 1e-7,
    },
    "Pressure": {
        "pascals": 1.0,
        "kilopascals": 1000.0,
        "megapascals": 1e6,
        "bar": 1e5,
        "millibar": 100.0,
        "atmospheres": 101325.0,
        "psi": 6894.76,
        "torr": 133.322,
        "mmHg": 133.322,
    },
    "Area": {
        "sq meters": 1.0,
        "sq kilometers": 1e6,
        "sq centimeters": 1e-4,
        "sq miles": 2.59e6,
        "sq feet": 0.0929,
        "sq inches": 6.452e-4,
        "acres": 4046.86,
        "hectares": 10000.0,
    },
    "Volume": {
        "liters": 1.0,
        "milliliters": 0.001,
        "cubic meters": 1000.0,
        "cubic centimeters": 0.001,
        "gallons (US)": 3.78541,
        "gallons (UK)": 4.54609,
        "pints (US)": 0.473176,
        "cups": 0.236588,
        "fluid ounces": 0.0295735,
        "tablespoons": 0.0147868,
        "cubic feet": 28.3168,
        "cubic inches": 0.0163871,
    },
}

def convert_temperature(value, from_unit, to_unit):
    def to_kelvin(v, u):
        if u == "Celsius": return v + 273.15
        if u == "Fahrenheit": return (v + 459.67) * 5/9
        if u == "Kelvin": return v
        if u == "Rankine": return v * 5/9
    def from_kelvin(k, u):
        if u == "Celsius": return k - 273.15
        if u == "Fahrenheit": return k * 9/5 - 459.67
        if u == "Kelvin": return k
        if u == "Rankine": return k * 9/5
    k = to_kelvin(value, from_unit)
    return from_kelvin(k, to_unit)

class UnitScienceWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Scientific Unit Converter")
        self.set_default_size(700, 480)
        self._updating = False
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(12); vbox.set_margin_bottom(12)
        vbox.set_margin_start(16); vbox.set_margin_end(16)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Scientific Unit Converter", css_classes=["title"]))

        cat_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        cat_box.append(Gtk.Label(label="Category:"))
        self.cat_combo = Gtk.ComboBoxText()
        for cat in CONVERSIONS:
            self.cat_combo.append_text(cat)
        self.cat_combo.set_active(0)
        self.cat_combo.connect("changed", self.on_category_changed)
        self.cat_combo.set_hexpand(True)
        cat_box.append(self.cat_combo)
        vbox.append(cat_box)

        conv_frame = Gtk.Frame(label="Convert")
        grid = Gtk.Grid()
        grid.set_row_spacing(8); grid.set_column_spacing(10)
        grid.set_margin_top(8); grid.set_margin_start(8); grid.set_margin_end(8); grid.set_margin_bottom(8)

        self.from_entry = Gtk.Entry()
        self.from_entry.set_hexpand(True)
        self.from_entry.connect("changed", self.on_convert)
        self.from_combo = Gtk.ComboBoxText()
        self.from_combo.connect("changed", self.on_convert)
        grid.attach(self.from_entry, 0, 0, 1, 1)
        grid.attach(self.from_combo, 1, 0, 1, 1)

        grid.attach(Gtk.Label(label="="), 0, 1, 2, 1)

        self.to_entry = Gtk.Entry()
        self.to_entry.set_hexpand(True)
        self.to_entry.connect("changed", self.on_to_changed)
        self.to_combo = Gtk.ComboBoxText()
        self.to_combo.connect("changed", self.on_convert)
        grid.attach(self.to_entry, 0, 2, 1, 1)
        grid.attach(self.to_combo, 1, 2, 1, 1)

        swap_btn = Gtk.Button(label="⇅ Swap")
        swap_btn.connect("clicked", self.on_swap)
        grid.attach(swap_btn, 0, 3, 2, 1)
        conv_frame.set_child(grid)
        vbox.append(conv_frame)

        all_frame = Gtk.Frame(label="All Conversions")
        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        self.all_view = Gtk.TextView()
        self.all_view.set_editable(False)
        self.all_view.set_monospace(True)
        scroll.set_child(self.all_view)
        all_frame.set_child(scroll)
        vbox.append(all_frame)

        self.populate_units("Length")
        self.from_entry.set_text("1")

    def populate_units(self, category):
        units = list(CONVERSIONS[category].keys())
        for combo in [self.from_combo, self.to_combo]:
            combo.remove_all()
            for u in units:
                combo.append_text(u)
        self.from_combo.set_active(0)
        self.to_combo.set_active(1 if len(units) > 1 else 0)

    def on_category_changed(self, combo):
        cat = combo.get_active_text()
        if cat:
            self.populate_units(cat)
            self.on_convert(None)

    def on_convert(self, widget):
        if self._updating:
            return
        self._updating = True
        try:
            value = float(self.from_entry.get_text())
        except ValueError:
            self._updating = False
            return
        cat = self.cat_combo.get_active_text()
        from_unit = self.from_combo.get_active_text()
        to_unit = self.to_combo.get_active_text()
        if not all([cat, from_unit, to_unit]):
            self._updating = False
            return
        result = self.do_convert(value, cat, from_unit, to_unit)
        if result is not None:
            self.to_entry.set_text(f"{result:.6g}")
        self.refresh_all(value, cat, from_unit)
        self._updating = False

    def on_to_changed(self, entry):
        if self._updating:
            return
        self._updating = True
        try:
            value = float(entry.get_text())
        except ValueError:
            self._updating = False
            return
        cat = self.cat_combo.get_active_text()
        from_unit = self.to_combo.get_active_text()
        to_unit = self.from_combo.get_active_text()
        result = self.do_convert(value, cat, from_unit, to_unit)
        if result is not None:
            self.from_entry.set_text(f"{result:.6g}")
        self._updating = False

    def do_convert(self, value, cat, from_unit, to_unit):
        if cat == "Temperature":
            try:
                return convert_temperature(value, from_unit, to_unit)
            except Exception:
                return None
        units = CONVERSIONS.get(cat, {})
        from_factor = units.get(from_unit)
        to_factor = units.get(to_unit)
        if from_factor is None or to_factor is None:
            return None
        return value * from_factor / to_factor

    def refresh_all(self, value, cat, from_unit):
        units = CONVERSIONS.get(cat, {})
        lines = []
        for unit in units:
            result = self.do_convert(value, cat, from_unit, unit)
            if result is not None:
                marker = " ←" if unit == from_unit else ""
                lines.append(f"{result:<18.6g}  {unit}{marker}")
        self.all_view.get_buffer().set_text("\n".join(lines))

    def on_swap(self, btn):
        fi = self.from_combo.get_active()
        ti = self.to_combo.get_active()
        self.from_combo.set_active(ti)
        self.to_combo.set_active(fi)

class UnitScienceApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.UnitScience")
    def do_activate(self):
        win = UnitScienceWindow(self); win.present()

def main():
    app = UnitScienceApp(); app.run(None)

if __name__ == "__main__":
    main()
