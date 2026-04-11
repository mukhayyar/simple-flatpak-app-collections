#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import subprocess, threading, math

class WifiInfoWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("WiFi Info")
        self.set_default_size(580, 520)
        self.signal = -70
        self.build_ui()
        GLib.timeout_add(3000, self.refresh)
        self.refresh()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(12); vbox.set_margin_bottom(12)
        vbox.set_margin_start(12); vbox.set_margin_end(12)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="WiFi Information", css_classes=["title"]))

        refresh_btn = Gtk.Button(label="Refresh")
        refresh_btn.connect("clicked", lambda b: self.refresh())
        vbox.append(refresh_btn)

        self.gauge = Gtk.DrawingArea()
        self.gauge.set_size_request(380, 200)
        self.gauge.set_halign(Gtk.Align.CENTER)
        self.gauge.set_draw_func(self.on_draw_gauge)
        vbox.append(self.gauge)

        self.info_view = Gtk.TextView()
        self.info_view.set_editable(False); self.info_view.set_monospace(True)
        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        scroll.set_child(self.info_view)
        vbox.append(scroll)

    def refresh(self):
        threading.Thread(target=self.gather_wifi_info, daemon=True).start()
        return True

    def gather_wifi_info(self):
        lines = []
        try:
            result = subprocess.run(["iwconfig"], capture_output=True, text=True, timeout=5)
            output = result.stdout + result.stderr
            current_iface = None
            for line in output.splitlines():
                if line and not line.startswith(" "):
                    iface = line.split()[0]
                    if "IEEE" in line or "ESSID" in line:
                        current_iface = iface
                        lines.append(f"=== {iface} ===")
                        if "ESSID:" in line:
                            ssid = line.split("ESSID:")[1].strip().strip('"')
                            lines.append(f"SSID: {ssid}")
                elif current_iface:
                    if "Frequency:" in line:
                        freq = line.split("Frequency:")[1].split()[0]
                        lines.append(f"Frequency: {freq} GHz")
                        if "Channel" in line:
                            ch = line.split("Channel:")[1].split()[0] if "Channel:" in line else line.split("(Channel")[1].split(")")[0]
                            lines.append(f"Channel: {ch}")
                    if "Signal level=" in line:
                        sig = line.split("Signal level=")[1].split()[0]
                        try:
                            self.signal = int(sig)
                        except Exception:
                            pass
                        lines.append(f"Signal: {sig} dBm")
                    if "Bit Rate=" in line:
                        rate = line.split("Bit Rate=")[1].split()[0]
                        lines.append(f"Bit Rate: {rate} Mb/s")
                    if "Link Quality=" in line:
                        lq = line.split("Link Quality=")[1].split()[0]
                        lines.append(f"Link Quality: {lq}")
        except Exception as e:
            lines.append(f"iwconfig error: {e}")

        try:
            result = subprocess.run(["nmcli", "-t", "-f", "active,ssid,signal,freq,chan,rate",
                                     "dev", "wifi"], capture_output=True, text=True, timeout=5)
            active_lines = [l for l in result.stdout.splitlines() if l.startswith("yes")]
            if active_lines:
                lines.append("\n--- nmcli info ---")
                for l in active_lines:
                    parts = l.split(":")
                    if len(parts) >= 6:
                        lines.append(f"SSID: {parts[1]}, Signal: {parts[2]}%, Freq: {parts[3]}, Channel: {parts[4]}")
                        try:
                            self.signal = -70 + int(parts[2]) * 0.3
                        except Exception:
                            pass
        except Exception:
            pass

        GLib.idle_add(self.show_info, "\n".join(lines))

    def show_info(self, text):
        self.info_view.get_buffer().set_text(text if text else "No WiFi information available")
        self.gauge.queue_draw()
        return False

    def on_draw_gauge(self, area, cr, w, h):
        cx, cy = w/2, h * 0.85
        r = min(w, h) * 0.7
        signal = max(-90, min(-20, self.signal))
        quality = (signal + 90) / 70.0

        cr.set_source_rgb(0.1, 0.1, 0.15)
        cr.rectangle(0, 0, w, h); cr.fill()

        for i, (color, threshold) in enumerate([((0.8,0.2,0.2), 0.33), ((0.8,0.8,0.2), 0.66), ((0.2,0.8,0.2), 1.0)]):
            start_angle = math.pi + i * math.pi/3
            end_angle = math.pi + (i+1) * math.pi/3
            cr.set_source_rgb(*color)
            cr.set_line_width(12)
            cr.arc(cx, cy, r, start_angle, end_angle)
            cr.stroke()

        needle_angle = math.pi + quality * math.pi
        nx = cx + (r - 20) * math.cos(needle_angle)
        ny = cy + (r - 20) * math.sin(needle_angle)
        cr.set_source_rgb(1, 1, 1)
        cr.set_line_width(3)
        cr.move_to(cx, cy); cr.line_to(nx, ny); cr.stroke()
        cr.arc(cx, cy, 6, 0, 6.28); cr.fill()

        cr.set_font_size(14)
        cr.move_to(cx - 30, cy - r + 20)
        cr.set_source_rgb(1, 1, 1)
        cr.show_text(f"{signal} dBm")

        strength = "Excellent" if quality > 0.7 else ("Good" if quality > 0.4 else ("Fair" if quality > 0.2 else "Poor"))
        cr.set_font_size(12)
        cr.move_to(cx - 30, cy - 10)
        cr.show_text(f"{strength} ({quality*100:.0f}%)")

class WifiInfoApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.WifiInfo")
    def do_activate(self):
        win = WifiInfoWindow(self)
        win.present()

def main():
    app = WifiInfoApp()
    app.run(None)

if __name__ == "__main__":
    main()
