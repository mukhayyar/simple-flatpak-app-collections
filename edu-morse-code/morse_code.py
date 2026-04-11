#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gst
import threading

Gst.init(None)

MORSE = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..',
    '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
    '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
    '.': '.-.-.-', ',': '--..--', '?': '..--..', '/': '-..-.', '-': '-....-',
    ' ': '/'
}
REVERSE_MORSE = {v: k for k, v in MORSE.items()}

class MorseCodeWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Morse Code Translator")
        self.set_default_size(700, 520)
        self.pipeline = None
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(12); vbox.set_margin_bottom(12)
        vbox.set_margin_start(12); vbox.set_margin_end(12)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Morse Code Translator", css_classes=["title"]))

        speed_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        speed_box.set_halign(Gtk.Align.CENTER)
        speed_box.append(Gtk.Label(label="Speed (WPM):"))
        self.speed_spin = Gtk.SpinButton.new_with_range(5, 40, 1)
        self.speed_spin.set_value(15)
        speed_box.append(self.speed_spin)
        speed_box.append(Gtk.Label(label="Freq (Hz):"))
        self.freq_spin = Gtk.SpinButton.new_with_range(200, 1200, 50)
        self.freq_spin.set_value(600)
        speed_box.append(self.freq_spin)
        vbox.append(speed_box)

        text_frame = Gtk.Frame(label="Text → Morse")
        text_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        text_vbox.set_margin_top(4); text_vbox.set_margin_start(4); text_vbox.set_margin_end(4); text_vbox.set_margin_bottom(4)
        self.text_entry = Gtk.Entry()
        self.text_entry.set_placeholder_text("Type text here...")
        self.text_entry.connect("changed", self.on_text_changed)
        text_vbox.append(self.text_entry)
        self.morse_output = Gtk.Label(label="")
        self.morse_output.set_wrap(True)
        self.morse_output.set_selectable(True)
        text_vbox.append(self.morse_output)
        play_btn = Gtk.Button(label="▶ Play Morse Audio")
        play_btn.connect("clicked", self.on_play)
        text_vbox.append(play_btn)
        text_frame.set_child(text_vbox)
        vbox.append(text_frame)

        morse_frame = Gtk.Frame(label="Morse → Text")
        morse_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        morse_vbox.set_margin_top(4); morse_vbox.set_margin_start(4); morse_vbox.set_margin_end(4); morse_vbox.set_margin_bottom(4)
        self.morse_entry = Gtk.Entry()
        self.morse_entry.set_placeholder_text("Type morse code (dots, dashes, spaces)...")
        self.morse_entry.connect("changed", self.on_morse_changed)
        morse_vbox.append(self.morse_entry)
        self.decoded_label = Gtk.Label(label="")
        self.decoded_label.set_selectable(True)
        morse_vbox.append(self.decoded_label)
        morse_frame.set_child(morse_vbox)
        vbox.append(morse_frame)

        ref_frame = Gtk.Frame(label="Quick Reference")
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(120)
        ref_grid = Gtk.Grid()
        ref_grid.set_row_spacing(2)
        ref_grid.set_column_spacing(10)
        ref_grid.set_margin_start(6); ref_grid.set_margin_top(4)
        letters = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        for i, ch in enumerate(letters):
            lbl = Gtk.Label(label=f"{ch}: {MORSE[ch]}", xalign=0)
            lbl.set_css_classes(["monospace"])
            ref_grid.attach(lbl, i // 13, i % 13, 1, 1)
        scroll.set_child(ref_grid)
        ref_frame.set_child(scroll)
        vbox.append(ref_frame)

    def on_text_changed(self, entry):
        text = entry.get_text().upper()
        parts = []
        for ch in text:
            if ch in MORSE:
                parts.append(MORSE[ch])
            else:
                parts.append('?')
        self.morse_output.set_text(' '.join(parts))

    def on_morse_changed(self, entry):
        morse = entry.get_text().strip()
        words = morse.split(' / ')
        result = []
        for word in words:
            chars = word.split()
            decoded = ''
            for c in chars:
                decoded += REVERSE_MORSE.get(c, '?')
            result.append(decoded)
        self.decoded_label.set_text(' '.join(result))

    def on_play(self, btn):
        morse = self.morse_output.get_text()
        if not morse:
            return
        threading.Thread(target=self.play_morse, args=(morse,), daemon=True).start()

    def play_morse(self, morse_str):
        wpm = int(self.speed_spin.get_value())
        freq = int(self.freq_spin.get_value())
        dit_ms = int(1200 / wpm)

        for symbol in morse_str:
            if symbol == '.':
                self._beep(freq, dit_ms)
            elif symbol == '-':
                self._beep(freq, dit_ms * 3)
            elif symbol == ' ':
                import time; time.sleep(dit_ms * 2 / 1000)
            elif symbol == '/':
                import time; time.sleep(dit_ms * 4 / 1000)
            import time; time.sleep(dit_ms / 1000)

    def _beep(self, freq, duration_ms):
        import time
        pipeline_str = f"audiotestsrc freq={freq} wave=0 ! audio/x-raw,channels=1 ! volume volume=0.5 ! autoaudiosink"
        p = Gst.parse_launch(pipeline_str)
        p.set_state(Gst.State.PLAYING)
        time.sleep(duration_ms / 1000)
        p.set_state(Gst.State.NULL)

class MorseCodeApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.MorseCode")
    def do_activate(self):
        win = MorseCodeWindow(self); win.present()

def main():
    app = MorseCodeApp(); app.run(None)

if __name__ == "__main__":
    main()
