#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import os, threading

def fmt_kb(n):
    try:
        n = int(n)
    except Exception:
        return str(n)
    if n >= 1048576: return f"{n/1048576:.1f} GB"
    if n >= 1024: return f"{n/1024:.1f} MB"
    return f"{n} kB"

def get_meminfo():
    info = {}
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0].rstrip(':')
                    val = int(parts[1]) if parts[1].isdigit() else parts[1]
                    info[key] = val
    except Exception:
        pass
    return info

def get_process_memory():
    procs = []
    try:
        pids = [p for p in os.listdir("/proc") if p.isdigit()]
    except Exception:
        return []
    for pid in pids:
        try:
            with open(f"/proc/{pid}/status") as f:
                status = {}
                for line in f:
                    if ":\t" in line:
                        k, v = line.split(":\t", 1)
                        status[k] = v.strip()
            name = status.get("Name", "?")
            vm_rss = int(status.get("VmRSS", "0 kB").split()[0])
            vm_virt = int(status.get("VmSize", "0 kB").split()[0])
            vm_swap = int(status.get("VmSwap", "0 kB").split()[0])
            procs.append({"pid": int(pid), "name": name, "rss": vm_rss, "virt": vm_virt, "swap": vm_swap})
        except Exception:
            continue
    return sorted(procs, key=lambda p: p["rss"], reverse=True)[:50]

class MemoryMapWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Memory Map")
        self.set_default_size(900, 640)
        self.meminfo = {}
        self.procs = []
        self.build_ui()
        self.refresh()
        GLib.timeout_add(2000, self.refresh)

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(6); vbox.set_margin_bottom(6)
        vbox.set_margin_start(6); vbox.set_margin_end(6)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Memory Map", css_classes=["title"]))

        # Memory gauge
        gauge_frame = Gtk.Frame(label="Physical Memory Usage")
        self.gauge = Gtk.DrawingArea()
        self.gauge.set_size_request(-1, 80)
        self.gauge.set_draw_func(self.draw_gauge)
        gauge_frame.set_child(self.gauge)
        vbox.append(gauge_frame)

        # Stats grid
        stats_frame = Gtk.Frame(label="Memory Statistics")
        stats_grid = Gtk.Grid()
        stats_grid.set_row_spacing(4); stats_grid.set_column_spacing(20)
        stats_grid.set_margin_top(6); stats_grid.set_margin_start(8); stats_grid.set_margin_bottom(6)
        self.stat_labels = {}
        stat_keys = [
            ("MemTotal", "Total RAM"), ("MemFree", "Free"),
            ("MemAvailable", "Available"), ("Buffers", "Buffers"),
            ("Cached", "Cached"), ("SwapTotal", "Swap Total"),
            ("SwapFree", "Swap Free"), ("Shmem", "Shared"),
            ("Mapped", "Mapped"), ("AnonPages", "Anonymous"),
        ]
        for i, (key, label) in enumerate(stat_keys):
            row = i % 5
            col = (i // 5) * 2
            name_lbl = Gtk.Label(label=f"{label}:", xalign=1)
            val_lbl = Gtk.Label(label="--", xalign=0)
            self.stat_labels[key] = val_lbl
            stats_grid.attach(name_lbl, col, row, 1, 1)
            stats_grid.attach(val_lbl, col + 1, row, 1, 1)
        stats_frame.set_child(stats_grid)
        vbox.append(stats_frame)

        # Process list
        proc_frame = Gtk.Frame(label="Top Processes by RSS")
        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        self.proc_store = Gtk.ListStore(int, str, str, str, str)
        tree = Gtk.TreeView(model=self.proc_store)
        tree.get_selection().connect("changed", self.on_proc_selected)
        for i, (title, width) in enumerate([("PID", 70), ("Name", 180), ("RSS", 100), ("Virtual", 100), ("Swap", 80)]):
            col = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i)
            col.set_resizable(True); col.set_fixed_width(width)
            col.set_sort_column_id(i)
            tree.append_column(col)
        scroll.set_child(tree)
        proc_frame.set_child(scroll)
        vbox.append(proc_frame)

        self.detail_label = Gtk.Label(label="Select a process to see its memory maps", xalign=0)
        vbox.append(self.detail_label)

    def refresh(self):
        threading.Thread(target=self._load, daemon=True).start()
        return True

    def _load(self):
        meminfo = get_meminfo()
        procs = get_process_memory()
        GLib.idle_add(self._show, meminfo, procs)

    def _show(self, meminfo, procs):
        self.meminfo = meminfo
        self.procs = procs
        for key, lbl in self.stat_labels.items():
            val = meminfo.get(key, "N/A")
            lbl.set_text(fmt_kb(val) if isinstance(val, int) else str(val))
        self.proc_store.clear()
        for p in procs:
            self.proc_store.append([p["pid"], p["name"], fmt_kb(p["rss"]), fmt_kb(p["virt"]), fmt_kb(p["swap"])])
        self.gauge.queue_draw()
        return False

    def draw_gauge(self, area, cr, w, h):
        cr.set_source_rgb(0.1, 0.1, 0.15); cr.rectangle(0, 0, w, h); cr.fill()
        total = self.meminfo.get("MemTotal", 0)
        free = self.meminfo.get("MemAvailable", 0)
        buffers = self.meminfo.get("Buffers", 0)
        cached = self.meminfo.get("Cached", 0)
        swap_total = self.meminfo.get("SwapTotal", 0)
        swap_free = self.meminfo.get("SwapFree", 0)
        if not total:
            return

        bar_h = 28
        pad = 10
        lbl_w = 100

        def draw_bar(y, label, used, total, color_used, color_free):
            if total == 0: return
            cr.set_source_rgb(0.6, 0.6, 0.7); cr.set_font_size(11)
            cr.move_to(pad, y + bar_h - 6); cr.show_text(label)
            bar_x = pad + lbl_w
            bar_w = w - bar_x - pad
            cr.set_source_rgb(0.2, 0.2, 0.3)
            cr.rectangle(bar_x, y, bar_w, bar_h); cr.fill()
            used_w = int(used / total * bar_w)
            cr.set_source_rgb(*color_used)
            cr.rectangle(bar_x, y, used_w, bar_h); cr.fill()
            cr.set_source_rgb(0.9, 0.9, 0.9); cr.set_font_size(10)
            pct = used / total * 100
            cr.move_to(bar_x + 4, y + bar_h - 6)
            cr.show_text(f"{fmt_kb(used)} / {fmt_kb(total)} ({pct:.1f}%)")

        used_mem = total - free - buffers - cached
        draw_bar(4, "RAM", max(0, used_mem), total, (0.3, 0.6, 0.9), (0.2, 0.3, 0.4))
        if swap_total > 0:
            draw_bar(36, "Swap", swap_total - swap_free, swap_total, (0.9, 0.5, 0.3), (0.2, 0.2, 0.3))

    def on_proc_selected(self, selection):
        model, iter_ = selection.get_selected()
        if not iter_:
            return
        pid = model[iter_][0]
        try:
            with open(f"/proc/{pid}/maps") as f:
                maps_text = f.read()
            lines = maps_text.strip().split('\n')
            self.detail_label.set_text(f"Memory maps for PID {pid}: {len(lines)} regions\n" + "\n".join(lines[:10]) + ("..." if len(lines) > 10 else ""))
        except Exception as e:
            self.detail_label.set_text(f"Cannot read maps for PID {pid}: {e}")

class MemoryMapApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.MemoryMap")
    def do_activate(self):
        win = MemoryMapWindow(self); win.present()

def main():
    app = MemoryMapApp(); app.run(None)

if __name__ == "__main__":
    main()
