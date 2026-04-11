#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, GLib, Gst
import os, time

Gst.init(None)

class AudioRecorderWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Audio Recorder")
        self.set_default_size(420, 320)
        self.recording = False
        self.pipeline = None
        self.start_time = 0
        self.timeout_id = None
        self.output_file = os.path.expanduser("~/recording.wav")

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_top(20); vbox.set_margin_bottom(20)
        vbox.set_margin_start(20); vbox.set_margin_end(20)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Audio Recorder", css_classes=["title"]))

        self.timer_label = Gtk.Label(label="00:00")
        css = Gtk.CssProvider()
        css.load_from_data(b".timer { font-size: 48px; font-weight: bold; }")
        Gtk.StyleContext.add_provider_for_display(self.get_display(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.timer_label.set_css_classes(["timer"])
        vbox.append(self.timer_label)

        file_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        file_box.append(Gtk.Label(label="Save to:"))
        self.file_entry = Gtk.Entry()
        self.file_entry.set_text(self.output_file)
        self.file_entry.set_hexpand(True)
        file_box.append(self.file_entry)
        browse_btn = Gtk.Button(label="Browse")
        browse_btn.connect("clicked", self.on_browse)
        file_box.append(browse_btn)
        vbox.append(file_box)

        self.record_btn = Gtk.Button(label="Start Recording")
        self.record_btn.connect("clicked", self.on_toggle)
        vbox.append(self.record_btn)

        self.status_label = Gtk.Label(label="Ready to record")
        vbox.append(self.status_label)

        self.recordings_label = Gtk.Label(label="")
        vbox.append(self.recordings_label)

    def on_browse(self, btn):
        dialog = Gtk.FileDialog()
        dialog.set_title("Save Recording As")
        dialog.save(self, None, self.on_save_dialog)

    def on_save_dialog(self, dialog, result):
        try:
            f = dialog.save_finish(result)
            if f:
                path = f.get_path()
                if not path.endswith(".wav"):
                    path += ".wav"
                self.file_entry.set_text(path)
                self.output_file = path
        except Exception:
            pass

    def on_toggle(self, btn):
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        self.output_file = self.file_entry.get_text()
        pipeline_str = (
            f"pulsesrc ! audioconvert ! audioresample ! "
            f"wavenc ! filesink location=\"{self.output_file}\""
        )
        self.pipeline = Gst.parse_launch(pipeline_str)
        self.pipeline.set_state(Gst.State.PLAYING)
        self.recording = True
        self.start_time = time.time()
        self.record_btn.set_label("Stop Recording")
        self.status_label.set_text("Recording...")
        self.timeout_id = GLib.timeout_add(1000, self.update_timer)

    def stop_recording(self):
        if self.pipeline:
            self.pipeline.send_event(Gst.Event.new_eos())
            GLib.timeout_add(500, self.finish_pipeline)
        self.recording = False
        if self.timeout_id:
            GLib.source_remove(self.timeout_id)
        self.record_btn.set_label("Start Recording")

    def finish_pipeline(self):
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
        elapsed = time.time() - self.start_time
        self.status_label.set_text(f"Saved: {self.output_file}")
        self.recordings_label.set_text(f"Duration: {int(elapsed)}s")
        return False

    def update_timer(self):
        if not self.recording:
            return False
        elapsed = int(time.time() - self.start_time)
        mins = elapsed // 60
        secs = elapsed % 60
        self.timer_label.set_text(f"{mins:02d}:{secs:02d}")
        return True

class AudioRecorderApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.AudioRecorder")
    def do_activate(self):
        win = AudioRecorderWindow(self)
        win.present()

def main():
    app = AudioRecorderApp()
    app.run(None)

if __name__ == "__main__":
    main()
