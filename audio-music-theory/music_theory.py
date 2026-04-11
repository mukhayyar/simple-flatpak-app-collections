#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk
import math

NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
CIRCLE = ["C", "G", "D", "A", "E", "B", "F#", "Db", "Ab", "Eb", "Bb", "F"]
MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11]
MINOR_SCALE = [0, 2, 3, 5, 7, 8, 10]

CHORD_PROG = {
    "Major": ["I", "ii", "iii", "IV", "V", "vi", "vii°"],
    "Minor": ["i", "ii°", "III", "iv", "v", "VI", "VII"],
}

class MusicTheoryWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Music Theory Reference")
        self.set_default_size(700, 580)
        self.selected_key = "C"
        self.mode = "Major"

        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_child(paned)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        left.set_margin_top(12); left.set_margin_start(12)
        left.set_size_request(340, -1)

        left.append(Gtk.Label(label="Circle of Fifths"))
        self.circle_area = Gtk.DrawingArea()
        self.circle_area.set_size_request(320, 320)
        self.circle_area.set_draw_func(self.draw_circle)
        ctrl = Gtk.GestureClick()
        ctrl.connect("pressed", self.on_circle_click)
        self.circle_area.add_controller(ctrl)
        left.append(self.circle_area)

        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        mode_box.set_halign(Gtk.Align.CENTER)
        for m in ["Major", "Minor"]:
            btn = Gtk.ToggleButton(label=m)
            btn.set_active(m == "Major")
            btn.connect("toggled", self.on_mode, m)
            mode_box.append(btn)
        left.append(mode_box)
        paned.set_start_child(left)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        right.set_margin_top(12); right.set_margin_start(8); right.set_margin_end(12)

        self.key_label = Gtk.Label(label="Key: C Major")
        right.append(self.key_label)

        self.scale_label = Gtk.Label(label="Scale: C D E F G A B")
        self.scale_label.set_xalign(0)
        right.append(self.scale_label)

        self.relative_label = Gtk.Label(label="Relative Minor: A minor")
        self.relative_label.set_xalign(0)
        right.append(self.relative_label)

        right.append(Gtk.Label(label="Chord Progressions:", xalign=0))
        self.prog_label = Gtk.Label(label="")
        self.prog_label.set_xalign(0)
        self.prog_label.set_wrap(True)
        right.append(self.prog_label)

        right.append(Gtk.Label(label="Diatonic Chords:", xalign=0))
        self.chords_label = Gtk.Label(label="")
        self.chords_label.set_xalign(0)
        self.chords_label.set_wrap(True)
        right.append(self.chords_label)

        right.append(Gtk.Label(label="Intervals:", xalign=0))
        self.intervals_label = Gtk.Label(label="")
        self.intervals_label.set_xalign(0)
        self.intervals_label.set_wrap(True)
        right.append(self.intervals_label)

        paned.set_end_child(right)
        self.update_info()

    def on_mode(self, btn, mode):
        if btn.get_active():
            self.mode = mode
            self.update_info()

    def draw_circle(self, area, cr, w, h):
        cx, cy = w / 2, h / 2
        r_outer = min(w, h) * 0.45
        r_inner = r_outer * 0.55
        for i, note in enumerate(CIRCLE):
            angle = -math.pi / 2 + i * 2 * math.pi / 12
            next_angle = angle + 2 * math.pi / 12
            mid_angle = (angle + next_angle) / 2
            if note.replace("b", "").replace("#", "") == self.selected_key.replace("b", "").replace("#", ""):
                cr.set_source_rgb(0.9, 0.6, 0.1)
            else:
                cr.set_source_rgb(0.2, 0.5, 0.8)
            cr.move_to(cx, cy)
            cr.arc(cx, cy, r_outer, angle, next_angle)
            cr.close_path()
            cr.fill_preserve()
            cr.set_source_rgb(1, 1, 1)
            cr.stroke()
            tx = cx + (r_outer + r_inner) / 2 * math.cos(mid_angle)
            ty = cy + (r_outer + r_inner) / 2 * math.sin(mid_angle)
            cr.set_source_rgb(1, 1, 1)
            cr.move_to(tx - 8, ty + 5)
            cr.show_text(note)

        minor_keys = ["Am", "Em", "Bm", "F#m", "C#m", "G#m", "Ebm", "Bbm", "Fm", "Cm", "Gm", "Dm"]
        for i, note in enumerate(minor_keys):
            angle = -math.pi / 2 + i * 2 * math.pi / 12
            next_angle = angle + 2 * math.pi / 12
            mid_angle = (angle + next_angle) / 2
            cr.set_source_rgb(0.15, 0.35, 0.6)
            cr.move_to(cx, cy)
            cr.arc(cx, cy, r_inner, angle, next_angle)
            cr.close_path()
            cr.fill_preserve()
            cr.set_source_rgb(0.8, 0.8, 0.8)
            cr.stroke()
            tx = cx + r_inner * 0.7 * math.cos(mid_angle)
            ty = cy + r_inner * 0.7 * math.sin(mid_angle)
            cr.set_source_rgb(0.9, 0.9, 0.9)
            cr.move_to(tx - 8, ty + 4)
            cr.show_text(note)

    def on_circle_click(self, ctrl, n, x, y):
        w = self.circle_area.get_width()
        h = self.circle_area.get_height()
        cx, cy = w / 2, h / 2
        dx, dy = x - cx, y - cy
        angle = math.atan2(dy, dx) + math.pi / 2
        if angle < 0: angle += 2 * math.pi
        idx = int(angle / (2 * math.pi / 12)) % 12
        self.selected_key = CIRCLE[idx]
        self.update_info()
        self.circle_area.queue_draw()

    def update_info(self):
        key = self.selected_key
        note_idx = NOTES.index(key) if key in NOTES else 0
        scale_intervals = MAJOR_SCALE if self.mode == "Major" else MINOR_SCALE
        scale_notes = [NOTES[(note_idx + i) % 12] for i in scale_intervals]
        self.key_label.set_text(f"Key: {key} {self.mode}")
        self.scale_label.set_text(f"Scale: {' '.join(scale_notes)}")

        if self.mode == "Major":
            rel_idx = (note_idx + 9) % 12
            self.relative_label.set_text(f"Relative Minor: {NOTES[rel_idx]} minor")
        else:
            rel_idx = (note_idx + 3) % 12
            self.relative_label.set_text(f"Relative Major: {NOTES[rel_idx]} Major")

        prog_nums = ["I-IV-V-I", "I-vi-IV-V", "I-V-vi-IV", "ii-V-I"]
        self.prog_label.set_text("Common: " + " | ".join(prog_nums))

        chord_names = []
        for i, (interval, roman) in enumerate(zip(scale_intervals, CHORD_PROG.get(self.mode, []))):
            root = NOTES[(note_idx + interval) % 12]
            chord_names.append(f"{roman}={root}")
        self.chords_label.set_text(", ".join(chord_names))

        interval_names = ["P1", "M2", "M3", "P4", "P5", "M6", "M7"] if self.mode == "Major" else ["P1", "M2", "m3", "P4", "P5", "m6", "m7"]
        pairs = [f"{n}:{i}" for n, i in zip(scale_notes, interval_names)]
        self.intervals_label.set_text(", ".join(pairs))

class MusicTheoryApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.MusicTheory")
    def do_activate(self):
        win = MusicTheoryWindow(self)
        win.present()

def main():
    app = MusicTheoryApp()
    app.run(None)

if __name__ == "__main__":
    main()
