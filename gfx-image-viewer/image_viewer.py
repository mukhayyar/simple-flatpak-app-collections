#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GdkPixbuf
import os

class ImageViewerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Image Viewer")
        self.set_default_size(900, 700)
        self.pixbuf = None
        self.zoom = 1.0
        self.angle = 0
        self.current_file = None
        self.folder_files = []
        self.folder_idx = 0
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(vbox)

        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        toolbar.set_margin_top(4); toolbar.set_margin_bottom(4)
        toolbar.set_margin_start(6); toolbar.set_margin_end(6)

        open_btn = Gtk.Button(label="Open")
        open_btn.connect("clicked", self.on_open)
        toolbar.append(open_btn)
        prev_btn = Gtk.Button(label="← Prev")
        prev_btn.connect("clicked", self.on_prev)
        toolbar.append(prev_btn)
        next_btn = Gtk.Button(label="Next →")
        next_btn.connect("clicked", self.on_next)
        toolbar.append(next_btn)

        for label, func in [("Zoom In", self.zoom_in), ("Zoom Out", self.zoom_out),
                             ("Fit", self.zoom_fit), ("1:1", self.zoom_actual)]:
            btn = Gtk.Button(label=label)
            btn.connect("clicked", func)
            toolbar.append(btn)

        rot_btn = Gtk.Button(label="Rotate 90°")
        rot_btn.connect("clicked", self.on_rotate)
        toolbar.append(rot_btn)

        flip_btn = Gtk.Button(label="Flip H")
        flip_btn.connect("clicked", self.on_flip)
        toolbar.append(flip_btn)

        full_btn = Gtk.Button(label="Fullscreen")
        full_btn.connect("clicked", self.on_fullscreen)
        toolbar.append(full_btn)

        self.info_label = Gtk.Label(label="Open an image file")
        self.info_label.set_hexpand(True)
        toolbar.append(self.info_label)
        vbox.append(toolbar)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        self.picture = Gtk.Picture()
        self.picture.set_can_shrink(True)
        self.picture.set_hexpand(True)
        self.picture.set_vexpand(True)
        scroll.set_child(self.picture)
        vbox.append(scroll)

        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self.on_key)
        self.add_controller(key_ctrl)

    def on_open(self, btn):
        dialog = Gtk.FileDialog()
        dialog.set_title("Open Image")
        dialog.open(self, None, self.on_file_chosen)

    def on_file_chosen(self, dialog, result):
        try:
            f = dialog.open_finish(result)
            if f:
                self.load_file(f.get_path())
        except Exception:
            pass

    def load_file(self, path):
        try:
            self.pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
            self.current_file = path
            folder = os.path.dirname(path)
            exts = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff"}
            self.folder_files = sorted([
                os.path.join(folder, f) for f in os.listdir(folder)
                if os.path.splitext(f)[1].lower() in exts
            ])
            self.folder_idx = self.folder_files.index(path) if path in self.folder_files else 0
            self.angle = 0
            self.apply_transform()
            name = os.path.basename(path)
            w, h = self.pixbuf.get_width(), self.pixbuf.get_height()
            self.set_title(f"Image Viewer — {name}")
            self.info_label.set_text(f"{name} | {w}×{h} | {os.path.getsize(path)//1024}KB | Zoom: {self.zoom:.0%}")
        except Exception as e:
            self.info_label.set_text(f"Error: {e}")

    def apply_transform(self):
        if not self.pixbuf: return
        pb = self.pixbuf
        for _ in range(self.angle // 90):
            pb = pb.rotate_simple(GdkPixbuf.PixbufRotation.CLOCKWISE)
        w = int(pb.get_width() * self.zoom)
        h = int(pb.get_height() * self.zoom)
        if w > 0 and h > 0:
            scaled = pb.scale_simple(w, h, GdkPixbuf.InterpType.BILINEAR)
            self.picture.set_pixbuf(scaled)

    def zoom_in(self, *a): self.zoom = min(5.0, self.zoom * 1.25); self.apply_transform()
    def zoom_out(self, *a): self.zoom = max(0.1, self.zoom / 1.25); self.apply_transform()
    def zoom_fit(self, *a): self.zoom = 1.0; self.apply_transform()
    def zoom_actual(self, *a): self.zoom = 1.0; self.picture.set_can_shrink(False); self.apply_transform()

    def on_rotate(self, *a):
        self.angle = (self.angle + 90) % 360
        self.apply_transform()

    def on_flip(self, *a):
        if self.pixbuf:
            self.pixbuf = self.pixbuf.flip(True)
            self.apply_transform()

    def on_fullscreen(self, *a):
        if self.is_fullscreen():
            self.unfullscreen()
        else:
            self.fullscreen()

    def on_prev(self, *a):
        if self.folder_files and self.folder_idx > 0:
            self.folder_idx -= 1
            self.load_file(self.folder_files[self.folder_idx])

    def on_next(self, *a):
        if self.folder_files and self.folder_idx < len(self.folder_files) - 1:
            self.folder_idx += 1
            self.load_file(self.folder_files[self.folder_idx])

    def on_key(self, ctrl, keyval, keycode, state):
        if keyval == Gdk.KEY_Left: self.on_prev(None)
        elif keyval == Gdk.KEY_Right: self.on_next(None)
        elif keyval == Gdk.KEY_plus or keyval == Gdk.KEY_equal: self.zoom_in()
        elif keyval == Gdk.KEY_minus: self.zoom_out()
        elif keyval == Gdk.KEY_f: self.on_fullscreen()
        return True

class ImageViewerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.ImageViewer")
    def do_activate(self):
        win = ImageViewerWindow(self)
        win.present()

def main():
    app = ImageViewerApp()
    app.run(None)

if __name__ == "__main__":
    main()
