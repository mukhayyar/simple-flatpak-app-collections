#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib
import math

W, H = 480, 400
PADDLE_W, PADDLE_H = 80, 12
BALL_R = 8
BRICK_ROWS, BRICK_COLS = 5, 10
BRICK_W = W // BRICK_COLS
BRICK_H = 20
BRICK_Y_OFF = 60
BRICK_COLORS = [(0.9,0.2,0.2), (0.9,0.5,0.1), (0.9,0.9,0.1), (0.1,0.8,0.2), (0.1,0.5,0.9)]

class BreakoutWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Breakout")
        self.set_default_size(W + 20, H + 80)
        self.init_game()
        self.build_ui()

    def init_game(self):
        self.paddle_x = W // 2 - PADDLE_W // 2
        self.ball_x = W // 2
        self.ball_y = H - 60
        self.ball_dx = 3.5
        self.ball_dy = -3.5
        self.lives = 3
        self.score = 0
        self.level = 1
        self.running = False
        self.game_over = False
        self.won = False
        self.bricks = []
        for row in range(BRICK_ROWS):
            for col in range(BRICK_COLS):
                self.bricks.append([col * BRICK_W + 2, BRICK_Y_OFF + row * (BRICK_H + 4), True])

    def build_ui(self):
        self.set_child(None)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.score_label = Gtk.Label(label="Score: 0")
        self.lives_label = Gtk.Label(label="Lives: ❤❤❤")
        self.level_label = Gtk.Label(label="Level: 1")
        top.append(self.score_label); top.append(self.lives_label); top.append(self.level_label)
        vbox.append(top)

        self.canvas = Gtk.DrawingArea()
        self.canvas.set_size_request(W, H)
        self.canvas.set_draw_func(self.on_draw)
        vbox.append(self.canvas)

        ctrl = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        ctrl.set_halign(Gtk.Align.CENTER)
        start_btn = Gtk.Button(label="Start / Pause")
        start_btn.connect("clicked", self.on_start)
        ctrl.append(start_btn)
        reset_btn = Gtk.Button(label="Reset")
        reset_btn.connect("clicked", self.on_reset)
        ctrl.append(reset_btn)
        vbox.append(ctrl)

        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self.on_mouse_move)
        self.canvas.add_controller(motion)

        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self.on_key)
        self.add_controller(key_ctrl)

    def on_mouse_move(self, ctrl, x, y):
        self.paddle_x = max(0, min(W - PADDLE_W, int(x) - PADDLE_W // 2))
        self.canvas.queue_draw()

    def on_key(self, ctrl, keyval, keycode, state):
        speed = 20
        if keyval == Gdk.KEY_Left:
            self.paddle_x = max(0, self.paddle_x - speed)
        elif keyval == Gdk.KEY_Right:
            self.paddle_x = min(W - PADDLE_W, self.paddle_x + speed)
        elif keyval == Gdk.KEY_space:
            self.on_start(None)
        self.canvas.queue_draw()
        return True

    def on_start(self, btn):
        if self.game_over or self.won:
            self.init_game()
            self.build_ui()
            return
        self.running = not self.running
        if self.running:
            self.timeout_id = GLib.timeout_add(16, self.tick)

    def on_reset(self, btn):
        if hasattr(self, 'timeout_id'):
            GLib.source_remove(self.timeout_id)
        self.init_game()
        self.build_ui()

    def tick(self):
        if not self.running:
            return False
        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy

        if self.ball_x <= BALL_R or self.ball_x >= W - BALL_R:
            self.ball_dx = -self.ball_dx
        if self.ball_y <= BALL_R:
            self.ball_dy = -self.ball_dy
        if self.ball_y >= H + BALL_R:
            self.lives -= 1
            if self.lives <= 0:
                self.game_over = True
                self.running = False
            else:
                self.ball_x = W // 2
                self.ball_y = H - 60
                self.ball_dy = -abs(self.ball_dy)
            hearts = "❤" * self.lives
            self.lives_label.set_text(f"Lives: {hearts}")

        px, py = self.paddle_x, H - PADDLE_H - 8
        if (py - BALL_R <= self.ball_y <= py + PADDLE_H + BALL_R and
                px <= self.ball_x <= px + PADDLE_W):
            offset = (self.ball_x - (px + PADDLE_W/2)) / (PADDLE_W / 2)
            angle = math.radians(60 + offset * 30)
            speed = math.hypot(self.ball_dx, self.ball_dy)
            self.ball_dx = speed * math.cos(angle - math.pi/2)
            self.ball_dy = -abs(speed * math.sin(angle - math.pi/2))

        hit_any = False
        for brick in self.bricks:
            if not brick[2]: continue
            bx, by = brick[0], brick[1]
            if (bx - BALL_R <= self.ball_x <= bx + BRICK_W + BALL_R and
                    by - BALL_R <= self.ball_y <= by + BRICK_H + BALL_R):
                brick[2] = False
                self.ball_dy = -self.ball_dy
                self.score += 10
                self.score_label.set_text(f"Score: {self.score}")
                hit_any = True
                break

        if all(not b[2] for b in self.bricks):
            self.won = True
            self.running = False

        self.canvas.queue_draw()
        return self.running

    def on_draw(self, area, cr, w, h):
        cr.set_source_rgb(0.05, 0.05, 0.1)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        for i, brick in enumerate(self.bricks):
            if brick[2]:
                row = i // BRICK_COLS
                r, g, b = BRICK_COLORS[row % len(BRICK_COLORS)]
                cr.set_source_rgb(r, g, b)
                cr.rectangle(brick[0], brick[1], BRICK_W - 4, BRICK_H)
                cr.fill()

        cr.set_source_rgb(0.7, 0.7, 0.9)
        cr.rectangle(self.paddle_x, H - PADDLE_H - 8, PADDLE_W, PADDLE_H)
        cr.fill()

        cr.set_source_rgb(1, 1, 0.5)
        cr.arc(self.ball_x, self.ball_y, BALL_R, 0, 6.28)
        cr.fill()

        if self.game_over or self.won:
            cr.set_source_rgba(0, 0, 0, 0.7)
            cr.rectangle(0, 0, w, h)
            cr.fill()
            cr.set_source_rgb(1, 1, 1)
            cr.set_font_size(28)
            msg = "You Win! 🎉" if self.won else "Game Over"
            cr.move_to(w/2 - 60, h/2)
            cr.show_text(msg)
            cr.set_font_size(16)
            cr.move_to(w/2 - 80, h/2 + 30)
            cr.show_text("Click Start to play again")

        if not self.running and not self.game_over and not self.won:
            cr.set_source_rgba(0, 0, 0, 0.5)
            cr.rectangle(0, 0, w, h)
            cr.fill()
            cr.set_source_rgb(1, 1, 1)
            cr.set_font_size(20)
            cr.move_to(w/2 - 80, h/2)
            cr.show_text("Click Start to play")

class BreakoutApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.Breakout")
    def do_activate(self):
        win = BreakoutWindow(self)
        win.present()

def main():
    app = BreakoutApp()
    app.run(None)

if __name__ == "__main__":
    main()
