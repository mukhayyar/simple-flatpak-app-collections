#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import subprocess, threading, re

def run_cmd(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

class BootAnalyzerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Boot Analyzer")
        self.set_default_size(1000, 660)
        self.build_ui()
        self.load_data()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(6); vbox.set_margin_bottom(6)
        vbox.set_margin_start(6); vbox.set_margin_end(6)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Boot Time Analyzer", css_classes=["title"]))

        self.summary_label = Gtk.Label(label="Loading boot data...", xalign=0)
        self.summary_label.set_wrap(True)
        vbox.append(self.summary_label)

        notebook = Gtk.Notebook()
        vbox.append(notebook)

        # Blame tab
        blame_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        blame_page.set_margin_top(6); blame_page.set_margin_start(6); blame_page.set_margin_end(6); blame_page.set_margin_bottom(6)
        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        self.blame_store = Gtk.ListStore(str, str, str)
        blame_tree = Gtk.TreeView(model=self.blame_store)
        blame_tree.get_selection().connect("changed", self.on_blame_selected)
        for i, (title, width) in enumerate([("Unit", 360), ("Time (ms)", 120), ("Description", 300)]):
            col = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i)
            col.set_resizable(True); col.set_fixed_width(width); col.set_sort_column_id(i)
            blame_tree.append_column(col)
        scroll.set_child(blame_tree)
        blame_page.append(scroll)
        self.blame_detail = Gtk.Label(label="", xalign=0, wrap=True)
        blame_page.append(self.blame_detail)
        notebook.append_page(blame_page, Gtk.Label(label="Boot Blame"))

        # Chart tab
        chart_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        chart_page.set_margin_top(6); chart_page.set_margin_start(6)
        chart_frame = Gtk.Frame(label="Boot Time Chart (top 20 units)")
        self.chart = Gtk.DrawingArea()
        self.chart.set_vexpand(True)
        self.chart.set_draw_func(self.draw_chart)
        chart_frame.set_child(self.chart)
        chart_page.append(chart_frame)
        notebook.append_page(chart_page, Gtk.Label(label="Chart"))

        # Journal tab
        journal_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        journal_page.set_margin_top(6); journal_page.set_margin_start(6); journal_page.set_margin_end(6); journal_page.set_margin_bottom(6)
        scroll2 = Gtk.ScrolledWindow(); scroll2.set_vexpand(True)
        self.journal_view = Gtk.TextView()
        self.journal_view.set_editable(False); self.journal_view.set_monospace(True)
        scroll2.set_child(self.journal_view)
        journal_page.append(scroll2)
        filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        filter_box.append(Gtk.Label(label="Filter:"))
        self.journal_filter = Gtk.SearchEntry()
        self.journal_filter.set_hexpand(True)
        self.journal_filter.connect("search-changed", self.on_journal_filter)
        filter_box.append(self.journal_filter)
        journal_page.append(filter_box)
        notebook.append_page(journal_page, Gtk.Label(label="Boot Log"))

        # Critical chain tab
        chain_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        chain_page.set_margin_top(6); chain_page.set_margin_start(6); chain_page.set_margin_end(6); chain_page.set_margin_bottom(6)
        scroll3 = Gtk.ScrolledWindow(); scroll3.set_vexpand(True)
        self.chain_view = Gtk.TextView()
        self.chain_view.set_editable(False); self.chain_view.set_monospace(True)
        scroll3.set_child(self.chain_view)
        chain_page.append(scroll3)
        notebook.append_page(chain_page, Gtk.Label(label="Critical Chain"))

        self.blame_data = []
        self.journal_lines = []

    def load_data(self):
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        blame_out = run_cmd(["systemd-analyze", "blame", "--no-pager"])
        time_out = run_cmd(["systemd-analyze", "time"])
        journal_out = run_cmd(["journalctl", "-b", "-0", "-n", "200", "--no-pager", "--output=short"])
        chain_out = run_cmd(["systemd-analyze", "critical-chain", "--no-pager"])
        GLib.idle_add(self._show, blame_out, time_out, journal_out, chain_out)

    def _show(self, blame_out, time_out, journal_out, chain_out):
        self.summary_label.set_text(time_out if time_out else "systemd-analyze not available")

        self.blame_store.clear()
        self.blame_data = []
        blame_re = re.compile(r'^\s*([\d.]+(?:min\s*)?\d*(?:\.\d+)?(?:ms|s|min))\s+(.+)$', re.MULTILINE)
        for line in blame_out.split('\n'):
            line = line.strip()
            if not line: continue
            parts = line.split(None, 1)
            if len(parts) == 2:
                time_str, unit = parts[0], parts[1]
                try:
                    if 'ms' in time_str:
                        ms = float(time_str.replace('ms', ''))
                    elif 's' in time_str and 'min' not in time_str:
                        ms = float(time_str.replace('s', '')) * 1000
                    elif 'min' in time_str:
                        ms = float(time_str.replace('min', '').strip()) * 60000
                    else:
                        continue
                    self.blame_data.append((unit, ms))
                    self.blame_store.append([unit, f"{ms:.0f}", ""])
                except Exception:
                    pass

        self.journal_lines = journal_out.split('\n')
        self.journal_view.get_buffer().set_text(journal_out)
        self.chain_view.get_buffer().set_text(chain_out)
        self.chart.queue_draw()
        return False

    def draw_chart(self, area, cr, w, h):
        cr.set_source_rgb(0.08, 0.08, 0.12); cr.rectangle(0, 0, w, h); cr.fill()
        if not self.blame_data:
            return
        top = self.blame_data[:20]
        max_ms = max(ms for _, ms in top) or 1
        bar_h = (h - 20) / len(top)
        colors = [(0.3,0.6,0.9),(0.9,0.4,0.3),(0.3,0.8,0.4),(0.9,0.7,0.2)]
        for i, (unit, ms) in enumerate(top):
            bw = int(ms / max_ms * (w - 220))
            y = i * bar_h + 4
            cr.set_source_rgb(*colors[i % len(colors)])
            cr.rectangle(200, y, bw, bar_h - 3); cr.fill()
            cr.set_source_rgb(0.8, 0.8, 0.8); cr.set_font_size(9)
            name = unit[:28]
            cr.move_to(2, y + bar_h - 4); cr.show_text(name)
            cr.move_to(204 + bw, y + bar_h - 4); cr.show_text(f"{ms:.0f}ms")

    def on_blame_selected(self, selection):
        model, iter_ = selection.get_selected()
        if iter_:
            unit = model[iter_][0]
            ms = model[iter_][1]
            out = run_cmd(["systemctl", "status", unit, "--no-pager", "-l"], timeout=5)
            self.blame_detail.set_text(f"{unit}: {ms}ms\n{out[:300]}")

    def on_journal_filter(self, entry):
        q = entry.get_text().lower()
        if not q:
            self.journal_view.get_buffer().set_text("\n".join(self.journal_lines))
        else:
            filtered = [l for l in self.journal_lines if q in l.lower()]
            self.journal_view.get_buffer().set_text("\n".join(filtered))

class BootAnalyzerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.BootAnalyzer")
    def do_activate(self):
        win = BootAnalyzerWindow(self); win.present()

def main():
    app = BootAnalyzerApp(); app.run(None)

if __name__ == "__main__":
    main()
