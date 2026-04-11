#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import time

class StopwatchWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Stopwatch")
        self.set_default_size(480, 480)
        self.running = False
        self.start_time = None
        self.elapsed = 0.0
        self.laps = []
        self.last_lap_time = 0.0
        self.build_ui()
        GLib.timeout_add(10, self.update)

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(20); vbox.set_margin_bottom(20)
        vbox.set_margin_start(20); vbox.set_margin_end(20)
        vbox.set_halign(Gtk.Align.CENTER)
        self.set_child(vbox)

        self.display = Gtk.Label(label="00:00.000")
        self.display.set_markup("<span font='64' weight='bold' font_family='monospace'>00:00.000</span>")
        vbox.append(self.display)

        self.lap_display = Gtk.Label(label="Lap: 00:00.000")
        self.lap_display.set_markup("<span font='18' font_family='monospace'>Lap: 00:00.000</span>")
        vbox.append(self.lap_display)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        btn_box.set_halign(Gtk.Align.CENTER)
        self.start_btn = Gtk.Button(label="▶ Start")
        self.start_btn.set_size_request(120, 50)
        self.start_btn.connect("clicked", self.on_start_stop)
        self.lap_btn = Gtk.Button(label="⚑ Lap")
        self.lap_btn.set_size_request(100, 50)
        self.lap_btn.connect("clicked", self.on_lap)
        self.reset_btn = Gtk.Button(label="⟳ Reset")
        self.reset_btn.set_size_request(100, 50)
        self.reset_btn.connect("clicked", self.on_reset)
        btn_box.append(self.start_btn); btn_box.append(self.lap_btn); btn_box.append(self.reset_btn)
        vbox.append(btn_box)

        lap_frame = Gtk.Frame(label="Laps")
        scroll = Gtk.ScrolledWindow(); scroll.set_size_request(-1, 160)
        self.lap_store = Gtk.ListStore(int, str, str, str)
        lap_tree = Gtk.TreeView(model=self.lap_store)
        for i, title in enumerate(["#", "Lap Time", "Total", "Delta"]):
            col = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i)
            col.set_resizable(True)
            lap_tree.append_column(col)
        scroll.set_child(lap_tree)
        lap_frame.set_child(scroll)
        vbox.append(lap_frame)

        self.stats_label = Gtk.Label(label="", xalign=0)
        vbox.append(self.stats_label)

    def fmt_time(self, t):
        mins = int(t // 60)
        secs = t % 60
        ms = int((t - int(t)) * 1000)
        return f"{mins:02d}:{int(secs):02d}.{ms:03d}"

    def on_start_stop(self, btn):
        if self.running:
            self.elapsed += time.perf_counter() - self.start_time
            self.start_time = None
            self.running = False
            self.start_btn.set_label("▶ Resume")
        else:
            self.start_time = time.perf_counter()
            self.running = True
            self.start_btn.set_label("⏸ Pause")

    def on_lap(self, btn):
        total = self.elapsed
        if self.running:
            total += time.perf_counter() - self.start_time
        if total == 0:
            return
        lap_time = total - self.last_lap_time
        n = len(self.laps) + 1
        delta = ""
        if self.laps:
            prev_lap = self.laps[-1][1]
            d = lap_time - prev_lap
            delta = f"+{self.fmt_time(d)}" if d >= 0 else f"-{self.fmt_time(-d)}"
        self.laps.append((n, lap_time, total))
        self.lap_store.append([n, self.fmt_time(lap_time), self.fmt_time(total), delta])
        self.last_lap_time = total
        self.update_stats()

    def on_reset(self, btn):
        self.running = False
        self.start_time = None
        self.elapsed = 0.0
        self.last_lap_time = 0.0
        self.laps = []
        self.lap_store.clear()
        self.display.set_markup("<span font='64' weight='bold' font_family='monospace'>00:00.000</span>")
        self.lap_display.set_markup("<span font='18' font_family='monospace'>Lap: 00:00.000</span>")
        self.start_btn.set_label("▶ Start")
        self.stats_label.set_text("")

    def update(self):
        if self.running:
            total = self.elapsed + time.perf_counter() - self.start_time
            self.display.set_markup(f"<span font='64' weight='bold' font_family='monospace'>{self.fmt_time(total)}</span>")
            lap_time = total - self.last_lap_time
            self.lap_display.set_markup(f"<span font='18' font_family='monospace'>Lap: {self.fmt_time(lap_time)}</span>")
        return True

    def update_stats(self):
        if not self.laps:
            return
        lap_times = [l[1] for l in self.laps]
        best = min(lap_times)
        worst = max(lap_times)
        avg = sum(lap_times) / len(lap_times)
        self.stats_label.set_text(f"Best: {self.fmt_time(best)}  |  Worst: {self.fmt_time(worst)}  |  Avg: {self.fmt_time(avg)}")

class StopwatchApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.Stopwatch")
    def do_activate(self):
        win = StopwatchWindow(self); win.present()

def main():
    app = StopwatchApp(); app.run(None)

if __name__ == "__main__":
    main()
