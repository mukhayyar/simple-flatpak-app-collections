#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib
import random, os

CELL = 24
COLS, ROWS = 20, 20
WIDTH, HEIGHT = COLS * CELL, ROWS * CELL

SAVE_DIR = os.path.expanduser("~/.local/share/com.pens.Snake")
SCORE_FILE = os.path.join(SAVE_DIR, "score.txt")

def load_high_score():
    try:
        os.makedirs(SAVE_DIR, exist_ok=True)
        with open(SCORE_FILE) as f:
            return int(f.read().strip())
    except Exception:
        return 0

def save_high_score(s):
    os.makedirs(SAVE_DIR, exist_ok=True)
    with open(SCORE_FILE, "w") as f:
        f.write(str(s))

class SnakeWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Snake")
        self.set_default_size(WIDTH + 20, HEIGHT + 80)
        self.high_score = load_high_score()
        self.init_game()

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        self.score_label = Gtk.Label(label=f"Score: 0  High: {self.high_score}")
        vbox.append(self.score_label)

        self.canvas = Gtk.DrawingArea()
        self.canvas.set_size_request(WIDTH, HEIGHT)
        self.canvas.set_draw_func(self.on_draw)
        vbox.append(self.canvas)

        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self.on_key)
        self.add_controller(key_ctrl)

        self.timeout_id = GLib.timeout_add(150, self.tick)

    def init_game(self):
        mid = (COLS // 2, ROWS // 2)
        self.snake = [mid, (mid[0]-1, mid[1]), (mid[0]-2, mid[1])]
        self.direction = (1, 0)
        self.next_dir = (1, 0)
        self.score = 0
        self.game_over = False
        self.place_food()

    def place_food(self):
        empty = [(x, y) for x in range(COLS) for y in range(ROWS) if (x, y) not in self.snake]
        if empty:
            self.food = random.choice(empty)

    def on_key(self, ctrl, keyval, keycode, state):
        dirs = {
            Gdk.KEY_Up: (0, -1), Gdk.KEY_w: (0, -1),
            Gdk.KEY_Down: (0, 1), Gdk.KEY_s: (0, 1),
            Gdk.KEY_Left: (-1, 0), Gdk.KEY_a: (-1, 0),
            Gdk.KEY_Right: (1, 0), Gdk.KEY_d: (1, 0),
        }
        if self.game_over and keyval == Gdk.KEY_Return:
            self.init_game()
            return True
        if keyval in dirs:
            nd = dirs[keyval]
            if nd[0] != -self.direction[0] or nd[1] != -self.direction[1]:
                self.next_dir = nd
        return True

    def tick(self):
        if self.game_over:
            return True
        self.direction = self.next_dir
        head = (self.snake[0][0] + self.direction[0], self.snake[0][1] + self.direction[1])
        if not (0 <= head[0] < COLS and 0 <= head[1] < ROWS) or head in self.snake:
            self.game_over = True
            if self.score > self.high_score:
                self.high_score = self.score
                save_high_score(self.high_score)
        else:
            self.snake.insert(0, head)
            if head == self.food:
                self.score += 10
                interval = max(60, 150 - (self.score // 50) * 10)
                GLib.source_remove(self.timeout_id)
                self.timeout_id = GLib.timeout_add(interval, self.tick)
                self.place_food()
            else:
                self.snake.pop()
        self.score_label.set_text(f"Score: {self.score}  High: {self.high_score}")
        self.canvas.queue_draw()
        return True

    def on_draw(self, area, cr, w, h):
        cr.set_source_rgb(0.08, 0.08, 0.08)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        for i, (x, y) in enumerate(self.snake):
            r = 0.1 + i / len(self.snake) * 0.1
            cr.set_source_rgb(0.2 - r, 0.8 - r * 2, 0.2)
            cr.rectangle(x * CELL + 1, y * CELL + 1, CELL - 2, CELL - 2)
            cr.fill()

        cr.set_source_rgb(0.9, 0.2, 0.2)
        fx, fy = self.food
        cr.arc(fx * CELL + CELL/2, fy * CELL + CELL/2, CELL/2 - 2, 0, 6.28)
        cr.fill()

        if self.game_over:
            cr.set_source_rgba(0, 0, 0, 0.7)
            cr.rectangle(0, 0, w, h)
            cr.fill()
            cr.set_source_rgb(1, 1, 1)
            cr.set_font_size(32)
            cr.move_to(w/2 - 80, h/2 - 20)
            cr.show_text("GAME OVER")
            cr.set_font_size(16)
            cr.move_to(w/2 - 100, h/2 + 20)
            cr.show_text(f"Score: {self.score}  Press Enter to restart")

class SnakeApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.Snake")
    def do_activate(self):
        win = SnakeWindow(self)
        win.present()

def main():
    app = SnakeApp()
    app.run(None)

if __name__ == "__main__":
    main()
