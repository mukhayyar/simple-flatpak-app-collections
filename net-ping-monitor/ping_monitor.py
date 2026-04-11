#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import subprocess, threading, time, collections

MAX_HISTORY = 60

class HostMonitor:
    def __init__(self, host):
        self.host = host
        self.history = collections.deque(maxlen=MAX_HISTORY)
        self.sent = 0; self.received = 0
        self.min_ms = float('inf'); self.max_ms = 0; self.avg_ms = 0

    def ping(self):
        self.sent += 1
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "2", self.host],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "time=" in line:
                        ms = float(line.split("time=")[1].split()[0])
                        self.history.append(ms)
                        self.received += 1
                        self.min_ms = min(self.min_ms, ms)
                        self.max_ms = max(self.max_ms, ms)
                        self.avg_ms = sum(self.history) / len(self.history)
                        return ms
            self.history.append(-1)
            return -1
        except Exception:
            self.history.append(-1)
            return -1

    def packet_loss(self):
        if self.sent == 0: return 0
        return (self.sent - self.received) / self.sent * 100

class PingMonitorWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Ping Monitor")
        self.set_default_size(800, 600)
        self.monitors = {}
        self.running = False
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(6); vbox.set_margin_bottom(6)
        vbox.set_margin_start(6); vbox.set_margin_end(6)
        self.set_child(vbox)

        ctrl = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.host_entry = Gtk.Entry()
        self.host_entry.set_placeholder_text("Enter hostname or IP...")
        self.host_entry.set_hexpand(True)
        ctrl.append(self.host_entry)
        add_btn = Gtk.Button(label="Add Host")
        add_btn.connect("clicked", self.on_add_host)
        ctrl.append(add_btn)
        self.start_btn = Gtk.Button(label="Start")
        self.start_btn.connect("clicked", self.on_toggle)
        ctrl.append(self.start_btn)
        vbox.append(ctrl)

        for host in ["8.8.8.8", "1.1.1.1", "google.com"]:
            self.monitors[host] = HostMonitor(host)

        self.stats_grid = Gtk.Grid()
        self.stats_grid.set_column_spacing(12); self.stats_grid.set_row_spacing(4)
        for i, h in enumerate(["Host", "Last", "Min", "Avg", "Max", "Loss%", "Status"]):
            lbl = Gtk.Label(label=h, xalign=0)
            lbl.set_markup(f"<b>{h}</b>")
            self.stats_grid.attach(lbl, i, 0, 1, 1)
        self.host_rows = {}
        self.update_stats_grid()
        vbox.append(self.stats_grid)

        graph_frame = Gtk.Frame(label="Response Time History")
        self.graph = Gtk.DrawingArea()
        self.graph.set_size_request(760, 200)
        self.graph.set_draw_func(self.on_draw_graph)
        graph_frame.set_child(self.graph)
        vbox.append(graph_frame)

    def update_stats_grid(self):
        while self.stats_grid.get_child_at(0, len(self.monitors) + 2):
            self.stats_grid.remove_row(len(self.monitors) + 2)
        for row_idx, (host, mon) in enumerate(self.monitors.items(), 1):
            if host not in self.host_rows:
                labels = []
                for col in range(7):
                    lbl = Gtk.Label(label="-", xalign=0)
                    self.stats_grid.attach(lbl, col, row_idx, 1, 1)
                    labels.append(lbl)
                del_btn = Gtk.Button(label="×")
                del_btn.connect("clicked", self.on_remove, host)
                self.stats_grid.attach(del_btn, 7, row_idx, 1, 1)
                self.host_rows[host] = labels

    def on_add_host(self, btn):
        host = self.host_entry.get_text().strip()
        if host and host not in self.monitors:
            self.monitors[host] = HostMonitor(host)
            self.update_stats_grid()
            self.host_entry.set_text("")

    def on_remove(self, btn, host):
        if host in self.monitors:
            del self.monitors[host]
            if host in self.host_rows:
                del self.host_rows[host]
            self.update_stats_grid()

    def on_toggle(self, btn):
        if self.running:
            self.running = False
            self.start_btn.set_label("Start")
        else:
            self.running = True
            self.start_btn.set_label("Stop")
            threading.Thread(target=self.ping_loop, daemon=True).start()

    def ping_loop(self):
        while self.running:
            for host, mon in list(self.monitors.items()):
                threading.Thread(target=self.do_ping, args=(mon,), daemon=True).start()
            GLib.idle_add(self.refresh_ui)
            time.sleep(2)

    def do_ping(self, mon):
        mon.ping()

    def refresh_ui(self):
        for host, mon in self.monitors.items():
            if host in self.host_rows:
                labels = self.host_rows[host]
                last = mon.history[-1] if mon.history else -1
                labels[0].set_text(host)
                labels[1].set_text(f"{last:.1f}ms" if last >= 0 else "timeout")
                labels[2].set_text(f"{mon.min_ms:.1f}" if mon.min_ms != float('inf') else "-")
                labels[3].set_text(f"{mon.avg_ms:.1f}" if mon.avg_ms else "-")
                labels[4].set_text(f"{mon.max_ms:.1f}" if mon.max_ms else "-")
                labels[5].set_text(f"{mon.packet_loss():.0f}%")
                status = "OK" if last >= 0 else "FAIL"
                labels[6].set_markup(f'<span foreground="{"green" if last >= 0 else "red"}">{status}</span>')
        self.graph.queue_draw()
        return False

    def on_draw_graph(self, area, cr, w, h):
        cr.set_source_rgb(0.1, 0.1, 0.15)
        cr.rectangle(0, 0, w, h); cr.fill()
        colors = [(0.8,0.2,0.2), (0.2,0.8,0.2), (0.2,0.2,0.8), (0.8,0.8,0.2)]
        for idx, (host, mon) in enumerate(self.monitors.items()):
            hist = [v for v in mon.history if v >= 0]
            if len(hist) < 2: continue
            mx = max(hist) or 1
            r, g, b = colors[idx % len(colors)]
            cr.set_source_rgb(r, g, b)
            cr.set_line_width(1.5)
            step = w / (MAX_HISTORY - 1)
            pts = list(mon.history)
            valid_start = None
            for i, v in enumerate(pts):
                x = i * step
                if v < 0:
                    if valid_start is not None:
                        cr.stroke(); valid_start = None
                    continue
                y = h - (v / mx) * (h - 20) - 10
                if valid_start is None:
                    cr.move_to(x, y); valid_start = i
                else:
                    cr.line_to(x, y)
            cr.stroke()
            cr.set_font_size(10)
            cr.move_to(4, (idx + 1) * 14)
            cr.set_source_rgb(r, g, b)
            cr.show_text(f"{host}: avg={mon.avg_ms:.1f}ms")

class PingMonitorApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.PingMonitor")
    def do_activate(self):
        win = PingMonitorWindow(self)
        win.present()

def main():
    app = PingMonitorApp()
    app.run(None)

if __name__ == "__main__":
    main()
