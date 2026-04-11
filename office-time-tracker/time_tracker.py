#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import json, os, time, datetime, math

DATA_DIR = os.path.expanduser("~/.local/share/com.pens.TimeTracker")
DATA_FILE = os.path.join(DATA_DIR, "data.json")

class TimeTrackerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Time Tracker")
        self.set_default_size(800, 640)
        os.makedirs(DATA_DIR, exist_ok=True)
        self.data = self.load_data()
        self.active_project = None
        self.session_start = None
        self.build_ui()
        GLib.timeout_add(1000, self.update_timer)

    def load_data(self):
        try:
            with open(DATA_FILE) as f:
                return json.load(f)
        except Exception:
            return {"projects": {}, "sessions": []}

    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump(self.data, f)

    def build_ui(self):
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_child(paned)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        left.set_size_request(250, -1)
        left.set_margin_top(8); left.set_margin_start(8); left.set_margin_bottom(8)

        add_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.proj_entry = Gtk.Entry(); self.proj_entry.set_placeholder_text("New project name...")
        self.proj_entry.set_hexpand(True)
        add_btn = Gtk.Button(label="+"); add_btn.connect("clicked", self.on_add_project)
        add_box.append(self.proj_entry); add_box.append(add_btn)
        left.append(add_box)

        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        self.proj_list = Gtk.ListBox()
        self.proj_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.proj_list.connect("row-selected", self.on_project_selected)
        scroll.set_child(self.proj_list)
        left.append(scroll)
        paned.set_start_child(left)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        right.set_margin_top(8); right.set_margin_start(8); right.set_margin_end(8); right.set_margin_bottom(8)

        self.proj_label = Gtk.Label(label="Select a project")
        right.append(self.proj_label)

        self.timer_label = Gtk.Label(label="00:00:00")
        css = Gtk.CssProvider()
        css.load_from_data(b".big-timer { font-size: 48px; font-weight: bold; }")
        Gtk.StyleContext.add_provider_for_display(self.get_display(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.timer_label.set_css_classes(["big-timer"])
        right.append(self.timer_label)

        ctrl = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        ctrl.set_halign(Gtk.Align.CENTER)
        self.start_btn = Gtk.Button(label="Start")
        self.start_btn.connect("clicked", self.on_toggle)
        ctrl.append(self.start_btn)
        right.append(ctrl)

        totals_frame = Gtk.Frame(label="Totals")
        self.totals_view = Gtk.TextView(); self.totals_view.set_editable(False); self.totals_view.set_monospace(True)
        totals_scroll = Gtk.ScrolledWindow(); totals_scroll.set_min_content_height(120)
        totals_scroll.set_child(self.totals_view); totals_frame.set_child(totals_scroll)
        right.append(totals_frame)

        chart_frame = Gtk.Frame(label="Time per Project")
        self.chart = Gtk.DrawingArea(); self.chart.set_size_request(-1, 180)
        self.chart.set_draw_func(self.draw_chart); chart_frame.set_child(self.chart)
        right.append(chart_frame)

        export_btn = Gtk.Button(label="Export CSV"); export_btn.connect("clicked", self.on_export)
        right.append(export_btn)
        paned.set_end_child(right)

        self.refresh_projects()
        self.refresh_totals()

    def on_add_project(self, btn):
        name = self.proj_entry.get_text().strip()
        if name and name not in self.data["projects"]:
            self.data["projects"][name] = {"total_seconds": 0}
            self.save_data()
            self.refresh_projects()
            self.proj_entry.set_text("")

    def refresh_projects(self):
        while self.proj_list.get_row_at_index(0):
            self.proj_list.remove(self.proj_list.get_row_at_index(0))
        for name in self.data["projects"]:
            row = Gtk.ListBoxRow()
            lbl = Gtk.Label(label=name, xalign=0)
            lbl.set_margin_start(6); lbl.set_margin_top(4); lbl.set_margin_bottom(4)
            row.set_child(lbl); row._project_name = name
            self.proj_list.append(row)

    def on_project_selected(self, listbox, row):
        if row:
            if self.active_project:
                self.stop_timer()
            self.active_project = row._project_name
            self.proj_label.set_text(f"Project: {self.active_project}")

    def on_toggle(self, btn):
        if not self.active_project: return
        if self.session_start:
            self.stop_timer()
            self.start_btn.set_label("Start")
        else:
            self.session_start = time.time()
            self.start_btn.set_label("Stop")

    def stop_timer(self):
        if self.session_start and self.active_project:
            elapsed = time.time() - self.session_start
            proj = self.data["projects"].get(self.active_project, {})
            proj["total_seconds"] = proj.get("total_seconds", 0) + elapsed
            self.data["projects"][self.active_project] = proj
            session = {"project": self.active_project, "start": self.session_start,
                       "duration": elapsed, "date": datetime.date.today().isoformat()}
            self.data["sessions"].append(session)
            self.save_data()
            self.session_start = None
            self.refresh_totals()
            self.chart.queue_draw()

    def update_timer(self):
        if self.session_start:
            elapsed = time.time() - self.session_start
            h, r = divmod(int(elapsed), 3600)
            m, s = divmod(r, 60)
            self.timer_label.set_text(f"{h:02d}:{m:02d}:{s:02d}")
        return True

    def fmt_duration(self, secs):
        h, r = divmod(int(secs), 3600)
        m, s = divmod(r, 60)
        return f"{h}h {m}m" if h else f"{m}m {s}s"

    def refresh_totals(self):
        lines = ["Project             Total\n" + "-"*35]
        for name, proj in self.data["projects"].items():
            total = proj.get("total_seconds", 0)
            lines.append(f"{name[:20]:<22}{self.fmt_duration(total)}")
        self.totals_view.get_buffer().set_text("\n".join(lines))

    def draw_chart(self, area, cr, w, h):
        cr.set_source_rgb(0.1,0.1,0.15); cr.rectangle(0,0,w,h); cr.fill()
        projects = {n: p.get("total_seconds",0) for n,p in self.data["projects"].items() if p.get("total_seconds",0) > 0}
        if not projects: return
        mx = max(projects.values()) or 1
        bw = w / (len(projects) + 1)
        colors = [(0.3,0.6,0.9),(0.9,0.4,0.3),(0.3,0.9,0.5),(0.9,0.8,0.2),(0.7,0.3,0.9)]
        for i, (name, total) in enumerate(projects.items()):
            bh = (total / mx) * (h - 40)
            cr.set_source_rgb(*colors[i % len(colors)])
            cr.rectangle(i*bw + bw*0.1, h-30-bh, bw*0.8, bh); cr.fill()
            cr.set_source_rgb(0.9,0.9,0.9); cr.set_font_size(9)
            cr.move_to(i*bw+2, h-15); cr.show_text(name[:10])
            cr.move_to(i*bw+2, h-32-bh); cr.show_text(self.fmt_duration(total))

    def on_export(self, btn):
        dialog = Gtk.FileDialog(); dialog.save(self, None, self.do_export)

    def do_export(self, dialog, result):
        try:
            f = dialog.save_finish(result)
            if f:
                with open(f.get_path(), "w") as fp:
                    fp.write("Project,Date,Duration(s)\n")
                    for s in self.data["sessions"]:
                        fp.write(f"{s['project']},{s.get('date','')},{s['duration']:.0f}\n")
        except Exception: pass

class TimeTrackerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.TimeTracker")
    def do_activate(self):
        win = TimeTrackerWindow(self); win.present()

def main():
    app = TimeTrackerApp(); app.run(None)

if __name__ == "__main__":
    main()
