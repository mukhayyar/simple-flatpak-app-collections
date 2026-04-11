#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import os, threading

def get_disk_usage(path):
    try:
        stat = os.statvfs(path)
        total = stat.f_blocks * stat.f_frsize
        free = stat.f_bavail * stat.f_frsize
        used = (stat.f_blocks - stat.f_bfree) * stat.f_frsize
        return total, used, free
    except Exception:
        return 0, 0, 0

def fmt_size(n):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"

def get_mounts():
    mounts = []
    try:
        with open("/proc/mounts") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 3:
                    dev, mountpoint, fstype = parts[0], parts[1], parts[2]
                    if mountpoint.startswith('/') and fstype not in ('proc','sysfs','devtmpfs','tmpfs','cgroup','cgroup2','devpts','mqueue','hugetlbfs','bpf','tracefs','securityfs','configfs','debugfs','fusectl','selinuxfs','autofs','pstore'):
                        mounts.append((dev, mountpoint, fstype))
    except Exception:
        pass
    return mounts

def scan_dir(path, depth=0, max_depth=2):
    entries = []
    if depth > max_depth:
        return entries
    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    if entry.is_file(follow_symlinks=False):
                        entries.append((entry.path, entry.stat(follow_symlinks=False).st_size, False))
                    elif entry.is_dir(follow_symlinks=False):
                        size = dir_size(entry.path)
                        entries.append((entry.path, size, True))
                except Exception:
                    pass
    except Exception:
        pass
    return sorted(entries, key=lambda e: e[1], reverse=True)

def dir_size(path, max_files=500):
    total = 0
    count = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            if count >= max_files:
                break
            try:
                total += os.path.getsize(os.path.join(dirpath, f))
                count += 1
            except Exception:
                pass
        if count >= max_files:
            break
    return total

class DiskUsageWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Disk Usage")
        self.set_default_size(900, 640)
        self.current_path = os.path.expanduser("~")
        self.scan_results = []
        self.build_ui()
        self.refresh_mounts()
        self.scan_directory(self.current_path)

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(6); vbox.set_margin_bottom(6)
        vbox.set_margin_start(6); vbox.set_margin_end(6)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Disk Usage Analyzer", css_classes=["title"]))

        mounts_frame = Gtk.Frame(label="Mounted Filesystems")
        scroll_m = Gtk.ScrolledWindow(); scroll_m.set_min_content_height(120)
        self.mounts_store = Gtk.ListStore(str, str, str, str, str, str)
        mounts_tree = Gtk.TreeView(model=self.mounts_store)
        for i, title in enumerate(["Device", "Mount", "Type", "Total", "Used", "Free"]):
            col = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i)
            col.set_resizable(True)
            mounts_tree.append_column(col)
        scroll_m.set_child(mounts_tree)
        mounts_frame.set_child(scroll_m)
        vbox.append(mounts_frame)

        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        nav_box.append(Gtk.Label(label="Browse:"))
        self.path_entry = Gtk.Entry()
        self.path_entry.set_text(self.current_path)
        self.path_entry.set_hexpand(True)
        self.path_entry.connect("activate", self.on_path_activated)
        nav_box.append(self.path_entry)
        browse_btn = Gtk.Button(label="📂 Browse")
        browse_btn.connect("clicked", self.on_browse)
        nav_box.append(browse_btn)
        up_btn = Gtk.Button(label="⬆ Up")
        up_btn.connect("clicked", self.on_up)
        nav_box.append(up_btn)
        vbox.append(nav_box)

        self.gauge = Gtk.DrawingArea()
        self.gauge.set_size_request(-1, 40)
        self.gauge.set_draw_func(self.draw_gauge)
        vbox.append(self.gauge)

        files_frame = Gtk.Frame(label="Directory Contents (by size)")
        scroll_f = Gtk.ScrolledWindow(); scroll_f.set_vexpand(True)
        self.files_store = Gtk.ListStore(str, str, str)
        files_tree = Gtk.TreeView(model=self.files_store)
        files_tree.get_selection().connect("changed", self.on_entry_selected)
        for i, title in enumerate(["Name", "Size", "Type"]):
            col = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i)
            col.set_resizable(True); col.set_sort_column_id(i)
            files_tree.append_column(col)
        scroll_f.set_child(files_tree)
        files_frame.set_child(scroll_f)
        vbox.append(files_frame)

        self.status_label = Gtk.Label(label="Scanning...", xalign=0)
        vbox.append(self.status_label)

        self.mount_total = 0; self.mount_used = 0; self.mount_free = 0

    def refresh_mounts(self):
        self.mounts_store.clear()
        for dev, mp, fstype in get_mounts():
            total, used, free = get_disk_usage(mp)
            if total > 0:
                self.mounts_store.append([dev, mp, fstype,
                    fmt_size(total), fmt_size(used), fmt_size(free)])
        total, used, free = get_disk_usage(self.current_path)
        self.mount_total = total; self.mount_used = used; self.mount_free = free
        self.gauge.queue_draw()

    def scan_directory(self, path):
        self.status_label.set_text(f"Scanning {path}...")
        def worker():
            results = scan_dir(path)
            GLib.idle_add(self.show_results, results, path)
        threading.Thread(target=worker, daemon=True).start()

    def show_results(self, results, path):
        self.scan_results = results
        self.files_store.clear()
        for entry_path, size, is_dir in results[:200]:
            name = os.path.basename(entry_path)
            kind = "Directory" if is_dir else "File"
            self.files_store.append([name, fmt_size(size), kind])
        self.status_label.set_text(f"{path}  |  {len(results)} entries")
        total, used, free = get_disk_usage(path)
        self.mount_total = total; self.mount_used = used; self.mount_free = free
        self.gauge.queue_draw()
        return False

    def draw_gauge(self, area, cr, w, h):
        cr.set_source_rgb(0.15, 0.15, 0.2); cr.rectangle(0, 0, w, h); cr.fill()
        if self.mount_total == 0:
            return
        pct = self.mount_used / self.mount_total
        used_w = int(pct * w)
        color = (0.3, 0.7, 0.3) if pct < 0.7 else ((0.9, 0.7, 0.2) if pct < 0.9 else (0.9, 0.3, 0.3))
        cr.set_source_rgb(*color); cr.rectangle(0, 0, used_w, h); cr.fill()
        cr.set_source_rgb(0.9, 0.9, 0.9); cr.set_font_size(11)
        cr.move_to(10, h - 6)
        cr.show_text(f"Used: {fmt_size(self.mount_used)} / {fmt_size(self.mount_total)} ({pct*100:.1f}%)  Free: {fmt_size(self.mount_free)}")

    def on_entry_selected(self, selection):
        model, iter_ = selection.get_selected()
        if not iter_:
            return
        name = model[iter_][0]
        full_path = os.path.join(self.current_path, name)
        if model[iter_][2] == "Directory":
            self.current_path = full_path
            self.path_entry.set_text(full_path)
            self.scan_directory(full_path)
            self.refresh_mounts()

    def on_path_activated(self, entry):
        path = entry.get_text()
        if os.path.isdir(path):
            self.current_path = path
            self.scan_directory(path)
            self.refresh_mounts()

    def on_up(self, btn):
        parent = os.path.dirname(self.current_path)
        if parent != self.current_path:
            self.current_path = parent
            self.path_entry.set_text(parent)
            self.scan_directory(parent)
            self.refresh_mounts()

    def on_browse(self, btn):
        dialog = Gtk.FileDialog()
        dialog.select_folder(self, None, self.on_folder_selected)

    def on_folder_selected(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
            if folder:
                path = folder.get_path()
                self.current_path = path
                self.path_entry.set_text(path)
                self.scan_directory(path)
                self.refresh_mounts()
        except Exception:
            pass

class DiskUsageApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.DiskUsage")
    def do_activate(self):
        win = DiskUsageWindow(self); win.present()

def main():
    app = DiskUsageApp(); app.run(None)

if __name__ == "__main__":
    main()
