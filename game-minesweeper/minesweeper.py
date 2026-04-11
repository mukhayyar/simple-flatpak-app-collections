#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib
import random, time

DIFFICULTIES = {"Beginner": (9, 9, 10), "Intermediate": (16, 16, 40), "Expert": (30, 16, 99)}

class MinesweeperWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Minesweeper")
        self.cols, self.rows, self.mines = 9, 9, 10
        self.setup()
        self.build_ui()

    def setup(self):
        self.revealed = set()
        self.flagged = set()
        self.mine_locs = set()
        self.numbers = {}
        self.game_over = False
        self.won = False
        self.started = False
        self.start_time = 0
        self.elapsed = 0

    def build_ui(self):
        for child in list(self.get_child() and [self.get_child()] or []):
            self.set_child(None)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.mine_label = Gtk.Label(label=f"Mines: {self.mines}")
        top.append(self.mine_label)
        reset_btn = Gtk.Button(label="😊")
        reset_btn.connect("clicked", self.on_reset)
        top.append(reset_btn)
        self.time_label = Gtk.Label(label="Time: 0")
        top.append(self.time_label)
        vbox.append(top)

        diff_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        for d in DIFFICULTIES:
            btn = Gtk.Button(label=d)
            btn.connect("clicked", self.on_difficulty, d)
            diff_box.append(btn)
        vbox.append(diff_box)

        cell_size = min(32, 600 // self.cols)
        self.cell_size = cell_size
        grid = Gtk.Grid()
        grid.set_row_spacing(0); grid.set_column_spacing(0)
        self.buttons = {}
        for row in range(self.rows):
            for col in range(self.cols):
                btn = Gtk.Button(label="")
                btn.set_size_request(cell_size, cell_size)
                btn.set_css_classes(["flat"])
                click = Gtk.GestureClick()
                click.set_button(0)
                click.connect("pressed", self.on_cell_click, col, row)
                btn.add_controller(click)
                grid.attach(btn, col, row, 1, 1)
                self.buttons[(col, row)] = btn
        vbox.append(grid)

        self.timer_id = GLib.timeout_add(1000, self.update_timer)

    def on_difficulty(self, btn, d):
        self.cols, self.rows, self.mines = DIFFICULTIES[d]
        self.setup()
        self.build_ui()

    def place_mines(self, safe_col, safe_row):
        safe = set()
        for dc in range(-1, 2):
            for dr in range(-1, 2):
                nc, nr = safe_col + dc, safe_row + dr
                if 0 <= nc < self.cols and 0 <= nr < self.rows:
                    safe.add((nc, nr))
        candidates = [(c, r) for c in range(self.cols) for r in range(self.rows) if (c, r) not in safe]
        self.mine_locs = set(random.sample(candidates, min(self.mines, len(candidates))))
        for c, r in [(cc, rr) for cc in range(self.cols) for rr in range(self.rows)]:
            if (c, r) not in self.mine_locs:
                count = sum(1 for dc in range(-1, 2) for dr in range(-1, 2) if (c+dc, r+dr) in self.mine_locs)
                if count > 0:
                    self.numbers[(c, r)] = count

    def on_cell_click(self, gesture, n, x, y, col, row):
        if self.game_over or self.won:
            return
        button = gesture.get_current_button()
        if button == 3:
            self.toggle_flag(col, row)
        elif button == 1:
            if (col, row) in self.flagged:
                return
            if not self.started:
                self.started = True
                self.start_time = time.time()
                self.place_mines(col, row)
            self.reveal(col, row)
        self.update_buttons()

    def toggle_flag(self, col, row):
        if (col, row) in self.revealed:
            return
        if (col, row) in self.flagged:
            self.flagged.remove((col, row))
        else:
            self.flagged.add((col, row))
        remaining = self.mines - len(self.flagged)
        self.mine_label.set_text(f"Mines: {remaining}")

    def reveal(self, col, row):
        if (col, row) in self.revealed or (col, row) in self.flagged:
            return
        if not (0 <= col < self.cols and 0 <= row < self.rows):
            return
        self.revealed.add((col, row))
        if (col, row) in self.mine_locs:
            self.game_over = True
            self.revealed.update(self.mine_locs)
            return
        if (col, row) not in self.numbers:
            for dc in range(-1, 2):
                for dr in range(-1, 2):
                    if dc or dr:
                        self.reveal(col + dc, row + dr)
        safe = {(c, r) for c in range(self.cols) for r in range(self.rows)} - self.mine_locs
        if safe == self.revealed:
            self.won = True
            self.elapsed = int(time.time() - self.start_time)

    def update_buttons(self):
        COLORS = {1: "#0000ff", 2: "#008000", 3: "#ff0000", 4: "#000080",
                  5: "#800000", 6: "#008080", 7: "#000000", 8: "#808080"}
        for (col, row), btn in self.buttons.items():
            if (col, row) in self.revealed:
                if (col, row) in self.mine_locs:
                    btn.set_label("💣")
                elif (col, row) in self.numbers:
                    n = self.numbers[(col, row)]
                    btn.set_label(str(n))
                else:
                    btn.set_label(" ")
                btn.set_sensitive(False)
            elif (col, row) in self.flagged:
                btn.set_label("🚩")
            else:
                btn.set_label("")
        if self.won:
            self.set_title("Minesweeper — You Win! 🎉")
        elif self.game_over:
            self.set_title("Minesweeper — Game Over 💥")

    def update_timer(self):
        if self.started and not self.game_over and not self.won:
            self.elapsed = int(time.time() - self.start_time)
        self.time_label.set_text(f"Time: {self.elapsed}s")
        return True

    def on_reset(self, btn):
        self.setup()
        self.build_ui()

class MinesweeperApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.Minesweeper")
    def do_activate(self):
        win = MinesweeperWindow(self)
        win.present()

def main():
    app = MinesweeperApp()
    app.run(None)

if __name__ == "__main__":
    main()
