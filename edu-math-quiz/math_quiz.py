#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import random, time

class MathQuizWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Math Quiz")
        self.set_default_size(500, 480)
        self.score = 0
        self.total = 0
        self.streak = 0
        self.best_streak = 0
        self.difficulty = "medium"
        self.op = "+"
        self.q_start = None
        self.build_ui()
        self.new_question()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_top(20); vbox.set_margin_bottom(20)
        vbox.set_margin_start(30); vbox.set_margin_end(30)
        self.set_child(vbox)

        diff_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        diff_box.set_halign(Gtk.Align.CENTER)
        diff_box.append(Gtk.Label(label="Difficulty:"))
        diff_combo = Gtk.ComboBoxText()
        for d in ["easy", "medium", "hard"]:
            diff_combo.append_text(d)
        diff_combo.set_active(1)
        diff_combo.connect("changed", lambda c: setattr(self, "difficulty", c.get_active_text()))
        diff_box.append(diff_combo)

        diff_box.append(Gtk.Label(label="Operation:"))
        op_combo = Gtk.ComboBoxText()
        for op in ["+", "-", "×", "÷", "mixed"]:
            op_combo.append_text(op)
        op_combo.set_active(4)
        op_combo.connect("changed", self.on_op_changed)
        diff_box.append(op_combo)
        vbox.append(diff_box)

        stats_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        stats_box.set_halign(Gtk.Align.CENTER)
        self.score_label = Gtk.Label(label="Score: 0/0")
        self.streak_label = Gtk.Label(label="Streak: 0")
        self.best_label = Gtk.Label(label="Best: 0")
        self.timer_label = Gtk.Label(label="Time: --")
        for lbl in [self.score_label, self.streak_label, self.best_label, self.timer_label]:
            lbl.set_css_classes(["heading"])
            stats_box.append(lbl)
        vbox.append(stats_box)

        self.question_label = Gtk.Label(label="")
        self.question_label.set_markup("<span font='32' weight='bold'>?</span>")
        self.question_label.set_margin_top(20)
        self.question_label.set_margin_bottom(20)
        vbox.append(self.question_label)

        self.mc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.mc_box.set_halign(Gtk.Align.CENTER)
        self.mc_btns = []
        for i in range(4):
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            row.set_halign(Gtk.Align.CENTER)
            btn = Gtk.Button()
            btn.set_size_request(120, 44)
            btn.connect("clicked", self.on_answer, i)
            self.mc_btns.append(btn)
            row.append(btn)
            if i % 2 == 1 and i > 0:
                pass
            self.mc_box.append(row)
        vbox.append(self.mc_box)

        self.feedback_label = Gtk.Label(label="")
        self.feedback_label.set_markup("<span font='16'> </span>")
        vbox.append(self.feedback_label)

        next_btn = Gtk.Button(label="Next Question →")
        next_btn.set_halign(Gtk.Align.CENTER)
        next_btn.connect("clicked", lambda b: self.new_question())
        vbox.append(next_btn)

        GLib.timeout_add(200, self.update_timer)

    def on_op_changed(self, combo):
        self.op = combo.get_active_text()

    def gen_nums(self):
        d = self.difficulty
        if d == "easy":
            return random.randint(1, 10), random.randint(1, 10)
        elif d == "medium":
            return random.randint(1, 50), random.randint(1, 50)
        else:
            return random.randint(1, 200), random.randint(1, 200)

    def new_question(self):
        ops = ["+", "-", "×", "÷"] if self.op == "mixed" else [self.op]
        op = random.choice(ops)
        a, b = self.gen_nums()
        if op == "-" and a < b:
            a, b = b, a
        if op == "÷":
            b = max(1, b % 12 + 1)
            a = a // b * b + b
        self.correct_answer = eval(f"{a}{op.replace('×','*').replace('÷','/')}{b}")
        if op == "÷":
            self.correct_answer = a // b
        self.question_label.set_markup(f"<span font='32' weight='bold'>{a} {op} {b} = ?</span>")
        self.feedback_label.set_markup("<span font='16'> </span>")
        wrong_answers = set()
        while len(wrong_answers) < 3:
            offset = random.choice([-10,-5,-3,-2,-1,1,2,3,5,10])
            w = self.correct_answer + offset
            if w != self.correct_answer and w not in wrong_answers:
                wrong_answers.add(w)
        choices = list(wrong_answers) + [self.correct_answer]
        random.shuffle(choices)
        for i, btn in enumerate(self.mc_btns):
            btn.set_label(str(choices[i]))
            btn._value = choices[i]
            btn.set_sensitive(True)
            css = Gtk.CssProvider()
            css.load_from_data(b"button { }")
            btn.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.q_start = time.time()

    def on_answer(self, btn, idx):
        chosen = btn._value
        self.total += 1
        elapsed = time.time() - self.q_start if self.q_start else 0
        for b in self.mc_btns:
            b.set_sensitive(False)
        if chosen == self.correct_answer:
            self.score += 1
            self.streak += 1
            if self.streak > self.best_streak:
                self.best_streak = self.streak
            self.feedback_label.set_markup(f"<span font='16' foreground='#98c379'>✓ Correct! ({elapsed:.1f}s)</span>")
            css = Gtk.CssProvider()
            css.load_from_data(b"button { background: #2d5a2d; }")
            btn.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        else:
            self.streak = 0
            self.feedback_label.set_markup(f"<span font='16' foreground='#e06c75'>✗ Wrong! Answer: {self.correct_answer}</span>")
            css = Gtk.CssProvider()
            css.load_from_data(b"button { background: #5a2d2d; }")
            btn.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            for b in self.mc_btns:
                if b._value == self.correct_answer:
                    css2 = Gtk.CssProvider()
                    css2.load_from_data(b"button { background: #2d5a2d; }")
                    b.get_style_context().add_provider(css2, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        pct = int(self.score / self.total * 100) if self.total else 0
        self.score_label.set_text(f"Score: {self.score}/{self.total} ({pct}%)")
        self.streak_label.set_text(f"Streak: {self.streak}")
        self.best_label.set_text(f"Best: {self.best_streak}")

    def update_timer(self):
        if self.q_start:
            elapsed = time.time() - self.q_start
            self.timer_label.set_text(f"Time: {elapsed:.1f}s")
        return True

class MathQuizApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.MathQuiz")
    def do_activate(self):
        win = MathQuizWindow(self); win.present()

def main():
    app = MathQuizApp(); app.run(None)

if __name__ == "__main__":
    main()
