#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import subprocess, os, threading

AUTOSTART_DIR = os.path.expanduser("~/.config/autostart")

def get_user_autostart():
    entries = []
    os.makedirs(AUTOSTART_DIR, exist_ok=True)
    for fname in os.listdir(AUTOSTART_DIR):
        if fname.endswith(".desktop"):
            path = os.path.join(AUTOSTART_DIR, fname)
            entry = parse_desktop(path)
            entry["file"] = fname
            entry["path"] = path
            entry["scope"] = "User"
            entries.append(entry)
    return entries

def get_system_autostart():
    entries = []
    for sdir in ["/etc/xdg/autostart"]:
        if not os.path.isdir(sdir):
            continue
        for fname in os.listdir(sdir):
            if fname.endswith(".desktop"):
                path = os.path.join(sdir, fname)
                entry = parse_desktop(path)
                entry["file"] = fname
                entry["path"] = path
                entry["scope"] = "System"
                entries.append(entry)
    return entries

def parse_desktop(path):
    entry = {"name": "", "exec": "", "comment": "", "enabled": True, "hidden": False}
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("Name="):
                    entry["name"] = line[5:]
                elif line.startswith("Exec="):
                    entry["exec"] = line[5:]
                elif line.startswith("Comment="):
                    entry["comment"] = line[8:]
                elif line.startswith("Hidden="):
                    entry["hidden"] = line[7:].lower() == "true"
                elif line.startswith("X-GNOME-Autostart-enabled="):
                    entry["enabled"] = line.split("=")[1].lower() == "true"
    except Exception:
        pass
    if not entry["name"]:
        entry["name"] = os.path.basename(path).replace(".desktop", "")
    return entry

def set_enabled(path, enabled):
    lines = []
    try:
        with open(path) as f:
            lines = f.readlines()
    except Exception:
        return
    new_lines = []
    found = False
    for line in lines:
        if line.startswith("X-GNOME-Autostart-enabled=") or line.startswith("Hidden="):
            found = True
            new_lines.append(f"X-GNOME-Autostart-enabled={'true' if enabled else 'false'}\n")
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"X-GNOME-Autostart-enabled={'true' if enabled else 'false'}\n")
    try:
        with open(path, "w") as f:
            f.writelines(new_lines)
    except Exception:
        pass

def get_systemd_services():
    svcs = []
    try:
        out = subprocess.check_output(["systemctl", "--user", "list-unit-files", "--type=service", "--no-pager"], text=True)
        for line in out.strip().split('\n')[1:]:
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0].replace(".service", "")
                state = parts[1]
                svcs.append({"name": name, "state": state})
    except Exception:
        pass
    return svcs[:30]

class StartupManagerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Startup Manager")
        self.set_default_size(900, 640)
        self.entries = []
        self.build_ui()
        self.refresh()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(6); vbox.set_margin_bottom(6)
        vbox.set_margin_start(6); vbox.set_margin_end(6)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Startup Manager", css_classes=["title"]))

        notebook = Gtk.Notebook()
        vbox.append(notebook)

        # Autostart tab
        autostart_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        autostart_page.set_margin_top(8); autostart_page.set_margin_start(8); autostart_page.set_margin_end(8); autostart_page.set_margin_bottom(8)

        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        self.store = Gtk.ListStore(str, str, str, str, bool, str)
        tree = Gtk.TreeView(model=self.store)

        toggle_renderer = Gtk.CellRendererToggle()
        toggle_renderer.connect("toggled", self.on_toggle)
        toggle_col = Gtk.TreeViewColumn("Enabled", toggle_renderer, active=4)
        tree.append_column(toggle_col)

        for i, (title, width) in enumerate([("Name", 180), ("Command", 220), ("Comment", 200), ("Scope", 70)]):
            col = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i)
            col.set_resizable(True); col.set_fixed_width(width)
            tree.append_column(col)

        tree.get_selection().connect("changed", self.on_selection)
        scroll.set_child(tree)
        autostart_page.append(scroll)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_halign(Gtk.Align.CENTER)
        add_btn = Gtk.Button(label="+ Add Entry")
        add_btn.connect("clicked", self.on_add)
        delete_btn = Gtk.Button(label="✗ Delete")
        delete_btn.connect("clicked", self.on_delete)
        refresh_btn = Gtk.Button(label="⟳ Refresh")
        refresh_btn.connect("clicked", lambda b: self.refresh())
        btn_box.append(add_btn); btn_box.append(delete_btn); btn_box.append(refresh_btn)
        autostart_page.append(btn_box)

        self.detail_label = Gtk.Label(label="Select an entry to see details", xalign=0)
        self.detail_label.set_wrap(True)
        autostart_page.append(self.detail_label)

        notebook.append_page(autostart_page, Gtk.Label(label="Autostart (.desktop)"))

        # Systemd user services tab
        svc_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        svc_page.set_margin_top(8); svc_page.set_margin_start(8); svc_page.set_margin_end(8); svc_page.set_margin_bottom(8)
        scroll2 = Gtk.ScrolledWindow(); scroll2.set_vexpand(True)
        self.svc_store = Gtk.ListStore(str, str)
        svc_tree = Gtk.TreeView(model=self.svc_store)
        for i, title in enumerate(["Service", "State"]):
            col = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i)
            col.set_resizable(True)
            svc_tree.append_column(col)
        scroll2.set_child(svc_tree)
        svc_page.append(scroll2)
        notebook.append_page(svc_page, Gtk.Label(label="Systemd User"))

        self.selected_path = None

    def refresh(self):
        self.store.clear()
        self.entries = get_user_autostart() + get_system_autostart()
        for e in self.entries:
            enabled = e.get("enabled", True) and not e.get("hidden", False)
            self.store.append([e["name"], e["exec"][:60], e["comment"][:60], e["scope"], enabled, e["path"]])

        self.svc_store.clear()
        for svc in get_systemd_services():
            self.svc_store.append([svc["name"], svc["state"]])

    def on_toggle(self, renderer, path):
        iter_ = self.store.get_iter(path)
        current = self.store[iter_][4]
        file_path = self.store[iter_][5]
        scope = self.store[iter_][3]
        if scope == "System":
            self.detail_label.set_text("Cannot modify system-wide entries. Copy to user autostart first.")
            return
        new_val = not current
        self.store[iter_][4] = new_val
        set_enabled(file_path, new_val)

    def on_selection(self, selection):
        model, iter_ = selection.get_selected()
        if iter_:
            path = model[iter_][5]
            self.selected_path = path
            e = next((en for en in self.entries if en["path"] == path), None)
            if e:
                self.detail_label.set_text(
                    f"Name: {e['name']}\nCommand: {e['exec']}\nComment: {e['comment']}\nFile: {path}"
                )

    def on_add(self, btn):
        dialog = Gtk.Dialog(title="Add Autostart Entry", transient_for=self)
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Add", Gtk.ResponseType.OK)
        content = dialog.get_content_area()
        grid = Gtk.Grid(); grid.set_row_spacing(6); grid.set_column_spacing(8)
        grid.set_margin_top(12); grid.set_margin_start(12); grid.set_margin_end(12); grid.set_margin_bottom(12)
        name_entry = Gtk.Entry(); name_entry.set_hexpand(True)
        exec_entry = Gtk.Entry(); exec_entry.set_hexpand(True)
        comment_entry = Gtk.Entry(); comment_entry.set_hexpand(True)
        grid.attach(Gtk.Label(label="Name:", xalign=1), 0, 0, 1, 1)
        grid.attach(name_entry, 1, 0, 1, 1)
        grid.attach(Gtk.Label(label="Command:", xalign=1), 0, 1, 1, 1)
        grid.attach(exec_entry, 1, 1, 1, 1)
        grid.attach(Gtk.Label(label="Comment:", xalign=1), 0, 2, 1, 1)
        grid.attach(comment_entry, 1, 2, 1, 1)
        content.append(grid)
        dialog.present()
        dialog.connect("response", lambda d, r: self._add_response(d, r, name_entry, exec_entry, comment_entry))

    def _add_response(self, dialog, response, name_e, exec_e, comment_e):
        if response == Gtk.ResponseType.OK:
            name = name_e.get_text().strip()
            exec_cmd = exec_e.get_text().strip()
            comment = comment_e.get_text().strip()
            if name and exec_cmd:
                fname = name.replace(" ", "-").lower() + ".desktop"
                path = os.path.join(AUTOSTART_DIR, fname)
                content = f"[Desktop Entry]\nType=Application\nName={name}\nExec={exec_cmd}\nComment={comment}\nX-GNOME-Autostart-enabled=true\n"
                with open(path, "w") as f:
                    f.write(content)
                self.refresh()
        dialog.destroy()

    def on_delete(self, btn):
        if not self.selected_path or not self.selected_path.startswith(AUTOSTART_DIR):
            self.detail_label.set_text("Select a user autostart entry to delete")
            return
        try:
            os.remove(self.selected_path)
            self.refresh()
        except Exception as e:
            self.detail_label.set_text(f"Error: {e}")

class StartupManagerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.StartupManager")
    def do_activate(self):
        win = StartupManagerWindow(self); win.present()

def main():
    app = StartupManagerApp(); app.run(None)

if __name__ == "__main__":
    main()
