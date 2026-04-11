#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import subprocess, threading

def run_cmd(cmd, timeout=5):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.returncode
    except Exception as e:
        return str(e), -1

def get_services():
    out, rc = run_cmd(["systemctl", "list-units", "--type=service", "--all",
                        "--no-pager", "--no-legend", "--plain"])
    services = []
    if rc == 0:
        for line in out.split('\n'):
            parts = line.split(None, 4)
            if len(parts) >= 4:
                name = parts[0].replace(".service", "")
                load = parts[1]
                active = parts[2]
                sub = parts[3]
                desc = parts[4] if len(parts) > 4 else ""
                services.append({
                    "name": name, "load": load, "active": active,
                    "sub": sub, "desc": desc
                })
    return services

class ServiceMonitorWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Service Monitor")
        self.set_default_size(1000, 660)
        self.all_services = []
        self.build_ui()
        self.refresh_services()
        GLib.timeout_add(10000, self.refresh_services)

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(6); vbox.set_margin_bottom(6)
        vbox.set_margin_start(6); vbox.set_margin_end(6)
        self.set_child(vbox)

        top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        top_box.append(Gtk.Label(label="Service Monitor (systemd)", css_classes=["title"]))
        self.count_label = Gtk.Label(label="")
        self.count_label.set_hexpand(True); self.count_label.set_xalign(1)
        top_box.append(self.count_label)
        vbox.append(top_box)

        filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        filter_box.append(Gtk.Label(label="Filter:"))
        self.filter_entry = Gtk.SearchEntry()
        self.filter_entry.set_hexpand(True)
        self.filter_entry.connect("search-changed", self.on_filter)
        filter_box.append(self.filter_entry)

        state_combo = Gtk.ComboBoxText()
        for s in ["All", "active", "inactive", "failed"]:
            state_combo.append_text(s)
        state_combo.set_active(0)
        state_combo.connect("changed", lambda c: setattr(self, "state_filter", c.get_active_text()) or self.on_filter(None))
        filter_box.append(state_combo)
        self.state_filter = "All"

        refresh_btn = Gtk.Button(label="⟳ Refresh")
        refresh_btn.connect("clicked", lambda b: self.refresh_services())
        filter_box.append(refresh_btn)
        vbox.append(filter_box)

        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        self.store = Gtk.ListStore(str, str, str, str, str)
        self.tree = Gtk.TreeView(model=self.store)
        self.tree.get_selection().connect("changed", self.on_selection_changed)

        for i, (title, width) in enumerate([("Name", 200), ("Load", 80), ("Active", 90), ("Sub", 90), ("Description", 300)]):
            renderer = Gtk.CellRendererText()
            col = Gtk.TreeViewColumn(title, renderer, text=i)
            col.set_resizable(True); col.set_fixed_width(width)
            col.set_sort_column_id(i)
            self.tree.append_column(col)

        scroll.set_child(self.tree)
        vbox.append(scroll)

        detail_frame = Gtk.Frame(label="Service Details / Log")
        scroll2 = Gtk.ScrolledWindow(); scroll2.set_min_content_height(140)
        self.detail_view = Gtk.TextView()
        self.detail_view.set_editable(False); self.detail_view.set_monospace(True)
        scroll2.set_child(self.detail_view)
        detail_frame.set_child(scroll2)
        vbox.append(detail_frame)

        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        action_box.set_halign(Gtk.Align.CENTER)
        for label, action in [("▶ Start", "start"), ("■ Stop", "stop"),
                               ("⟳ Restart", "restart"), ("Status", "status"),
                               ("📋 Logs", "logs")]:
            btn = Gtk.Button(label=label)
            btn.connect("clicked", self.on_action, action)
            action_box.append(btn)
        vbox.append(action_box)

        self.selected_service = None

    def refresh_services(self):
        threading.Thread(target=self._load_services, daemon=True).start()
        return True

    def _load_services(self):
        svcs = get_services()
        GLib.idle_add(self._show_services, svcs)

    def _show_services(self, svcs):
        self.all_services = svcs
        q = self.filter_entry.get_text().lower()
        self.populate_store(svcs, q, self.state_filter)
        active = sum(1 for s in svcs if s["active"] == "active")
        failed = sum(1 for s in svcs if s["active"] == "failed")
        self.count_label.set_text(f"{len(svcs)} services  |  {active} active  |  {failed} failed")
        return False

    def populate_store(self, svcs, q="", state_filter="All"):
        self.store.clear()
        for s in svcs:
            if q and q not in s["name"].lower() and q not in s["desc"].lower():
                continue
            if state_filter != "All" and s["active"] != state_filter:
                continue
            self.store.append([s["name"], s["load"], s["active"], s["sub"], s["desc"]])

    def on_filter(self, widget):
        q = self.filter_entry.get_text().lower()
        self.populate_store(self.all_services, q, self.state_filter)

    def on_selection_changed(self, selection):
        model, iter_ = selection.get_selected()
        if iter_:
            self.selected_service = model[iter_][0]

    def on_action(self, btn, action):
        if not self.selected_service:
            self.detail_view.get_buffer().set_text("Select a service first")
            return
        svc = self.selected_service + ".service"
        if action in ("start", "stop", "restart"):
            threading.Thread(target=self._run_action, args=(action, svc), daemon=True).start()
        elif action == "status":
            out, _ = run_cmd(["systemctl", "status", svc, "--no-pager", "-l"])
            self.detail_view.get_buffer().set_text(out)
        elif action == "logs":
            out, _ = run_cmd(["journalctl", "-u", svc, "-n", "50", "--no-pager"])
            self.detail_view.get_buffer().set_text(out)

    def _run_action(self, action, svc):
        out, rc = run_cmd(["systemctl", action, svc])
        GLib.idle_add(self.detail_view.get_buffer().set_text,
                      f"{action} {svc}: {'OK' if rc == 0 else 'FAILED'}\n{out}")
        GLib.idle_add(self.refresh_services)

class ServiceMonitorApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.ServiceMonitor")
    def do_activate(self):
        win = ServiceMonitorWindow(self); win.present()

def main():
    app = ServiceMonitorApp(); app.run(None)

if __name__ == "__main__":
    main()
