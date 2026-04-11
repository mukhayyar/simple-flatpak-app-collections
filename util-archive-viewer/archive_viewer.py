#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import zipfile, tarfile, os, threading

def fmt_size(n):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if abs(n) < 1024: return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"

class ArchiveViewerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Archive Viewer")
        self.set_default_size(900, 620)
        self.current_archive = None
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(6); vbox.set_margin_bottom(6)
        vbox.set_margin_start(6); vbox.set_margin_end(6)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Archive Viewer (ZIP/TAR)", css_classes=["title"]))

        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.path_entry = Gtk.Entry()
        self.path_entry.set_hexpand(True)
        self.path_entry.set_placeholder_text("Path to archive...")
        self.path_entry.connect("activate", lambda e: self.open_archive(e.get_text()))
        nav_box.append(self.path_entry)
        browse_btn = Gtk.Button(label="📂 Open Archive")
        browse_btn.connect("clicked", self.on_browse)
        nav_box.append(browse_btn)
        vbox.append(nav_box)

        self.info_label = Gtk.Label(label="Open a ZIP or TAR archive", xalign=0)
        vbox.append(self.info_label)

        hpaned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.append(hpaned)

        scroll = Gtk.ScrolledWindow(); scroll.set_size_request(420, -1); scroll.set_vexpand(True)
        self.store = Gtk.ListStore(str, str, str, str, str)
        tree = Gtk.TreeView(model=self.store)
        tree.get_selection().connect("changed", self.on_selection)

        for i, (title, width) in enumerate([("Name", 240), ("Size", 80), ("Compressed", 90), ("Date", 140), ("Type", 80)]):
            col = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i)
            col.set_resizable(True); col.set_fixed_width(width); col.set_sort_column_id(i)
            tree.append_column(col)

        scroll.set_child(tree)
        hpaned.set_start_child(scroll)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        right.set_margin_start(8)

        detail_frame = Gtk.Frame(label="File Preview")
        detail_scroll = Gtk.ScrolledWindow(); detail_scroll.set_vexpand(True)
        self.detail_view = Gtk.TextView()
        self.detail_view.set_editable(False); self.detail_view.set_monospace(True); self.detail_view.set_wrap_mode(Gtk.WrapMode.CHAR)
        detail_scroll.set_child(self.detail_view)
        detail_frame.set_child(detail_scroll)
        right.append(detail_frame)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        extract_sel_btn = Gtk.Button(label="Extract Selected")
        extract_sel_btn.connect("clicked", self.on_extract_selected)
        extract_all_btn = Gtk.Button(label="Extract All")
        extract_all_btn.connect("clicked", self.on_extract_all)
        btn_box.append(extract_sel_btn); btn_box.append(extract_all_btn)
        right.append(btn_box)

        create_frame = Gtk.Frame(label="Create Archive")
        create_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        create_box.set_margin_top(4); create_box.set_margin_start(4); create_box.set_margin_end(4); create_box.set_margin_bottom(4)
        self.create_path = Gtk.Entry(); self.create_path.set_placeholder_text("Folder to compress..."); self.create_path.set_hexpand(True)
        create_box.append(self.create_path)
        self.create_format = Gtk.ComboBoxText()
        for f in ["ZIP", "TAR.GZ", "TAR.BZ2"]:
            self.create_format.append_text(f)
        self.create_format.set_active(0)
        create_box.append(self.create_format)
        create_btn = Gtk.Button(label="Create")
        create_btn.connect("clicked", self.on_create)
        create_box.append(create_btn)
        create_frame.set_child(create_box)
        right.append(create_frame)

        hpaned.set_end_child(right)

        self.selected_member = None

    def on_browse(self, btn):
        dialog = Gtk.FileDialog()
        dialog.open(self, None, self.on_file_chosen)

    def on_file_chosen(self, dialog, result):
        try:
            f = dialog.open_finish(result)
            if f:
                path = f.get_path()
                self.path_entry.set_text(path)
                self.open_archive(path)
        except Exception:
            pass

    def open_archive(self, path):
        self.store.clear()
        self.current_archive = path
        threading.Thread(target=self._load_archive, args=(path,), daemon=True).start()

    def _load_archive(self, path):
        entries = []
        info_text = ""
        try:
            if path.endswith('.zip'):
                with zipfile.ZipFile(path) as zf:
                    members = zf.infolist()
                    for m in members:
                        date = f"{m.date_time[0]}-{m.date_time[1]:02d}-{m.date_time[2]:02d}"
                        ftype = "Dir" if m.filename.endswith('/') else "File"
                        comp = fmt_size(m.compress_size) if m.compress_size > 0 else "-"
                        entries.append([m.filename, fmt_size(m.file_size), comp, date, ftype])
                    total = sum(m.file_size for m in members)
                    comp_total = sum(m.compress_size for m in members)
                    ratio = (1 - comp_total/total)*100 if total > 0 else 0
                    info_text = f"ZIP Archive: {path}\n{len(members)} files | Total: {fmt_size(total)} | Compressed: {fmt_size(comp_total)} | Ratio: {ratio:.1f}%"
            elif path.endswith(('.tar.gz', '.tgz', '.tar.bz2', '.tar', '.tar.xz')):
                with tarfile.open(path) as tf:
                    members = tf.getmembers()
                    for m in members:
                        import datetime
                        date = datetime.datetime.fromtimestamp(m.mtime).strftime("%Y-%m-%d") if m.mtime else "-"
                        ftype = "Dir" if m.isdir() else "File"
                        entries.append([m.name, fmt_size(m.size), "-", date, ftype])
                    total = sum(m.size for m in members)
                    info_text = f"TAR Archive: {path}\n{len(members)} entries | Total: {fmt_size(total)}"
            else:
                info_text = f"Unsupported format: {os.path.basename(path)}"
        except Exception as e:
            info_text = f"Error: {e}"
        GLib.idle_add(self._show_entries, entries, info_text)

    def _show_entries(self, entries, info_text):
        self.store.clear()
        for e in entries:
            self.store.append(e)
        self.info_label.set_text(info_text)
        return False

    def on_selection(self, selection):
        model, iter_ = selection.get_selected()
        if not iter_:
            return
        name = model[iter_][0]
        self.selected_member = name
        path = self.current_archive
        if not path:
            return
        preview = ""
        try:
            if path.endswith('.zip'):
                with zipfile.ZipFile(path) as zf:
                    try:
                        data = zf.read(name)
                        text = data[:4096].decode('utf-8', errors='replace')
                        preview = text
                    except Exception:
                        preview = "(Binary file - cannot preview)"
            elif path.endswith(('.tar.gz', '.tgz', '.tar.bz2', '.tar', '.tar.xz')):
                with tarfile.open(path) as tf:
                    try:
                        m = tf.getmember(name)
                        if m.isfile():
                            f = tf.extractfile(m)
                            if f:
                                data = f.read(4096)
                                preview = data.decode('utf-8', errors='replace')
                        else:
                            preview = "(Directory)"
                    except Exception:
                        preview = "(Cannot preview)"
        except Exception as e:
            preview = f"Error: {e}"
        self.detail_view.get_buffer().set_text(preview)

    def on_extract_selected(self, btn):
        if not self.selected_member or not self.current_archive:
            return
        dialog = Gtk.FileDialog()
        dialog.select_folder(self, None, lambda d, r: self._do_extract_selected(d, r))

    def _do_extract_selected(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
            if folder:
                dest = folder.get_path()
                path = self.current_archive
                member = self.selected_member
                if path.endswith('.zip'):
                    with zipfile.ZipFile(path) as zf:
                        zf.extract(member, dest)
                elif path.endswith(('.tar.gz', '.tgz', '.tar.bz2', '.tar', '.tar.xz')):
                    with tarfile.open(path) as tf:
                        tf.extract(member, dest)
                self.info_label.set_text(f"Extracted to {dest}")
        except Exception as e:
            self.info_label.set_text(f"Error: {e}")

    def on_extract_all(self, btn):
        if not self.current_archive:
            return
        dialog = Gtk.FileDialog()
        dialog.select_folder(self, None, lambda d, r: self._do_extract_all(d, r))

    def _do_extract_all(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
            if folder:
                dest = folder.get_path()
                path = self.current_archive
                if path.endswith('.zip'):
                    with zipfile.ZipFile(path) as zf:
                        zf.extractall(dest)
                elif path.endswith(('.tar.gz', '.tgz', '.tar.bz2', '.tar', '.tar.xz')):
                    with tarfile.open(path) as tf:
                        tf.extractall(dest)
                self.info_label.set_text(f"Extracted all to {dest}")
        except Exception as e:
            self.info_label.set_text(f"Error: {e}")

    def on_create(self, btn):
        src = self.create_path.get_text().strip()
        if not src or not os.path.exists(src):
            self.info_label.set_text("Enter a valid path to compress")
            return
        fmt = self.create_format.get_active_text()
        dialog = Gtk.FileDialog()
        dialog.save(self, None, lambda d, r: self._do_create(d, r, src, fmt))

    def _do_create(self, dialog, result, src, fmt):
        try:
            f = dialog.save_finish(result)
            if f:
                dest = f.get_path()
                if fmt == "ZIP":
                    with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED) as zf:
                        if os.path.isdir(src):
                            for root, dirs, files in os.walk(src):
                                for file in files:
                                    fp = os.path.join(root, file)
                                    zf.write(fp, os.path.relpath(fp, os.path.dirname(src)))
                        else:
                            zf.write(src, os.path.basename(src))
                elif fmt == "TAR.GZ":
                    with tarfile.open(dest, 'w:gz') as tf:
                        tf.add(src, arcname=os.path.basename(src))
                elif fmt == "TAR.BZ2":
                    with tarfile.open(dest, 'w:bz2') as tf:
                        tf.add(src, arcname=os.path.basename(src))
                self.info_label.set_text(f"Created: {dest}")
                self.open_archive(dest)
        except Exception as e:
            self.info_label.set_text(f"Error: {e}")

class ArchiveViewerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.ArchiveViewer")
    def do_activate(self):
        win = ArchiveViewerWindow(self); win.present()

def main():
    app = ArchiveViewerApp(); app.run(None)

if __name__ == "__main__":
    main()
