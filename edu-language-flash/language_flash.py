#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import json, os, random, time

DATA_DIR = os.path.expanduser("~/.local/share/com.pens.LanguageFlash")
DATA_FILE = os.path.join(DATA_DIR, "cards.json")

SAMPLE_DECKS = {
    "Spanish Basics": [
        {"front": "Hello", "back": "Hola"}, {"front": "Goodbye", "back": "Adiós"},
        {"front": "Thank you", "back": "Gracias"}, {"front": "Please", "back": "Por favor"},
        {"front": "Yes", "back": "Sí"}, {"front": "No", "back": "No"},
        {"front": "Good morning", "back": "Buenos días"}, {"front": "Good night", "back": "Buenas noches"},
        {"front": "Water", "back": "Agua"}, {"front": "Food", "back": "Comida"},
    ],
    "French Basics": [
        {"front": "Hello", "back": "Bonjour"}, {"front": "Goodbye", "back": "Au revoir"},
        {"front": "Thank you", "back": "Merci"}, {"front": "Please", "back": "S'il vous plaît"},
        {"front": "Yes", "back": "Oui"}, {"front": "No", "back": "Non"},
        {"front": "Cat", "back": "Chat"}, {"front": "Dog", "back": "Chien"},
        {"front": "Book", "back": "Livre"}, {"front": "House", "back": "Maison"},
    ],
    "Japanese Hiragana": [
        {"front": "あ (a)", "back": "a"}, {"front": "い (i)", "back": "i"},
        {"front": "う (u)", "back": "u"}, {"front": "え (e)", "back": "e"},
        {"front": "お (o)", "back": "o"}, {"front": "か (ka)", "back": "ka"},
        {"front": "き (ki)", "back": "ki"}, {"front": "く (ku)", "back": "ku"},
        {"front": "け (ke)", "back": "ke"}, {"front": "こ (ko)", "back": "ko"},
    ],
}

class LanguageFlashWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Language Flashcards")
        self.set_default_size(640, 520)
        os.makedirs(DATA_DIR, exist_ok=True)
        self.data = self.load_data()
        self.current_deck = None
        self.cards = []
        self.index = 0
        self.showing_back = False
        self.correct = 0
        self.total_shown = 0
        self.build_ui()
        self.refresh_decks()

    def load_data(self):
        try:
            with open(DATA_FILE) as f:
                return json.load(f)
        except Exception:
            return {"decks": SAMPLE_DECKS}

    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump(self.data, f)

    def build_ui(self):
        hpaned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_child(hpaned)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        left.set_size_request(200, -1)
        left.set_margin_top(8); left.set_margin_start(8); left.set_margin_bottom(8)

        left.append(Gtk.Label(label="Decks:", xalign=0))
        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        self.deck_list = Gtk.ListBox()
        self.deck_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.deck_list.connect("row-selected", self.on_deck_selected)
        scroll.set_child(self.deck_list)
        left.append(scroll)

        new_deck_entry = Gtk.Entry()
        new_deck_entry.set_placeholder_text("New deck name...")
        left.append(new_deck_entry)
        add_btn = Gtk.Button(label="+ Add Deck")
        add_btn.connect("clicked", lambda b: self.add_deck(new_deck_entry))
        left.append(add_btn)
        hpaned.set_start_child(left)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        right.set_margin_top(8); right.set_margin_end(8); right.set_margin_bottom(8); right.set_margin_start(4)

        self.progress_label = Gtk.Label(label="Select a deck to start")
        right.append(self.progress_label)

        self.card_frame = Gtk.Frame()
        self.card_btn = Gtk.Button()
        self.card_btn.set_size_request(-1, 180)
        self.card_btn.connect("clicked", self.on_flip)
        self.card_label = Gtk.Label(label="Select a deck")
        self.card_label.set_wrap(True)
        self.card_label.set_markup("<span font='24'>Select a deck</span>")
        self.card_btn.set_child(self.card_label)
        self.card_frame.set_child(self.card_btn)
        right.append(self.card_frame)

        self.hint_label = Gtk.Label(label="Click card to flip")
        right.append(self.hint_label)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_halign(Gtk.Align.CENTER)
        wrong_btn = Gtk.Button(label="✗ Wrong")
        wrong_btn.connect("clicked", lambda b: self.on_rate(False))
        correct_btn = Gtk.Button(label="✓ Correct")
        correct_btn.connect("clicked", lambda b: self.on_rate(True))
        shuffle_btn = Gtk.Button(label="⟳ Shuffle")
        shuffle_btn.connect("clicked", lambda b: self.shuffle_deck())
        btn_box.append(wrong_btn); btn_box.append(correct_btn); btn_box.append(shuffle_btn)
        right.append(btn_box)

        add_frame = Gtk.Frame(label="Add Card to Current Deck")
        add_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        add_box.set_margin_top(4); add_box.set_margin_start(4); add_box.set_margin_end(4); add_box.set_margin_bottom(4)
        self.front_entry = Gtk.Entry(); self.front_entry.set_placeholder_text("Front")
        self.back_entry = Gtk.Entry(); self.back_entry.set_placeholder_text("Back"); self.back_entry.set_hexpand(True)
        add_card_btn = Gtk.Button(label="Add")
        add_card_btn.connect("clicked", self.on_add_card)
        add_box.append(self.front_entry); add_box.append(self.back_entry); add_box.append(add_card_btn)
        add_frame.set_child(add_box)
        right.append(add_frame)

        hpaned.set_end_child(right)

    def refresh_decks(self):
        while self.deck_list.get_row_at_index(0):
            self.deck_list.remove(self.deck_list.get_row_at_index(0))
        for name in self.data["decks"]:
            row = Gtk.ListBoxRow()
            n = len(self.data["decks"][name])
            lbl = Gtk.Label(label=f"{name} ({n})", xalign=0)
            lbl.set_margin_start(6); lbl.set_margin_top(4); lbl.set_margin_bottom(4)
            row.set_child(lbl)
            row._deck_name = name
            self.deck_list.append(row)

    def on_deck_selected(self, listbox, row):
        if row:
            self.current_deck = row._deck_name
            self.cards = list(self.data["decks"][self.current_deck])
            self.index = 0
            self.correct = 0
            self.total_shown = 0
            self.showing_back = False
            self.show_card()

    def show_card(self):
        if not self.cards:
            self.card_label.set_markup("<span font='20'>No cards in deck</span>")
            return
        self.index = self.index % len(self.cards)
        card = self.cards[self.index]
        side = "back" if self.showing_back else "front"
        text = card[side]
        self.card_label.set_markup(f"<span font='24'>{GLib.markup_escape_text(text)}</span>")
        self.hint_label.set_text("(showing back — rate yourself)" if self.showing_back else "(showing front — click to see answer)")
        self.progress_label.set_text(f"{self.current_deck}  |  Card {self.index+1}/{len(self.cards)}  |  ✓ {self.correct}/{self.total_shown}")

    def on_flip(self, btn):
        self.showing_back = not self.showing_back
        self.show_card()

    def on_rate(self, correct):
        if self.showing_back:
            self.total_shown += 1
            if correct:
                self.correct += 1
            self.index += 1
            self.showing_back = False
            self.show_card()

    def shuffle_deck(self):
        if self.cards:
            random.shuffle(self.cards)
            self.index = 0
            self.showing_back = False
            self.show_card()

    def add_deck(self, entry):
        name = entry.get_text().strip()
        if name and name not in self.data["decks"]:
            self.data["decks"][name] = []
            self.save_data()
            self.refresh_decks()
            entry.set_text("")

    def on_add_card(self, btn):
        if not self.current_deck:
            return
        front = self.front_entry.get_text().strip()
        back = self.back_entry.get_text().strip()
        if front and back:
            self.data["decks"][self.current_deck].append({"front": front, "back": back})
            self.save_data()
            self.cards = list(self.data["decks"][self.current_deck])
            self.front_entry.set_text("")
            self.back_entry.set_text("")
            self.refresh_decks()

class LanguageFlashApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.LanguageFlash")
    def do_activate(self):
        win = LanguageFlashWindow(self); win.present()

def main():
    app = LanguageFlashApp(); app.run(None)

if __name__ == "__main__":
    main()
