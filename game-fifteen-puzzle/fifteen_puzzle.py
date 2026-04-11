#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import random, time, os

SAVE_DIR = os.path.expanduser("~/.local/share/com.pens.FifteenPuzzle")
BEST_FILE = os.path.join(SAVE_DIR, "best.txt")

def load_best():
    try:
        with open(BEST_FILE) as f:
            return float(f.read().strip())
    except Exception:
        return None

def save_best(t):
    os.makedirs(SAVE_DIR, exist_ok=True)
    with open(BEST_FILE, "w") as f:
        f.write(str(t))

CELL = 100
SIZE = 4

class FifteenPuzzleWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("15 Puzzle")
        self.set_default_size(SIZE * CELL + 40, SIZE * CELL + 120)
        self.best_time = load_best()
        self.init_puzzle()
        self.build_ui()

    def init_puzzle(self):
        nums = list(range(16))
        random.shuffle(nums)
        while not self.is_solvable(nums):
            random.shuffle(nums)
        self.tiles = nums
        self.blank = self.tiles.index(0)
        self.moves = 0
        self.start_time = None
        self.elapsed = 0
        self.won = False

    def is_solvable(self, tiles):
        inv = sum(1 for i in range(16) for j in range(i+1, 16)
                  if tiles[i] and tiles[j] and tiles[i] > tiles[j])
        blank_row = tiles.index(0) // SIZE
        return (inv + blank_row) % 2 == 0

    def build_ui(self):
        self.set_child(None)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.moves_label = Gtk.Label(label=f"Moves: {self.moves}")
        self.time_label = Gtk.Label(label="Time: 0.0s")
        best_text = f"Best: {self.best_time:.1f}s" if self.best_time else "Best: --"
        self.best_label = Gtk.Label(label=best_text)
        top.append(self.moves_label); top.append(self.time_label); top.append(self.best_label)
        shuffle_btn = Gtk.Button(label="Shuffle")
        shuffle_btn.connect("clicked", self.on_shuffle)
        top.append(shuffle_btn)
        vbox.append(top)

        grid = Gtk.Grid()
        grid.set_row_spacing(2); grid.set_column_spacing(2)
        self.buttons = []
        for i in range(SIZE * SIZE):
            btn = Gtk.Button()
            btn.set_size_request(CELL, CELL)
            num = self.tiles[i]
            if num == 0:
                btn.set_label("")
                btn.set_sensitive(False)
                btn.set_css_classes(["flat"])
            else:
                btn.set_label(str(num))
                btn.connect("clicked", self.on_tile_click, i)
            grid.attach(btn, i % SIZE, i // SIZE, 1, 1)
            self.buttons.append(btn)
        vbox.append(grid)

        self.timer_id = GLib.timeout_add(100, self.update_timer)

    def on_tile_click(self, btn, idx):
        if self.won:
            return
        blank = self.blank
        col, row = idx % SIZE, idx // SIZE
        bcol, brow = blank % SIZE, blank // SIZE
        if (abs(col - bcol) + abs(row - brow)) == 1:
            if not self.start_time:
                self.start_time = time.time()
            self.tiles[blank], self.tiles[idx] = self.tiles[idx], self.tiles[blank]
            self.blank = idx
            self.moves += 1
            self.refresh_grid()
            if self.tiles == list(range(1, 16)) + [0]:
                self.won = True
                t = time.time() - self.start_time
                self.elapsed = t
                if self.best_time is None or t < self.best_time:
                    self.best_time = t
                    save_best(t)
                    self.best_label.set_text(f"Best: {t:.1f}s")
                self.set_title(f"15 Puzzle — Solved in {t:.1f}s!")

    def refresh_grid(self):
        for i, btn in enumerate(self.buttons):
            num = self.tiles[i]
            if num == 0:
                btn.set_label("")
                btn.set_sensitive(False)
            else:
                btn.set_label(str(num))
                btn.set_sensitive(True)
        self.moves_label.set_text(f"Moves: {self.moves}")

    def update_timer(self):
        if self.start_time and not self.won:
            self.elapsed = time.time() - self.start_time
        self.time_label.set_text(f"Time: {self.elapsed:.1f}s")
        return True

    def on_shuffle(self, btn):
        if hasattr(self, 'timer_id'):
            GLib.source_remove(self.timer_id)
        self.init_puzzle()
        self.build_ui()

class FifteenPuzzleApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.FifteenPuzzle")
    def do_activate(self):
        win = FifteenPuzzleWindow(self)
        win.present()

def main():
    app = FifteenPuzzleApp()
    app.run(None)

if __name__ == "__main__":
    main()
