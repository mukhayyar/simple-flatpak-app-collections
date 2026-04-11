#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk

KEYBOARD_LAYOUT = [
    ["`","1","2","3","4","5","6","7","8","9","0","-","=","⌫"],
    ["Tab","q","w","e","r","t","y","u","i","o","p","[","]","\\"],
    ["Caps","a","s","d","f","g","h","j","k","l",";","'","↵"],
    ["⇧","z","x","c","v","b","n","m",",",".","/","⇧"],
    ["Ctrl","Alt","Space","Alt","Ctrl"],
]

WIDE_KEYS = {"Tab", "Caps", "⇧", "Ctrl", "Alt", "⌫", "↵", "Space"}

class OnScreenKeyboard(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("On-Screen Keyboard")
        self.set_default_size(900, 400)
        self.shift = False
        self.caps = False
        self.output_text = ""
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="On-Screen Keyboard", css_classes=["title"]))

        # Output area
        out_frame = Gtk.Frame(label="Output Text")
        out_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        out_box.set_margin_top(4); out_box.set_margin_start(8)
        out_box.set_margin_end(8); out_box.set_margin_bottom(4)
        self.output_entry = Gtk.Entry()
        self.output_entry.set_hexpand(True)
        self.output_entry.set_editable(True)
        out_box.append(self.output_entry)
        copy_btn = Gtk.Button(label="Copy")
        copy_btn.connect("clicked", self.on_copy)
        out_box.append(copy_btn)
        clear_btn = Gtk.Button(label="Clear")
        clear_btn.connect("clicked", self.on_clear)
        out_box.append(clear_btn)
        out_frame.set_child(out_box)
        vbox.append(out_frame)

        # Keyboard area
        kb_frame = Gtk.Frame(label="Keyboard")
        kb_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        kb_vbox.set_margin_top(6); kb_vbox.set_margin_start(8)
        kb_vbox.set_margin_end(8); kb_vbox.set_margin_bottom(6)

        self.key_buttons = {}
        for row_idx, row in enumerate(KEYBOARD_LAYOUT):
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            row_box.set_halign(Gtk.Align.CENTER)
            for key in row:
                btn = Gtk.Button()
                btn.set_label(key)
                if key in WIDE_KEYS:
                    btn.set_size_request(70 if key in {"Space"} else 56, 40)
                    if key == "Space":
                        btn.set_hexpand(True)
                        btn.set_size_request(200, 40)
                else:
                    btn.set_size_request(40, 40)
                btn._key = key
                btn.connect("clicked", self.on_key_press)
                row_box.append(btn)
                if key not in self.key_buttons:
                    self.key_buttons[key] = []
                self.key_buttons[key].append(btn)
            kb_vbox.append(row_box)
        kb_frame.set_child(kb_vbox)
        vbox.append(kb_frame)

        # Numpad row
        numpad_frame = Gtk.Frame(label="Numpad")
        numpad_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        numpad_box.set_margin_top(4); numpad_box.set_margin_start(8)
        numpad_box.set_margin_end(8); numpad_box.set_margin_bottom(4)
        for key in ["7","8","9","+","4","5","6","-","1","2","3","×","0",".","/","="]:
            btn = Gtk.Button(label=key)
            btn.set_size_request(44, 36)
            btn._key = key
            btn.connect("clicked", self.on_key_press)
            numpad_box.append(btn)
        numpad_frame.set_child(numpad_box)
        vbox.append(numpad_frame)

        # Status
        self.status_label = Gtk.Label(label="Shift: OFF  Caps: OFF", xalign=0)
        vbox.append(self.status_label)

    def on_key_press(self, btn):
        key = btn._key
        if key == "⇧":
            self.shift = not self.shift
            self.update_shift_display()
        elif key == "Caps":
            self.caps = not self.caps
            self.update_shift_display()
        elif key == "⌫":
            text = self.output_entry.get_text()
            if text:
                self.output_entry.set_text(text[:-1])
                self.output_entry.set_position(-1)
        elif key == "↵":
            text = self.output_entry.get_text()
            self.output_entry.set_text(text + "\n")
            self.output_entry.set_position(-1)
        elif key == "Space":
            self.insert_char(" ")
        elif key == "Tab":
            self.insert_char("\t")
        elif key in ("Ctrl", "Alt", "Fn"):
            pass  # modifier display only
        else:
            char = key
            if self.shift ^ self.caps:
                char = self.shift_map(key)
            self.insert_char(char)
            if self.shift:
                self.shift = False
                self.update_shift_display()

        self.status_label.set_text(f"Shift: {'ON' if self.shift else 'OFF'}  Caps: {'ON' if self.caps else 'OFF'}")

    def shift_map(self, key):
        map = {
            '`':'~', '1':'!', '2':'@', '3':'#', '4':'$', '5':'%',
            '6':'^', '7':'&', '8':'*', '9':'(', '0':')', '-':'_', '=':'+',
            '[':'{', ']':'}', '\\':'|', ';':':', "'":'"', ',':'<', '.':'>', '/':'?',
        }
        if key in map:
            return map[key]
        return key.upper()

    def update_shift_display(self):
        active = self.shift ^ self.caps
        for key, btns in self.key_buttons.items():
            if len(key) == 1 and key.isalpha():
                display = key.upper() if active else key.lower()
                for btn in btns:
                    btn.set_label(display)

    def insert_char(self, char):
        pos = self.output_entry.get_position()
        text = self.output_entry.get_text()
        new_text = text[:pos] + char + text[pos:]
        self.output_entry.set_text(new_text)
        self.output_entry.set_position(pos + len(char))

    def on_copy(self, btn):
        text = self.output_entry.get_text()
        clipboard = self.get_display().get_clipboard()
        clipboard.set(text)
        self.status_label.set_text(f"Copied {len(text)} characters")

    def on_clear(self, btn):
        self.output_entry.set_text("")

class OnScreenKeyboardApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.OnScreenKeyboard")
    def do_activate(self):
        win = OnScreenKeyboard(self); win.present()

def main():
    app = OnScreenKeyboardApp(); app.run(None)

if __name__ == "__main__":
    main()
