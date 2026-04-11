#!/usr/bin/env python3
import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

CONVERSIONS = {
    "Length": {
        "units": ["m", "km", "mi", "ft", "in"],
        "to_base": {
            "m": 1.0,
            "km": 1000.0,
            "mi": 1609.344,
            "ft": 0.3048,
            "in": 0.0254,
        },
    },
    "Weight": {
        "units": ["kg", "g", "lb", "oz"],
        "to_base": {
            "kg": 1.0,
            "g": 0.001,
            "lb": 0.453592,
            "oz": 0.0283495,
        },
    },
    "Temperature": {
        "units": ["C", "F", "K"],
        "to_base": None,  # Special handling
    },
    "Speed": {
        "units": ["km/h", "m/s", "mph"],
        "to_base": {
            "km/h": 1.0 / 3.6,
            "m/s": 1.0,
            "mph": 0.44704,
        },
    },
    "Area": {
        "units": ["m²", "km²", "ft²", "acres"],
        "to_base": {
            "m²": 1.0,
            "km²": 1_000_000.0,
            "ft²": 0.092903,
            "acres": 4046.86,
        },
    },
}


def convert_temperature(value, from_unit, to_unit):
    if from_unit == to_unit:
        return value
    # Convert to Celsius first
    if from_unit == "C":
        celsius = value
    elif from_unit == "F":
        celsius = (value - 32) * 5 / 9
    elif from_unit == "K":
        celsius = value - 273.15
    # Then to target
    if to_unit == "C":
        return celsius
    elif to_unit == "F":
        return celsius * 9 / 5 + 32
    elif to_unit == "K":
        return celsius + 273.15


def convert_value(value, from_unit, to_unit, category):
    if from_unit == to_unit:
        return value
    if category == "Temperature":
        return convert_temperature(value, from_unit, to_unit)
    to_base = CONVERSIONS[category]["to_base"]
    base_value = value * to_base[from_unit]
    return base_value / to_base[to_unit]


class UnitConverterWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Unit Converter")
        self.set_default_size(480, 400)

        css_provider = Gtk.CssProvider()
        css = b"""
        .title-label {
            font-size: 22px;
            font-weight: bold;
            margin-bottom: 8px;
        }
        .result-label {
            font-size: 18px;
            font-weight: bold;
            color: #2196F3;
            margin-top: 8px;
        }
        .section-label {
            font-size: 13px;
            color: #666;
        }
        """
        css_provider.load_from_data(css)
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        outer.set_margin_top(20)
        outer.set_margin_bottom(20)
        outer.set_margin_start(30)
        outer.set_margin_end(30)
        self.set_child(outer)

        title = Gtk.Label(label="Unit Converter")
        title.add_css_class("title-label")
        title.set_halign(Gtk.Align.CENTER)
        outer.append(title)

        # Category selector
        cat_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        cat_row.set_halign(Gtk.Align.CENTER)
        cat_label = Gtk.Label(label="Category:")
        cat_label.add_css_class("section-label")
        cat_row.append(cat_label)

        self.cat_combo = Gtk.ComboBoxText()
        for cat in CONVERSIONS:
            self.cat_combo.append_text(cat)
        self.cat_combo.set_active(0)
        self.cat_combo.connect("changed", self.on_category_changed)
        cat_row.append(self.cat_combo)
        outer.append(cat_row)

        outer.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # From row
        from_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        from_row.set_margin_top(14)
        from_label = Gtk.Label(label="From:")
        from_label.set_size_request(60, -1)
        from_label.set_halign(Gtk.Align.START)
        from_row.append(from_label)

        self.from_entry = Gtk.Entry()
        self.from_entry.set_placeholder_text("Enter value")
        self.from_entry.set_hexpand(True)
        self.from_entry.connect("changed", self.on_value_changed)
        from_row.append(self.from_entry)

        self.from_unit_combo = Gtk.ComboBoxText()
        self.from_unit_combo.set_size_request(80, -1)
        self.from_unit_combo.connect("changed", self.on_value_changed)
        from_row.append(self.from_unit_combo)
        outer.append(from_row)

        # To row
        to_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        to_row.set_margin_top(10)
        to_label = Gtk.Label(label="To:")
        to_label.set_size_request(60, -1)
        to_label.set_halign(Gtk.Align.START)
        to_row.append(to_label)

        self.to_entry = Gtk.Entry()
        self.to_entry.set_placeholder_text("Result")
        self.to_entry.set_editable(False)
        self.to_entry.set_hexpand(True)
        to_row.append(self.to_entry)

        self.to_unit_combo = Gtk.ComboBoxText()
        self.to_unit_combo.set_size_request(80, -1)
        self.to_unit_combo.connect("changed", self.on_value_changed)
        to_row.append(self.to_unit_combo)
        outer.append(to_row)

        # Convert button
        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        btn_row.set_margin_top(18)
        btn_row.set_halign(Gtk.Align.CENTER)
        convert_btn = Gtk.Button(label="Convert")
        convert_btn.set_size_request(140, 44)
        convert_btn.connect("clicked", self.on_convert_clicked)
        btn_row.append(convert_btn)
        outer.append(btn_row)

        # Result label
        self.result_label = Gtk.Label(label="")
        self.result_label.add_css_class("result-label")
        self.result_label.set_halign(Gtk.Align.CENTER)
        self.result_label.set_margin_top(10)
        outer.append(self.result_label)

        self._populate_units("Length")

    def _populate_units(self, category):
        units = CONVERSIONS[category]["units"]
        for combo in (self.from_unit_combo, self.to_unit_combo):
            combo.remove_all()
            for u in units:
                combo.append_text(u)
        self.from_unit_combo.set_active(0)
        self.to_unit_combo.set_active(1 if len(units) > 1 else 0)

    def on_category_changed(self, combo):
        cat = combo.get_active_text()
        if cat:
            self._populate_units(cat)
            self.to_entry.set_text("")
            self.result_label.set_text("")

    def on_value_changed(self, _widget):
        self.on_convert_clicked(None)

    def on_convert_clicked(self, _btn):
        raw = self.from_entry.get_text().strip()
        from_unit = self.from_unit_combo.get_active_text()
        to_unit = self.to_unit_combo.get_active_text()
        category = self.cat_combo.get_active_text()

        if not raw or not from_unit or not to_unit or not category:
            return

        try:
            value = float(raw)
        except ValueError:
            self.to_entry.set_text("")
            self.result_label.set_text("Invalid input")
            return

        result = convert_value(value, from_unit, to_unit, category)
        # Format nicely
        if abs(result) >= 1e6 or (abs(result) < 1e-4 and result != 0):
            formatted = f"{result:.6e}"
        else:
            formatted = f"{result:.6g}"
        self.to_entry.set_text(formatted)
        self.result_label.set_text(f"{raw} {from_unit} = {formatted} {to_unit}")


def on_activate(app):
    win = UnitConverterWindow(app)
    win.present()


if __name__ == "__main__":
    app = Gtk.Application(application_id="com.pens.UnitConverter")
    app.connect("activate", on_activate)
    app.run(None)
