#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import datetime, time

CITIES = [
    ("New York", "America/New_York", -5, "🇺🇸"),
    ("Los Angeles", "America/Los_Angeles", -8, "🇺🇸"),
    ("Chicago", "America/Chicago", -6, "🇺🇸"),
    ("London", "Europe/London", 0, "🇬🇧"),
    ("Paris", "Europe/Paris", 1, "🇫🇷"),
    ("Berlin", "Europe/Berlin", 1, "🇩🇪"),
    ("Moscow", "Europe/Moscow", 3, "🇷🇺"),
    ("Dubai", "Asia/Dubai", 4, "🇦🇪"),
    ("Mumbai", "Asia/Kolkata", 5, "🇮🇳"),
    ("Dhaka", "Asia/Dhaka", 6, "🇧🇩"),
    ("Bangkok", "Asia/Bangkok", 7, "🇹🇭"),
    ("Jakarta", "Asia/Jakarta", 7, "🇮🇩"),
    ("Singapore", "Asia/Singapore", 8, "🇸🇬"),
    ("Hong Kong", "Asia/Hong_Kong", 8, "🇭🇰"),
    ("Shanghai", "Asia/Shanghai", 8, "🇨🇳"),
    ("Tokyo", "Asia/Tokyo", 9, "🇯🇵"),
    ("Seoul", "Asia/Seoul", 9, "🇰🇷"),
    ("Sydney", "Australia/Sydney", 11, "🇦🇺"),
    ("Auckland", "Pacific/Auckland", 13, "🇳🇿"),
    ("São Paulo", "America/Sao_Paulo", -3, "🇧🇷"),
    ("Buenos Aires", "America/Argentina/Buenos_Aires", -3, "🇦🇷"),
    ("Toronto", "America/Toronto", -5, "🇨🇦"),
    ("Mexico City", "America/Mexico_City", -6, "🇲🇽"),
    ("Cairo", "Africa/Cairo", 2, "🇪🇬"),
    ("Nairobi", "Africa/Nairobi", 3, "🇰🇪"),
]

def get_utc_offset_time(utc_offset):
    now_utc = datetime.datetime.utcnow()
    offset = datetime.timedelta(hours=utc_offset)
    local = now_utc + offset
    return local

class TimezoneWorldWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("World Timezone Clock")
        self.set_default_size(780, 600)
        self.pinned = set()
        self.build_ui()
        GLib.timeout_add(1000, self.update_times)

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        title_box.append(Gtk.Label(label="World Timezone Clock", css_classes=["title"]))
        self.utc_label = Gtk.Label(label="UTC: --")
        self.utc_label.set_hexpand(True)
        self.utc_label.set_xalign(1)
        title_box.append(self.utc_label)
        vbox.append(title_box)

        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Filter cities...")
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("search-changed", self.on_search)
        search_box.append(self.search_entry)
        vbox.append(search_box)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        self.grid = Gtk.Grid()
        self.grid.set_row_spacing(4)
        self.grid.set_column_spacing(16)
        self.grid.set_margin_start(4)

        headers = ["", "City", "Timezone", "Local Time", "Date", "UTC Offset"]
        for col, h in enumerate(headers):
            lbl = Gtk.Label(label=h, xalign=0)
            lbl.set_markup(f"<b>{h}</b>")
            self.grid.attach(lbl, col, 0, 1, 1)

        self.rows = []
        for i, (city, tz, offset, flag) in enumerate(CITIES):
            row_widgets = []
            pin_btn = Gtk.Button(label="☆")
            pin_btn.set_size_request(30, -1)
            pin_btn._city = city
            pin_btn.connect("clicked", self.on_pin, pin_btn)
            self.grid.attach(pin_btn, 0, i + 1, 1, 1)
            row_widgets.append(pin_btn)

            city_lbl = Gtk.Label(label=f"{flag} {city}", xalign=0)
            self.grid.attach(city_lbl, 1, i + 1, 1, 1)
            row_widgets.append(city_lbl)

            tz_lbl = Gtk.Label(label=tz, xalign=0)
            tz_lbl.set_css_classes(["monospace"])
            self.grid.attach(tz_lbl, 2, i + 1, 1, 1)
            row_widgets.append(tz_lbl)

            time_lbl = Gtk.Label(label="--:--:--", xalign=0)
            time_lbl.set_css_classes(["monospace"])
            time_lbl._utc_offset = offset
            self.grid.attach(time_lbl, 3, i + 1, 1, 1)
            row_widgets.append(time_lbl)

            date_lbl = Gtk.Label(label="----", xalign=0)
            self.grid.attach(date_lbl, 4, i + 1, 1, 1)
            row_widgets.append(date_lbl)

            offset_str = f"UTC{'+' if offset >= 0 else ''}{offset}"
            off_lbl = Gtk.Label(label=offset_str, xalign=0)
            self.grid.attach(off_lbl, 5, i + 1, 1, 1)
            row_widgets.append(off_lbl)

            self.rows.append((city, row_widgets))

        scroll.set_child(self.grid)
        vbox.append(scroll)

        converter_frame = Gtk.Frame(label="Time Converter")
        conv_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        conv_box.set_margin_top(4); conv_box.set_margin_start(4); conv_box.set_margin_end(4); conv_box.set_margin_bottom(4)
        conv_box.append(Gtk.Label(label="Convert:"))
        self.conv_h = Gtk.SpinButton.new_with_range(0, 23, 1)
        self.conv_h.set_value(12)
        conv_box.append(self.conv_h)
        conv_box.append(Gtk.Label(label=":"))
        self.conv_m = Gtk.SpinButton.new_with_range(0, 59, 1)
        conv_box.append(self.conv_m)
        conv_box.append(Gtk.Label(label="From:"))
        self.conv_from = Gtk.ComboBoxText()
        for city, _, _, _ in CITIES:
            self.conv_from.append_text(city)
        self.conv_from.set_active(0)
        conv_box.append(self.conv_from)
        conv_box.append(Gtk.Label(label="To:"))
        self.conv_to = Gtk.ComboBoxText()
        for city, _, _, _ in CITIES:
            self.conv_to.append_text(city)
        self.conv_to.set_active(12)
        conv_box.append(self.conv_to)
        go_btn = Gtk.Button(label="Convert")
        go_btn.connect("clicked", self.on_convert)
        conv_box.append(go_btn)
        self.conv_result = Gtk.Label(label="")
        conv_box.append(self.conv_result)
        converter_frame.set_child(conv_box)
        vbox.append(converter_frame)

        self.update_times()

    def update_times(self):
        now_utc = datetime.datetime.utcnow()
        self.utc_label.set_text(f"UTC: {now_utc.strftime('%H:%M:%S %Y-%m-%d')}")
        for i, (city, tz, offset, flag) in enumerate(CITIES):
            row_widgets = self.rows[i][1]
            time_lbl = row_widgets[3]
            date_lbl = row_widgets[4]
            local = now_utc + datetime.timedelta(hours=offset)
            time_lbl.set_text(local.strftime("%H:%M:%S"))
            date_lbl.set_text(local.strftime("%Y-%m-%d %a"))
        return True

    def on_search(self, entry):
        q = entry.get_text().lower()
        for city, row_widgets in self.rows:
            visible = not q or q in city.lower()
            for w in row_widgets:
                w.set_visible(visible)

    def on_pin(self, btn, pin_btn):
        city = pin_btn._city
        if city in self.pinned:
            self.pinned.discard(city)
            pin_btn.set_label("☆")
        else:
            self.pinned.add(city)
            pin_btn.set_label("★")

    def on_convert(self, btn):
        h = int(self.conv_h.get_value())
        m = int(self.conv_m.get_value())
        from_city = self.conv_from.get_active_text()
        to_city = self.conv_to.get_active_text()
        from_offset = next((o for c, _, o, _ in CITIES if c == from_city), 0)
        to_offset = next((o for c, _, o, _ in CITIES if c == to_city), 0)
        total_min = h * 60 + m - from_offset * 60 + to_offset * 60
        total_min = total_min % (24 * 60)
        rh, rm = divmod(total_min, 60)
        self.conv_result.set_text(f"→ {rh:02d}:{rm:02d} in {to_city}")

class TimezoneWorldApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.TimezoneWorld")
    def do_activate(self):
        win = TimezoneWorldWindow(self); win.present()

def main():
    app = TimezoneWorldApp(); app.run(None)

if __name__ == "__main__":
    main()
