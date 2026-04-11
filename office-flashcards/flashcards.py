#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
import json, os, random, datetime

DATA_DIR = os.path.expanduser("~/.local/share/com.pens.Flashcards")
DATA_FILE = os.path.join(DATA_DIR, "decks.json")

class FlashcardsWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app); self.set_title("Flashcards"); self.set_default_size(800,640)
        os.makedirs(DATA_DIR, exist_ok=True)
        self.decks = self.load(); self.current_deck = None; self.study_cards = []; self.study_idx = 0; self.showing_front = True
        self.build_ui(); self.refresh_decks()

    def load(self):
        try:
            with open(DATA_FILE) as f: return json.load(f)
        except Exception: return {}
    def save(self):
        with open(DATA_FILE, "w") as f: json.dump(self.decks, f)

    def build_ui(self):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0); self.set_child(hbox)
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4); left.set_size_request(220,-1)
        left.set_margin_top(6); left.set_margin_start(6); left.set_margin_bottom(6)
        deck_input = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.deck_entry = Gtk.Entry(); self.deck_entry.set_placeholder_text("New deck name..."); self.deck_entry.set_hexpand(True)
        add_deck_btn = Gtk.Button(label="+"); add_deck_btn.connect("clicked", self.on_add_deck)
        deck_input.append(self.deck_entry); deck_input.append(add_deck_btn); left.append(deck_input)
        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        self.deck_list = Gtk.ListBox(); self.deck_list.connect("row-selected", self.on_deck_selected); scroll.set_child(self.deck_list); left.append(scroll)
        hbox.append(left); hbox.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        right.set_hexpand(True); right.set_margin_top(8); right.set_margin_start(8); right.set_margin_end(8); right.set_margin_bottom(8)
        
        add_card_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.front_entry = Gtk.Entry(); self.front_entry.set_placeholder_text("Front..."); self.front_entry.set_hexpand(True)
        self.back_entry = Gtk.Entry(); self.back_entry.set_placeholder_text("Back..."); self.back_entry.set_hexpand(True)
        add_card_btn = Gtk.Button(label="Add Card"); add_card_btn.connect("clicked", self.on_add_card)
        add_card_box.append(self.front_entry); add_card_box.append(self.back_entry); add_card_box.append(add_card_btn)
        right.append(add_card_box)
        
        study_btn = Gtk.Button(label="Study Deck"); study_btn.connect("clicked", self.on_start_study); right.append(study_btn)
        
        self.card_frame = Gtk.Frame(label="Study Card")
        card_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8); card_vbox.set_margin_top(20); card_vbox.set_margin_bottom(20); card_vbox.set_margin_start(20); card_vbox.set_margin_end(20)
        self.card_label = Gtk.Label(label="Start studying to see cards")
        css = Gtk.CssProvider(); css.load_from_data(b".card-text { font-size: 24px; }")
        Gtk.StyleContext.add_provider_for_display(self.get_display(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.card_label.set_css_classes(["card-text"]); self.card_label.set_wrap(True)
        self.card_label.set_size_request(-1, 120)
        card_vbox.append(self.card_label)
        flip_btn = Gtk.Button(label="Flip Card"); flip_btn.connect("clicked", self.on_flip); card_vbox.append(flip_btn)
        rating_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8); rating_box.set_halign(Gtk.Align.CENTER)
        for label, score in [("Hard ×", 1), ("OK ✓", 2), ("Easy ✓✓", 3)]:
            btn = Gtk.Button(label=label); btn.connect("clicked", self.on_rate, score); rating_box.append(btn)
        card_vbox.append(rating_box)
        self.card_frame.set_child(card_vbox); right.append(self.card_frame)
        
        self.stats_label = Gtk.Label(label="No deck selected"); right.append(self.stats_label)
        
        cards_frame = Gtk.Frame(label="Cards in Deck")
        cards_scroll = Gtk.ScrolledWindow(); cards_scroll.set_min_content_height(100)
        self.cards_list = Gtk.ListBox(); cards_scroll.set_child(self.cards_list); cards_frame.set_child(cards_scroll); right.append(cards_frame)
        hbox.append(right)

    def refresh_decks(self):
        while self.deck_list.get_row_at_index(0): self.deck_list.remove(self.deck_list.get_row_at_index(0))
        for name in self.decks:
            row = Gtk.ListBoxRow()
            lbl = Gtk.Label(label=f"{name} ({len(self.decks[name])} cards)", xalign=0); lbl.set_margin_start(6); lbl.set_margin_top(3); lbl.set_margin_bottom(3)
            row.set_child(lbl); row._deck_name = name; self.deck_list.append(row)

    def on_add_deck(self, btn):
        name = self.deck_entry.get_text().strip()
        if name and name not in self.decks:
            self.decks[name] = []; self.save(); self.refresh_decks(); self.deck_entry.set_text("")

    def on_deck_selected(self, listbox, row):
        if row: self.current_deck = row._deck_name; self.refresh_cards()

    def refresh_cards(self):
        while self.cards_list.get_row_at_index(0): self.cards_list.remove(self.cards_list.get_row_at_index(0))
        if not self.current_deck: return
        deck = self.decks[self.current_deck]
        for i, card in enumerate(deck):
            row = Gtk.ListBoxRow()
            lbl = Gtk.Label(label=f"Q: {card['front'][:30]} → A: {card['back'][:30]}", xalign=0); lbl.set_margin_start(6); lbl.set_margin_top(2); lbl.set_margin_bottom(2)
            row.set_child(lbl); self.cards_list.append(row)
        count = len(deck)
        self.stats_label.set_text(f"Deck: {self.current_deck} — {count} cards")

    def on_add_card(self, btn):
        if not self.current_deck: return
        front = self.front_entry.get_text().strip(); back = self.back_entry.get_text().strip()
        if front and back:
            self.decks[self.current_deck].append({"front": front, "back": back, "ease": 2, "due": 0})
            self.save(); self.front_entry.set_text(""); self.back_entry.set_text(""); self.refresh_cards()

    def on_start_study(self, btn):
        if not self.current_deck: return
        now = datetime.date.today().toordinal()
        deck = self.decks[self.current_deck]
        due = [c for c in deck if c.get("due", 0) <= now]
        self.study_cards = due if due else deck[:]
        random.shuffle(self.study_cards); self.study_idx = 0; self.showing_front = True
        self.show_card()

    def show_card(self):
        if not self.study_cards or self.study_idx >= len(self.study_cards):
            self.card_label.set_text("Done! All cards reviewed."); return
        card = self.study_cards[self.study_idx]
        self.showing_front = True; self.card_label.set_text(f"Q: {card['front']}")

    def on_flip(self, btn):
        if not self.study_cards or self.study_idx >= len(self.study_cards): return
        card = self.study_cards[self.study_idx]
        if self.showing_front:
            self.showing_front = False; self.card_label.set_text(f"A: {card['back']}")
        else:
            self.showing_front = True; self.card_label.set_text(f"Q: {card['front']}")

    def on_rate(self, btn, score):
        if not self.study_cards or self.study_idx >= len(self.study_cards): return
        card = self.study_cards[self.study_idx]
        delay = {1: 1, 2: 3, 3: 7}.get(score, 1)
        card["due"] = datetime.date.today().toordinal() + delay
        card["ease"] = max(1, min(4, card.get("ease", 2) + (score - 2)))
        self.save(); self.study_idx += 1; self.show_card()

class FlashcardsApp(Gtk.Application):
    def __init__(self): super().__init__(application_id="com.pens.Flashcards")
    def do_activate(self): FlashcardsWindow(self).present()

def main(): FlashcardsApp().run(None)
if __name__ == "__main__": main()
