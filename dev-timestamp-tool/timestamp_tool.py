#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk
import time, datetime

class TimestampToolWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Timestamp Tool")
        self.set_default_size(600, 520)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(16); vbox.set_margin_bottom(16)
        vbox.set_margin_start(16); vbox.set_margin_end(16)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Timestamp Tool", css_classes=["title"]))

        self.current_label = Gtk.Label(label="")
        vbox.append(self.current_label)
        GLib.timeout_add(1000, self.update_current)
        self.update_current()

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.append(sep)

        epoch_frame = Gtk.Frame(label="Unix Timestamp → Human Date")
        epoch_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        epoch_box.set_margin_top(8); epoch_box.set_margin_start(8)
        epoch_box.set_margin_bottom(8); epoch_box.set_margin_end(8)

        input_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.epoch_entry = Gtk.Entry()
        self.epoch_entry.set_placeholder_text("Enter Unix timestamp...")
        self.epoch_entry.set_hexpand(True)
        self.epoch_entry.connect("changed", self.on_epoch_changed)
        input_row.append(self.epoch_entry)

        self.unit_combo = Gtk.ComboBoxText()
        for u in ["seconds", "milliseconds", "nanoseconds"]:
            self.unit_combo.append_text(u)
        self.unit_combo.set_active(0)
        self.unit_combo.connect("changed", self.on_epoch_changed)
        input_row.append(self.unit_combo)

        now_btn = Gtk.Button(label="Now")
        now_btn.connect("clicked", lambda b: self.epoch_entry.set_text(str(int(time.time()))))
        input_row.append(now_btn)
        epoch_box.append(input_row)

        self.utc_label = Gtk.Label(label="UTC: -"); self.utc_label.set_xalign(0)
        self.local_label = Gtk.Label(label="Local: -"); self.local_label.set_xalign(0)
        self.iso_label = Gtk.Label(label="ISO 8601: -"); self.iso_label.set_xalign(0)
        self.relative_label = Gtk.Label(label="Relative: -"); self.relative_label.set_xalign(0)
        for lbl in [self.utc_label, self.local_label, self.iso_label, self.relative_label]:
            lbl.set_selectable(True)
            epoch_box.append(lbl)
        epoch_frame.set_child(epoch_box)
        vbox.append(epoch_frame)

        date_frame = Gtk.Frame(label="Human Date → Unix Timestamp")
        date_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        date_box.set_margin_top(8); date_box.set_margin_start(8)
        date_box.set_margin_bottom(8); date_box.set_margin_end(8)

        date_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.date_entry = Gtk.Entry()
        self.date_entry.set_placeholder_text("YYYY-MM-DD HH:MM:SS")
        self.date_entry.set_hexpand(True)
        date_row.append(self.date_entry)

        self.utc_toggle = Gtk.CheckButton(label="UTC")
        self.utc_toggle.set_active(True)
        date_row.append(self.utc_toggle)

        conv_btn = Gtk.Button(label="Convert")
        conv_btn.connect("clicked", self.on_date_convert)
        date_row.append(conv_btn)
        date_box.append(date_row)

        self.epoch_result_label = Gtk.Label(label="Timestamp: -")
        self.epoch_result_label.set_xalign(0)
        self.epoch_result_label.set_selectable(True)
        date_box.append(self.epoch_result_label)
        date_frame.set_child(date_box)
        vbox.append(date_frame)

    def update_current(self):
        now = time.time()
        dt = datetime.datetime.utcnow()
        self.current_label.set_text(
            f"Now: {int(now)} | {dt.strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )
        return True

    def on_epoch_changed(self, *args):
        text = self.epoch_entry.get_text().strip()
        if not text:
            return
        try:
            val = int(text)
            unit = self.unit_combo.get_active()
            if unit == 1: val //= 1000
            elif unit == 2: val //= 1_000_000_000
            dt_utc = datetime.datetime.utcfromtimestamp(val)
            dt_local = datetime.datetime.fromtimestamp(val)
            self.utc_label.set_text(f"UTC: {dt_utc.strftime('%Y-%m-%d %H:%M:%S')}")
            self.local_label.set_text(f"Local: {dt_local.strftime('%Y-%m-%d %H:%M:%S')}")
            self.iso_label.set_text(f"ISO 8601: {dt_utc.isoformat()}Z")
            diff = val - int(time.time())
            if abs(diff) < 60: rel = f"{abs(diff)} seconds {'ago' if diff < 0 else 'from now'}"
            elif abs(diff) < 3600: rel = f"{abs(diff)//60} minutes {'ago' if diff < 0 else 'from now'}"
            elif abs(diff) < 86400: rel = f"{abs(diff)//3600} hours {'ago' if diff < 0 else 'from now'}"
            else: rel = f"{abs(diff)//86400} days {'ago' if diff < 0 else 'from now'}"
            self.relative_label.set_text(f"Relative: {rel}")
        except Exception as e:
            self.utc_label.set_text(f"Error: {e}")

    def on_date_convert(self, btn):
        text = self.date_entry.get_text().strip()
        try:
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
                try:
                    dt = datetime.datetime.strptime(text, fmt)
                    break
                except Exception:
                    pass
            else:
                raise ValueError("Unrecognized date format")
            if self.utc_toggle.get_active():
                ts = int(dt.replace(tzinfo=datetime.timezone.utc).timestamp())
            else:
                ts = int(dt.timestamp())
            self.epoch_result_label.set_text(
                f"Timestamp: {ts} (ms: {ts*1000}, ns: {ts*1_000_000_000})"
            )
        except Exception as e:
            self.epoch_result_label.set_text(f"Error: {e}")

class TimestampToolApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.TimestampTool")
    def do_activate(self):
        win = TimestampToolWindow(self)
        win.present()

def main():
    app = TimestampToolApp()
    app.run(None)

if __name__ == "__main__":
    main()
