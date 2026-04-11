#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import time, threading, math, os, multiprocessing

def bench_fibonacci(n=35):
    def fib(n):
        if n < 2: return n
        return fib(n-1) + fib(n-2)
    start = time.perf_counter()
    fib(n)
    return time.perf_counter() - start

def bench_primes(limit=100000):
    start = time.perf_counter()
    sieve = [True] * (limit + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(math.sqrt(limit)) + 1):
        if sieve[i]:
            for j in range(i*i, limit+1, i):
                sieve[j] = False
    return time.perf_counter() - start

def bench_float(n=5_000_000):
    start = time.perf_counter()
    x = 0.0
    for i in range(n):
        x += math.sin(i) * math.cos(i)
    return time.perf_counter() - start

def bench_sort(n=500_000):
    import random
    data = [random.random() for _ in range(n)]
    start = time.perf_counter()
    data.sort()
    return time.perf_counter() - start

def bench_string(n=100_000):
    start = time.perf_counter()
    s = ""
    for i in range(n):
        s += str(i)
    return time.perf_counter() - start

def bench_memory(n=1_000_000):
    start = time.perf_counter()
    data = list(range(n))
    data2 = [x * 2 for x in data]
    del data, data2
    return time.perf_counter() - start

BENCHMARKS = [
    ("Fibonacci (n=35)", bench_fibonacci),
    ("Prime Sieve (100k)", bench_primes),
    ("Float Math (5M ops)", bench_float),
    ("Sort (500k items)", bench_sort),
    ("String concat (100k)", bench_string),
    ("Memory alloc (1M)", bench_memory),
]

class CPUBenchmarkWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("CPU Benchmark")
        self.set_default_size(700, 580)
        self.results = {}
        self.running = False
        self.build_ui()
        self.load_system_info()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(16); vbox.set_margin_bottom(16)
        vbox.set_margin_start(20); vbox.set_margin_end(20)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="CPU Benchmark", css_classes=["title"]))

        self.sys_label = Gtk.Label(label="Loading system info...", xalign=0)
        self.sys_label.set_wrap(True)
        vbox.append(self.sys_label)

        self.progress = Gtk.ProgressBar()
        self.progress.set_fraction(0)
        vbox.append(self.progress)

        self.status_label = Gtk.Label(label="Press 'Run All Benchmarks' to start", xalign=0)
        vbox.append(self.status_label)

        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        self.result_store = Gtk.ListStore(str, str, str)
        tree = Gtk.TreeView(model=self.result_store)
        for i, (title, width) in enumerate([("Benchmark", 250), ("Time (s)", 120), ("Score", 120)]):
            col = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i)
            col.set_resizable(True); col.set_fixed_width(width)
            tree.append_column(col)
        scroll.set_child(tree)
        vbox.append(scroll)

        self.chart = Gtk.DrawingArea()
        self.chart.set_size_request(-1, 120)
        self.chart.set_draw_func(self.draw_chart)
        vbox.append(self.chart)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_halign(Gtk.Align.CENTER)
        self.run_btn = Gtk.Button(label="▶ Run All Benchmarks")
        self.run_btn.connect("clicked", self.on_run_all)
        btn_box.append(self.run_btn)
        for label, fn in BENCHMARKS:
            btn = Gtk.Button(label=f"Run: {label[:20]}")
            btn.connect("clicked", self.on_run_single, label, fn)
            btn_box.append(btn)
        vbox.append(btn_box)

    def load_system_info(self):
        info_parts = []
        try:
            with open("/proc/cpuinfo") as f:
                cpu_info = f.read()
            model_line = next((l for l in cpu_info.split('\n') if 'model name' in l), "")
            model = model_line.split(':')[1].strip() if ':' in model_line else "Unknown CPU"
            cores = cpu_info.count('processor\t:')
            info_parts.append(f"CPU: {model} ({cores} logical cores)")
        except Exception:
            info_parts.append(f"CPU cores: {multiprocessing.cpu_count()}")
        try:
            with open("/proc/meminfo") as f:
                mem = f.read()
            total_line = next(l for l in mem.split('\n') if 'MemTotal' in l)
            total_kb = int(total_line.split()[1])
            info_parts.append(f"RAM: {total_kb//1024} MB")
        except Exception:
            pass
        try:
            uname = os.uname()
            info_parts.append(f"OS: {uname.sysname} {uname.release}")
        except Exception:
            pass
        self.sys_label.set_text("  |  ".join(info_parts))

    def on_run_all(self, btn):
        if self.running:
            return
        self.running = True
        self.run_btn.set_sensitive(False)
        self.result_store.clear()
        self.results = {}
        threading.Thread(target=self._run_all, daemon=True).start()

    def _run_all(self):
        total = len(BENCHMARKS)
        for i, (name, fn) in enumerate(BENCHMARKS):
            GLib.idle_add(self.status_label.set_text, f"Running: {name}...")
            GLib.idle_add(self.progress.set_fraction, i / total)
            t = fn()
            score = int(100 / t) if t > 0 else 9999
            self.results[name] = (t, score)
            GLib.idle_add(self.result_store.append, [name, f"{t:.4f}", str(score)])
        GLib.idle_add(self.on_done)

    def on_done(self):
        self.running = False
        self.run_btn.set_sensitive(True)
        total_score = sum(s for _, (_, s) in self.results.items())
        self.status_label.set_text(f"Done! Total score: {total_score}")
        self.progress.set_fraction(1)
        self.chart.queue_draw()
        return False

    def on_run_single(self, btn, label, fn):
        threading.Thread(target=self._run_single, args=(label, fn), daemon=True).start()

    def _run_single(self, label, fn):
        GLib.idle_add(self.status_label.set_text, f"Running: {label}...")
        t = fn()
        score = int(100 / t) if t > 0 else 9999
        self.results[label] = (t, score)
        GLib.idle_add(self.result_store.append, [label, f"{t:.4f}", str(score)])
        GLib.idle_add(self.status_label.set_text, f"{label}: {t:.4f}s (score: {score})")
        GLib.idle_add(self.chart.queue_draw)

    def draw_chart(self, area, cr, w, h):
        cr.set_source_rgb(0.08, 0.08, 0.12); cr.rectangle(0, 0, w, h); cr.fill()
        if not self.results:
            return
        names = list(self.results.keys())
        scores = [self.results[n][1] for n in names]
        mx = max(scores) or 1
        bw = w / len(names)
        colors = [(0.3,0.6,0.9),(0.9,0.4,0.3),(0.3,0.8,0.4),(0.9,0.7,0.2),(0.7,0.3,0.9),(0.3,0.9,0.9)]
        for i, (name, score) in enumerate(zip(names, scores)):
            bh = int(score / mx * (h - 30))
            cr.set_source_rgb(*colors[i % len(colors)])
            cr.rectangle(i*bw + 2, h - 20 - bh, bw - 4, bh); cr.fill()
            cr.set_source_rgb(0.9, 0.9, 0.9); cr.set_font_size(8)
            cr.move_to(i*bw + 4, h - 4)
            label_short = name.split("(")[0].strip()[:12]
            cr.show_text(label_short)
            cr.move_to(i*bw + 4, h - 24 - bh)
            cr.show_text(str(score))

class CPUBenchmarkApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.CPUBenchmark")
    def do_activate(self):
        win = CPUBenchmarkWindow(self); win.present()

def main():
    app = CPUBenchmarkApp(); app.run(None)

if __name__ == "__main__":
    main()
