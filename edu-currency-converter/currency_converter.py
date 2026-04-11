#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import urllib.request, json, threading, time

FALLBACK_RATES = {
    "USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 149.5, "IDR": 15700.0,
    "AUD": 1.53, "CAD": 1.36, "CHF": 0.89, "CNY": 7.24, "INR": 83.1,
    "MXN": 17.2, "BRL": 4.97, "KRW": 1325.0, "SGD": 1.34, "HKD": 7.82,
    "NOK": 10.6, "SEK": 10.4, "DKK": 6.88, "NZD": 1.63, "ZAR": 18.6,
    "TRY": 30.5, "SAR": 3.75, "AED": 3.67, "THB": 35.1, "MYR": 4.67,
}

class CurrencyConverterWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Currency Converter")
        self.set_default_size(560, 500)
        self.rates = FALLBACK_RATES.copy()
        self.last_update = "offline (built-in rates)"
        self.build_ui()
        threading.Thread(target=self.fetch_rates, daemon=True).start()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(16); vbox.set_margin_bottom(16)
        vbox.set_margin_start(16); vbox.set_margin_end(16)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Currency Converter", css_classes=["title"]))

        self.status_label = Gtk.Label(label="Using built-in rates...")
        self.status_label.set_xalign(0)
        vbox.append(self.status_label)

        currencies = sorted(FALLBACK_RATES.keys())

        from_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        from_box.append(Gtk.Label(label="Amount:"))
        self.amount_entry = Gtk.Entry()
        self.amount_entry.set_text("1.00")
        self.amount_entry.set_hexpand(True)
        self.amount_entry.connect("changed", self.on_convert)
        from_box.append(self.amount_entry)
        from_box.append(Gtk.Label(label="From:"))
        self.from_combo = Gtk.ComboBoxText()
        for c in currencies:
            self.from_combo.append_text(c)
        self.from_combo.set_active(currencies.index("USD"))
        self.from_combo.connect("changed", self.on_convert)
        from_box.append(self.from_combo)
        vbox.append(from_box)

        swap_btn = Gtk.Button(label="⇅ Swap")
        swap_btn.set_halign(Gtk.Align.CENTER)
        swap_btn.connect("clicked", self.on_swap)
        vbox.append(swap_btn)

        to_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        to_box.append(Gtk.Label(label="Result:"))
        self.result_entry = Gtk.Entry()
        self.result_entry.set_editable(False)
        self.result_entry.set_hexpand(True)
        to_box.append(self.result_entry)
        to_box.append(Gtk.Label(label="To:"))
        self.to_combo = Gtk.ComboBoxText()
        for c in currencies:
            self.to_combo.append_text(c)
        self.to_combo.set_active(currencies.index("EUR"))
        self.to_combo.connect("changed", self.on_convert)
        to_box.append(self.to_combo)
        vbox.append(to_box)

        rate_frame = Gtk.Frame(label="Exchange Rates (vs USD)")
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        self.rates_view = Gtk.TextView()
        self.rates_view.set_editable(False)
        self.rates_view.set_monospace(True)
        scroll.set_child(self.rates_view)
        rate_frame.set_child(scroll)
        vbox.append(rate_frame)

        self.refresh_rates_view()

    def fetch_rates(self):
        try:
            url = "https://api.exchangerate-api.com/v4/latest/USD"
            with urllib.request.urlopen(url, timeout=5) as r:
                data = json.loads(r.read())
                self.rates = data["rates"]
                self.rates["USD"] = 1.0
                self.last_update = data.get("date", "today")
                GLib.idle_add(self.update_ui_rates)
        except Exception:
            pass

    def update_ui_rates(self):
        self.status_label.set_text(f"Live rates updated: {self.last_update}")
        self.refresh_rates_view()
        self.on_convert(None)
        return False

    def refresh_rates_view(self):
        lines = []
        for code in sorted(self.rates.keys()):
            rate = self.rates[code]
            lines.append(f"{code:6s}  {rate:>12.4f}")
        self.rates_view.get_buffer().set_text("\n".join(lines))

    def on_convert(self, widget):
        try:
            amount = float(self.amount_entry.get_text())
        except ValueError:
            self.result_entry.set_text("Invalid")
            return
        from_code = self.from_combo.get_active_text()
        to_code = self.to_combo.get_active_text()
        if not from_code or not to_code:
            return
        from_rate = self.rates.get(from_code, 1.0)
        to_rate = self.rates.get(to_code, 1.0)
        result = amount / from_rate * to_rate
        self.result_entry.set_text(f"{result:.4f}")

    def on_swap(self, btn):
        fi = self.from_combo.get_active()
        ti = self.to_combo.get_active()
        self.from_combo.set_active(ti)
        self.to_combo.set_active(fi)

class CurrencyConverterApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.CurrencyConverter")
    def do_activate(self):
        win = CurrencyConverterWindow(self); win.present()

def main():
    app = CurrencyConverterApp(); app.run(None)

if __name__ == "__main__":
    main()
