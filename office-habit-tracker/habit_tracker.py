#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import json, os, datetime

DATA_DIR = os.path.expanduser("~/.local/share/com.pens.HabitTracker")
DATA_FILE = os.path.join(DATA_DIR, "habits.json")

class HabitTrackerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Habit Tracker")
        self.set_default_size(900, 640)
        os.makedirs(DATA_DIR, exist_ok=True)
        self.data = self.load_data()
        self.today = datetime.date.today().isoformat()
        self.view_month = datetime.date.today().replace(day=1)
        self.build_ui()
        self.refresh()

    def load_data(self):
        try:
            with open(DATA_FILE) as f:
                return json.load(f)
        except Exception:
            return {"habits": [], "completions": {}}

    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump(self.data, f)

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        add_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.habit_entry = Gtk.Entry()
        self.habit_entry.set_placeholder_text("New habit name...")
        self.habit_entry.set_hexpand(True)
        add_btn = Gtk.Button(label="Add Habit")
        add_btn.connect("clicked", self.on_add_habit)
        add_box.append(self.habit_entry); add_box.append(add_btn)
        vbox.append(add_box)

        today_frame = Gtk.Frame(label=f"Today — {self.today}")
        self.today_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.today_box.set_margin_top(6); self.today_box.set_margin_start(6)
        self.today_box.set_margin_bottom(6); self.today_box.set_margin_end(6)
        today_frame.set_child(self.today_box)
        vbox.append(today_frame)

        month_nav = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        month_nav.set_halign(Gtk.Align.CENTER)
        prev_btn = Gtk.Button(label="←"); prev_btn.connect("clicked", self.on_prev_month)
        next_btn = Gtk.Button(label="→"); next_btn.connect("clicked", self.on_next_month)
        self.month_label = Gtk.Label(label="")
        month_nav.append(prev_btn); month_nav.append(self.month_label); month_nav.append(next_btn)
        vbox.append(month_nav)

        grid_frame = Gtk.Frame(label="Monthly Grid")
        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        self.grid_area = Gtk.DrawingArea()
        self.grid_area.set_size_request(850, 300)
        self.grid_area.set_draw_func(self.draw_grid)
        scroll.set_child(self.grid_area)
        grid_frame.set_child(scroll)
        vbox.append(grid_frame)

        self.stats_label = Gtk.Label(label="")
        vbox.append(self.stats_label)

    def on_add_habit(self, btn):
        name = self.habit_entry.get_text().strip()
        if name and name not in self.data["habits"]:
            self.data["habits"].append(name)
            self.save_data()
            self.refresh()
            self.habit_entry.set_text("")

    def refresh(self):
        while self.today_box.get_first_child():
            self.today_box.remove(self.today_box.get_first_child())

        for habit in self.data["habits"]:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            key = f"{self.today}:{habit}"
            done = key in self.data["completions"]
            cb = Gtk.CheckButton(label=habit)
            cb.set_active(done)
            cb.connect("toggled", self.on_habit_toggled, habit)

            streak = self.calc_streak(habit)
            pct = self.calc_completion(habit)
            info = Gtk.Label(label=f"🔥 {streak}d | {pct:.0f}%")
            del_btn = Gtk.Button(label="×")
            del_btn.connect("clicked", self.on_delete_habit, habit)
            row.append(cb); row.append(info); row.append(del_btn)
            self.today_box.append(row)

        self.month_label.set_text(self.view_month.strftime("%B %Y"))
        self.grid_area.queue_draw()
        self.refresh_stats()

    def on_habit_toggled(self, cb, habit):
        key = f"{self.today}:{habit}"
        if cb.get_active():
            self.data["completions"][key] = True
        elif key in self.data["completions"]:
            del self.data["completions"][key]
        self.save_data()
        self.grid_area.queue_draw()
        self.refresh_stats()

    def on_delete_habit(self, btn, habit):
        self.data["habits"].remove(habit)
        self.save_data()
        self.refresh()

    def on_prev_month(self, btn):
        if self.view_month.month == 1:
            self.view_month = self.view_month.replace(year=self.view_month.year-1, month=12)
        else:
            self.view_month = self.view_month.replace(month=self.view_month.month-1)
        self.refresh()

    def on_next_month(self, btn):
        if self.view_month.month == 12:
            self.view_month = self.view_month.replace(year=self.view_month.year+1, month=1)
        else:
            self.view_month = self.view_month.replace(month=self.view_month.month+1)
        self.refresh()

    def calc_streak(self, habit):
        streak = 0
        d = datetime.date.today()
        while True:
            if f"{d.isoformat()}:{habit}" in self.data["completions"]:
                streak += 1
                d -= datetime.timedelta(days=1)
            else:
                break
        return streak

    def calc_completion(self, habit):
        total = len([k for k in self.data["completions"] if k.endswith(f":{habit}")])
        days = max(1, (datetime.date.today() - datetime.date(2024,1,1)).days)
        return min(100, total / days * 100)

    def refresh_stats(self):
        if not self.data["habits"]: return
        stats = []
        for h in self.data["habits"]:
            stats.append(f"{h}: {self.calc_streak(h)}-day streak, {self.calc_completion(h):.0f}% completion")
        self.stats_label.set_text("  |  ".join(stats[:3]))

    def draw_grid(self, area, cr, w, h):
        cr.set_source_rgb(0.1,0.1,0.15); cr.rectangle(0,0,w,h); cr.fill()
        habits = self.data["habits"]
        if not habits: return
        year, month = self.view_month.year, self.view_month.month
        import calendar
        days_in_month = calendar.monthrange(year, month)[1]
        cell_w = (w - 100) / days_in_month
        cell_h = (h - 20) / len(habits)
        cr.set_source_rgb(0.7,0.7,0.7); cr.set_font_size(9)
        for d in range(1, days_in_month+1):
            cr.move_to(100 + (d-1)*cell_w + 2, 14)
            cr.show_text(str(d))
        for hi, habit in enumerate(habits):
            y = 20 + hi * cell_h
            cr.set_source_rgb(0.8,0.8,0.8)
            cr.move_to(2, y + cell_h*0.6); cr.show_text(habit[:12])
            for d in range(1, days_in_month+1):
                date_str = f"{year:04d}-{month:02d}-{d:02d}"
                key = f"{date_str}:{habit}"
                done = key in self.data["completions"]
                if done:
                    cr.set_source_rgb(0.2, 0.8, 0.2)
                else:
                    cr.set_source_rgb(0.2, 0.2, 0.25)
                cr.rectangle(100 + (d-1)*cell_w + 1, y + 2, cell_w - 3, cell_h - 4)
                cr.fill()

class HabitTrackerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.HabitTracker")
    def do_activate(self):
        win = HabitTrackerWindow(self); win.present()

def main():
    app = HabitTrackerApp(); app.run(None)

if __name__ == "__main__":
    main()
