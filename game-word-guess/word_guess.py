#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk
import random

WORDS = [
    "ABOUT","ABOVE","ABUSE","ACTOR","ACUTE","ADMIT","ADOPT","ADULT","AFTER","AGAIN",
    "AGENT","AGREE","AHEAD","ALARM","ALBUM","ALERT","ALIKE","ALIGN","ALIVE","ALLEY",
    "ALLOW","ALONE","ALONG","ALTER","ANGEL","ANGLE","ANGRY","ANIME","ANNEX","APPLE",
    "APPLY","ARENA","ARGUE","ARISE","ARMOR","ARRAY","ARROW","ARTSY","ASIDE","ASKED",
    "ATTIC","AUDIO","AUDIT","AUGUR","AWFUL","AZURE","BADGE","BASIC","BASIS","BATCH",
    "BEACH","BEARD","BEAST","BEGIN","BEING","BELOW","BENCH","BIBLE","BIRTH","BLACK",
    "BLADE","BLAME","BLAND","BLAST","BLAZE","BLEED","BLEND","BLESS","BLIND","BLOCK",
    "BLOOD","BLOOM","BLOWN","BOARD","BONUS","BOOST","BOUND","BOXER","BRAIN","BRAND",
    "BRAVE","BREAD","BREAK","BREED","BRICK","BRIDE","BRIEF","BRING","BRINK","BROAD",
    "BROKE","BROOD","BRUSH","BUILD","BUILT","BURST","BUYER","CABLE","CAMEL","CAMEO",
    "CANDY","CANON","CARGO","CARRY","CAUSE","CEASE","CHAIN","CHAIR","CHAOS","CHARM",
    "CHASE","CHEAP","CHECK","CHEEK","CHESS","CHEST","CHIEF","CHILD","CHINA","CIVIL",
    "CLAIM","CLASH","CLASS","CLEAN","CLEAR","CLICK","CLIFF","CLIMB","CLING","CLOCK",
    "CLONE","CLOSE","CLOUD","COACH","COAST","COBRA","COMIC","COMMA","COMET","CORAL",
    "COULD","COUNT","COURT","COVER","CRAFT","CRANE","CRASH","CRAZY","CREAM","CREEP",
    "CROSS","CROWD","CROWN","CRUDE","CRUEL","CRUSH","CURVE","CYCLE","DAILY","DANCE",
    "DEATH","DEBUT","DELAY","DELTA","DENSE","DEPOT","DEPTH","DERBY","DEMON","DEVIL",
    "DIRTY","DISCO","DIZZY","DRAMA","DRANK","DRAWN","DREAM","DRESS","DRINK","DRIVE",
    "DRONE","DROVE","DROWN","DUSTY","DWARF","DYING","EAGER","EARLY","EARTH","EIGHT",
    "ELECT","ELITE","EMPTY","ENEMY","ENTRY","EQUAL","EQUIP","ESSAY","EVERY","EXACT",
]

LETTER_COLORS = {"correct": "#538d4e", "present": "#b59f3b", "absent": "#3a3a3c", "unused": "#818384"}

class WordGuessWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Word Guess")
        self.set_default_size(420, 620)
        self.init_game()
        self.build_ui()

    def init_game(self):
        self.secret = random.choice(WORDS)
        self.current_row = 0
        self.current_col = 0
        self.guesses = [[""] * 5 for _ in range(6)]
        self.results = [[""] * 5 for _ in range(6)]
        self.game_done = False
        self.keyboard_state = {}

    def build_ui(self):
        self.set_child(None)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="WORD GUESS", css_classes=["title"]))

        css = Gtk.CssProvider()
        css.load_from_data(b"""
.correct { background-color: #538d4e; color: white; font-weight: bold; font-size: 18px; }
.present { background-color: #b59f3b; color: white; font-weight: bold; font-size: 18px; }
.absent { background-color: #3a3a3c; color: white; font-weight: bold; font-size: 18px; }
.current { background-color: #565758; color: white; font-size: 18px; }
.empty { background-color: #121213; color: #818384; font-size: 18px; border: 2px solid #3a3a3c; }
.key-correct { background-color: #538d4e; color: white; }
.key-present { background-color: #b59f3b; color: white; }
.key-absent { background-color: #3a3a3c; color: white; }
""")
        Gtk.StyleContext.add_provider_for_display(self.get_display(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        board = Gtk.Grid()
        board.set_row_spacing(4); board.set_column_spacing(4)
        board.set_halign(Gtk.Align.CENTER)
        self.cells = []
        for r in range(6):
            row = []
            for c in range(5):
                lbl = Gtk.Label(label=" ", css_classes=["empty"])
                lbl.set_size_request(52, 52)
                board.attach(lbl, c, r, 1, 1)
                row.append(lbl)
            self.cells.append(row)
        vbox.append(board)

        self.status_label = Gtk.Label(label="Type a 5-letter word and press Enter")
        vbox.append(self.status_label)

        keyboard_rows = ["QWERTYUIOP", "ASDFGHJKL", "ENTER|ZXCVBNM|DEL"]
        self.key_buttons = {}
        for kr in keyboard_rows:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            row.set_halign(Gtk.Align.CENTER)
            for key in kr.split("|"):
                if key == "ENTER":
                    btn = Gtk.Button(label="Enter")
                    btn.connect("clicked", self.on_enter)
                elif key == "DEL":
                    btn = Gtk.Button(label="Del")
                    btn.connect("clicked", self.on_delete)
                else:
                    btn = Gtk.Button(label=key)
                    for ch in key:
                        self.key_buttons[ch] = btn
                    btn.connect("clicked", self.on_key_btn, key)
                row.append(btn)
            vbox.append(row)

        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self.on_key_press)
        self.add_controller(key_ctrl)

        new_btn = Gtk.Button(label="New Game")
        new_btn.connect("clicked", self.on_new_game)
        vbox.append(new_btn)

    def on_key_press(self, ctrl, keyval, keycode, state):
        if self.game_done:
            return True
        name = Gdk.keyval_name(keyval)
        if name and len(name) == 1 and name.upper() in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            self.type_letter(name.upper())
        elif keyval == Gdk.KEY_Return:
            self.on_enter(None)
        elif keyval == Gdk.KEY_BackSpace:
            self.on_delete(None)
        return True

    def on_key_btn(self, btn, key):
        self.type_letter(key)

    def type_letter(self, ch):
        if self.game_done or self.current_col >= 5:
            return
        self.guesses[self.current_row][self.current_col] = ch
        self.cells[self.current_row][self.current_col].set_label(ch)
        self.cells[self.current_row][self.current_col].set_css_classes(["current"])
        self.current_col += 1

    def on_delete(self, btn):
        if self.current_col > 0:
            self.current_col -= 1
            self.guesses[self.current_row][self.current_col] = ""
            self.cells[self.current_row][self.current_col].set_label(" ")
            self.cells[self.current_row][self.current_col].set_css_classes(["empty"])

    def on_enter(self, btn):
        if self.game_done or self.current_col < 5:
            if self.current_col < 5:
                self.status_label.set_text("Type all 5 letters first!")
            return
        guess = "".join(self.guesses[self.current_row])
        if guess not in WORDS:
            self.status_label.set_text("Not a recognized word, try again")
            return
        result = self.check_guess(guess, self.secret)
        self.results[self.current_row] = result
        for c, (letter, res) in enumerate(zip(guess, result)):
            self.cells[self.current_row][c].set_label(letter)
            self.cells[self.current_row][c].set_css_classes([res])
            if letter in self.key_buttons:
                old = self.keyboard_state.get(letter, "")
                priority = {"correct": 3, "present": 2, "absent": 1, "": 0}
                if priority.get(res, 0) > priority.get(old, 0):
                    self.keyboard_state[letter] = res
                    self.key_buttons[letter].set_css_classes([f"key-{res}"])
        if guess == self.secret:
            self.status_label.set_text(f"Correct! You got it in {self.current_row + 1} tries!")
            self.game_done = True
        else:
            self.current_row += 1
            self.current_col = 0
            if self.current_row >= 6:
                self.status_label.set_text(f"Game over! The word was: {self.secret}")
                self.game_done = True
            else:
                self.status_label.set_text(f"Try {self.current_row + 1}/6")

    def check_guess(self, guess, secret):
        result = ["absent"] * 5
        secret_left = list(secret)
        for i, (g, s) in enumerate(zip(guess, secret)):
            if g == s:
                result[i] = "correct"
                secret_left[i] = None
        for i, g in enumerate(guess):
            if result[i] == "correct":
                continue
            if g in secret_left:
                result[i] = "present"
                secret_left[secret_left.index(g)] = None
        return result

    def on_new_game(self, btn):
        self.init_game()
        self.build_ui()

class WordGuessApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.WordGuess")
    def do_activate(self):
        win = WordGuessWindow(self)
        win.present()

def main():
    app = WordGuessApp()
    app.run(None)

if __name__ == "__main__":
    main()
