#!/usr/bin/env python3
"""AGL System Diagnostics -- com.pens.AGLDiagnostics
Real-time system monitoring for Automotive Grade Linux embedded systems.
Monitors CPU, memory, disk, network, and load average in a live dashboard.
"""
import gi, os, time
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

def rfile(p):
    try:
        with open(p) as f: return f.read()
    except: return ""

_prev_cpu = None
def cpu_pct():
    global _prev_cpu
    for line in rfile("/proc/stat").splitlines():
        if line.startswith("cpu "):
            vals = list(map(int, line.split()[1:9]))
            idle, total = vals[3]+vals[4], sum(vals)
            if _prev_cpu:
                pi, pt = _prev_cpu; _prev_cpu = (idle, total)
                dt = total - pt
                return (1 - (idle-pi)/dt)*100 if dt else 0
            _prev_cpu = (idle, total); return 0
    return 0

def mem_mb():
    d = {}
    for line in rfile("/proc/meminfo").splitlines():
        p = line.split()
        if len(p) >= 2: d[p[0].rstrip(":")] = int(p[1]) if p[1].isdigit() else 0
    total = d.get("MemTotal", 1); avail = d.get("MemAvailable", 0)
    return (total-avail)/1024, total/1024

def disk_gb():
    try:
        st = os.statvfs("/"); tot = st.f_blocks*st.f_frsize/1e9; free = st.f_bavail*st.f_frsize/1e9
        return tot-free, tot
    except: return 0, 1

def load_avg():
    p = rfile("/proc/loadavg").split()
    return tuple(float(x) for x in p[:3]) if len(p) >= 3 else (0,0,0)

def net_bytes():
    total_rx = total_tx = 0
    for line in rfile("/proc/net/dev").splitlines()[2:]:
        cols = line.split()
        if len(cols) >= 10 and not cols[0].startswith("lo"):
            try: total_rx += int(cols[1]); total_tx += int(cols[9])
            except: pass
    return total_rx, total_tx

def uptime_str():
    raw = rfile("/proc/uptime").split()
    if not raw: return "—"
    s = int(float(raw[0])); h,r = divmod(s,3600); m,sc = divmod(r,60)
    return f"{h:02d}:{m:02d}:{sc:02d}"

_prev_net = (0, 0, 0.0)

class DiagApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='com.pens.AGLDiagnostics')

    def do_activate(self):
        win = Gtk.ApplicationWindow(application=self, title='AGL System Diagnostics')
        win.set_default_size(580, 480)
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        win.set_child(root)

        hdr = Gtk.HeaderBar()
        hdr.set_title_widget(Gtk.Label(label='AGL System Diagnostics'))
        self.uptime_lbl = Gtk.Label()
        hdr.pack_end(self.uptime_lbl)
        win.set_titlebar(hdr)

        grid = Gtk.Grid(row_spacing=14, column_spacing=14,
                        margin_top=20, margin_bottom=16,
                        margin_start=20, margin_end=20)
        root.append(grid)

        rows = [
            ("CPU Usage",    "%",     True),
            ("Memory",       "MB",    True),
            ("Disk (root)",  "GB",    True),
            ("Load avg 1m",  "",      False),
            ("Network RX",   "KB/s",  False),
            ("Network TX",   "KB/s",  False),
        ]
        self.bars = []; self.vlbls = []
        for i, (name, unit, has_bar) in enumerate(rows):
            nl = Gtk.Label(label=name, halign=Gtk.Align.START)
            nl.set_size_request(130, -1)
            grid.attach(nl, 0, i, 1, 1)
            if has_bar:
                bar = Gtk.ProgressBar(hexpand=True, show_text=True)
                bar.set_size_request(280, 22)
                grid.attach(bar, 1, i, 1, 1)
                self.bars.append(bar)
            else:
                self.bars.append(None)
                grid.attach(Gtk.Label(), 1, i, 1, 1)
            vl = Gtk.Label(halign=Gtk.Align.START)
            vl.set_size_request(120, -1)
            grid.attach(vl, 2, i, 1, 1)
            self.vlbls.append(vl)

        sep = Gtk.Separator(margin_top=4, margin_bottom=4)
        root.append(sep)
        self.footer = Gtk.Label(halign=Gtk.Align.START,
                                margin_start=20, margin_bottom=12)
        root.append(self.footer)

        win.present()
        self._refresh()
        GLib.timeout_add(1500, self._refresh)

    def _refresh(self):
        global _prev_net
        cpu = cpu_pct()
        mu, mt = mem_mb()
        du, dt = disk_gb()
        l1, l5, l15 = load_avg()
        rx, tx = net_bytes()
        now = time.time()
        prev_rx, prev_tx, prev_t = _prev_net
        dt_t = max(now - prev_t, 0.001)
        rx_rate = (rx - prev_rx) / dt_t / 1024
        tx_rate = (tx - prev_tx) / dt_t / 1024
        _prev_net = (rx, tx, now)
        ncpu = os.cpu_count() or 1

        vals = [
            (cpu/100, f"{cpu:.1f} %"),
            (mu/mt if mt else 0, f"{mu:.0f} / {mt:.0f} MB"),
            (du/dt if dt else 0, f"{du:.1f} / {dt:.1f} GB"),
            (None,   f"{l1:.2f}"),
            (None,   f"{max(0,rx_rate):.1f} KB/s"),
            (None,   f"{max(0,tx_rate):.1f} KB/s"),
        ]
        for i, (frac, txt) in enumerate(vals):
            if frac is not None and self.bars[i]:
                self.bars[i].set_fraction(min(frac, 1.0))
                self.bars[i].set_text(txt)
            self.vlbls[i].set_text(txt)

        self.uptime_lbl.set_markup(f"<span size='small' color='gray'>Up {uptime_str()}</span>")
        self.footer.set_markup(
            f"<span size='small' color='gray'>Load: {l1:.2f}  {l5:.2f}  {l15:.2f}  "
            f"(1m/5m/15m)  |  CPUs: {ncpu}</span>")
        return True

if __name__ == '__main__':
    DiagApp().run()
