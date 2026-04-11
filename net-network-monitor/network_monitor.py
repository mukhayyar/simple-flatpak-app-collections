#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import os, time, collections

MAX_HISTORY = 60

def read_net_stats():
    stats = {}
    try:
        with open("/proc/net/dev") as f:
            for line in f:
                parts = line.strip().split(":")
                if len(parts) == 2:
                    iface = parts[0].strip()
                    vals = parts[1].split()
                    if len(vals) >= 9:
                        stats[iface] = {
                            "rx_bytes": int(vals[0]),
                            "rx_packets": int(vals[1]),
                            "rx_errors": int(vals[2]),
                            "tx_bytes": int(vals[8]),
                            "tx_packets": int(vals[9]),
                            "tx_errors": int(vals[10]),
                        }
    except Exception:
        pass
    return stats

class NetworkMonitorWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Network Monitor")
        self.set_default_size(800, 600)
        self.iface = None
        self.prev_stats = None
        self.prev_time = None
        self.rx_history = collections.deque(maxlen=MAX_HISTORY)
        self.tx_history = collections.deque(maxlen=MAX_HISTORY)
        self.max_rate = 1
        self.build_ui()
        GLib.timeout_add(1000, self.update)

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(6); vbox.set_margin_bottom(6)
        vbox.set_margin_start(6); vbox.set_margin_end(6)
        self.set_child(vbox)

        ctrl = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        ctrl.append(Gtk.Label(label="Interface:"))
        self.iface_combo = Gtk.ComboBoxText()
        stats = read_net_stats()
        for iface in stats:
            self.iface_combo.append_text(iface)
        if stats:
            self.iface_combo.set_active(0)
            self.iface = list(stats.keys())[0]
        self.iface_combo.connect("changed", self.on_iface_changed)
        ctrl.append(self.iface_combo)
        vbox.append(ctrl)

        stats_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)

        self.rx_label = Gtk.Label(label="RX: --")
        self.tx_label = Gtk.Label(label="TX: --")
        self.rx_total_label = Gtk.Label(label="RX Total: --")
        self.tx_total_label = Gtk.Label(label="TX Total: --")
        for lbl in [self.rx_label, self.tx_label, self.rx_total_label, self.tx_total_label]:
            stats_box.append(lbl)
        vbox.append(stats_box)

        graph_frame = Gtk.Frame(label="RX (green) / TX (red) — KB/s")
        self.graph = Gtk.DrawingArea()
        self.graph.set_size_request(760, 250)
        self.graph.set_draw_func(self.on_draw)
        self.graph.set_vexpand(True)
        graph_frame.set_child(self.graph)
        vbox.append(graph_frame)

        details_frame = Gtk.Frame(label="Interface Details")
        self.details_view = Gtk.TextView()
        self.details_view.set_editable(False)
        self.details_view.set_monospace(True)
        details_scroll = Gtk.ScrolledWindow()
        details_scroll.set_min_content_height(100)
        details_scroll.set_child(self.details_view)
        details_frame.set_child(details_scroll)
        vbox.append(details_frame)

    def on_iface_changed(self, combo):
        self.iface = combo.get_active_text()
        self.rx_history.clear()
        self.tx_history.clear()
        self.prev_stats = None

    def update(self):
        stats = read_net_stats()
        now = time.time()
        if self.iface and self.iface in stats:
            cur = stats[self.iface]
            if self.prev_stats and self.prev_time:
                dt = now - self.prev_time
                prev = self.prev_stats
                rx_rate = (cur["rx_bytes"] - prev["rx_bytes"]) / dt
                tx_rate = (cur["tx_bytes"] - prev["tx_bytes"]) / dt
                self.rx_history.append(rx_rate)
                self.tx_history.append(tx_rate)
                self.max_rate = max(1, max(max(self.rx_history, default=0), max(self.tx_history, default=0)))
                self.rx_label.set_text(f"RX: {self.fmt_rate(rx_rate)}")
                self.tx_label.set_text(f"TX: {self.fmt_rate(tx_rate)}")
            self.rx_total_label.set_text(f"RX Total: {self.fmt_bytes(cur['rx_bytes'])}")
            self.tx_total_label.set_text(f"TX Total: {self.fmt_bytes(cur['tx_bytes'])}")
            details = (f"Packets RX: {cur['rx_packets']}  TX: {cur['tx_packets']}\n"
                       f"Errors  RX: {cur['rx_errors']}  TX: {cur['tx_errors']}")
            self.details_view.get_buffer().set_text(details)
            self.prev_stats = cur
            self.prev_time = now
            self.graph.queue_draw()
        return True

    def fmt_rate(self, bps):
        kbps = bps / 1024
        if kbps > 1024: return f"{kbps/1024:.2f} MB/s"
        return f"{kbps:.1f} KB/s"

    def fmt_bytes(self, b):
        if b > 1e9: return f"{b/1e9:.2f} GB"
        if b > 1e6: return f"{b/1e6:.2f} MB"
        return f"{b/1024:.1f} KB"

    def on_draw(self, area, cr, w, h):
        cr.set_source_rgb(0.05, 0.05, 0.1)
        cr.rectangle(0, 0, w, h); cr.fill()
        step = w / MAX_HISTORY

        for hist, color in [(self.rx_history, (0.2, 0.8, 0.2)), (self.tx_history, (0.8, 0.2, 0.2))]:
            if len(hist) < 2: continue
            cr.set_source_rgb(*color)
            cr.set_line_width(1.5)
            pts = list(hist)
            x0 = (MAX_HISTORY - len(pts)) * step
            cr.move_to(x0, h - (pts[0] / self.max_rate) * (h - 10) - 5)
            for i, v in enumerate(pts[1:], 1):
                cr.line_to(x0 + i * step, h - (v / self.max_rate) * (h - 10) - 5)
            cr.stroke()

        cr.set_source_rgb(0.3, 0.3, 0.3)
        cr.set_font_size(10)
        cr.move_to(2, 14)
        cr.set_source_rgb(0.8, 0.8, 0.8)
        cr.show_text(f"Max: {self.fmt_rate(self.max_rate)}")

class NetworkMonitorApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.NetworkMonitor")
    def do_activate(self):
        win = NetworkMonitorWindow(self)
        win.present()

def main():
    app = NetworkMonitorApp()
    app.run(None)

if __name__ == "__main__":
    main()
