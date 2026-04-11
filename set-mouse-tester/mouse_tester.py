#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk
import time, math

class MouseTesterWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Mouse Tester")
        self.set_default_size(800, 560)
        self.click_history = []
        self.trail = []
        self.mouse_x = 0; self.mouse_y = 0
        self.button_states = {}
        self.scroll_count = 0
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Mouse Tester", css_classes=["title"]))

        info_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        info_box.set_halign(Gtk.Align.CENTER)
        self.pos_label = Gtk.Label(label="Position: --")
        self.btn_label = Gtk.Label(label="Button: --")
        self.scroll_label = Gtk.Label(label="Scroll: 0")
        self.speed_label = Gtk.Label(label="Speed: --")
        for lbl in [self.pos_label, self.btn_label, self.scroll_label, self.speed_label]:
            lbl.set_css_classes(["heading"])
            info_box.append(lbl)
        vbox.append(info_box)

        canvas_frame = Gtk.Frame(label="Mouse Canvas (click here)")
        self.canvas = Gtk.DrawingArea()
        self.canvas.set_vexpand(True)
        self.canvas.set_draw_func(self.draw_canvas)

        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self.on_motion)
        self.canvas.add_controller(motion)

        click = Gtk.GestureClick()
        click.set_button(0)
        click.connect("pressed", self.on_pressed)
        click.connect("released", self.on_released)
        self.canvas.add_controller(click)

        scroll = Gtk.EventControllerScroll(flags=Gtk.EventControllerScrollFlags.BOTH_AXES)
        scroll.connect("scroll", self.on_scroll)
        self.canvas.add_controller(scroll)

        canvas_frame.set_child(self.canvas)
        vbox.append(canvas_frame)

        buttons_frame = Gtk.Frame(label="Mouse Buttons Visual")
        buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        buttons_box.set_halign(Gtk.Align.CENTER)
        buttons_box.set_margin_top(6); buttons_box.set_margin_bottom(6)
        self.button_widgets = {}
        for i, label in [(1, "Left"), (2, "Middle"), (3, "Right"), (8, "Back"), (9, "Forward")]:
            btn_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            btn_vbox.set_halign(Gtk.Align.CENTER)
            indicator = Gtk.DrawingArea()
            indicator.set_size_request(50, 50)
            indicator._button = i
            indicator.set_draw_func(self.draw_button_indicator)
            lbl = Gtk.Label(label=label)
            btn_vbox.append(indicator); btn_vbox.append(lbl)
            buttons_box.append(btn_vbox)
            self.button_widgets[i] = indicator
        buttons_frame.set_child(buttons_box)
        vbox.append(buttons_frame)

        history_frame = Gtk.Frame(label="Click History")
        scroll_h = Gtk.ScrolledWindow(); scroll_h.set_min_content_height(80)
        self.history_view = Gtk.TextView()
        self.history_view.set_editable(False); self.history_view.set_monospace(True)
        scroll_h.set_child(self.history_view)
        history_frame.set_child(scroll_h)
        vbox.append(history_frame)

        self.last_pos = None
        self.last_time = None

    def on_motion(self, ctrl, x, y):
        now = time.perf_counter()
        if self.last_pos and self.last_time:
            dx = x - self.last_pos[0]
            dy = y - self.last_pos[1]
            dt = now - self.last_time
            if dt > 0:
                speed = math.sqrt(dx**2 + dy**2) / dt
                self.speed_label.set_text(f"Speed: {speed:.0f} px/s")
        self.last_pos = (x, y)
        self.last_time = now
        self.mouse_x = x; self.mouse_y = y
        self.pos_label.set_text(f"Position: {int(x)}, {int(y)}")
        self.trail.append((x, y))
        if len(self.trail) > 200:
            self.trail = self.trail[-200:]
        self.canvas.queue_draw()

    def on_pressed(self, gesture, n_press, x, y):
        btn = gesture.get_current_button()
        self.button_states[btn] = True
        ts = time.strftime("%H:%M:%S.") + f"{int(time.time() * 1000) % 1000:03d}"
        btn_names = {1: "Left", 2: "Middle", 3: "Right", 8: "Back", 9: "Forward"}
        name = btn_names.get(btn, f"Btn{btn}")
        msg = f"[{ts}] {name} press at ({int(x)}, {int(y)}) n={n_press}"
        self.click_history.append(msg)
        self.click_history = self.click_history[-50:]
        self.history_view.get_buffer().set_text("\n".join(self.click_history[-12:]))
        self.btn_label.set_text(f"Button: {name}")
        self.canvas.queue_draw()
        for w in self.button_widgets.values():
            w.queue_draw()
        self.trail.append(("CLICK", x, y, btn))

    def on_released(self, gesture, n_press, x, y):
        btn = gesture.get_current_button()
        self.button_states[btn] = False
        for w in self.button_widgets.values():
            w.queue_draw()

    def on_scroll(self, ctrl, dx, dy):
        self.scroll_count += 1
        direction = "↑" if dy < 0 else "↓" if dy > 0 else ("←" if dx < 0 else "→")
        self.scroll_label.set_text(f"Scroll: {self.scroll_count} {direction}")

    def draw_canvas(self, area, cr, w, h):
        cr.set_source_rgb(0.08, 0.08, 0.12); cr.rectangle(0, 0, w, h); cr.fill()
        cr.set_source_rgba(0.3, 0.3, 0.4, 0.3); cr.set_line_width(0.5)
        for x in range(0, w, 50):
            cr.move_to(x, 0); cr.line_to(x, h); cr.stroke()
        for y in range(0, h, 50):
            cr.move_to(0, y); cr.line_to(w, y); cr.stroke()

        # Trail
        for i, point in enumerate(self.trail):
            if isinstance(point, tuple) and len(point) == 2:
                alpha = i / len(self.trail) * 0.6
                cr.set_source_rgba(0.5, 0.7, 0.9, alpha)
                cr.arc(point[0], point[1], 2, 0, math.tau)
                cr.fill()
            elif isinstance(point, tuple) and len(point) == 4 and point[0] == "CLICK":
                _, x, y, btn = point
                colors = {1: (0.2, 0.8, 0.2), 2: (0.9, 0.8, 0.2), 3: (0.9, 0.3, 0.3)}
                cr.set_source_rgb(*colors.get(btn, (0.7, 0.7, 0.7)))
                cr.arc(x, y, 8, 0, math.tau); cr.stroke()
                cr.arc(x, y, 3, 0, math.tau); cr.fill()

        # Cursor
        cr.set_source_rgb(1, 1, 1); cr.set_line_width(1.5)
        cr.move_to(self.mouse_x - 12, self.mouse_y)
        cr.line_to(self.mouse_x + 12, self.mouse_y); cr.stroke()
        cr.move_to(self.mouse_x, self.mouse_y - 12)
        cr.line_to(self.mouse_x, self.mouse_y + 12); cr.stroke()
        cr.arc(self.mouse_x, self.mouse_y, 4, 0, math.tau); cr.stroke()

        cr.set_source_rgb(0.8, 0.8, 0.8); cr.set_font_size(10)
        cr.move_to(self.mouse_x + 14, self.mouse_y - 4)
        cr.show_text(f"({int(self.mouse_x)}, {int(self.mouse_y)})")

    def draw_button_indicator(self, area, cr, w, h):
        btn = area._button
        pressed = self.button_states.get(btn, False)
        if pressed:
            cr.set_source_rgb(0.2, 0.8, 0.2)
        else:
            cr.set_source_rgb(0.25, 0.25, 0.35)
        cr.rectangle(4, 4, w - 8, h - 8); cr.fill()
        cr.set_source_rgb(0.5, 0.5, 0.6); cr.set_line_width(1.5)
        cr.rectangle(4, 4, w - 8, h - 8); cr.stroke()
        cr.set_source_rgb(0.9, 0.9, 0.9); cr.set_font_size(10)
        cr.move_to(w//2 - 6, h//2 + 4)
        cr.show_text(str(btn))

class MouseTesterApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.MouseTester")
    def do_activate(self):
        win = MouseTesterWindow(self); win.present()

def main():
    app = MouseTesterApp(); app.run(None)

if __name__ == "__main__":
    main()
