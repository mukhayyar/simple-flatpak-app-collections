#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk
import subprocess, time

def set_gsettings(schema, key, value):
    try:
        subprocess.run(["gsettings", "set", schema, key, str(value)],
                       capture_output=True, timeout=3)
    except Exception:
        pass

def get_gsettings(schema, key):
    try:
        return subprocess.check_output(["gsettings", "get", schema, key],
                                        text=True, timeout=3).strip()
    except Exception:
        return ""

class ClickAssistWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Click Assist")
        self.set_default_size(680, 560)
        self.dwell_active = False
        self.dwell_time = 1.0
        self.click_count = 0
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(12); vbox.set_margin_bottom(12)
        vbox.set_margin_start(16); vbox.set_margin_end(16)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Click Assist", css_classes=["title"]))

        # Mouse keys
        mousekeys_frame = Gtk.Frame(label="Mouse Keys (keyboard-controlled mouse)")
        mk_grid = Gtk.Grid()
        mk_grid.set_row_spacing(8); mk_grid.set_column_spacing(12)
        mk_grid.set_margin_top(8); mk_grid.set_margin_start(12)
        mk_grid.set_margin_end(12); mk_grid.set_margin_bottom(8)

        cur_mk = get_gsettings("org.gnome.desktop.a11y.keyboard", "mousekeys-enable")
        mk_enabled = cur_mk.strip() == "true"
        self.mk_switch = Gtk.Switch()
        self.mk_switch.set_active(mk_enabled)
        self.mk_switch.connect("notify::active", self.on_mousekeys_toggle)
        mk_grid.attach(Gtk.Label(label="Enable Mouse Keys (numpad):", xalign=1), 0, 0, 1, 1)
        mk_grid.attach(self.mk_switch, 1, 0, 1, 1)

        mk_grid.attach(Gtk.Label(label="Max speed (px/s):", xalign=1), 0, 1, 1, 1)
        cur_speed = get_gsettings("org.gnome.desktop.a11y.keyboard", "mousekeys-max-speed")
        self.speed_spin = Gtk.SpinButton.new_with_range(10, 1000, 10)
        try:
            self.speed_spin.set_value(float(cur_speed))
        except ValueError:
            self.speed_spin.set_value(750)
        self.speed_spin.connect("value-changed", lambda s: set_gsettings(
            "org.gnome.desktop.a11y.keyboard", "mousekeys-max-speed", int(s.get_value())))
        mk_grid.attach(self.speed_spin, 1, 1, 1, 1)

        mk_grid.attach(Gtk.Label(label="Acceleration time (ms):", xalign=1), 0, 2, 1, 1)
        self.accel_spin = Gtk.SpinButton.new_with_range(10, 5000, 100)
        self.accel_spin.set_value(1200)
        self.accel_spin.connect("value-changed", lambda s: set_gsettings(
            "org.gnome.desktop.a11y.keyboard", "mousekeys-accel-time", int(s.get_value())))
        mk_grid.attach(self.accel_spin, 1, 2, 1, 1)
        mousekeys_frame.set_child(mk_grid)
        vbox.append(mousekeys_frame)

        # Dwell click
        dwell_frame = Gtk.Frame(label="Dwell Click (hover to click)")
        dw_grid = Gtk.Grid()
        dw_grid.set_row_spacing(8); dw_grid.set_column_spacing(12)
        dw_grid.set_margin_top(8); dw_grid.set_margin_start(12)
        dw_grid.set_margin_end(12); dw_grid.set_margin_bottom(8)

        cur_dwell = get_gsettings("org.gnome.desktop.a11y.mouse", "dwell-click-enabled")
        dw_enabled = cur_dwell.strip() == "true"
        self.dwell_switch = Gtk.Switch()
        self.dwell_switch.set_active(dw_enabled)
        self.dwell_switch.connect("notify::active", self.on_dwell_toggle)
        dw_grid.attach(Gtk.Label(label="Enable Dwell Click:", xalign=1), 0, 0, 1, 1)
        dw_grid.attach(self.dwell_switch, 1, 0, 1, 1)

        dw_grid.attach(Gtk.Label(label="Dwell time (s):", xalign=1), 0, 1, 1, 1)
        cur_dwell_t = get_gsettings("org.gnome.desktop.a11y.mouse", "dwell-time")
        self.dwell_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.2, 3.0, 0.1)
        try:
            self.dwell_scale.set_value(float(cur_dwell_t))
        except ValueError:
            self.dwell_scale.set_value(1.2)
        self.dwell_scale.set_hexpand(True)
        self.dwell_scale.set_draw_value(True)
        self.dwell_scale.connect("value-changed", lambda s: set_gsettings(
            "org.gnome.desktop.a11y.mouse", "dwell-time", s.get_value()))
        dw_grid.attach(self.dwell_scale, 1, 1, 1, 1)

        dw_grid.attach(Gtk.Label(label="Threshold (px):", xalign=1), 0, 2, 1, 1)
        self.threshold_spin = Gtk.SpinButton.new_with_range(1, 30, 1)
        self.threshold_spin.set_value(10)
        self.threshold_spin.connect("value-changed", lambda s: set_gsettings(
            "org.gnome.desktop.a11y.mouse", "dwell-threshold", int(s.get_value())))
        dw_grid.attach(self.threshold_spin, 1, 2, 1, 1)
        dwell_frame.set_child(dw_grid)
        vbox.append(dwell_frame)

        # Sticky keys
        sticky_frame = Gtk.Frame(label="Sticky Keys (hold modifier keys)")
        sk_grid = Gtk.Grid()
        sk_grid.set_row_spacing(8); sk_grid.set_column_spacing(12)
        sk_grid.set_margin_top(8); sk_grid.set_margin_start(12)
        sk_grid.set_margin_end(12); sk_grid.set_margin_bottom(8)

        cur_sk = get_gsettings("org.gnome.desktop.a11y.keyboard", "stickykeys-enable")
        sk_enabled = cur_sk.strip() == "true"
        self.sk_switch = Gtk.Switch()
        self.sk_switch.set_active(sk_enabled)
        self.sk_switch.connect("notify::active", lambda s, p: set_gsettings(
            "org.gnome.desktop.a11y.keyboard", "stickykeys-enable",
            str(s.get_active()).lower()))
        sk_grid.attach(Gtk.Label(label="Enable Sticky Keys:", xalign=1), 0, 0, 1, 1)
        sk_grid.attach(self.sk_switch, 1, 0, 1, 1)

        cur_bounce = get_gsettings("org.gnome.desktop.a11y.keyboard", "bouncekeys-enable")
        bk_enabled = cur_bounce.strip() == "true"
        self.bk_switch = Gtk.Switch()
        self.bk_switch.set_active(bk_enabled)
        self.bk_switch.connect("notify::active", lambda s, p: set_gsettings(
            "org.gnome.desktop.a11y.keyboard", "bouncekeys-enable",
            str(s.get_active()).lower()))
        sk_grid.attach(Gtk.Label(label="Enable Bounce Keys (ignore rapid repeats):", xalign=1), 0, 1, 1, 1)
        sk_grid.attach(self.bk_switch, 1, 1, 1, 1)

        cur_slow = get_gsettings("org.gnome.desktop.a11y.keyboard", "slowkeys-enable")
        slow_enabled = cur_slow.strip() == "true"
        self.slow_switch = Gtk.Switch()
        self.slow_switch.set_active(slow_enabled)
        self.slow_switch.connect("notify::active", lambda s, p: set_gsettings(
            "org.gnome.desktop.a11y.keyboard", "slowkeys-enable",
            str(s.get_active()).lower()))
        sk_grid.attach(Gtk.Label(label="Enable Slow Keys (delay before key accepted):", xalign=1), 0, 2, 1, 1)
        sk_grid.attach(self.slow_switch, 1, 2, 1, 1)
        sticky_frame.set_child(sk_grid)
        vbox.append(sticky_frame)

        # Click test area
        test_frame = Gtk.Frame(label="Click Test Area")
        test_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        test_box.set_margin_top(6); test_box.set_margin_start(8)
        test_box.set_margin_end(8); test_box.set_margin_bottom(6)
        self.click_counter_label = Gtk.Label(label="Clicks: 0")
        test_box.append(self.click_counter_label)

        target_btn = Gtk.Button(label="Click Target (large)")
        target_btn.set_size_request(200, 60)
        target_btn.set_halign(Gtk.Align.CENTER)
        target_btn.connect("clicked", self.on_target_click)
        test_box.append(target_btn)
        test_frame.set_child(test_box)
        vbox.append(test_frame)

        self.status_label = Gtk.Label(label="", xalign=0)
        vbox.append(self.status_label)

    def on_mousekeys_toggle(self, switch, param):
        val = str(switch.get_active()).lower()
        set_gsettings("org.gnome.desktop.a11y.keyboard", "mousekeys-enable", val)
        self.status_label.set_text(f"Mouse Keys: {'enabled' if switch.get_active() else 'disabled'}")

    def on_dwell_toggle(self, switch, param):
        val = str(switch.get_active()).lower()
        set_gsettings("org.gnome.desktop.a11y.mouse", "dwell-click-enabled", val)
        self.status_label.set_text(f"Dwell Click: {'enabled' if switch.get_active() else 'disabled'}")

    def on_target_click(self, btn):
        self.click_count += 1
        self.click_counter_label.set_text(f"Clicks: {self.click_count}")
        self.status_label.set_text(f"Clicked at {time.strftime('%H:%M:%S')}")

class ClickAssistApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.ClickAssist")
    def do_activate(self):
        win = ClickAssistWindow(self); win.present()

def main():
    app = ClickAssistApp(); app.run(None)

if __name__ == "__main__":
    main()
