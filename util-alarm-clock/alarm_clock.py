#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gst
import datetime, time, threading

Gst.init(None)

class AlarmClockWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Alarm Clock")
        self.set_default_size(500, 500)
        self.alarms = []
        self.build_ui()
        GLib.timeout_add(1000, self.tick)

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(20); vbox.set_margin_bottom(20)
        vbox.set_margin_start(20); vbox.set_margin_end(20)
        self.set_child(vbox)

        self.clock_label = Gtk.Label(label="00:00:00")
        self.clock_label.set_markup("<span font='48' weight='bold' font_family='monospace'>00:00:00</span>")
        vbox.append(self.clock_label)

        self.date_label = Gtk.Label(label="")
        vbox.append(self.date_label)

        add_frame = Gtk.Frame(label="Add Alarm")
        add_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        add_box.set_margin_top(8); add_box.set_margin_start(8); add_box.set_margin_end(8); add_box.set_margin_bottom(8)

        time_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        time_box.set_halign(Gtk.Align.CENTER)
        time_box.append(Gtk.Label(label="Hour:"))
        self.hour_spin = Gtk.SpinButton.new_with_range(0, 23, 1)
        self.hour_spin.set_value(datetime.datetime.now().hour)
        time_box.append(self.hour_spin)
        time_box.append(Gtk.Label(label=":"))
        self.min_spin = Gtk.SpinButton.new_with_range(0, 59, 1)
        self.min_spin.set_value(0)
        time_box.append(self.min_spin)
        time_box.append(Gtk.Label(label=":"))
        self.sec_spin = Gtk.SpinButton.new_with_range(0, 59, 1)
        self.sec_spin.set_value(0)
        time_box.append(self.sec_spin)
        add_box.append(time_box)

        label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        label_box.append(Gtk.Label(label="Label:"))
        self.label_entry = Gtk.Entry()
        self.label_entry.set_placeholder_text("Wake up!")
        self.label_entry.set_hexpand(True)
        label_box.append(self.label_entry)
        add_box.append(label_box)

        repeat_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.repeat_check = Gtk.CheckButton(label="Repeat daily")
        repeat_box.append(self.repeat_check)
        sound_combo = Gtk.ComboBoxText()
        for s in ["Beep", "Chime", "Bell"]:
            sound_combo.append_text(s)
        sound_combo.set_active(0)
        self.sound_combo = sound_combo
        repeat_box.append(sound_combo)
        add_box.append(repeat_box)

        add_btn = Gtk.Button(label="+ Add Alarm")
        add_btn.set_halign(Gtk.Align.CENTER)
        add_btn.connect("clicked", self.on_add)
        add_box.append(add_btn)

        add_frame.set_child(add_box)
        vbox.append(add_frame)

        alarm_frame = Gtk.Frame(label="Active Alarms")
        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        self.alarm_store = Gtk.ListStore(str, str, str, bool, int)
        alarm_tree = Gtk.TreeView(model=self.alarm_store)

        toggle_renderer = Gtk.CellRendererToggle()
        toggle_renderer.connect("toggled", self.on_alarm_toggled)
        alarm_tree.append_column(Gtk.TreeViewColumn("Active", toggle_renderer, active=3))

        for i, title in enumerate(["Time", "Label", "Sound"]):
            col = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i)
            col.set_resizable(True)
            alarm_tree.append_column(col)

        del_renderer = Gtk.CellRendererText()
        alarm_tree.get_selection().connect("changed", self.on_alarm_selected)
        scroll.set_child(alarm_tree)
        alarm_frame.set_child(scroll)
        vbox.append(alarm_frame)

        del_btn = Gtk.Button(label="✗ Delete Selected")
        del_btn.set_halign(Gtk.Align.CENTER)
        del_btn.connect("clicked", self.on_delete)
        self.alarm_tree = alarm_tree
        vbox.append(del_btn)

        self.selected_idx = None

    def tick(self):
        now = datetime.datetime.now()
        self.clock_label.set_markup(f"<span font='48' weight='bold' font_family='monospace'>{now.strftime('%H:%M:%S')}</span>")
        self.date_label.set_text(now.strftime("%A, %B %d, %Y"))
        for i, alarm in enumerate(self.alarms):
            if not alarm["active"]:
                continue
            alarm_time = alarm["time"]
            if (now.hour == alarm_time.hour and
                    now.minute == alarm_time.minute and
                    now.second == alarm_time.second):
                self.trigger_alarm(alarm, i)
        return True

    def trigger_alarm(self, alarm, idx):
        self.ring_sound(alarm.get("sound", "Beep"))
        dialog = Gtk.MessageDialog(transient_for=self, modal=True,
                                   message_type=Gtk.MessageType.INFO,
                                   buttons=Gtk.ButtonsType.OK,
                                   text=f"Alarm! {alarm.get('label', 'Wake up!')}")
        dialog.connect("response", lambda d, r: d.destroy())
        dialog.present()
        if not alarm.get("repeat", False):
            alarm["active"] = False
            self.alarm_store[idx][3] = False

    def ring_sound(self, sound_type):
        threading.Thread(target=self._ring, args=(sound_type,), daemon=True).start()

    def _ring(self, sound_type):
        freqs = {"Beep": 880, "Chime": 523, "Bell": 660}
        freq = freqs.get(sound_type, 880)
        for _ in range(3):
            p = Gst.parse_launch(f"audiotestsrc freq={freq} wave=0 ! audio/x-raw,channels=1 ! volume volume=0.7 ! autoaudiosink")
            p.set_state(Gst.State.PLAYING)
            time.sleep(0.4)
            p.set_state(Gst.State.NULL)
            time.sleep(0.15)

    def on_add(self, btn):
        h = int(self.hour_spin.get_value())
        m = int(self.min_spin.get_value())
        s = int(self.sec_spin.get_value())
        label = self.label_entry.get_text() or "Alarm"
        sound = self.sound_combo.get_active_text()
        repeat = self.repeat_check.get_active()
        alarm_time = datetime.time(h, m, s)
        alarm = {"time": alarm_time, "label": label, "sound": sound, "repeat": repeat, "active": True}
        idx = len(self.alarms)
        self.alarms.append(alarm)
        time_str = f"{h:02d}:{m:02d}:{s:02d}"
        self.alarm_store.append([time_str, label, sound, True, idx])
        self.label_entry.set_text("")

    def on_alarm_toggled(self, renderer, path):
        iter_ = self.alarm_store.get_iter(path)
        idx = self.alarm_store[iter_][4]
        current = self.alarm_store[iter_][3]
        self.alarm_store[iter_][3] = not current
        self.alarms[idx]["active"] = not current

    def on_alarm_selected(self, selection):
        model, iter_ = selection.get_selected()
        if iter_:
            self.selected_idx = model[iter_][4]

    def on_delete(self, btn):
        if self.selected_idx is not None:
            self.alarms[self.selected_idx]["active"] = False
            idx = self.selected_idx
            iter_ = self.alarm_store.get_iter_first()
            while iter_:
                if self.alarm_store[iter_][4] == idx:
                    self.alarm_store.remove(iter_)
                    break
                iter_ = self.alarm_store.iter_next(iter_)

class AlarmClockApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.AlarmClock")
    def do_activate(self):
        win = AlarmClockWindow(self); win.present()

def main():
    app = AlarmClockApp(); app.run(None)

if __name__ == "__main__":
    main()
