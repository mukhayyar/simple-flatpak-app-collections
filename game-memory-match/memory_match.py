#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib
import random, time

EMOJIS = ["🍕", "🚀", "🎸", "🌈", "🦊", "🎯", "🍀", "⚡", "🎃", "🌺",
          "🦋", "🎭", "🍦", "🎪", "🦄", "🌙", "🎨", "🎵", "🏆", "🌊"]

class MemoryMatchWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Memory Match")
        self.set_default_size(600, 620)
        self.grid_size = 4
        self.init_game()
        self.build_ui()

    def init_game(self):
        n = self.grid_size
        pairs = EMOJIS[:n*n//2] * 2
        random.shuffle(pairs)
        self.cards = pairs
        self.revealed = [False] * (n * n)
        self.matched = [False] * (n * n)
        self.flipped = []
        self.moves = 0
        self.start_time = None
        self.elapsed = 0
        self.done = False
        self.lock = False

    def build_ui(self):
        self.set_child(None)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.moves_label = Gtk.Label(label="Moves: 0")
        self.time_label = Gtk.Label(label="Time: 0s")
        top.append(self.moves_label); top.append(self.time_label)

        diff_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        for label, size in [("4×4", 4), ("6×6", 6)]:
            btn = Gtk.Button(label=label)
            btn.connect("clicked", self.on_difficulty, size)
            diff_box.append(btn)
        top.append(diff_box)

        new_btn = Gtk.Button(label="New Game")
        new_btn.connect("clicked", self.on_new_game)
        top.append(new_btn)
        vbox.append(top)

        n = self.grid_size
        cell = min(80, 540 // n)
        grid = Gtk.Grid()
        grid.set_row_spacing(4); grid.set_column_spacing(4)
        grid.set_halign(Gtk.Align.CENTER)
        self.card_buttons = []
        for i in range(n * n):
            btn = Gtk.Button(label="?")
            btn.set_size_request(cell, cell)
            btn.connect("clicked", self.on_card_click, i)
            grid.attach(btn, i % n, i // n, 1, 1)
            self.card_buttons.append(btn)
        vbox.append(grid)

        self.status_label = Gtk.Label(label="Find all matching pairs!")
        vbox.append(self.status_label)

        self.timer_id = GLib.timeout_add(1000, self.tick_timer)

    def on_difficulty(self, btn, size):
        self.grid_size = size
        if hasattr(self, 'timer_id'):
            GLib.source_remove(self.timer_id)
        self.init_game()
        self.build_ui()

    def on_new_game(self, btn):
        if hasattr(self, 'timer_id'):
            GLib.source_remove(self.timer_id)
        self.init_game()
        self.build_ui()

    def on_card_click(self, btn, idx):
        if self.lock or self.revealed[idx] or self.matched[idx] or self.done:
            return
        if not self.start_time:
            self.start_time = time.time()
        self.revealed[idx] = True
        btn.set_label(self.cards[idx])
        self.flipped.append(idx)
        if len(self.flipped) == 2:
            self.moves += 1
            self.moves_label.set_text(f"Moves: {self.moves}")
            a, b = self.flipped
            if self.cards[a] == self.cards[b]:
                self.matched[a] = self.matched[b] = True
                self.card_buttons[a].set_sensitive(False)
                self.card_buttons[b].set_sensitive(False)
                self.flipped = []
                if all(self.matched):
                    self.done = True
                    self.status_label.set_text(f"You won in {self.moves} moves and {int(self.elapsed)}s!")
            else:
                self.lock = True
                GLib.timeout_add(800, self.hide_cards, a, b)
                self.flipped = []

    def hide_cards(self, a, b):
        self.revealed[a] = self.revealed[b] = False
        self.card_buttons[a].set_label("?")
        self.card_buttons[b].set_label("?")
        self.lock = False
        return False

    def tick_timer(self):
        if self.start_time and not self.done:
            self.elapsed = time.time() - self.start_time
        self.time_label.set_text(f"Time: {int(self.elapsed)}s")
        return True

class MemoryMatchApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.MemoryMatch")
    def do_activate(self):
        win = MemoryMatchWindow(self)
        win.present()

def main():
    app = MemoryMatchApp()
    app.run(None)

if __name__ == "__main__":
    main()
