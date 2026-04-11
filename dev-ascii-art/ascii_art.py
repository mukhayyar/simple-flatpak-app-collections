#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

# Built-in ASCII art fonts - 3 fonts implemented as character maps
FONTS = {}

# Font 1: "block" - 5x5 block chars
BLOCK_FONT = {
    'A': ["  _  ", " / \ ", "/___\\", "|   |", "|   |"],
    'B': ["|--. ", "|  \\|", "|--' ", "|  /|", "|--' "],
    'C': [" ___ ", "/    ", "|    ", "\\    ", " ___/"],
    'D': ["|\\  ", "| \\ ", "|  |", "| / ", "|/  "],
    'E': ["|---", "|-- ", "|   ", "|-- ", "|---"],
    'F': ["|---", "|-- ", "|   ", "|   ", "|   "],
    'G': [" ___ ", "/    ", "| __ ", "|   |", " \\_/ "],
    'H': ["|  |", "|  |", "|--|", "|  |", "|  |"],
    'I': ["---", " | ", " | ", " | ", "---"],
    'J': ["  --", "   |", "   |", "   |", "__/|"],
    'K': ["| / ", "|/  ", "|\\  ", "| \\ ", "|  \\"],
    'L': ["|   ", "|   ", "|   ", "|   ", "|___"],
    'M': ["|\\  /|", "| \\/ |", "|    |", "|    |", "|    |"],
    'N': ["|\\  |", "| \\ |", "|  \\|", "|   |", "|   |"],
    'O': [" ___ ", "/   \\", "|   |", "\\   /", " --- "],
    'P': ["|--. ", "|  \\|", "|--' ", "|    ", "|    "],
    'Q': [" ___ ", "/   \\", "|   |", "\\_ _/", "   \\ "],
    'R': ["|--. ", "|  \\|", "|--' ", "| \\  ", "|  \\ "],
    'S': [" ___ ", "/    ", " --  ", "    \\", " ___/"],
    'T': ["-----", "  |  ", "  |  ", "  |  ", "  |  "],
    'U': ["|   |", "|   |", "|   |", "|   |", " --- "],
    'V': ["|   |", "|   |", " \\ / ", "  V  ", "     "],
    'W': ["|   |", "|   |", "| | |", "|/ \\|", "|   |"],
    'X': ["\\   /", " \\ / ", "  X  ", " / \\ ", "/   \\"],
    'Y': ["|   |", " \\ / ", "  |  ", "  |  ", "  |  "],
    'Z': ["|---\\", "   / ", "  /  ", " /   ", "/---|"],
    ' ': ["   ", "   ", "   ", "   ", "   "],
    '0': [" 0 ", "/ \\", "|0||", "\\ /", " 0 "],
    '1': [" 1 ", "/1 ", " 1 ", " 1 ", "_1_"],
    '2': ["222", "  2", "222", "2  ", "222"],
    '3': ["333", "  3", "333", "  3", "333"],
    '4': ["4 4", "4 4", "444", "  4", "  4"],
    '5': ["555", "5  ", "555", "  5", "555"],
    '6': ["666", "6  ", "666", "6 6", "666"],
    '7': ["777", "  7", "  7", "  7", "  7"],
    '8': ["888", "8 8", "888", "8 8", "888"],
    '9': ["999", "9 9", "999", "  9", "999"],
    '!': ["!", "!", "!", " ", "!"],
    '?': ["?", "?", " ", "?", " "],
}

# Font 2: "slim" - 3x5 simple
SLIM_FONT = {c: [c, "|", "|", "|", "-"] for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "}
SLIM_FONT.update({
    'A': ["^", "/\\", "  ", "||", "  "],
    'B': ["B", "|-", "|\\", "|-", "  "],
    'H': ["H", "||", "||", "HH", "  "],
    'I': ["I", " ", "I", " ", "I"],
    'O': ["O", "( )", "   ", "( )", "O"],
    ' ': [" ", " ", " ", " ", " "],
})

# Font 3: "banner" - simple single-line using unicode box chars
BANNER_CHARS = {
    'A': '▄▀▄', 'B': '█▄▄', 'C': '█▀▀', 'D': '█▄▄', 'E': '█▀▀',
    'F': '█▀▀', 'G': '█▀▄', 'H': '█ █', 'I': '█', 'J': '▄▄█',
    'K': '█▄▀', 'L': '█▄▄', 'M': '█▄█', 'N': '█▄█', 'O': '█▀█',
    'P': '█▀▄', 'Q': '█▀█', 'R': '█▀▄', 'S': '▀▄▄', 'T': '▀█▀',
    'U': '█ █', 'V': '▀▀▄', 'W': '█ █', 'X': '▀▄▀', 'Y': '▀▄▀',
    'Z': '▀▄▄', ' ': '   ',
    '0': '█▀█', '1': ' █ ', '2': '▀▄▄', '3': '▀▀█', '4': '█▄█',
    '5': '█▀▄', '6': '█▄█', '7': '▀▀█', '8': '█▄█', '9': '█▀█',
}

FONTS["Block"] = BLOCK_FONT
FONTS["Slim"] = SLIM_FONT

def render_block(text, font_data):
    lines = [""] * 5
    for char in text.upper():
        char_art = font_data.get(char, font_data.get(' ', ["  "] * 5))
        max_w = max(len(l) for l in char_art)
        for i in range(5):
            row = char_art[i] if i < len(char_art) else " " * max_w
            lines[i] += row.ljust(max_w) + "  "
    return "\n".join(lines)

def render_banner(text):
    top = ""
    mid = ""
    bot = ""
    for char in text.upper():
        c = BANNER_CHARS.get(char, "   ")
        top += "▄" * len(c) + " "
        mid += c + " "
        bot += "▀" * len(c) + " "
    return top + "\n" + mid + "\n" + bot

class AsciiArtWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("ASCII Art Generator")
        self.set_default_size(800, 560)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        ctrl = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        ctrl.append(Gtk.Label(label="Text:"))
        self.text_entry = Gtk.Entry()
        self.text_entry.set_text("Hello")
        self.text_entry.set_hexpand(True)
        self.text_entry.connect("changed", self.on_update)
        ctrl.append(self.text_entry)
        ctrl.append(Gtk.Label(label="Font:"))
        self.font_combo = Gtk.ComboBoxText()
        for f in ["Block", "Slim", "Banner"]:
            self.font_combo.append_text(f)
        self.font_combo.set_active(0)
        self.font_combo.connect("changed", self.on_update)
        ctrl.append(self.font_combo)
        vbox.append(ctrl)

        copy_btn = Gtk.Button(label="Copy Output")
        copy_btn.connect("clicked", self.on_copy)
        vbox.append(copy_btn)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        self.output_view = Gtk.TextView()
        self.output_view.set_monospace(True)
        self.output_view.set_editable(False)
        scroll.set_child(self.output_view)
        vbox.append(scroll)

        self.on_update(None)

    def on_update(self, *args):
        text = self.text_entry.get_text()
        font_name = self.font_combo.get_active_text()
        if font_name == "Banner":
            result = render_banner(text)
        else:
            font_data = FONTS.get(font_name, FONTS["Block"])
            result = render_block(text, font_data)
        self.output_view.get_buffer().set_text(result)

    def on_copy(self, btn):
        buf = self.output_view.get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
        Gdk.Display.get_default().get_clipboard().set(text)

class AsciiArtApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.AsciiArt")
    def do_activate(self):
        win = AsciiArtWindow(self)
        win.present()

def main():
    app = AsciiArtApp()
    app.run(None)

if __name__ == "__main__":
    main()
