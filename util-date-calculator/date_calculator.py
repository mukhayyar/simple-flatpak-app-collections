#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import datetime, calendar

class DateCalculatorWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Date Calculator")
        self.set_default_size(680, 560)
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(16); vbox.set_margin_bottom(16)
        vbox.set_margin_start(20); vbox.set_margin_end(20)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Date Calculator", css_classes=["title"]))

        notebook = Gtk.Notebook()
        vbox.append(notebook)

        # Difference page
        diff_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        diff_page.set_margin_top(12); diff_page.set_margin_start(12); diff_page.set_margin_end(12); diff_page.set_margin_bottom(12)
        diff_page.append(Gtk.Label(label="Calculate days between two dates", xalign=0))

        def date_row(label, default):
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            box.append(Gtk.Label(label=f"{label}:", xalign=0))
            entry = Gtk.Entry()
            entry.set_text(default)
            entry.set_placeholder_text("YYYY-MM-DD")
            entry.set_hexpand(True)
            box.append(entry)
            return box, entry

        today = datetime.date.today().isoformat()
        box1, self.date1_entry = date_row("From", today)
        box2, self.date2_entry = date_row("To", today)
        diff_page.append(box1); diff_page.append(box2)

        calc_btn = Gtk.Button(label="Calculate Difference")
        calc_btn.set_halign(Gtk.Align.CENTER)
        calc_btn.connect("clicked", self.on_calc_diff)
        diff_page.append(calc_btn)

        self.diff_result = Gtk.Label(label="", xalign=0)
        self.diff_result.set_wrap(True)
        self.diff_result.set_selectable(True)
        diff_page.append(self.diff_result)

        notebook.append_page(diff_page, Gtk.Label(label="Difference"))

        # Add/Subtract page
        add_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        add_page.set_margin_top(12); add_page.set_margin_start(12); add_page.set_margin_end(12); add_page.set_margin_bottom(12)

        base_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        base_box.append(Gtk.Label(label="Base date:"))
        self.base_entry = Gtk.Entry()
        self.base_entry.set_text(today)
        self.base_entry.set_hexpand(True)
        base_box.append(self.base_entry)
        add_page.append(base_box)

        ops_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        ops_box.set_halign(Gtk.Align.CENTER)
        for unit in ["days", "weeks", "months", "years"]:
            sub_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            sub_box.set_halign(Gtk.Align.CENTER)
            sub_box.append(Gtk.Label(label=unit.capitalize()))
            spin = Gtk.SpinButton.new_with_range(-9999, 9999, 1)
            spin.set_value(0)
            setattr(self, f"{unit}_spin", spin)
            sub_box.append(spin)
            ops_box.append(sub_box)
        add_page.append(ops_box)

        add_btn = Gtk.Button(label="Add/Subtract")
        add_btn.set_halign(Gtk.Align.CENTER)
        add_btn.connect("clicked", self.on_add_sub)
        add_page.append(add_btn)

        self.add_result = Gtk.Label(label="", xalign=0)
        self.add_result.set_wrap(True)
        self.add_result.set_selectable(True)
        add_page.append(self.add_result)

        notebook.append_page(add_page, Gtk.Label(label="Add/Subtract"))

        # Calendar page
        cal_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        cal_page.set_margin_top(8); cal_page.set_margin_start(8); cal_page.set_margin_end(8); cal_page.set_margin_bottom(8)

        cal_ctrl = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        cal_ctrl.set_halign(Gtk.Align.CENTER)
        self.cal_year = Gtk.SpinButton.new_with_range(1900, 2100, 1)
        self.cal_year.set_value(datetime.date.today().year)
        self.cal_month = Gtk.ComboBoxText()
        for m in calendar.month_name[1:]:
            self.cal_month.append_text(m)
        self.cal_month.set_active(datetime.date.today().month - 1)
        go_cal_btn = Gtk.Button(label="Show Calendar")
        go_cal_btn.connect("clicked", self.on_show_calendar)
        cal_ctrl.append(self.cal_year); cal_ctrl.append(self.cal_month); cal_ctrl.append(go_cal_btn)
        cal_page.append(cal_ctrl)

        cal_scroll = Gtk.ScrolledWindow(); cal_scroll.set_vexpand(True)
        self.cal_view = Gtk.TextView()
        self.cal_view.set_editable(False); self.cal_view.set_monospace(True)
        cal_scroll.set_child(self.cal_view)
        cal_page.append(cal_scroll)

        notebook.append_page(cal_page, Gtk.Label(label="Calendar"))

        # Special dates page
        special_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        special_page.set_margin_top(12); special_page.set_margin_start(12); special_page.set_margin_end(12); special_page.set_margin_bottom(12)

        spec_entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        spec_entry_box.append(Gtk.Label(label="Date:"))
        self.spec_entry = Gtk.Entry()
        self.spec_entry.set_text(today)
        self.spec_entry.set_hexpand(True)
        spec_entry_box.append(self.spec_entry)
        spec_btn = Gtk.Button(label="Analyze")
        spec_btn.connect("clicked", self.on_analyze)
        spec_entry_box.append(spec_btn)
        special_page.append(spec_entry_box)

        spec_scroll = Gtk.ScrolledWindow(); spec_scroll.set_vexpand(True)
        self.spec_view = Gtk.TextView()
        self.spec_view.set_editable(False)
        spec_scroll.set_child(self.spec_view)
        special_page.append(spec_scroll)

        notebook.append_page(special_page, Gtk.Label(label="Date Info"))

        self.on_show_calendar(None)

    def parse_date(self, text):
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d.%m.%Y"]:
            try:
                return datetime.datetime.strptime(text.strip(), fmt).date()
            except ValueError:
                pass
        raise ValueError(f"Cannot parse date: {text}")

    def on_calc_diff(self, btn):
        try:
            d1 = self.parse_date(self.date1_entry.get_text())
            d2 = self.parse_date(self.date2_entry.get_text())
        except ValueError as e:
            self.diff_result.set_text(str(e))
            return
        delta = d2 - d1
        days = abs(delta.days)
        weeks, rem_days = divmod(days, 7)
        months = abs((d2.year - d1.year) * 12 + d2.month - d1.month)
        years = abs(d2.year - d1.year)
        direction = "after" if delta.days >= 0 else "before"
        lines = [
            f"{d2.strftime('%A, %B %d, %Y')} is {direction} {d1.strftime('%A, %B %d, %Y')}",
            f"Total days: {days}",
            f"Weeks: {weeks} weeks and {rem_days} days",
            f"Approximate months: {months}",
            f"Approximate years: {years}",
        ]
        self.diff_result.set_text("\n".join(lines))

    def on_add_sub(self, btn):
        try:
            base = self.parse_date(self.base_entry.get_text())
        except ValueError as e:
            self.add_result.set_text(str(e))
            return
        days = int(self.days_spin.get_value())
        weeks = int(self.weeks_spin.get_value())
        months = int(self.months_spin.get_value())
        years = int(self.years_spin.get_value())
        result = base + datetime.timedelta(days=days + weeks * 7)
        # Add months
        m = result.month + months
        y = result.year + (m - 1) // 12
        m = (m - 1) % 12 + 1
        try:
            result = result.replace(year=y, month=m)
        except ValueError:
            result = result.replace(year=y, month=m, day=1)
        # Add years
        try:
            result = result.replace(year=result.year + years)
        except ValueError:
            result = result.replace(year=result.year + years, day=28)
        lines = [
            f"Base date: {base.isoformat()} ({base.strftime('%A')})",
            f"Adjustment: +{days}d +{weeks}w +{months}mo +{years}yr",
            f"Result: {result.isoformat()} ({result.strftime('%A, %B %d, %Y')})",
            f"Days elapsed: {(result - base).days}",
        ]
        self.add_result.set_text("\n".join(lines))

    def on_show_calendar(self, btn):
        year = int(self.cal_year.get_value())
        month = self.cal_month.get_active() + 1
        cal_text = calendar.month(year, month)
        today = datetime.date.today()
        lines = []
        for line in cal_text.split('\n'):
            lines.append(line)
        self.cal_view.get_buffer().set_text(cal_text + f"\n\nToday: {today.isoformat()}")

    def on_analyze(self, btn):
        try:
            d = self.parse_date(self.spec_entry.get_text())
        except ValueError as e:
            self.spec_view.get_buffer().set_text(str(e))
            return
        today = datetime.date.today()
        delta = (d - today).days
        week_num = d.isocalendar()[1]
        day_of_year = d.timetuple().tm_yday
        days_in_month = calendar.monthrange(d.year, d.month)[1]
        is_leap = calendar.isleap(d.year)
        quarter = (d.month - 1) // 3 + 1
        unix_ts = int((d - datetime.date(1970, 1, 1)).total_seconds()) if d >= datetime.date(1970, 1, 1) else "N/A"
        lines = [
            f"Date: {d.isoformat()}",
            f"Day: {d.strftime('%A')}",
            f"Week number: {week_num}",
            f"Day of year: {day_of_year}",
            f"Quarter: Q{quarter}",
            f"Days in month: {days_in_month}",
            f"Leap year: {'Yes' if is_leap else 'No'}",
            f"Unix timestamp: {unix_ts}",
            f"Days from today: {delta} ({'future' if delta > 0 else ('past' if delta < 0 else 'today')})",
            f"ISO format: {d.isoformat()}",
        ]
        self.spec_view.get_buffer().set_text("\n".join(lines))

class DateCalculatorApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.DateCalculator")
    def do_activate(self):
        win = DateCalculatorWindow(self); win.present()

def main():
    app = DateCalculatorApp(); app.run(None)

if __name__ == "__main__":
    main()
