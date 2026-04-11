#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, Gst, GLib
import math

Gst.init(None)

NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
CHORDS = {
    "Major": [0, 4, 7],
    "Minor": [0, 3, 7],
    "7th": [0, 4, 7, 10],
    "Major7": [0, 4, 7, 11],
    "Minor7": [0, 3, 7, 10],
    "9th": [0, 4, 7, 10, 14],
    "Diminished": [0, 3, 6],
    "Augmented": [0, 4, 8],
    "Sus2": [0, 2, 7],
    "Sus4": [0, 5, 7],
}

def note_freq(midi): return 440.0 * (2 ** ((midi - 69) / 12.0))
def note_midi(name, octave=4): return NOTES.index(name) + (octave + 1) * 12

class ChordFinderWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Chord Finder")
        self.set_default_size(600, 500)
        self.chord_notes = []
        self.pipeline = None

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(16); vbox.set_margin_bottom(16)
        vbox.set_margin_start(16); vbox.set_margin_end(16)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Chord Finder", css_classes=["title"]))

        sel_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        sel_box.set_halign(Gtk.Align.CENTER)

        note_frame = Gtk.Frame(label="Root Note")
        note_grid = Gtk.FlowBox()
        note_grid.set_max_children_per_line(6)
        self.note_btns = {}
        for n in NOTES:
            btn = Gtk.ToggleButton(label=n)
            btn.connect("toggled", self.on_note_toggled, n)
            note_grid.append(btn)
            self.note_btns[n] = btn
        note_frame.set_child(note_grid)
        sel_box.append(note_frame)

        chord_frame = Gtk.Frame(label="Chord Type")
        chord_list = Gtk.ListBox()
        chord_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        chord_list.connect("row-selected", self.on_chord_selected)
        for c in CHORDS:
            row = Gtk.ListBoxRow()
            row.set_child(Gtk.Label(label=c, xalign=0, margin_start=8))
            chord_list.append(row)
        chord_frame.set_child(chord_list)
        sel_box.append(chord_frame)
        vbox.append(sel_box)

        self.chord_label = Gtk.Label(label="Notes: -")
        vbox.append(self.chord_label)

        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_size_request(560, 120)
        self.drawing_area.set_draw_func(self.on_draw_piano)
        vbox.append(self.drawing_area)

        play_btn = Gtk.Button(label="Play Chord")
        play_btn.connect("clicked", self.on_play)
        vbox.append(play_btn)

        self.root = "C"
        self.chord_type = "Major"

    def on_note_toggled(self, btn, note):
        for n, b in self.note_btns.items():
            if n != note:
                b.set_active(False)
        self.root = note
        self.update_chord()

    def on_chord_selected(self, listbox, row):
        if row:
            self.chord_type = row.get_child().get_text()
            self.update_chord()

    def update_chord(self):
        intervals = CHORDS.get(self.chord_type, [0, 4, 7])
        root_idx = NOTES.index(self.root)
        self.chord_notes = [(root_idx + i) % 12 for i in intervals]
        names = [NOTES[n] for n in self.chord_notes]
        self.chord_label.set_text(f"{self.root} {self.chord_type}: {' - '.join(names)}")
        self.drawing_area.queue_draw()

    def on_play(self, btn):
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
        root_midi = note_midi(self.root, 4)
        intervals = CHORDS.get(self.chord_type, [0, 4, 7])
        freqs = [note_freq(root_midi + i) for i in intervals]
        mixer_inputs = " ".join(
            f"audiotestsrc wave=0 freq={f:.1f} volume=0.3 num-buffers=80 ! audioconvert ! audiomixer0. "
            for f in freqs
        )
        pipe = f"audiomixer name=audiomixer0 ! audioconvert ! autoaudiosink {mixer_inputs}"
        try:
            self.pipeline = Gst.parse_launch(pipe)
            self.pipeline.set_state(Gst.State.PLAYING)
            GLib.timeout_add(2000, self.stop_pipeline)
        except Exception as e:
            pass

    def stop_pipeline(self):
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
        return False

    def on_draw_piano(self, area, cr, w, h):
        num_keys = 24
        white_keys = [i for i in range(num_keys) if (i % 12) not in [1, 3, 6, 8, 10]]
        kw = w / len(white_keys)
        root_idx = NOTES.index(self.root)
        white_idx = 0
        positions = {}
        for i in range(num_keys):
            note = i % 12
            is_black = note in [1, 3, 6, 8, 10]
            positions[i] = (white_idx, is_black)
            if not is_black:
                white_idx += 1

        for i in range(num_keys):
            note = i % 12
            wi, is_black = positions[i]
            highlight = note in self.chord_notes
            if not is_black:
                cr.set_source_rgb(1 if not highlight else 0.3, 1 if not highlight else 0.8, 0.3 if highlight else 1)
                cr.rectangle(wi * kw + 1, 0, kw - 2, h)
                cr.fill()
                cr.set_source_rgb(0, 0, 0)
                cr.rectangle(wi * kw + 1, 0, kw - 2, h)
                cr.stroke()

        for i in range(num_keys):
            note = i % 12
            wi, is_black = positions[i]
            highlight = note in self.chord_notes
            if is_black:
                cr.set_source_rgb(0.2 if not highlight else 0.2, 0.6 if highlight else 0.2, 0.2 if highlight else 0.2)
                cr.rectangle(wi * kw - kw * 0.3, 0, kw * 0.6, h * 0.6)
                cr.fill()

class ChordFinderApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.ChordFinder")
    def do_activate(self):
        win = ChordFinderWindow(self)
        win.present()

def main():
    app = ChordFinderApp()
    app.run(None)

if __name__ == "__main__":
    main()
