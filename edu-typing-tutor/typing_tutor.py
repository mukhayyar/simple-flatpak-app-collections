#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk
import time, random

SENTENCES = [
    "The quick brown fox jumps over the lazy dog.",
    "Pack my box with five dozen liquor jugs.",
    "How vexingly quick daft zebras jump.",
    "The five boxing wizards jump quickly.",
    "Sphinx of black quartz, judge my vow.",
    "Two driven jocks help fax my big quiz.",
    "The job requires extra pluck and zeal from every young wage earner.",
    "A mad boxer shot a quick, gloved jab to the jaw of his dizzy opponent.",
    "Amazingly few discotheques provide jukeboxes.",
    "We promptly judged antique ivory buckles for the next prize.",
    "Sixty zippers were quickly picked from the woven jute bag.",
    "All questions asked by five watched experts amaze the judge.",
    "Back in my quaint garden jokingly yelled five workmen.",
    "Few black taxis drive up major roads on quiet hazy nights.",
    "The quick onyx goblin jumps over the lazy dwarf.",
]

class TypingTutorWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Typing Tutor")
        self.set_default_size(800, 520)
        self.target_text = ""
        self.start_time = None
        self.wpm_history = []
        self.build_ui()
        self.new_sentence()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(16); vbox.set_margin_bottom(16)
        vbox.set_margin_start(16); vbox.set_margin_end(16)
        self.set_child(vbox)

        title = Gtk.Label(label="Typing Tutor")
        title.set_css_classes(["title"])
        vbox.append(title)

        stats_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        stats_box.set_halign(Gtk.Align.CENTER)
        self.wpm_label = Gtk.Label(label="WPM: 0")
        self.acc_label = Gtk.Label(label="Accuracy: 100%")
        self.time_label = Gtk.Label(label="Time: 0s")
        self.best_label = Gtk.Label(label="Best WPM: 0")
        for lbl in [self.wpm_label, self.acc_label, self.time_label, self.best_label]:
            lbl.set_css_classes(["heading"])
            stats_box.append(lbl)
        vbox.append(stats_box)

        frame = Gtk.Frame(label="Type this text:")
        self.target_view = Gtk.TextView()
        self.target_view.set_editable(False)
        self.target_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.target_view.set_pixels_above_lines(4)
        self.target_buf = self.target_view.get_buffer()
        tt = self.target_buf.get_tag_table()
        correct_tag = Gtk.TextTag.new("correct")
        correct_tag.set_property("foreground", "#98c379")
        tt.add(correct_tag)
        wrong_tag = Gtk.TextTag.new("wrong")
        wrong_tag.set_property("foreground", "#e06c75")
        wrong_tag.set_property("background", "#3e2020")
        tt.add(wrong_tag)
        cursor_tag = Gtk.TextTag.new("cursor")
        cursor_tag.set_property("background", "#61afef")
        cursor_tag.set_property("foreground", "#282c34")
        tt.add(cursor_tag)
        frame.set_child(self.target_view)
        vbox.append(frame)

        input_frame = Gtk.Frame(label="Your input:")
        self.input_entry = Gtk.Entry()
        self.input_entry.set_placeholder_text("Start typing here...")
        self.input_entry.connect("changed", self.on_input_changed)
        input_frame.set_child(self.input_entry)
        vbox.append(input_frame)

        chart_frame = Gtk.Frame(label="WPM History")
        self.chart = Gtk.DrawingArea()
        self.chart.set_size_request(-1, 100)
        self.chart.set_draw_func(self.draw_chart)
        chart_frame.set_child(self.chart)
        vbox.append(chart_frame)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_halign(Gtk.Align.CENTER)
        new_btn = Gtk.Button(label="New Sentence")
        new_btn.connect("clicked", lambda b: self.new_sentence())
        btn_box.append(new_btn)
        vbox.append(btn_box)

        GLib.timeout_add(200, self.update_timer)

    def new_sentence(self):
        self.target_text = random.choice(SENTENCES)
        self.start_time = None
        self.target_buf.set_text(self.target_text)
        self.input_entry.set_text("")
        self.input_entry.grab_focus()
        self.update_highlighting("")

    def on_input_changed(self, entry):
        typed = entry.get_text()
        if typed and self.start_time is None:
            self.start_time = time.time()
        self.update_highlighting(typed)
        if typed == self.target_text:
            self.complete_round(typed)

    def update_highlighting(self, typed):
        buf = self.target_buf
        start = buf.get_start_iter()
        end = buf.get_end_iter()
        buf.remove_all_tags(start, end)
        for i, ch in enumerate(typed):
            if i >= len(self.target_text):
                break
            s = buf.get_iter_at_offset(i)
            e = buf.get_iter_at_offset(i + 1)
            tag = "correct" if ch == self.target_text[i] else "wrong"
            buf.apply_tag_by_name(tag, s, e)
        pos = len(typed)
        if pos < len(self.target_text):
            s = buf.get_iter_at_offset(pos)
            e = buf.get_iter_at_offset(pos + 1)
            buf.apply_tag_by_name("cursor", s, e)

        if self.start_time and typed:
            elapsed = time.time() - self.start_time
            words = len(typed.split())
            wpm = int(words / elapsed * 60) if elapsed > 0 else 0
            correct = sum(1 for a, b in zip(typed, self.target_text) if a == b)
            acc = int(correct / len(typed) * 100) if typed else 100
            self.wpm_label.set_text(f"WPM: {wpm}")
            self.acc_label.set_text(f"Accuracy: {acc}%")

    def update_timer(self):
        if self.start_time:
            elapsed = int(time.time() - self.start_time)
            self.time_label.set_text(f"Time: {elapsed}s")
        return True

    def complete_round(self, typed):
        if not self.start_time:
            return
        elapsed = time.time() - self.start_time
        words = len(self.target_text.split())
        wpm = int(words / elapsed * 60)
        self.wpm_history.append(wpm)
        if self.wpm_history:
            self.best_label.set_text(f"Best WPM: {max(self.wpm_history)}")
        self.chart.queue_draw()
        GLib.timeout_add(500, lambda: self.new_sentence())

    def draw_chart(self, area, cr, w, h):
        cr.set_source_rgb(0.1, 0.1, 0.15)
        cr.rectangle(0, 0, w, h)
        cr.fill()
        if not self.wpm_history:
            return
        mx = max(max(self.wpm_history), 1)
        n = len(self.wpm_history)
        bw = w / max(n, 1)
        colors = [(0.4, 0.6, 0.9)]
        for i, wpm in enumerate(self.wpm_history):
            bh = (wpm / mx) * (h - 20)
            cr.set_source_rgb(0.3, 0.7, 0.5)
            cr.rectangle(i * bw + 1, h - bh - 15, bw - 2, bh)
            cr.fill()
            cr.set_source_rgb(0.9, 0.9, 0.9)
            cr.set_font_size(9)
            cr.move_to(i * bw + 2, h - 2)
            cr.show_text(str(wpm))

class TypingTutorApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.TypingTutor")
    def do_activate(self):
        win = TypingTutorWindow(self); win.present()

def main():
    app = TypingTutorApp(); app.run(None)

if __name__ == "__main__":
    main()
