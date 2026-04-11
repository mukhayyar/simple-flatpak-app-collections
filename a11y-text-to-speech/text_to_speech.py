#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, GLib, Gst
import subprocess, threading, os, tempfile

Gst.init(None)

def espeak_available():
    try:
        subprocess.run(["espeak", "--version"], capture_output=True, timeout=3)
        return True
    except Exception:
        return False

def festival_available():
    try:
        subprocess.run(["festival", "--version"], capture_output=True, timeout=3)
        return True
    except Exception:
        return False

class TextToSpeechWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Text to Speech")
        self.set_default_size(700, 560)
        self.playing = False
        self.proc = None
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(12); vbox.set_margin_bottom(12)
        vbox.set_margin_start(16); vbox.set_margin_end(16)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Text to Speech", css_classes=["title"]))

        # Text input
        text_frame = Gtk.Frame(label="Text to Speak")
        text_scroll = Gtk.ScrolledWindow()
        text_scroll.set_min_content_height(140)
        self.text_view = Gtk.TextView()
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.text_view.set_monospace(False)
        self.text_view.get_buffer().set_text(
            "Welcome to Text to Speech. This application converts text to spoken audio.\n\n"
            "You can use this tool to help with accessibility, proofreading, or learning."
        )
        text_scroll.set_child(self.text_view)
        text_frame.set_child(text_scroll)
        vbox.append(text_frame)

        # Controls
        ctrl_frame = Gtk.Frame(label="Speech Controls")
        ctrl_grid = Gtk.Grid()
        ctrl_grid.set_row_spacing(8); ctrl_grid.set_column_spacing(12)
        ctrl_grid.set_margin_top(8); ctrl_grid.set_margin_start(12)
        ctrl_grid.set_margin_end(12); ctrl_grid.set_margin_bottom(8)

        ctrl_grid.attach(Gtk.Label(label="Engine:", xalign=1), 0, 0, 1, 1)
        self.engine_combo = Gtk.ComboBoxText()
        for eng in ["espeak", "festival", "spd-say", "pico2wave"]:
            self.engine_combo.append_text(eng)
        self.engine_combo.set_active(0)
        ctrl_grid.attach(self.engine_combo, 1, 0, 1, 1)

        ctrl_grid.attach(Gtk.Label(label="Voice/Language:", xalign=1), 0, 1, 1, 1)
        self.voice_combo = Gtk.ComboBoxText()
        for v in ["en", "en-us", "en-gb", "de", "fr", "es", "it", "pt", "ru", "ja", "zh"]:
            self.voice_combo.append_text(v)
        self.voice_combo.set_active(0)
        ctrl_grid.attach(self.voice_combo, 1, 1, 1, 1)

        ctrl_grid.attach(Gtk.Label(label="Speed (wpm):", xalign=1), 0, 2, 1, 1)
        self.speed_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 80, 300, 5)
        self.speed_scale.set_value(160)
        self.speed_scale.set_hexpand(True)
        self.speed_scale.set_draw_value(True)
        ctrl_grid.attach(self.speed_scale, 1, 2, 1, 1)

        ctrl_grid.attach(Gtk.Label(label="Pitch:", xalign=1), 0, 3, 1, 1)
        self.pitch_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 99, 1)
        self.pitch_scale.set_value(50)
        self.pitch_scale.set_draw_value(True)
        ctrl_grid.attach(self.pitch_scale, 1, 3, 1, 1)

        ctrl_grid.attach(Gtk.Label(label="Volume:", xalign=1), 0, 4, 1, 1)
        self.vol_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 200, 5)
        self.vol_scale.set_value(100)
        self.vol_scale.set_draw_value(True)
        ctrl_grid.attach(self.vol_scale, 1, 4, 1, 1)

        ctrl_frame.set_child(ctrl_grid)
        vbox.append(ctrl_frame)

        # Buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_box.set_halign(Gtk.Align.CENTER)

        self.speak_btn = Gtk.Button(label="▶ Speak")
        self.speak_btn.add_css_class("suggested-action")
        self.speak_btn.connect("clicked", self.on_speak)
        btn_box.append(self.speak_btn)

        stop_btn = Gtk.Button(label="■ Stop")
        stop_btn.add_css_class("destructive-action")
        stop_btn.connect("clicked", self.on_stop)
        btn_box.append(stop_btn)

        test_btn = Gtk.Button(label="Test (selected text)")
        test_btn.connect("clicked", self.on_speak_selection)
        btn_box.append(test_btn)
        vbox.append(btn_box)

        # Phonetic guide
        phonetic_frame = Gtk.Frame(label="Quick Reference - SSML/Phonetic")
        phonetic_view = Gtk.TextView()
        phonetic_view.set_editable(False)
        phonetic_view.get_buffer().set_text(
            "espeak commands: espeak -v en -s 160 -p 50 -a 100 \"Hello world\"\n"
            "Save to wav: espeak -v en --stdout \"text\" > output.wav\n"
            "Languages: espeak --voices (list all)\n"
            "festival: echo \"text\" | festival --tts\n"
            "spd-say: spd-say -r 0 -p 0 \"text\"\n"
        )
        phonetic_scroll = Gtk.ScrolledWindow()
        phonetic_scroll.set_min_content_height(80)
        phonetic_scroll.set_child(phonetic_view)
        phonetic_frame.set_child(phonetic_scroll)
        vbox.append(phonetic_frame)

        self.status_label = Gtk.Label(label="Ready", xalign=0)
        vbox.append(self.status_label)

    def get_text(self):
        buf = self.text_view.get_buffer()
        return buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False).strip()

    def get_selected_text(self):
        buf = self.text_view.get_buffer()
        try:
            start, end = buf.get_selection_bounds()
            return buf.get_text(start, end, False)
        except Exception:
            return self.get_text()

    def on_speak(self, btn):
        self.speak_text(self.get_text())

    def on_speak_selection(self, btn):
        self.speak_text(self.get_selected_text())

    def speak_text(self, text):
        if not text:
            self.status_label.set_text("No text to speak")
            return
        self.on_stop(None)
        engine = self.engine_combo.get_active_text()
        voice = self.voice_combo.get_active_text()
        speed = int(self.speed_scale.get_value())
        pitch = int(self.pitch_scale.get_value())
        vol = int(self.vol_scale.get_value())

        self.status_label.set_text(f"Speaking via {engine}...")
        self.speak_btn.set_sensitive(False)

        def run():
            try:
                if engine == "espeak":
                    cmd = ["espeak", "-v", voice, "-s", str(speed), "-p", str(pitch),
                           "-a", str(vol), text]
                elif engine == "festival":
                    cmd = ["bash", "-c", f'echo "{text}" | festival --tts']
                elif engine == "spd-say":
                    cmd = ["spd-say", "-r", str(speed-175), "-p", str(pitch-50), text]
                elif engine == "pico2wave":
                    tmp = tempfile.mktemp(suffix=".wav")
                    cmd = ["pico2wave", "-l", voice if "-" in voice else "en-US",
                           "-w", tmp, text]
                else:
                    cmd = ["espeak", text]
                self.proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.proc.wait()
            except FileNotFoundError:
                GLib.idle_add(self.status_label.set_text,
                    f"Engine '{engine}' not found. Install it first.")
            except Exception as e:
                GLib.idle_add(self.status_label.set_text, f"Error: {e}")
            finally:
                GLib.idle_add(self.speak_btn.set_sensitive, True)
                GLib.idle_add(self.status_label.set_text, "Done")
                self.proc = None

        threading.Thread(target=run, daemon=True).start()

    def on_stop(self, btn):
        if self.proc:
            try:
                self.proc.terminate()
            except Exception:
                pass
            self.proc = None
        self.speak_btn.set_sensitive(True)
        self.status_label.set_text("Stopped")

class TextToSpeechApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.TextToSpeech")
    def do_activate(self):
        win = TextToSpeechWindow(self); win.present()

def main():
    app = TextToSpeechApp(); app.run(None)

if __name__ == "__main__":
    main()
