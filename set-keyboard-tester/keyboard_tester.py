#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk
import time

class KeyboardTesterWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Keyboard Tester")
        self.set_default_size(800, 560)
        self.pressed_keys = set()
        self.key_history = []
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(12); vbox.set_margin_bottom(12)
        vbox.set_margin_start(12); vbox.set_margin_end(12)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Keyboard Tester", css_classes=["title"]))

        self.status_label = Gtk.Label(label="Press any key to test")
        self.status_label.set_markup("<span font='16'>Press any key to test</span>")
        vbox.append(self.status_label)

        self.key_display = Gtk.Label(label="")
        self.key_display.set_markup("<span font='48' weight='bold'> </span>")
        vbox.append(self.key_display)

        info_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        info_box.set_halign(Gtk.Align.CENTER)
        self.keyname_label = Gtk.Label(label="Key name: --")
        self.keyval_label = Gtk.Label(label="Keyval: --")
        self.keycode_label = Gtk.Label(label="Keycode: --")
        self.modifiers_label = Gtk.Label(label="Modifiers: --")
        for lbl in [self.keyname_label, self.keyval_label, self.keycode_label, self.modifiers_label]:
            info_box.append(lbl)
        vbox.append(info_box)

        visual_frame = Gtk.Frame(label="Keyboard Layout (simplified)")
        self.kb_area = Gtk.DrawingArea()
        self.kb_area.set_size_request(-1, 160)
        self.kb_area.set_draw_func(self.draw_keyboard)
        visual_frame.set_child(self.kb_area)
        vbox.append(visual_frame)

        history_frame = Gtk.Frame(label="Key History")
        scroll = Gtk.ScrolledWindow(); scroll.set_min_content_height(100)
        self.history_view = Gtk.TextView()
        self.history_view.set_editable(False); self.history_view.set_monospace(True)
        scroll.set_child(self.history_view)
        history_frame.set_child(scroll)
        vbox.append(history_frame)

        clear_btn = Gtk.Button(label="Clear History")
        clear_btn.set_halign(Gtk.Align.CENTER)
        clear_btn.connect("clicked", lambda b: self.clear_history())
        vbox.append(clear_btn)

        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self.on_key_pressed)
        key_ctrl.connect("key-released", self.on_key_released)
        self.add_controller(key_ctrl)

        self.KEYBOARD_ROWS = [
            ["Esc", "F1","F2","F3","F4","F5","F6","F7","F8","F9","F10","F11","F12"],
            ["`","1","2","3","4","5","6","7","8","9","0","-","=","BkSp"],
            ["Tab","Q","W","E","R","T","Y","U","I","O","P","[","]","\\"],
            ["CpLk","A","S","D","F","G","H","J","K","L",";","'","Enter"],
            ["LShft","Z","X","C","V","B","N","M",",",".","/","RShft"],
            ["LCtrl","Super","LAlt","Space","RAlt","Fn","Menu","RCtrl"],
        ]

    def on_key_pressed(self, ctrl, keyval, keycode, state):
        keyname = Gdk.keyval_name(keyval) or "?"
        key_char = chr(keyval) if 32 <= keyval <= 126 else keyname
        self.pressed_keys.add(keyname.lower())

        mods = []
        if state & Gdk.ModifierType.SHIFT_MASK: mods.append("Shift")
        if state & Gdk.ModifierType.CONTROL_MASK: mods.append("Ctrl")
        if state & Gdk.ModifierType.ALT_MASK: mods.append("Alt")
        if state & Gdk.ModifierType.SUPER_MASK: mods.append("Super")
        if state & Gdk.ModifierType.LOCK_MASK: mods.append("CapsLock")

        self.key_display.set_markup(f"<span font='48' weight='bold'>{GLib.markup_escape_text(key_char)}</span>")
        self.keyname_label.set_text(f"Key name: {keyname}")
        self.keyval_label.set_text(f"Keyval: {keyval}")
        self.keycode_label.set_text(f"Keycode: {keycode}")
        self.modifiers_label.set_text(f"Modifiers: {'+'.join(mods) or 'None'}")

        ts = time.strftime("%H:%M:%S")
        combo = "+".join(mods + [keyname]) if mods else keyname
        self.key_history.append(f"[{ts}] {combo} (keyval={keyval}, code={keycode})")
        self.key_history = self.key_history[-100:]
        self.history_view.get_buffer().set_text("\n".join(self.key_history[-20:]))
        scroll_end = self.history_view.get_buffer().get_end_iter()
        self.history_view.scroll_to_iter(scroll_end, 0, False, 0, 1)
        self.kb_area.queue_draw()
        return True

    def on_key_released(self, ctrl, keyval, keycode, state):
        keyname = Gdk.keyval_name(keyval) or "?"
        self.pressed_keys.discard(keyname.lower())
        self.kb_area.queue_draw()

    def clear_history(self):
        self.key_history = []
        self.history_view.get_buffer().set_text("")

    def draw_keyboard(self, area, cr, w, h):
        cr.set_source_rgb(0.15, 0.15, 0.2); cr.rectangle(0, 0, w, h); cr.fill()
        rows = self.KEYBOARD_ROWS
        row_y = 10
        for row in rows:
            n = len(row)
            key_w = (w - 20) / max(n, 14)
            for i, key in enumerate(row):
                x = 10 + i * key_w
                kw = key_w - 2
                if key in ("BkSp", "Enter", "LShft", "RShft", "Space", "LCtrl", "RCtrl"):
                    kw = key_w * 1.8 - 2
                in_pressed = (key.lower() in self.pressed_keys or
                              key.upper() in self.pressed_keys or
                              (key == "Space" and "space" in self.pressed_keys))
                if in_pressed:
                    cr.set_source_rgb(0.2, 0.7, 0.3)
                else:
                    cr.set_source_rgb(0.3, 0.3, 0.4)
                cr.rectangle(x, row_y, kw, 20); cr.fill()
                cr.set_source_rgb(0.1, 0.1, 0.15); cr.set_line_width(0.5)
                cr.rectangle(x, row_y, kw, 20); cr.stroke()
                cr.set_source_rgb(0.9, 0.9, 0.9); cr.set_font_size(8)
                cr.move_to(x + 2, row_y + 14)
                cr.show_text(key[:6])
            row_y += 24

class KeyboardTesterApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.KeyboardTester")
    def do_activate(self):
        win = KeyboardTesterWindow(self); win.present()

def main():
    app = KeyboardTesterApp(); app.run(None)

if __name__ == "__main__":
    main()
