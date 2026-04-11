#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk
import difflib

class DiffViewerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Diff Viewer")
        self.set_default_size(1000, 700)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        diff_btn = Gtk.Button(label="Compare")
        diff_btn.connect("clicked", self.on_diff)
        toolbar.append(diff_btn)
        self.status = Gtk.Label(label="Open two files or paste text, then click Compare")
        toolbar.append(self.status)
        vbox.append(toolbar)

        top_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        top_paned.set_size_request(-1, 280)

        left_frame = Gtk.Frame(label="File A")
        left_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        left_vbox.set_margin_top(4); left_vbox.set_margin_start(4)
        left_vbox.set_margin_bottom(4); left_vbox.set_margin_end(4)
        open_a = Gtk.Button(label="Open File A")
        open_a.connect("clicked", self.on_open_a)
        left_vbox.append(open_a)
        scroll_a = Gtk.ScrolledWindow()
        self.view_a = Gtk.TextView()
        self.view_a.set_monospace(True)
        self.buf_a = self.view_a.get_buffer()
        scroll_a.set_child(self.view_a)
        scroll_a.set_vexpand(True)
        left_vbox.append(scroll_a)
        left_frame.set_child(left_vbox)
        top_paned.set_start_child(left_frame)

        right_frame = Gtk.Frame(label="File B")
        right_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        right_vbox.set_margin_top(4); right_vbox.set_margin_start(4)
        right_vbox.set_margin_bottom(4); right_vbox.set_margin_end(4)
        open_b = Gtk.Button(label="Open File B")
        open_b.connect("clicked", self.on_open_b)
        right_vbox.append(open_b)
        scroll_b = Gtk.ScrolledWindow()
        self.view_b = Gtk.TextView()
        self.view_b.set_monospace(True)
        self.buf_b = self.view_b.get_buffer()
        scroll_b.set_child(self.view_b)
        scroll_b.set_vexpand(True)
        right_vbox.append(scroll_b)
        right_frame.set_child(right_vbox)
        top_paned.set_end_child(right_frame)
        vbox.append(top_paned)

        diff_frame = Gtk.Frame(label="Unified Diff")
        scroll_diff = Gtk.ScrolledWindow()
        scroll_diff.set_vexpand(True)
        self.diff_view = Gtk.TextView()
        self.diff_view.set_monospace(True)
        self.diff_view.set_editable(False)
        self.diff_buf = self.diff_view.get_buffer()
        tt = self.diff_buf.get_tag_table()
        for name, bg, fg in [("add", "#1e3a1e", "#a8d5a2"), ("del", "#3a1e1e", "#d5a2a2"), ("hunk", "#1e2a3a", "#a2b8d5")]:
            tag = Gtk.TextTag.new(name)
            tag.set_property("background", bg)
            tag.set_property("foreground", fg)
            tt.add(tag)
        scroll_diff.set_child(self.diff_view)
        diff_frame.set_child(scroll_diff)
        vbox.append(diff_frame)

    def on_open_a(self, btn):
        self._open_file(self.buf_a, "File A")

    def on_open_b(self, btn):
        self._open_file(self.buf_b, "File B")

    def _open_file(self, buf, name):
        dialog = Gtk.FileDialog()
        dialog.set_title(f"Open {name}")
        dialog.open(self, None, lambda d, r, b=buf: self._load_file(d, r, b))

    def _load_file(self, dialog, result, buf):
        try:
            f = dialog.open_finish(result)
            if f:
                with open(f.get_path(), "r", errors="replace") as fp:
                    buf.set_text(fp.read())
        except Exception:
            pass

    def on_diff(self, btn):
        text_a = self.buf_a.get_text(self.buf_a.get_start_iter(), self.buf_a.get_end_iter(), True)
        text_b = self.buf_b.get_text(self.buf_b.get_start_iter(), self.buf_b.get_end_iter(), True)
        lines_a = text_a.splitlines(keepends=True)
        lines_b = text_b.splitlines(keepends=True)
        diff = list(difflib.unified_diff(lines_a, lines_b, fromfile="File A", tofile="File B"))

        self.diff_buf.set_text("")
        added = deleted = 0
        for line in diff:
            end = self.diff_buf.get_end_iter()
            if line.startswith("+") and not line.startswith("+++"):
                self.diff_buf.insert_with_tags_by_name(end, line, "add")
                added += 1
            elif line.startswith("-") and not line.startswith("---"):
                self.diff_buf.insert_with_tags_by_name(end, line, "del")
                deleted += 1
            elif line.startswith("@@"):
                self.diff_buf.insert_with_tags_by_name(end, line, "hunk")
            else:
                self.diff_buf.insert(end, line)

        if not diff:
            self.diff_buf.set_text("Files are identical")
            self.status.set_text("No differences found")
        else:
            self.status.set_text(f"+{added} lines added, -{deleted} lines removed")

class DiffViewerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.DiffViewer")
    def do_activate(self):
        win = DiffViewerWindow(self)
        win.present()

def main():
    app = DiffViewerApp()
    app.run(None)

if __name__ == "__main__":
    main()
