#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk
import random, copy

TILE_COLORS = {
    0: (0.45, 0.41, 0.38), 2: (0.93, 0.89, 0.85), 4: (0.93, 0.87, 0.78),
    8: (0.95, 0.69, 0.47), 16: (0.96, 0.58, 0.39), 32: (0.96, 0.49, 0.37),
    64: (0.96, 0.37, 0.23), 128: (0.93, 0.81, 0.45), 256: (0.93, 0.80, 0.38),
    512: (0.93, 0.78, 0.31), 1024: (0.93, 0.76, 0.25), 2048: (0.93, 0.75, 0.18),
}
TEXT_COLORS = {0: (0.73, 0.68, 0.63), 2: (0.47, 0.43, 0.40), 4: (0.47, 0.43, 0.40)}

class Game2048Window(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("2048")
        self.set_default_size(440, 540)
        self.init_game()
        self.build_ui()

    def init_game(self):
        self.board = [[0]*4 for _ in range(4)]
        self.score = 0
        self.best = 0
        self.add_tile()
        self.add_tile()
        self.prev_board = None
        self.prev_score = 0
        self.won = False
        self.over = False

    def add_tile(self):
        empty = [(r, c) for r in range(4) for c in range(4) if self.board[r][c] == 0]
        if empty:
            r, c = random.choice(empty)
            self.board[r][c] = 4 if random.random() < 0.1 else 2

    def build_ui(self):
        self.set_child(None)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        top.append(Gtk.Label(label="2048", css_classes=["title"]))
        self.score_label = Gtk.Label(label=f"Score: {self.score}")
        self.best_label = Gtk.Label(label=f"Best: {self.best}")
        top.append(self.score_label); top.append(self.best_label)
        new_btn = Gtk.Button(label="New Game")
        new_btn.connect("clicked", self.on_new)
        top.append(new_btn)
        undo_btn = Gtk.Button(label="Undo")
        undo_btn.connect("clicked", self.on_undo)
        top.append(undo_btn)
        vbox.append(top)

        self.canvas = Gtk.DrawingArea()
        self.canvas.set_size_request(400, 400)
        self.canvas.set_draw_func(self.on_draw)
        vbox.append(self.canvas)

        self.status_label = Gtk.Label(label="Use arrow keys to slide tiles")
        vbox.append(self.status_label)

        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self.on_key)
        self.add_controller(key_ctrl)

    def on_new(self, btn):
        if self.score > self.best:
            self.best = self.score
        self.init_game()
        self.canvas.queue_draw()
        self.score_label.set_text(f"Score: {self.score}")
        self.best_label.set_text(f"Best: {self.best}")
        self.status_label.set_text("Use arrow keys to slide tiles")

    def on_undo(self, btn):
        if self.prev_board:
            self.board = self.prev_board
            self.score = self.prev_score
            self.prev_board = None
            self.canvas.queue_draw()
            self.score_label.set_text(f"Score: {self.score}")

    def on_key(self, ctrl, keyval, keycode, state):
        if self.over:
            return True
        dirs = {Gdk.KEY_Up: "up", Gdk.KEY_Down: "down",
                Gdk.KEY_Left: "left", Gdk.KEY_Right: "right"}
        if keyval in dirs:
            self.prev_board = copy.deepcopy(self.board)
            self.prev_score = self.score
            moved, pts = self.move(dirs[keyval])
            if moved:
                self.score += pts
                if self.score > self.best:
                    self.best = self.score
                self.add_tile()
                if not self.can_move():
                    self.over = True
                    self.status_label.set_text(f"Game Over! Score: {self.score}")
                elif any(2048 in row for row in self.board) and not self.won:
                    self.won = True
                    self.status_label.set_text("You reached 2048! Keep going!")
                self.score_label.set_text(f"Score: {self.score}")
                self.best_label.set_text(f"Best: {self.best}")
                self.canvas.queue_draw()
        return True

    def slide_row(self, row):
        nums = [x for x in row if x != 0]
        pts = 0
        result = []
        i = 0
        while i < len(nums):
            if i + 1 < len(nums) and nums[i] == nums[i+1]:
                merged = nums[i] * 2
                result.append(merged)
                pts += merged
                i += 2
            else:
                result.append(nums[i])
                i += 1
        result.extend([0] * (4 - len(result)))
        return result, pts

    def move(self, direction):
        moved = False
        total_pts = 0
        board = self.board
        if direction in ("left", "right"):
            for r in range(4):
                row = board[r] if direction == "left" else list(reversed(board[r]))
                new_row, pts = self.slide_row(row)
                if direction == "right":
                    new_row = list(reversed(new_row))
                if new_row != board[r]:
                    moved = True
                board[r] = new_row
                total_pts += pts
        else:
            for c in range(4):
                col = [board[r][c] for r in range(4)]
                if direction == "down":
                    col = list(reversed(col))
                new_col, pts = self.slide_row(col)
                if direction == "down":
                    new_col = list(reversed(new_col))
                if [board[r][c] for r in range(4)] != new_col:
                    moved = True
                for r in range(4):
                    board[r][c] = new_col[r]
                total_pts += pts
        return moved, total_pts

    def can_move(self):
        for r in range(4):
            for c in range(4):
                if self.board[r][c] == 0: return True
                if c < 3 and self.board[r][c] == self.board[r][c+1]: return True
                if r < 3 and self.board[r][c] == self.board[r+1][c]: return True
        return False

    def on_draw(self, area, cr, w, h):
        cell = min(w, h) // 4
        padding = 4
        cr.set_source_rgb(0.47, 0.43, 0.40)
        cr.rectangle(0, 0, w, h)
        cr.fill()
        for r in range(4):
            for c in range(4):
                val = self.board[r][c]
                color = TILE_COLORS.get(val, (0.36, 0.31, 0.28))
                cr.set_source_rgb(*color)
                x = c * cell + padding
                y = r * cell + padding
                cr.rectangle(x, y, cell - padding*2, cell - padding*2)
                cr.fill()
                if val:
                    tc = TEXT_COLORS.get(val, (1, 1, 1))
                    cr.set_source_rgb(*tc)
                    fs = 28 if val < 100 else (22 if val < 1000 else 18)
                    cr.set_font_size(fs)
                    text = str(val)
                    ext = cr.text_extents(text)
                    cr.move_to(x + (cell - padding*2)/2 - ext.width/2 - ext.x_bearing,
                               y + (cell - padding*2)/2 - ext.height/2 - ext.y_bearing)
                    cr.show_text(text)

class Game2048App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.Game2048")
    def do_activate(self):
        win = Game2048Window(self)
        win.present()

def main():
    app = Game2048App()
    app.run(None)

if __name__ == "__main__":
    main()
