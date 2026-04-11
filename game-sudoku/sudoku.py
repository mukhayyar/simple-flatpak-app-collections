#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib
import random, copy, time

def is_valid(board, row, col, num):
    if num in board[row]: return False
    if num in [board[r][col] for r in range(9)]: return False
    br, bc = (row // 3) * 3, (col // 3) * 3
    for r in range(br, br+3):
        for c in range(bc, bc+3):
            if board[r][c] == num: return False
    return True

def solve(board):
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                nums = list(range(1, 10))
                random.shuffle(nums)
                for n in nums:
                    if is_valid(board, r, c, n):
                        board[r][c] = n
                        if solve(board): return True
                        board[r][c] = 0
                return False
    return True

def generate_puzzle(holes=40):
    board = [[0]*9 for _ in range(9)]
    solve(board)
    solution = copy.deepcopy(board)
    positions = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(positions)
    for r, c in positions[:holes]:
        board[r][c] = 0
    return board, solution

class SudokuWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Sudoku")
        self.set_default_size(500, 580)
        self.selected = None
        self.start_time = time.time()
        self.elapsed = 0
        self.new_puzzle("Medium")

    def new_puzzle(self, difficulty):
        holes = {"Easy": 30, "Medium": 45, "Hard": 55}.get(difficulty, 45)
        self.original, self.solution = generate_puzzle(holes)
        self.current = copy.deepcopy(self.original)
        self.selected = None
        self.start_time = time.time()
        self.build_ui()

    def build_ui(self):
        self.set_child(None)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.time_label = Gtk.Label(label="Time: 0s")
        top.append(self.time_label)
        for d in ["Easy", "Medium", "Hard"]:
            btn = Gtk.Button(label=d)
            btn.connect("clicked", self.on_new, d)
            top.append(btn)
        hint_btn = Gtk.Button(label="Hint")
        hint_btn.connect("clicked", self.on_hint)
        top.append(hint_btn)
        vbox.append(top)

        css = Gtk.CssProvider()
        css.load_from_data(b"""
.sudoku-cell { font-size: 18px; border: 1px solid #555; }
.sudoku-selected { background-color: #3a5a8a; color: white; }
.sudoku-original { color: #cccccc; font-weight: bold; }
.sudoku-user { color: #5af; }
.sudoku-error { color: #f55; background-color: #4a1010; }
""")
        Gtk.StyleContext.add_provider_for_display(self.get_display(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        grid = Gtk.Grid()
        grid.set_halign(Gtk.Align.CENTER)
        grid.set_row_spacing(0); grid.set_column_spacing(0)
        self.cells = {}
        for r in range(9):
            for c in range(9):
                btn = Gtk.Button()
                btn.set_size_request(48, 48)
                val = self.current[r][c]
                if val:
                    btn.set_label(str(val))
                    btn.set_css_classes(["sudoku-cell", "sudoku-original"])
                else:
                    btn.set_label("")
                    btn.set_css_classes(["sudoku-cell"])
                btn.connect("clicked", self.on_cell_click, r, c)
                mr = 2 if r % 3 == 2 and r < 8 else 0
                mc = 2 if c % 3 == 2 and c < 8 else 0
                grid.attach(btn, c, r, 1, 1)
                if mr: grid.set_row_spacing(1)
                self.cells[(r, c)] = btn
        vbox.append(grid)

        num_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        num_box.set_halign(Gtk.Align.CENTER)
        for n in range(1, 10):
            btn = Gtk.Button(label=str(n))
            btn.set_size_request(44, 40)
            btn.connect("clicked", self.on_num_btn, n)
            num_box.append(btn)
        clear_btn = Gtk.Button(label="X")
        clear_btn.set_size_request(40, 40)
        clear_btn.connect("clicked", self.on_num_btn, 0)
        num_box.append(clear_btn)
        vbox.append(num_box)

        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self.on_key)
        self.add_controller(key_ctrl)

        self.status_label = Gtk.Label(label="Select a cell and type a number")
        vbox.append(self.status_label)

        self.timer_id = GLib.timeout_add(1000, self.update_timer)

    def update_timer(self):
        self.elapsed = int(time.time() - self.start_time)
        self.time_label.set_text(f"Time: {self.elapsed}s")
        return True

    def on_new(self, btn, d):
        self.new_puzzle(d)

    def on_cell_click(self, btn, r, c):
        self.selected = (r, c)
        self.highlight_selection()

    def highlight_selection(self):
        for (r, c), btn in self.cells.items():
            classes = ["sudoku-cell"]
            if self.original[r][c]:
                classes.append("sudoku-original")
            elif self.current[r][c]:
                if self.current[r][c] != self.solution[r][c]:
                    classes.append("sudoku-error")
                else:
                    classes.append("sudoku-user")
            if (r, c) == self.selected:
                classes.append("sudoku-selected")
            btn.set_css_classes(classes)

    def on_num_btn(self, btn, n):
        if self.selected:
            self.set_cell(*self.selected, n)

    def on_key(self, ctrl, keyval, keycode, state):
        if not self.selected:
            return True
        r, c = self.selected
        if keyval in range(Gdk.KEY_1, Gdk.KEY_9 + 1):
            self.set_cell(r, c, keyval - Gdk.KEY_0)
        elif keyval == Gdk.KEY_Delete or keyval == Gdk.KEY_BackSpace:
            self.set_cell(r, c, 0)
        elif keyval == Gdk.KEY_Up and r > 0: self.selected = (r-1, c); self.highlight_selection()
        elif keyval == Gdk.KEY_Down and r < 8: self.selected = (r+1, c); self.highlight_selection()
        elif keyval == Gdk.KEY_Left and c > 0: self.selected = (r, c-1); self.highlight_selection()
        elif keyval == Gdk.KEY_Right and c < 8: self.selected = (r, c+1); self.highlight_selection()
        return True

    def set_cell(self, r, c, n):
        if self.original[r][c]: return
        self.current[r][c] = n
        btn = self.cells[(r, c)]
        btn.set_label(str(n) if n else "")
        self.highlight_selection()
        if all(self.current[r][c] for r in range(9) for c in range(9)):
            if self.current == self.solution:
                self.status_label.set_text(f"Solved! Time: {self.elapsed}s")
            else:
                self.status_label.set_text("Some numbers are wrong!")

    def on_hint(self, btn):
        empties = [(r, c) for r in range(9) for c in range(9) if not self.current[r][c]]
        if empties:
            r, c = random.choice(empties)
            self.set_cell(r, c, self.solution[r][c])
            self.selected = (r, c)
            self.highlight_selection()

class SudokuApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.Sudoku")
    def do_activate(self):
        win = SudokuWindow(self)
        win.present()

def main():
    app = SudokuApp()
    app.run(None)

if __name__ == "__main__":
    main()
