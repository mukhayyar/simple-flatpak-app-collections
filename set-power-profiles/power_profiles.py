#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import subprocess, os

def run_cmd(cmd, timeout=5):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.returncode
    except Exception as e:
        return str(e), -1

def read_file(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except Exception:
        return ""

class PowerProfilesWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Power Profiles")
        self.set_default_size(680, 560)
        self.build_ui()
        GLib.timeout_add(3000, self.refresh_status)

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(12); vbox.set_margin_bottom(12)
        vbox.set_margin_start(16); vbox.set_margin_end(16)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Power Profiles", css_classes=["title"]))

        # Power-profiles-daemon
        ppd_frame = Gtk.Frame(label="Power Profile (power-profiles-daemon)")
        ppd_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        ppd_box.set_margin_top(8); ppd_box.set_margin_start(12)
        ppd_box.set_margin_end(12); ppd_box.set_margin_bottom(8)

        self.ppd_status = Gtk.Label(label="Checking...", xalign=0)
        ppd_box.append(self.ppd_status)

        profile_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        profile_box.set_halign(Gtk.Align.CENTER)
        self.profile_buttons = {}
        for profile in ["power-saver", "balanced", "performance"]:
            btn = Gtk.ToggleButton(label=profile.replace("-", " ").title())
            btn.connect("toggled", self.on_profile_toggled, profile)
            profile_box.append(btn)
            self.profile_buttons[profile] = btn
        ppd_box.append(profile_box)

        ppd_frame.set_child(ppd_box)
        vbox.append(ppd_frame)

        # Battery info
        bat_frame = Gtk.Frame(label="Battery Status")
        bat_grid = Gtk.Grid()
        bat_grid.set_row_spacing(6); bat_grid.set_column_spacing(16)
        bat_grid.set_margin_top(8); bat_grid.set_margin_start(12)
        bat_grid.set_margin_end(12); bat_grid.set_margin_bottom(8)

        self.bat_labels = {}
        bat_keys = [
            ("capacity", "Battery level"),
            ("status", "Status"),
            ("energy_now", "Energy now"),
            ("energy_full", "Energy full"),
            ("power_now", "Power draw"),
            ("technology", "Technology"),
            ("cycle_count", "Cycles"),
            ("manufacturer", "Manufacturer"),
            ("model_name", "Model"),
        ]
        for row, (key, label) in enumerate(bat_keys):
            lbl_key = Gtk.Label(label=f"{label}:", xalign=1)
            lbl_key.set_css_classes(["dim-label"])
            lbl_val = Gtk.Label(label="—", xalign=0)
            bat_grid.attach(lbl_key, 0, row, 1, 1)
            bat_grid.attach(lbl_val, 1, row, 1, 1)
            self.bat_labels[key] = lbl_val
        bat_frame.set_child(bat_grid)
        vbox.append(bat_frame)

        # CPU frequency scaling
        cpu_frame = Gtk.Frame(label="CPU Frequency Scaling")
        cpu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        cpu_box.set_margin_top(8); cpu_box.set_margin_start(12)
        cpu_box.set_margin_end(12); cpu_box.set_margin_bottom(8)

        gov_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        gov_box.append(Gtk.Label(label="CPU Governor:"))
        self.gov_label = Gtk.Label(label="—")
        gov_box.append(self.gov_label)

        self.gov_combo = Gtk.ComboBoxText()
        for gov in ["powersave", "conservative", "ondemand", "schedutil", "performance"]:
            self.gov_combo.append_text(gov)
        gov_box.append(self.gov_combo)

        set_gov_btn = Gtk.Button(label="Set (requires pkexec)")
        set_gov_btn.connect("clicked", self.on_set_governor)
        gov_box.append(set_gov_btn)
        cpu_box.append(gov_box)

        self.cpu_freq_label = Gtk.Label(label="", xalign=0)
        cpu_box.append(self.cpu_freq_label)
        cpu_frame.set_child(cpu_box)
        vbox.append(cpu_frame)

        # AC adapter
        ac_frame = Gtk.Frame(label="AC Adapter")
        ac_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        ac_box.set_margin_top(8); ac_box.set_margin_start(12)
        ac_box.set_margin_end(12); ac_box.set_margin_bottom(8)
        self.ac_label = Gtk.Label(label="—")
        ac_box.append(self.ac_label)
        ac_frame.set_child(ac_box)
        vbox.append(ac_frame)

        self.status_label = Gtk.Label(label="", xalign=0)
        vbox.append(self.status_label)

        self.refresh_status()

    def refresh_status(self):
        # power-profiles-daemon
        out, rc = run_cmd(["powerprofilesctl", "get"])
        if rc == 0:
            cur = out.strip()
            self.ppd_status.set_text(f"Active profile: {cur}")
            for p, btn in self.profile_buttons.items():
                btn.handler_block_by_func(self.on_profile_toggled)
                btn.set_active(p == cur)
                btn.handler_unblock_by_func(self.on_profile_toggled)
        else:
            self.ppd_status.set_text("power-profiles-daemon not available")

        # Battery
        bat_base = "/sys/class/power_supply"
        bat_dir = None
        ac_dir = None
        try:
            for name in os.listdir(bat_base):
                path = os.path.join(bat_base, name)
                t = read_file(os.path.join(path, "type"))
                if t == "Battery":
                    bat_dir = path
                elif t == "Mains":
                    ac_dir = path
        except Exception:
            pass

        if bat_dir:
            cap = read_file(os.path.join(bat_dir, "capacity"))
            self.bat_labels["capacity"].set_text(f"{cap}%" if cap else "—")
            for key in ["status", "technology", "cycle_count", "manufacturer", "model_name"]:
                val = read_file(os.path.join(bat_dir, key))
                if key in self.bat_labels:
                    self.bat_labels[key].set_text(val or "—")
            en_now = read_file(os.path.join(bat_dir, "energy_now"))
            en_full = read_file(os.path.join(bat_dir, "energy_full"))
            pwr = read_file(os.path.join(bat_dir, "power_now"))
            self.bat_labels["energy_now"].set_text(f"{int(en_now or 0)/1e6:.2f} Wh" if en_now else "—")
            self.bat_labels["energy_full"].set_text(f"{int(en_full or 0)/1e6:.2f} Wh" if en_full else "—")
            self.bat_labels["power_now"].set_text(f"{int(pwr or 0)/1e6:.2f} W" if pwr else "—")
        else:
            for lbl in self.bat_labels.values():
                lbl.set_text("No battery")

        if ac_dir:
            online = read_file(os.path.join(ac_dir, "online"))
            self.ac_label.set_text("Connected (charging)" if online == "1" else "Disconnected (on battery)")
        else:
            self.ac_label.set_text("No AC adapter info")

        # CPU governor
        gov = read_file("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
        self.gov_label.set_text(gov or "—")
        min_freq = read_file("/sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq")
        max_freq = read_file("/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq")
        cur_freq = read_file("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq")
        freq_info = []
        if min_freq: freq_info.append(f"Min: {int(min_freq)//1000} MHz")
        if max_freq: freq_info.append(f"Max: {int(max_freq)//1000} MHz")
        if cur_freq: freq_info.append(f"Current: {int(cur_freq)//1000} MHz")
        self.cpu_freq_label.set_text("  ".join(freq_info) or "Frequency info unavailable")

        return True  # keep timeout

    def on_profile_toggled(self, btn, profile):
        if not btn.get_active():
            return
        # Unselect others
        for p, b in self.profile_buttons.items():
            if p != profile:
                b.handler_block_by_func(self.on_profile_toggled)
                b.set_active(False)
                b.handler_unblock_by_func(self.on_profile_toggled)
        out, rc = run_cmd(["powerprofilesctl", "set", profile])
        if rc == 0:
            self.status_label.set_text(f"Set profile: {profile}")
        else:
            self.status_label.set_text(f"Failed to set profile: {out}")

    def on_set_governor(self, btn):
        gov = self.gov_combo.get_active_text()
        if not gov:
            return
        out, rc = run_cmd(["pkexec", "bash", "-c",
                           f"echo {gov} > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"])
        if rc == 0:
            self.status_label.set_text(f"CPU governor set to: {gov}")
        else:
            self.status_label.set_text(f"Failed (needs pkexec/root): {out}")

class PowerProfilesApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.PowerProfiles")
    def do_activate(self):
        win = PowerProfilesWindow(self); win.present()

def main():
    app = PowerProfilesApp(); app.run(None)

if __name__ == "__main__":
    main()
