#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib
import json, os, datetime, calendar as cal

DATA_DIR = os.path.expanduser("~/.local/share/com.pens.CalendarApp")
DATA_FILE = os.path.join(DATA_DIR, "events.json")

class CalendarAppWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app); self.set_title("Calendar"); self.set_default_size(900,680)
        os.makedirs(DATA_DIR, exist_ok=True)
        self.events = self.load_events()
        self.today = datetime.date.today()
        self.view_month = self.today.replace(day=1)
        self.selected_date = self.today
        self.build_ui()
        self.draw_calendar()

    def load_events(self):
        try:
            with open(DATA_FILE) as f: return json.load(f)
        except Exception: return {}
    def save_events(self):
        with open(DATA_FILE, "w") as f: json.dump(self.events, f)

    def build_ui(self):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        hbox.set_margin_top(8); hbox.set_margin_bottom(8); hbox.set_margin_start(8); hbox.set_margin_end(8)
        self.set_child(hbox)
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); left.set_hexpand(True)
        nav = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8); nav.set_halign(Gtk.Align.CENTER)
        prev_btn = Gtk.Button(label="←"); prev_btn.connect("clicked", self.on_prev_month)
        next_btn = Gtk.Button(label="→"); next_btn.connect("clicked", self.on_next_month)
        self.month_label = Gtk.Label(label=""); today_btn = Gtk.Button(label="Today"); today_btn.connect("clicked", self.on_today)
        nav.append(prev_btn); nav.append(self.month_label); nav.append(next_btn); nav.append(today_btn); left.append(nav)
        self.cal_grid = Gtk.Grid(); self.cal_grid.set_row_spacing(2); self.cal_grid.set_column_spacing(2); self.cal_grid.set_halign(Gtk.Align.CENTER)
        for i, day in enumerate(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]):
            lbl = Gtk.Label(label=day, width_chars=8); self.cal_grid.attach(lbl, i, 0, 1, 1)
        left.append(self.cal_grid); hbox.append(left)
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); right.set_size_request(280,-1)
        self.day_label = Gtk.Label(label=""); right.append(self.day_label)
        add_form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.event_title = Gtk.Entry(); self.event_title.set_placeholder_text("Event title..."); add_form.append(self.event_title)
        self.event_time = Gtk.Entry(); self.event_time.set_placeholder_text("Time (e.g. 14:00)"); add_form.append(self.event_time)
        add_btn = Gtk.Button(label="Add Event"); add_btn.connect("clicked", self.on_add_event); add_form.append(add_btn)
        right.append(add_form)
        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        self.events_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4); scroll.set_child(self.events_list); right.append(scroll)
        hbox.append(right)

    def draw_calendar(self):
        for row in range(1, 7):
            for col in range(7):
                existing = self.cal_grid.get_child_at(col, row)
                if existing: self.cal_grid.remove(existing)
        year, month = self.view_month.year, self.view_month.month
        self.month_label.set_text(self.view_month.strftime("%B %Y"))
        first_weekday = self.view_month.weekday()
        days_in_month = cal.monthrange(year, month)[1]
        day = 1
        for row in range(1, 7):
            for col in range(7):
                if (row == 1 and col < first_weekday) or day > days_in_month:
                    lbl = Gtk.Label(label=""); self.cal_grid.attach(lbl, col, row, 1, 1)
                    continue
                d = datetime.date(year, month, day)
                day_str = d.isoformat()
                has_events = day_str in self.events and len(self.events[day_str]) > 0
                is_today = d == self.today
                is_selected = d == self.selected_date
                label_text = f"{'[' if is_selected else ''}{day}{']' if is_selected else ''}"
                btn = Gtk.Button(label=label_text)
                btn.set_size_request(50, 40)
                if is_today:
                    css = Gtk.CssProvider(); css.load_from_data(b"button { background-color: #3498db; color: white; }")
                    btn.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
                if has_events:
                    indicator = Gtk.Label(label="●")
                    vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                    vbox.append(Gtk.Label(label=str(day))); vbox.append(indicator)
                    btn.set_child(vbox)
                btn.connect("clicked", self.on_day_clicked, d)
                self.cal_grid.attach(btn, col, row, 1, 1)
                day += 1
        self.load_day_events(self.selected_date)

    def on_day_clicked(self, btn, date):
        self.selected_date = date; self.load_day_events(date); self.draw_calendar()

    def load_day_events(self, date):
        while self.events_list.get_first_child(): self.events_list.remove(self.events_list.get_first_child())
        self.day_label.set_text(date.strftime("%A, %B %d, %Y"))
        day_events = self.events.get(date.isoformat(), [])
        for i, ev in enumerate(day_events):
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            lbl = Gtk.Label(label=f"{ev.get('time','')} {ev.get('title','')}", xalign=0, hexpand=True)
            del_btn = Gtk.Button(label="×"); del_btn.connect("clicked", self.on_del_event, date, i)
            row.append(lbl); row.append(del_btn); self.events_list.append(row)

    def on_add_event(self, btn):
        title = self.event_title.get_text().strip()
        if not title: return
        day_str = self.selected_date.isoformat()
        if day_str not in self.events: self.events[day_str] = []
        self.events[day_str].append({"title": title, "time": self.event_time.get_text()})
        self.save_events(); self.event_title.set_text(""); self.event_time.set_text("")
        self.load_day_events(self.selected_date); self.draw_calendar()

    def on_del_event(self, btn, date, idx):
        day_str = date.isoformat()
        if day_str in self.events and idx < len(self.events[day_str]):
            self.events[day_str].pop(idx); self.save_events()
            self.load_day_events(date); self.draw_calendar()

    def on_prev_month(self, btn):
        if self.view_month.month == 1: self.view_month = self.view_month.replace(year=self.view_month.year-1, month=12)
        else: self.view_month = self.view_month.replace(month=self.view_month.month-1)
        self.draw_calendar()

    def on_next_month(self, btn):
        if self.view_month.month == 12: self.view_month = self.view_month.replace(year=self.view_month.year+1, month=1)
        else: self.view_month = self.view_month.replace(month=self.view_month.month+1)
        self.draw_calendar()

    def on_today(self, btn):
        self.view_month = self.today.replace(day=1); self.selected_date = self.today; self.draw_calendar()

class CalendarAppApp(Gtk.Application):
    def __init__(self): super().__init__(application_id="com.pens.CalendarApp")
    def do_activate(self): CalendarAppWindow(self).present()

def main(): CalendarAppApp().run(None)
if __name__ == "__main__": main()
