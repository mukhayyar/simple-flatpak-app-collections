#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk
import subprocess, os

class DisplayInfoWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Display Info")
        self.set_default_size(700, 580)
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(12); vbox.set_margin_bottom(12)
        vbox.set_margin_start(16); vbox.set_margin_end(16)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Display Info", css_classes=["title"]))

        display = self.get_display()
        info = []

        monitors = []
        try:
            monitors_list = display.get_monitors()
            for i in range(monitors_list.get_n_items()):
                mon = monitors_list.get_item(i)
                monitors.append(mon)
        except Exception:
            pass

        for i, mon in enumerate(monitors):
            geo = mon.get_geometry()
            scale = mon.get_scale_factor()
            refresh = mon.get_refresh_rate() / 1000 if mon.get_refresh_rate() else 0
            connector = mon.get_connector() or f"Monitor {i+1}"
            manufacturer = mon.get_manufacturer() or "Unknown"
            model = mon.get_model() or "Unknown"
            info.append(f"Monitor {i+1}: {connector}")
            info.append(f"  Make/Model: {manufacturer} {model}")
            info.append(f"  Resolution: {geo.width}×{geo.height}")
            info.append(f"  Position: ({geo.x}, {geo.y})")
            info.append(f"  Scale: {scale}x")
            if refresh:
                info.append(f"  Refresh: {refresh:.1f} Hz")
            info.append("")

        # Try xrandr for more details
        try:
            xrandr = subprocess.check_output(["xrandr", "--query"], text=True, timeout=3)
            info.append("xrandr output:")
            info.extend(xrandr.strip().split('\n'))
        except Exception:
            pass

        try:
            wmctrl = subprocess.check_output(["wmctrl", "-d"], text=True, timeout=3)
            info.append("\nVirtual desktops:")
            info.extend(wmctrl.strip().split('\n'))
        except Exception:
            pass

        monitor_frame = Gtk.Frame(label="Monitors")
        scroll = Gtk.ScrolledWindow(); scroll.set_min_content_height(200)
        info_view = Gtk.TextView()
        info_view.set_editable(False); info_view.set_monospace(True)
        info_view.get_buffer().set_text("\n".join(info))
        scroll.set_child(info_view)
        monitor_frame.set_child(scroll)
        vbox.append(monitor_frame)

        brightness_frame = Gtk.Frame(label="Brightness (estimated)")
        b_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        b_box.set_margin_top(6); b_box.set_margin_start(8); b_box.set_margin_end(8); b_box.set_margin_bottom(6)
        b_box.append(Gtk.Label(label="Brightness:"))
        brightness_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        brightness_scale.set_value(100)
        brightness_scale.set_hexpand(True)
        brightness_scale.connect("value-changed", self.on_brightness)
        b_box.append(brightness_scale)
        brightness_frame.set_child(b_box)
        vbox.append(brightness_frame)

        gamma_frame = Gtk.Frame(label="Gamma Correction (xrandr)")
        g_grid = Gtk.Grid(); g_grid.set_row_spacing(6); g_grid.set_column_spacing(8)
        g_grid.set_margin_top(6); g_grid.set_margin_start(8); g_grid.set_margin_end(8); g_grid.set_margin_bottom(6)

        self.gamma_scales = {}
        for row, (channel, default) in enumerate([("Red", 1.0), ("Green", 1.0), ("Blue", 1.0)]):
            g_grid.attach(Gtk.Label(label=f"{channel}:", xalign=1), 0, row, 1, 1)
            scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.1, 3.0, 0.05)
            scale.set_value(default); scale.set_hexpand(True); scale.set_draw_value(True)
            scale.connect("value-changed", self.on_gamma_changed)
            g_grid.attach(scale, 1, row, 1, 1)
            self.gamma_scales[channel] = scale
        gamma_frame.set_child(g_grid)
        vbox.append(gamma_frame)

        reset_btn = Gtk.Button(label="Reset Gamma to 1.0:1.0:1.0")
        reset_btn.set_halign(Gtk.Align.CENTER)
        reset_btn.connect("clicked", self.on_reset_gamma)
        vbox.append(reset_btn)

        self.status_label = Gtk.Label(label="", xalign=0)
        vbox.append(self.status_label)

    def on_brightness(self, scale):
        val = scale.get_value() / 100.0
        try:
            result = subprocess.run(["xrandr", "--output", "eDP-1", "--brightness", str(val)],
                                    capture_output=True, text=True)
            if result.returncode != 0:
                result = subprocess.run(["xrandr", "--output", "HDMI-1", "--brightness", str(val)],
                                        capture_output=True, text=True)
            self.status_label.set_text(f"Brightness: {val:.2f}")
        except Exception as e:
            self.status_label.set_text(f"Note: xrandr not available ({e})")

    def on_gamma_changed(self, scale):
        r = self.gamma_scales["Red"].get_value()
        g = self.gamma_scales["Green"].get_value()
        b = self.gamma_scales["Blue"].get_value()
        gamma_str = f"{r:.2f}:{g:.2f}:{b:.2f}"
        try:
            subprocess.run(["xrandr", "--output", "eDP-1", "--gamma", gamma_str],
                           capture_output=True, text=True, timeout=2)
            self.status_label.set_text(f"Gamma: {gamma_str}")
        except Exception as e:
            self.status_label.set_text(f"Gamma: {gamma_str} (xrandr unavailable)")

    def on_reset_gamma(self, btn):
        for scale in self.gamma_scales.values():
            scale.set_value(1.0)

class DisplayInfoApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.DisplayInfo")
    def do_activate(self):
        win = DisplayInfoWindow(self); win.present()

def main():
    app = DisplayInfoApp(); app.run(None)

if __name__ == "__main__":
    main()
