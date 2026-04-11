#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gio
import subprocess, os

def get_gtk_settings():
    settings = Gtk.Settings.get_default()
    return {
        "theme": settings.get_property("gtk-theme-name"),
        "icon_theme": settings.get_property("gtk-icon-theme-name"),
        "font": settings.get_property("gtk-font-name"),
        "dark": settings.get_property("gtk-application-prefer-dark-theme"),
    }

def get_available_themes():
    themes = set()
    dirs = [
        "/usr/share/themes",
        os.path.expanduser("~/.themes"),
        os.path.expanduser("~/.local/share/themes"),
    ]
    for d in dirs:
        if os.path.isdir(d):
            for name in os.listdir(d):
                td = os.path.join(d, name)
                if os.path.isdir(td) and os.path.isdir(os.path.join(td, "gtk-4.0")):
                    themes.add(name)
    return sorted(themes) or ["Adwaita", "Adwaita-dark", "Default"]

def get_available_icon_themes():
    icons = set()
    dirs = [
        "/usr/share/icons",
        os.path.expanduser("~/.icons"),
        os.path.expanduser("~/.local/share/icons"),
    ]
    for d in dirs:
        if os.path.isdir(d):
            for name in os.listdir(d):
                if os.path.isdir(os.path.join(d, name)):
                    icons.add(name)
    return sorted(icons) or ["hicolor", "Adwaita"]

class ThemeSwitcherWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Theme Switcher")
        self.set_default_size(640, 560)
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_top(20); vbox.set_margin_bottom(20)
        vbox.set_margin_start(24); vbox.set_margin_end(24)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Theme Switcher", css_classes=["title"]))

        current = get_gtk_settings()

        dark_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        dark_box.set_halign(Gtk.Align.CENTER)
        dark_box.append(Gtk.Label(label="Prefer Dark Theme:"))
        self.dark_switch = Gtk.Switch()
        self.dark_switch.set_active(current["dark"])
        self.dark_switch.connect("notify::active", self.on_dark_toggled)
        dark_box.append(self.dark_switch)
        vbox.append(dark_box)

        theme_frame = Gtk.Frame(label="GTK Theme")
        theme_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        theme_vbox.set_margin_top(8); theme_vbox.set_margin_start(8); theme_vbox.set_margin_end(8); theme_vbox.set_margin_bottom(8)
        self.theme_combo = Gtk.ComboBoxText()
        themes = get_available_themes()
        for t in themes:
            self.theme_combo.append_text(t)
        cur_theme = current["theme"]
        if cur_theme in themes:
            self.theme_combo.set_active(themes.index(cur_theme))
        elif themes:
            self.theme_combo.set_active(0)
        self.theme_combo.connect("changed", self.on_theme_changed)
        theme_vbox.append(self.theme_combo)
        theme_frame.set_child(theme_vbox)
        vbox.append(theme_frame)

        icon_frame = Gtk.Frame(label="Icon Theme")
        icon_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        icon_vbox.set_margin_top(8); icon_vbox.set_margin_start(8); icon_vbox.set_margin_end(8); icon_vbox.set_margin_bottom(8)
        self.icon_combo = Gtk.ComboBoxText()
        icon_themes = get_available_icon_themes()
        for t in icon_themes:
            self.icon_combo.append_text(t)
        cur_icon = current["icon_theme"]
        if cur_icon in icon_themes:
            self.icon_combo.set_active(icon_themes.index(cur_icon))
        self.icon_combo.connect("changed", self.on_icon_changed)
        icon_vbox.append(self.icon_combo)
        icon_frame.set_child(icon_vbox)
        vbox.append(icon_frame)

        font_frame = Gtk.Frame(label="Font")
        font_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        font_vbox.set_margin_top(8); font_vbox.set_margin_start(8); font_vbox.set_margin_end(8); font_vbox.set_margin_bottom(8)
        font_btn = Gtk.FontDialogButton()
        font_dialog = Gtk.FontDialog()
        font_btn.set_dialog(font_dialog)
        font_vbox.append(font_btn)
        font_frame.set_child(font_vbox)
        vbox.append(font_frame)

        preview_frame = Gtk.Frame(label="Preview")
        preview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        preview_box.set_margin_top(8); preview_box.set_margin_start(8); preview_box.set_margin_end(8); preview_box.set_margin_bottom(8)
        preview_box.append(Gtk.Label(label="Sample text in current font and theme"))
        sample_btn = Gtk.Button(label="Sample Button")
        preview_box.append(sample_btn)
        sample_entry = Gtk.Entry(); sample_entry.set_text("Sample entry field")
        preview_box.append(sample_entry)
        sample_check = Gtk.CheckButton(label="Sample checkbox")
        preview_box.append(sample_check)
        preview_frame.set_child(preview_box)
        vbox.append(preview_frame)

        self.status_label = Gtk.Label(label=f"Current: {current['theme']} | Dark: {current['dark']}", xalign=0)
        vbox.append(self.status_label)

        gsettings_btn = Gtk.Button(label="Apply via GSettings (GNOME)")
        gsettings_btn.connect("clicked", self.on_gsettings)
        vbox.append(gsettings_btn)

    def on_dark_toggled(self, switch, param):
        val = switch.get_active()
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", val)
        self.status_label.set_text(f"Dark mode: {'on' if val else 'off'}")

    def on_theme_changed(self, combo):
        theme = combo.get_active_text()
        if theme:
            settings = Gtk.Settings.get_default()
            settings.set_property("gtk-theme-name", theme)
            self.status_label.set_text(f"Theme changed to: {theme}")

    def on_icon_changed(self, combo):
        icon_theme = combo.get_active_text()
        if icon_theme:
            settings = Gtk.Settings.get_default()
            settings.set_property("gtk-icon-theme-name", icon_theme)
            self.status_label.set_text(f"Icon theme: {icon_theme}")

    def on_gsettings(self, btn):
        theme = self.theme_combo.get_active_text()
        dark = self.dark_switch.get_active()
        icon = self.icon_combo.get_active_text()
        cmds = []
        if theme:
            cmds.append(["gsettings", "set", "org.gnome.desktop.interface", "gtk-theme", theme])
        if icon:
            cmds.append(["gsettings", "set", "org.gnome.desktop.interface", "icon-theme", icon])
        color_scheme = "prefer-dark" if dark else "default"
        cmds.append(["gsettings", "set", "org.gnome.desktop.interface", "color-scheme", color_scheme])
        results = []
        for cmd in cmds:
            try:
                r = subprocess.run(cmd, capture_output=True, text=True)
                results.append("OK" if r.returncode == 0 else r.stderr.strip())
            except Exception as e:
                results.append(str(e))
        self.status_label.set_text("GSettings: " + " | ".join(results))

class ThemeSwitcherApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.ThemeSwitcher")
    def do_activate(self):
        win = ThemeSwitcherWindow(self); win.present()

def main():
    app = ThemeSwitcherApp(); app.run(None)

if __name__ == "__main__":
    main()
