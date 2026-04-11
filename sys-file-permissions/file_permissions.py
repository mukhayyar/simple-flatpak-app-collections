#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import os, stat, pwd, grp, threading

def get_perm_string(mode):
    perms = ""
    for who in [(stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR),
                (stat.S_IRGRP, stat.S_IWGRP, stat.S_IXGRP),
                (stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH)]:
        for bit, ch in zip(who, "rwx"):
            perms += ch if mode & bit else "-"
    return perms

def get_file_info(path):
    try:
        s = os.stat(path)
        mode = s.st_mode
        perm_str = get_perm_string(mode)
        octal = oct(stat.S_IMODE(mode))
        try:
            owner = pwd.getpwuid(s.st_uid).pw_name
        except Exception:
            owner = str(s.st_uid)
        try:
            group = grp.getgrgid(s.st_gid).gr_name
        except Exception:
            group = str(s.st_gid)
        ftype = "Directory" if stat.S_ISDIR(mode) else ("Symlink" if stat.S_ISLNK(mode) else "File")
        import datetime
        mtime = datetime.datetime.fromtimestamp(s.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        return {
            "path": path, "mode": mode, "perm_str": perm_str, "octal": octal,
            "owner": owner, "group": group, "size": s.st_size, "type": ftype,
            "mtime": mtime, "uid": s.st_uid, "gid": s.st_gid,
        }
    except Exception as e:
        return {"error": str(e)}

class FilePermissionsWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("File Permissions Manager")
        self.set_default_size(900, 640)
        self.current_path = os.path.expanduser("~")
        self.file_info = None
        self.build_ui()
        self.load_directory(self.current_path)

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(6); vbox.set_margin_bottom(6)
        vbox.set_margin_start(6); vbox.set_margin_end(6)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="File Permissions Manager", css_classes=["title"]))

        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.path_entry = Gtk.Entry()
        self.path_entry.set_text(self.current_path)
        self.path_entry.set_hexpand(True)
        self.path_entry.connect("activate", self.on_path_go)
        nav_box.append(self.path_entry)
        go_btn = Gtk.Button(label="Go")
        go_btn.connect("clicked", self.on_path_go)
        up_btn = Gtk.Button(label="⬆ Up")
        up_btn.connect("clicked", self.on_up)
        browse_btn = Gtk.Button(label="📂 Browse")
        browse_btn.connect("clicked", self.on_browse)
        nav_box.append(go_btn); nav_box.append(up_btn); nav_box.append(browse_btn)
        vbox.append(nav_box)

        hpaned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.append(hpaned)

        scroll = Gtk.ScrolledWindow(); scroll.set_size_request(450, -1); scroll.set_vexpand(True)
        self.store = Gtk.ListStore(str, str, str, str, str, str)
        tree = Gtk.TreeView(model=self.store)
        tree.get_selection().connect("changed", self.on_selection)

        for i, (title, width) in enumerate([("Name", 200), ("Type", 70), ("Permissions", 100), ("Owner", 90), ("Group", 90), ("Size", 80)]):
            col = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i)
            col.set_resizable(True); col.set_fixed_width(width)
            col.set_sort_column_id(i)
            tree.append_column(col)
        scroll.set_child(tree)
        hpaned.set_start_child(scroll)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        right.set_margin_start(8); right.set_margin_top(4)

        info_frame = Gtk.Frame(label="File Info")
        self.info_view = Gtk.TextView()
        self.info_view.set_editable(False); self.info_view.set_monospace(True)
        info_frame.set_child(self.info_view)
        right.append(info_frame)

        perm_frame = Gtk.Frame(label="Change Permissions")
        perm_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        perm_vbox.set_margin_top(6); perm_vbox.set_margin_start(6); perm_vbox.set_margin_end(6); perm_vbox.set_margin_bottom(6)

        self.perm_checks = {}
        grid = Gtk.Grid(); grid.set_row_spacing(4); grid.set_column_spacing(12)
        headers = ["Read", "Write", "Execute"]
        who_labels = ["Owner", "Group", "Others"]
        for col_idx, hdr in enumerate(headers):
            grid.attach(Gtk.Label(label=hdr), col_idx + 1, 0, 1, 1)
        for row_idx, who in enumerate(who_labels):
            grid.attach(Gtk.Label(label=who, xalign=1), 0, row_idx + 1, 1, 1)
            for col_idx, perm in enumerate(["r", "w", "x"]):
                key = f"{who[0].lower()}{perm}"
                cb = Gtk.CheckButton()
                self.perm_checks[key] = cb
                grid.attach(cb, col_idx + 1, row_idx + 1, 1, 1)

        perm_vbox.append(grid)

        octal_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        octal_box.append(Gtk.Label(label="Octal:"))
        self.octal_entry = Gtk.Entry(); self.octal_entry.set_text("644")
        self.octal_entry.set_size_request(80, -1)
        octal_box.append(self.octal_entry)
        apply_btn = Gtk.Button(label="Apply")
        apply_btn.connect("clicked", self.on_apply)
        octal_box.append(apply_btn)
        perm_vbox.append(octal_box)

        perm_frame.set_child(perm_vbox)
        right.append(perm_frame)

        self.status_label = Gtk.Label(label="", xalign=0)
        right.append(self.status_label)
        hpaned.set_end_child(right)

    def load_directory(self, path):
        self.current_path = path
        self.path_entry.set_text(path)
        self.store.clear()
        try:
            entries = sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name.lower()))
        except Exception as e:
            self.status_label.set_text(f"Error: {e}")
            return
        for entry in entries:
            try:
                info = get_file_info(entry.path)
                if "error" in info:
                    continue
                size_str = f"{info['size']:,}" if info["type"] == "File" else ""
                self.store.append([entry.name, info["type"], info["perm_str"] + " " + info["octal"],
                                   info["owner"], info["group"], size_str])
            except Exception:
                pass

    def on_selection(self, selection):
        model, iter_ = selection.get_selected()
        if not iter_:
            return
        name = model[iter_][0]
        full_path = os.path.join(self.current_path, name)
        info = get_file_info(full_path)
        self.file_info = info
        if "error" in info:
            self.info_view.get_buffer().set_text(f"Error: {info['error']}")
            return
        text = "\n".join([
            f"Path:    {info['path']}",
            f"Type:    {info['type']}",
            f"Perms:   {info['perm_str']} ({info['octal']})",
            f"Owner:   {info['owner']} (uid={info['uid']})",
            f"Group:   {info['group']} (gid={info['gid']})",
            f"Size:    {info['size']:,} bytes",
            f"Modified: {info['mtime']}",
        ])
        self.info_view.get_buffer().set_text(text)
        self.octal_entry.set_text(info["octal"][2:])
        mode = info["mode"]
        for key, cb in self.perm_checks.items():
            who, perm = key[0], key[1]
            bit_map = {
                ("o", "r"): stat.S_IRUSR, ("o", "w"): stat.S_IWUSR, ("o", "x"): stat.S_IXUSR,
                ("g", "r"): stat.S_IRGRP, ("g", "w"): stat.S_IWGRP, ("g", "x"): stat.S_IXGRP,
                ("o2", "r"): stat.S_IROTH, ("o2", "w"): stat.S_IWOTH, ("o2", "x"): stat.S_IXOTH,
            }
            bit = {"o": {"r": stat.S_IRUSR, "w": stat.S_IWUSR, "x": stat.S_IXUSR},
                   "g": {"r": stat.S_IRGRP, "w": stat.S_IWGRP, "x": stat.S_IXGRP},
                   "o2": {"r": stat.S_IROTH, "w": stat.S_IWOTH, "x": stat.S_IXOTH}}.get(who if who != "o" else "o", {}).get(perm)
            if who == "o" and perm in "rwx":
                bit = {"r": stat.S_IRUSR, "w": stat.S_IWUSR, "x": stat.S_IXUSR}[perm]
            elif who == "g":
                bit = {"r": stat.S_IRGRP, "w": stat.S_IWGRP, "x": stat.S_IXGRP}[perm]
            else:
                bit = {"r": stat.S_IROTH, "w": stat.S_IWOTH, "x": stat.S_IXOTH}[perm]
            cb.set_active(bool(mode & bit))

        if info["type"] == "Directory":
            full_path_dir = full_path
            self.current_path = full_path_dir

    def on_apply(self, btn):
        if not self.file_info or "error" in self.file_info:
            return
        try:
            octal_str = self.octal_entry.get_text().strip()
            mode = int(octal_str, 8)
            os.chmod(self.file_info["path"], mode)
            self.status_label.set_text(f"Applied {octal_str} to {self.file_info['path']}")
            self.load_directory(self.current_path)
        except Exception as e:
            self.status_label.set_text(f"Error: {e}")

    def on_path_go(self, widget):
        path = self.path_entry.get_text()
        if os.path.isdir(path):
            self.load_directory(path)

    def on_up(self, btn):
        parent = os.path.dirname(self.current_path)
        if parent != self.current_path:
            self.load_directory(parent)

    def on_browse(self, btn):
        dialog = Gtk.FileDialog()
        dialog.select_folder(self, None, self.on_folder)

    def on_folder(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
            if folder:
                self.load_directory(folder.get_path())
        except Exception:
            pass

class FilePermissionsApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.FilePermissions")
    def do_activate(self):
        win = FilePermissionsWindow(self); win.present()

def main():
    app = FilePermissionsApp(); app.run(None)

if __name__ == "__main__":
    main()
