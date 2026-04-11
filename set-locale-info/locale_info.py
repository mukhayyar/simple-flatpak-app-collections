#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import locale, os, subprocess, datetime

def run_cmd(cmd, timeout=3):
    try:
        return subprocess.check_output(cmd, text=True, timeout=timeout, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""

class LocaleInfoWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Locale & Language Info")
        self.set_default_size(700, 600)
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(12); vbox.set_margin_bottom(12)
        vbox.set_margin_start(16); vbox.set_margin_end(16)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Locale & Language Info", css_classes=["title"]))

        # Current locale info
        locale_frame = Gtk.Frame(label="Current Locale Settings")
        locale_grid = Gtk.Grid()
        locale_grid.set_row_spacing(6); locale_grid.set_column_spacing(16)
        locale_grid.set_margin_top(8); locale_grid.set_margin_start(12)
        locale_grid.set_margin_end(12); locale_grid.set_margin_bottom(8)

        locale_vars = [
            ("LANG", os.environ.get("LANG", "not set")),
            ("LANGUAGE", os.environ.get("LANGUAGE", "not set")),
            ("LC_ALL", os.environ.get("LC_ALL", "not set")),
            ("LC_CTYPE", os.environ.get("LC_CTYPE", "not set")),
            ("LC_NUMERIC", os.environ.get("LC_NUMERIC", "not set")),
            ("LC_TIME", os.environ.get("LC_TIME", "not set")),
            ("LC_MONETARY", os.environ.get("LC_MONETARY", "not set")),
            ("LC_MESSAGES", os.environ.get("LC_MESSAGES", "not set")),
            ("LC_PAPER", os.environ.get("LC_PAPER", "not set")),
            ("LC_ADDRESS", os.environ.get("LC_ADDRESS", "not set")),
        ]
        for row, (key, val) in enumerate(locale_vars):
            lbl_key = Gtk.Label(label=f"{key}:", xalign=1)
            lbl_key.set_css_classes(["dim-label"])
            lbl_val = Gtk.Label(label=val, xalign=0)
            lbl_val.set_css_classes(["monospace"])
            locale_grid.attach(lbl_key, 0, row, 1, 1)
            locale_grid.attach(lbl_val, 1, row, 1, 1)
        locale_frame.set_child(locale_grid)
        vbox.append(locale_frame)

        # Python locale
        py_frame = Gtk.Frame(label="Python Locale")
        py_grid = Gtk.Grid()
        py_grid.set_row_spacing(6); py_grid.set_column_spacing(16)
        py_grid.set_margin_top(8); py_grid.set_margin_start(12)
        py_grid.set_margin_end(12); py_grid.set_margin_bottom(8)

        try:
            locale.setlocale(locale.LC_ALL, '')
            lc, enc = locale.getlocale()
        except Exception:
            lc, enc = "unknown", "unknown"

        py_info = [
            ("locale.getlocale()", f"{lc}, {enc}"),
            ("locale.getpreferredencoding()", locale.getpreferredencoding()),
            ("locale.localeconv() decimal_point", locale.localeconv().get('decimal_point', '.')),
            ("locale.localeconv() thousands_sep", locale.localeconv().get('thousands_sep', ',')),
            ("locale.localeconv() currency_symbol", locale.localeconv().get('currency_symbol', '$')),
        ]
        for row, (key, val) in enumerate(py_info):
            lbl_key = Gtk.Label(label=f"{key}:", xalign=1)
            lbl_key.set_css_classes(["dim-label"])
            lbl_val = Gtk.Label(label=str(val), xalign=0)
            py_grid.attach(lbl_key, 0, row, 1, 1)
            py_grid.attach(lbl_val, 1, row, 1, 1)
        py_frame.set_child(py_grid)
        vbox.append(py_frame)

        # Date/time format
        dt_frame = Gtk.Frame(label="Date & Time Formatting")
        dt_grid = Gtk.Grid()
        dt_grid.set_row_spacing(6); dt_grid.set_column_spacing(16)
        dt_grid.set_margin_top(8); dt_grid.set_margin_start(12)
        dt_grid.set_margin_end(12); dt_grid.set_margin_bottom(8)

        now = datetime.datetime.now()
        dt_samples = [
            ("Current date (locale)", now.strftime("%x")),
            ("Current time (locale)", now.strftime("%X")),
            ("Date+time (locale)", now.strftime("%c")),
            ("ISO 8601", now.isoformat()),
            ("Timezone", datetime.datetime.now().astimezone().tzname()),
        ]
        for row, (key, val) in enumerate(dt_samples):
            lbl_key = Gtk.Label(label=f"{key}:", xalign=1)
            lbl_key.set_css_classes(["dim-label"])
            lbl_val = Gtk.Label(label=val, xalign=0)
            dt_grid.attach(lbl_key, 0, row, 1, 1)
            dt_grid.attach(lbl_val, 1, row, 1, 1)
        dt_frame.set_child(dt_grid)
        vbox.append(dt_frame)

        # Available locales
        avail_frame = Gtk.Frame(label="Installed Locales")
        avail_scroll = Gtk.ScrolledWindow()
        avail_scroll.set_min_content_height(140)
        avail_view = Gtk.TextView()
        avail_view.set_editable(False)
        avail_view.set_monospace(True)
        locales_out = run_cmd(["locale", "-a"])
        if not locales_out:
            locales_out = "(locale -a not available)"
        avail_view.get_buffer().set_text(locales_out)
        avail_scroll.set_child(avail_view)
        avail_frame.set_child(avail_scroll)
        vbox.append(avail_frame)

        # Number formatting demo
        num_frame = Gtk.Frame(label="Number Formatting")
        num_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        num_box.set_margin_top(8); num_box.set_margin_start(12)
        num_box.set_margin_end(12); num_box.set_margin_bottom(8)

        try:
            num_formatted = locale.format_string("%d", 1234567, grouping=True)
            cur_formatted = locale.currency(1234.56, grouping=True)
        except Exception:
            num_formatted = "1,234,567"
            cur_formatted = "$1,234.56"

        num_box.append(Gtk.Label(label=f"1234567 → {num_formatted}"))
        num_box.append(Gtk.Label(label=f"1234.56 → {cur_formatted}"))
        num_frame.set_child(num_box)
        vbox.append(num_frame)

class LocaleInfoApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.LocaleInfo")
    def do_activate(self):
        win = LocaleInfoWindow(self); win.present()

def main():
    app = LocaleInfoApp(); app.run(None)

if __name__ == "__main__":
    main()
