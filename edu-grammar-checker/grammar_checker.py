#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import re

COMMON_ERRORS = [
    (r'\bthere\b', r'\btheir\b', "Possible confusion: 'there' vs 'their'"),
    (r'\btheir\b', r'\bthere\b', "Possible confusion: 'their' vs 'there'"),
    (r'\bits\b', r"\bit's\b", "Possible confusion: 'its' vs 'it's'"),
    (r"\bit's\b", r'\bits\b', "Possible confusion: 'it's' vs 'its'"),
    (r'\byour\b', r"\byou're\b", "Possible confusion: 'your' vs 'you're'"),
    (r"\byou're\b", r'\byour\b', "Possible confusion: 'you're' vs 'your'"),
    (r'\bthen\b', r'\bthan\b', "Possible confusion: 'then' vs 'than'"),
    (r'\bthan\b', r'\bthen\b', "Possible confusion: 'than' vs 'then'"),
    (r'\baffect\b', r'\beffect\b', "Possible confusion: 'affect' vs 'effect'"),
    (r'\blose\b', r'\bloose\b', "Possible confusion: 'lose' vs 'loose'"),
    (r'\bprincipal\b', r'\bprinciple\b', "Possible confusion: 'principal' vs 'principle'"),
    (r'\bcomplement\b', r'\bcompliment\b', "Possible confusion: 'complement' vs 'compliment'"),
    (r'\bstationary\b', r'\bstationery\b', "Possible confusion: 'stationary' vs 'stationery'"),
    (r'\badvice\b', r'\badvise\b', "Possible confusion: 'advice' vs 'advise'"),
    (r'\baccept\b', r'\bexcept\b', "Possible confusion: 'accept' vs 'except'"),
]

DOUBLE_SPACE = re.compile(r'  +')
DOUBLE_PUNCT = re.compile(r'([.!?,;:])\s*\1')
SENT_CAPITAL = re.compile(r'(?:^|[.!?]\s+)([a-z])')
DOUBLE_WORDS = re.compile(r'\b(\w+)\s+\1\b', re.IGNORECASE)

class GrammarCheckerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Grammar Checker")
        self.set_default_size(800, 560)
        self.build_ui()

    def build_ui(self):
        hpaned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_child(hpaned)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        left.set_margin_top(8); left.set_margin_start(8); left.set_margin_bottom(8)
        left.append(Gtk.Label(label="Enter your text:", xalign=0))
        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        self.text_view = Gtk.TextView()
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.text_buf = self.text_view.get_buffer()
        tt = self.text_buf.get_tag_table()
        warn_tag = Gtk.TextTag.new("warning")
        warn_tag.set_property("background", "#5a4020")
        warn_tag.set_property("underline", 2)
        tt.add(warn_tag)
        err_tag = Gtk.TextTag.new("error")
        err_tag.set_property("background", "#5a2020")
        err_tag.set_property("underline", 2)
        tt.add(err_tag)
        self.text_buf.connect("changed", self.on_text_changed)
        scroll.set_child(self.text_view)
        left.append(scroll)
        stats_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.word_label = Gtk.Label(label="Words: 0")
        self.char_label = Gtk.Label(label="Chars: 0")
        self.sent_label = Gtk.Label(label="Sentences: 0")
        for lbl in [self.word_label, self.char_label, self.sent_label]:
            stats_box.append(lbl)
        left.append(stats_box)
        check_btn = Gtk.Button(label="Check Grammar")
        check_btn.connect("clicked", self.on_check)
        left.append(check_btn)
        hpaned.set_start_child(left)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        right.set_margin_top(8); right.set_margin_end(8); right.set_margin_bottom(8); right.set_margin_start(4)
        right.append(Gtk.Label(label="Issues Found:", xalign=0))
        scroll2 = Gtk.ScrolledWindow(); scroll2.set_vexpand(True)
        self.issues_view = Gtk.TextView()
        self.issues_view.set_editable(False)
        self.issues_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.issues_buf = self.issues_view.get_buffer()
        scroll2.set_child(self.issues_view)
        right.append(scroll2)

        right.append(Gtk.Label(label="Suggestions:", xalign=0))
        scroll3 = Gtk.ScrolledWindow()
        scroll3.set_min_content_height(100)
        self.suggestions_view = Gtk.TextView()
        self.suggestions_view.set_editable(False)
        self.suggestions_view.set_wrap_mode(Gtk.WrapMode.WORD)
        scroll3.set_child(self.suggestions_view)
        right.append(scroll3)
        hpaned.set_end_child(right)

        sample = ("I seen the movie yesterday. Their going to the store tomorrow. "
                  "The the cat sat on the mat. She adviced me to take the advise. "
                  "Its a beautiful day. You're bag is over there. "
                  "He is more taller then me.  Double  spaces here.")
        self.text_buf.set_text(sample)

    def on_text_changed(self, buf):
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
        words = len(text.split())
        chars = len(text)
        sentences = len([s for s in re.split(r'[.!?]+', text) if s.strip()])
        self.word_label.set_text(f"Words: {words}")
        self.char_label.set_text(f"Chars: {chars}")
        self.sent_label.set_text(f"Sentences: {sentences}")

    def on_check(self, btn):
        buf = self.text_buf
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
        buf.remove_all_tags(buf.get_start_iter(), buf.get_end_iter())

        issues = []

        for m in DOUBLE_WORDS.finditer(text):
            start = buf.get_iter_at_offset(m.start())
            end = buf.get_iter_at_offset(m.end())
            buf.apply_tag_by_name("error", start, end)
            issues.append(f"[Repeated word] '{m.group()}' at position {m.start()}")

        for m in DOUBLE_SPACE.finditer(text):
            start = buf.get_iter_at_offset(m.start())
            end = buf.get_iter_at_offset(m.end())
            buf.apply_tag_by_name("warning", start, end)
            issues.append(f"[Double space] at position {m.start()}")

        for m in SENT_CAPITAL.finditer(text):
            pos = m.start(1)
            start = buf.get_iter_at_offset(pos)
            end = buf.get_iter_at_offset(pos + 1)
            buf.apply_tag_by_name("error", start, end)
            issues.append(f"[Capitalize] sentence starts with lowercase at position {pos}")

        for patt, _, desc in COMMON_ERRORS:
            for m in re.finditer(patt, text, re.IGNORECASE):
                start = buf.get_iter_at_offset(m.start())
                end = buf.get_iter_at_offset(m.end())
                buf.apply_tag_by_name("warning", start, end)
                issues.append(f"[Homophones] {desc} at position {m.start()}: '{m.group()}'")

        if issues:
            self.issues_buf.set_text(f"Found {len(issues)} issue(s):\n\n" + "\n".join(issues))
        else:
            self.issues_buf.set_text("No issues found!")

        suggestions = [
            "• Check homophones in context (there/their/they're, etc.)",
            "• Ensure sentences start with capital letters",
            "• Remove duplicate words and extra spaces",
            "• Use commas to separate clauses",
            "• Avoid run-on sentences",
            "• Use active voice when possible",
        ]
        self.suggestions_view.get_buffer().set_text("\n".join(suggestions))

class GrammarCheckerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.GrammarChecker")
    def do_activate(self):
        win = GrammarCheckerWindow(self); win.present()

def main():
    app = GrammarCheckerApp(); app.run(None)

if __name__ == "__main__":
    main()
