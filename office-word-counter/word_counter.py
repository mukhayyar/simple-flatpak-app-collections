#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
import re, collections, math

def flesch_score(text):
    sentences = max(1, len(re.split(r"[.!?]+", text)))
    words = len(text.split())
    syllables = sum(max(1, len(re.findall(r"[aeiouy]+", w.lower()))) for w in text.split())
    if words == 0: return 0
    return 206.835 - 1.015*(words/sentences) - 84.6*(syllables/words)

class WordCounterWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app); self.set_title("Word Counter"); self.set_default_size(900,700)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8); vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)
        ctrl = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        open_btn = Gtk.Button(label="Open File"); open_btn.connect("clicked", self.on_open); ctrl.append(open_btn)
        analyze_btn = Gtk.Button(label="Analyze"); analyze_btn.connect("clicked", self.on_analyze); ctrl.append(analyze_btn)
        vbox.append(ctrl)
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL); paned.set_vexpand(True)
        in_scroll = Gtk.ScrolledWindow()
        self.text_view = Gtk.TextView(); self.text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.text_buf = self.text_view.get_buffer(); self.text_buf.connect("changed", self.on_analyze)
        in_scroll.set_child(self.text_view); paned.set_start_child(in_scroll)
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4); right.set_size_request(320,-1)
        right.set_margin_start(6)
        self.stats_view = Gtk.TextView(); self.stats_view.set_editable(False); self.stats_view.set_monospace(True)
        stats_scroll = Gtk.ScrolledWindow(); stats_scroll.set_min_content_height(200); stats_scroll.set_child(self.stats_view); right.append(stats_scroll)
        self.chart = Gtk.DrawingArea(); self.chart.set_size_request(300,200); self.chart.set_draw_func(self.draw_chart); right.append(self.chart)
        paned.set_end_child(right); vbox.append(paned)
        self.top_words = []

    def on_open(self, btn):
        dialog = Gtk.FileDialog(); dialog.open(self, None, self.on_file)
    def on_file(self, dialog, result):
        try:
            f = dialog.open_finish(result)
            if f:
                with open(f.get_path()) as fp: self.text_buf.set_text(fp.read())
        except Exception: pass

    def on_analyze(self, *a):
        text = self.text_buf.get_text(self.text_buf.get_start_iter(), self.text_buf.get_end_iter(), True)
        words = len(text.split()); chars = len(text); chars_nospace = len(text.replace(" ","").replace("\n",""))
        sentences = len(re.split(r"[.!?]+", text))
        paragraphs = len([p for p in text.split("\n\n") if p.strip()])
        reading_time = max(1, words // 200)
        flesch = flesch_score(text)
        word_list = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        common = [w for w in word_list if len(w) > 3]
        counter = collections.Counter(common)
        self.top_words = counter.most_common(20)
        stats = (f"Words: {words}\nCharacters: {chars}\nChars (no spaces): {chars_nospace}\n"
                 f"Sentences: {sentences}\nParagraphs: {paragraphs}\nReading time: ~{reading_time} min\n"
                 f"Flesch score: {flesch:.1f}\n\nTop words:\n" +
                 "\n".join(f"  {w}: {c}" for w,c in self.top_words[:10]))
        self.stats_view.get_buffer().set_text(stats)
        self.chart.queue_draw()

    def draw_chart(self, area, cr, w, h):
        cr.set_source_rgb(0.1,0.1,0.15); cr.rectangle(0,0,w,h); cr.fill()
        if not self.top_words: return
        top = self.top_words[:10]; mx = top[0][1] if top else 1
        bh = (h - 20) / len(top)
        for i, (word, count) in enumerate(top):
            bw = (count/mx)*(w-80); y = i*bh
            cr.set_source_rgb(0.3,0.6,0.9); cr.rectangle(70, y+2, bw, bh-4); cr.fill()
            cr.set_source_rgb(0.9,0.9,0.9); cr.set_font_size(9)
            cr.move_to(2, y+bh*0.7); cr.show_text(word[:10])
            cr.move_to(75+bw, y+bh*0.7); cr.show_text(str(count))

class WordCounterApp(Gtk.Application):
    def __init__(self): super().__init__(application_id="com.pens.WordCounter")
    def do_activate(self): WordCounterWindow(self).present()

def main(): WordCounterApp().run(None)
if __name__ == "__main__": main()
