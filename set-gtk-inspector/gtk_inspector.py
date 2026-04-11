#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk, GObject
import os, subprocess

def run_cmd(cmd, timeout=3):
    try:
        return subprocess.check_output(cmd, text=True, timeout=timeout, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""

class GtkInspectorWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("GTK Inspector / Runtime Info")
        self.set_default_size(800, 640)
        self.build_ui()

    def build_ui(self):
        notebook = Gtk.Notebook()
        self.set_child(notebook)

        notebook.append_page(self.build_runtime_page(), Gtk.Label(label="Runtime"))
        notebook.append_page(self.build_settings_page(), Gtk.Label(label="GTK Settings"))
        notebook.append_page(self.build_css_page(), Gtk.Label(label="CSS/Theme"))
        notebook.append_page(self.build_display_page(), Gtk.Label(label="Display"))
        notebook.append_page(self.build_widget_demo_page(), Gtk.Label(label="Widget Demo"))

    def build_runtime_page(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(12); vbox.set_margin_bottom(12)
        vbox.set_margin_start(16); vbox.set_margin_end(16)

        vbox.append(Gtk.Label(label="GTK Runtime Information", css_classes=["title"]))

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        grid = Gtk.Grid()
        grid.set_row_spacing(6); grid.set_column_spacing(20)

        gtk_maj = Gtk.get_major_version()
        gtk_min = Gtk.get_minor_version()
        gtk_mic = Gtk.get_micro_version()

        runtime_info = [
            ("GTK Version", f"{gtk_maj}.{gtk_min}.{gtk_mic}"),
            ("GLib Version", f"{GLib.MAJOR_VERSION}.{GLib.MINOR_VERSION}.{GLib.MICRO_VERSION}"),
            ("GObject Version", f"{GObject.MAJOR_VERSION}.{GObject.MINOR_VERSION}.{GObject.MICRO_VERSION}" if hasattr(GObject, 'MAJOR_VERSION') else "—"),
            ("Python GTK binding", "PyGObject"),
            ("Display backend", os.environ.get("XDG_SESSION_TYPE", "unknown")),
            ("Wayland display", os.environ.get("WAYLAND_DISPLAY", "not set")),
            ("X display", os.environ.get("DISPLAY", "not set")),
            ("GDK backend", os.environ.get("GDK_BACKEND", "auto")),
            ("GTK Debug", os.environ.get("GTK_DEBUG", "none")),
            ("GTK Theme (env)", os.environ.get("GTK_THEME", "—")),
            ("Data dir", GLib.get_system_data_dirs()[0] if GLib.get_system_data_dirs() else "—"),
            ("User data dir", GLib.get_user_data_dir()),
            ("User config dir", GLib.get_user_config_dir()),
            ("User cache dir", GLib.get_user_cache_dir()),
            ("User runtime dir", GLib.get_user_runtime_dir()),
            ("App name", GLib.get_application_name() or "—"),
            ("Host name", GLib.get_host_name()),
            ("OS", run_cmd(["uname", "-srm"])),
        ]

        for row, (key, val) in enumerate(runtime_info):
            lbl_key = Gtk.Label(label=f"{key}:", xalign=1)
            lbl_key.set_css_classes(["dim-label"])
            lbl_val = Gtk.Label(label=str(val), xalign=0)
            lbl_val.set_selectable(True)
            grid.attach(lbl_key, 0, row, 1, 1)
            grid.attach(lbl_val, 1, row, 1, 1)

        scroll.set_child(grid)
        vbox.append(scroll)
        return vbox

    def build_settings_page(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(12); vbox.set_margin_bottom(12)
        vbox.set_margin_start(16); vbox.set_margin_end(16)

        vbox.append(Gtk.Label(label="GTK Settings Properties", css_classes=["title"]))

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)

        store = Gtk.ListStore(str, str)
        settings = Gtk.Settings.get_default()

        gtk_props = [
            "gtk-theme-name", "gtk-icon-theme-name", "gtk-font-name",
            "gtk-cursor-theme-name", "gtk-cursor-theme-size",
            "gtk-application-prefer-dark-theme", "gtk-enable-animations",
            "gtk-button-images", "gtk-sound-theme-name",
            "gtk-xft-antialias", "gtk-xft-hinting", "gtk-xft-hintstyle",
            "gtk-xft-rgba", "gtk-xft-dpi",
            "gtk-double-click-time", "gtk-double-click-distance",
            "gtk-long-press-time", "gtk-key-theme-name",
            "gtk-im-module", "gtk-entry-password-hint-timeout",
        ]
        for prop in gtk_props:
            try:
                val = settings.get_property(prop)
                store.append([prop, str(val)])
            except Exception:
                pass

        tree = Gtk.TreeView(model=store)
        tree.set_headers_visible(True)
        for i, title in enumerate(["Property", "Value"]):
            r = Gtk.CellRendererText()
            if i == 0:
                r.set_property("family", "Monospace")
            col = Gtk.TreeViewColumn(title, r, text=i)
            col.set_resizable(True)
            col.set_fixed_width(280 if i == 0 else 300)
            col.set_sort_column_id(i)
            tree.append_column(col)
        scroll.set_child(tree)
        vbox.append(scroll)
        return vbox

    def build_css_page(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(12); vbox.set_margin_bottom(12)
        vbox.set_margin_start(16); vbox.set_margin_end(16)

        vbox.append(Gtk.Label(label="CSS / Theme Info", css_classes=["title"]))

        # Theme paths
        theme_info = []
        for base in ["/usr/share/themes", os.path.expanduser("~/.themes"),
                     os.path.expanduser("~/.local/share/themes")]:
            if os.path.isdir(base):
                for name in sorted(os.listdir(base)):
                    td = os.path.join(base, name)
                    gtk4_css = os.path.join(td, "gtk-4.0", "gtk.css")
                    if os.path.exists(gtk4_css):
                        theme_info.append(f"[GTK4] {name}  ({base})")

        theme_view = Gtk.TextView()
        theme_view.set_editable(False)
        theme_view.set_monospace(True)
        theme_view.get_buffer().set_text("\n".join(theme_info) if theme_info else "(No GTK4 themes found)")

        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(200)
        scroll.set_vexpand(True)
        scroll.set_child(theme_view)
        vbox.append(Gtk.Label(label="Installed GTK4 Themes:", xalign=0))
        vbox.append(scroll)

        # Custom CSS tester
        vbox.append(Gtk.Label(label="Custom CSS Test:", xalign=0))
        self.css_entry = Gtk.TextView()
        self.css_entry.set_monospace(True)
        self.css_entry.get_buffer().set_text("button { background: #2a6ebb; color: white; }")
        css_scroll = Gtk.ScrolledWindow()
        css_scroll.set_min_content_height(80)
        css_scroll.set_child(self.css_entry)
        vbox.append(css_scroll)

        test_btn = Gtk.Button(label="Apply CSS to this window")
        test_btn.connect("clicked", self.on_apply_css)
        vbox.append(test_btn)
        self.css_status = Gtk.Label(label="", xalign=0)
        vbox.append(self.css_status)
        return vbox

    def on_apply_css(self, btn):
        buf = self.css_entry.get_buffer()
        css_text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)
        try:
            provider = Gtk.CssProvider()
            provider.load_from_data(css_text.encode())
            self.get_display().get_style_context() if hasattr(self.get_display(), 'get_style_context') else None
            Gtk.StyleContext.add_provider_for_display(
                self.get_display(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            self.css_status.set_text("CSS applied successfully")
        except Exception as e:
            self.css_status.set_text(f"Error: {e}")

    def build_display_page(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(12); vbox.set_margin_bottom(12)
        vbox.set_margin_start(16); vbox.set_margin_end(16)

        vbox.append(Gtk.Label(label="Display & Screen Info", css_classes=["title"]))

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        grid = Gtk.Grid()
        grid.set_row_spacing(6); grid.set_column_spacing(20)

        display = self.get_display()
        row = 0
        try:
            monitors = display.get_monitors()
            for i in range(monitors.get_n_items()):
                mon = monitors.get_item(i)
                geo = mon.get_geometry()
                info_items = [
                    (f"Monitor {i+1} connector", mon.get_connector() or "—"),
                    (f"Monitor {i+1} resolution", f"{geo.width}×{geo.height}"),
                    (f"Monitor {i+1} position", f"({geo.x}, {geo.y})"),
                    (f"Monitor {i+1} scale", str(mon.get_scale_factor())),
                    (f"Monitor {i+1} refresh", f"{mon.get_refresh_rate()/1000:.1f} Hz" if mon.get_refresh_rate() else "—"),
                    (f"Monitor {i+1} manufacturer", mon.get_manufacturer() or "—"),
                    (f"Monitor {i+1} model", mon.get_model() or "—"),
                ]
                for key, val in info_items:
                    lbl_key = Gtk.Label(label=f"{key}:", xalign=1)
                    lbl_key.set_css_classes(["dim-label"])
                    lbl_val = Gtk.Label(label=val, xalign=0)
                    grid.attach(lbl_key, 0, row, 1, 1)
                    grid.attach(lbl_val, 1, row, 1, 1)
                    row += 1
        except Exception as e:
            lbl = Gtk.Label(label=f"Monitor info error: {e}")
            grid.attach(lbl, 0, row, 2, 1)

        scroll.set_child(grid)
        vbox.append(scroll)
        return vbox

    def build_widget_demo_page(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(12); vbox.set_margin_bottom(12)
        vbox.set_margin_start(16); vbox.set_margin_end(16)

        vbox.append(Gtk.Label(label="Widget Demo (current theme preview)", css_classes=["title"]))

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        inner.set_margin_top(8); inner.set_margin_start(8)

        inner.append(Gtk.Label(label="Buttons:"))
        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        for style, label in [("", "Regular"), ("suggested-action", "Suggested"), ("destructive-action", "Destructive")]:
            b = Gtk.Button(label=label)
            if style:
                b.add_css_class(style)
            btn_row.append(b)
        inner.append(btn_row)

        inner.append(Gtk.Label(label="Entry & Switch:"))
        row2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        e = Gtk.Entry(); e.set_placeholder_text("Text entry"); e.set_hexpand(True)
        row2.append(e)
        sw = Gtk.Switch(); sw.set_active(True)
        row2.append(sw)
        inner.append(row2)

        inner.append(Gtk.Label(label="Check & Radio:"))
        row3 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        for label in ["Option A", "Option B", "Option C"]:
            cb = Gtk.CheckButton(label=label)
            row3.append(cb)
        inner.append(row3)

        inner.append(Gtk.Label(label="Progress bars:"))
        for val in [0.25, 0.5, 0.75, 1.0]:
            pb = Gtk.ProgressBar()
            pb.set_fraction(val)
            pb.set_show_text(True)
            inner.append(pb)

        inner.append(Gtk.Label(label="Scale slider:"))
        sl = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        sl.set_value(60); sl.set_draw_value(True)
        inner.append(sl)

        scroll.set_child(inner)
        vbox.append(scroll)
        return vbox

class GtkInspectorApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.GtkInspector")
    def do_activate(self):
        win = GtkInspectorWindow(self); win.present()

def main():
    app = GtkInspectorApp(); app.run(None)

if __name__ == "__main__":
    main()
