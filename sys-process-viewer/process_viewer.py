#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import os, threading, time

def read_proc_status(pid):
    try:
        with open(f"/proc/{pid}/status") as f:
            return dict(line.split(':\t', 1) for line in f if ':\t' in line)
    except Exception:
        return {}

def read_proc_stat(pid):
    try:
        with open(f"/proc/{pid}/stat") as f:
            return f.read().split()
    except Exception:
        return []

def get_processes():
    procs = []
    try:
        pids = [p for p in os.listdir("/proc") if p.isdigit()]
    except Exception:
        return []
    for pid in pids:
        try:
            status = read_proc_status(pid)
            name = status.get("Name", "").strip()
            state = status.get("State", "?").strip()
            ppid = status.get("PPid", "0").strip()
            vm_rss = status.get("VmRSS", "0 kB").strip().split()[0]
            threads = status.get("Threads", "1").strip()
            try:
                with open(f"/proc/{pid}/cmdline") as f:
                    cmdline = f.read().replace('\x00', ' ').strip()[:80]
            except Exception:
                cmdline = name
            procs.append({
                "pid": int(pid), "name": name, "state": state,
                "ppid": int(ppid), "rss_kb": int(vm_rss) if vm_rss.isdigit() else 0,
                "threads": int(threads) if threads.isdigit() else 1,
                "cmdline": cmdline,
            })
        except Exception:
            continue
    return sorted(procs, key=lambda p: p["rss_kb"], reverse=True)

class ProcessViewerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Process Viewer")
        self.set_default_size(1000, 640)
        self.all_procs = []
        self.sort_col = "rss_kb"
        self.sort_asc = False
        self.build_ui()
        self.refresh_procs()
        GLib.timeout_add(3000, self.refresh_procs)

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        vbox.set_margin_top(6); vbox.set_margin_bottom(6)
        vbox.set_margin_start(6); vbox.set_margin_end(6)
        self.set_child(vbox)

        top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        top_box.append(Gtk.Label(label="Process Viewer", css_classes=["title"]))
        self.count_label = Gtk.Label(label="")
        self.count_label.set_hexpand(True)
        self.count_label.set_xalign(1)
        top_box.append(self.count_label)
        vbox.append(top_box)

        filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        filter_box.append(Gtk.Label(label="Filter:"))
        self.filter_entry = Gtk.SearchEntry()
        self.filter_entry.set_hexpand(True)
        self.filter_entry.connect("search-changed", self.on_filter)
        filter_box.append(self.filter_entry)
        refresh_btn = Gtk.Button(label="⟳ Refresh")
        refresh_btn.connect("clicked", lambda b: self.refresh_procs())
        filter_box.append(refresh_btn)
        vbox.append(filter_box)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)

        self.store = Gtk.ListStore(int, str, str, int, int, str, str)
        self.tree = Gtk.TreeView(model=self.store)
        self.tree.set_headers_clickable(True)

        cols = [
            ("PID", 0, True),
            ("Name", 1, True),
            ("State", 2, True),
            ("PPID", 3, True),
            ("RSS (kB)", 4, True),
            ("Cmdline", 5, False),
            ("Threads", 6, False),
        ]
        for title, col_idx, clickable in cols:
            renderer = Gtk.CellRendererText()
            col = Gtk.TreeViewColumn(title, renderer, text=col_idx)
            col.set_resizable(True)
            col.set_sort_column_id(col_idx) if clickable else None
            self.tree.append_column(col)

        selection = self.tree.get_selection()
        selection.connect("changed", self.on_selection_changed)
        scroll.set_child(self.tree)
        vbox.append(scroll)

        info_frame = Gtk.Frame(label="Process Details")
        self.info_label = Gtk.Label(label="Select a process to see details")
        self.info_label.set_xalign(0)
        self.info_label.set_margin_top(4); self.info_label.set_margin_start(6)
        self.info_label.set_margin_bottom(4); self.info_label.set_margin_end(6)
        self.info_label.set_wrap(True)
        info_frame.set_child(self.info_label)
        vbox.append(info_frame)

    def refresh_procs(self):
        procs = get_processes()
        self.all_procs = procs
        q = self.filter_entry.get_text().lower()
        self.populate_store(procs, q)
        total_mem = sum(p["rss_kb"] for p in procs)
        self.count_label.set_text(f"{len(procs)} processes | Total RSS: {total_mem//1024} MB")
        return True

    def populate_store(self, procs, q=""):
        self.store.clear()
        for p in procs:
            if q and q not in p["name"].lower() and q not in str(p["pid"]) and q not in p["cmdline"].lower():
                continue
            self.store.append([
                p["pid"], p["name"], p["state"], p["ppid"],
                p["rss_kb"], p["cmdline"][:80], str(p["threads"])
            ])

    def on_filter(self, entry):
        q = entry.get_text().lower()
        self.populate_store(self.all_procs, q)

    def on_selection_changed(self, selection):
        model, iter_ = selection.get_selected()
        if iter_ is None:
            return
        pid = model[iter_][0]
        proc = next((p for p in self.all_procs if p["pid"] == pid), None)
        if proc:
            text = (f"PID: {proc['pid']}  |  Name: {proc['name']}  |  State: {proc['state']}\n"
                    f"Parent PID: {proc['ppid']}  |  RSS: {proc['rss_kb']} kB  |  Threads: {proc['threads']}\n"
                    f"Command: {proc['cmdline']}")
            self.info_label.set_text(text)
            try:
                with open(f"/proc/{pid}/environ", 'rb') as f:
                    env_count = f.read().count(b'\x00')
                self.info_label.set_text(text + f"\nEnv vars: {env_count}")
            except Exception:
                pass

class ProcessViewerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.ProcessViewer")
    def do_activate(self):
        win = ProcessViewerWindow(self); win.present()

def main():
    app = ProcessViewerApp(); app.run(None)

if __name__ == "__main__":
    main()
