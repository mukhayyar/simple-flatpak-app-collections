#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, GdkPixbuf
import math

def encode_code128(text):
    """Pure Python Code128B barcode encoder"""
    CODE128_B = {chr(i+32): i for i in range(96)}
    CODE128_B['\x00'] = 64
    START_B = 104
    STOP = 106

    values = [START_B]
    checksum = START_B
    for i, ch in enumerate(text):
        val = CODE128_B.get(ch, 0)
        values.append(val)
        checksum += val * (i + 1)
    values.append(checksum % 103)
    values.append(STOP)

    CODE128_PATTERNS = [
        "11011001100","11001101100","11001100110","10010011000","10010001100",
        "10001001100","10011001000","10011000100","10001100100","11001001000",
        "11001000100","11000100100","10110011100","10011011100","10011001110",
        "10111001100","10011101100","10011100110","11001110010","11001011100",
        "11001001110","11011100100","11001110100","11101101110","11101001100",
        "11100101100","11100100110","11101100100","11100110100","11100110010",
        "11011011000","11011000110","11000110110","10100011000","10001011000",
        "10001000110","10110001000","10001101000","10001100010","11010001000",
        "11000101000","11000100010","10110111000","10110001110","10001101110",
        "10111011000","10111000110","10001110110","11101110110","11010001110",
        "11000101110","11011101000","11011100010","11011101110","11101011000",
        "11101000110","11100010110","11101101000","11101100010","11100011010",
        "11101111010","11001000010","11110001010","10100110000","10100001100",
        "10010110000","10010000110","10000101100","10000100110","10110010000",
        "10110000100","10011010000","10011000010","10000110100","10000110010",
        "11000010010","11001010000","11110111010","11000010100","10001111010",
        "10100111100","10010111100","10010011110","10111100100","10011110100",
        "10011110010","11110100100","11110010100","11110010010","11011011110",
        "11011110110","11110110110","10101111000","10100011110","10001011110",
        "10111101000","10111100010","11110101000","11110100010","10111011110",
        "10111101110","11101011110","11110101110","11010000100","11010010000",
        "11010011100","1100011101011",
    ]
    bars = "1010011011"  # quiet zone
    for val in values:
        if val < len(CODE128_PATTERNS):
            bars += CODE128_PATTERNS[val]
    bars += "11"
    return bars

class BarcodeGenWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Barcode Generator")
        self.set_default_size(700, 480)
        self.barcode_data = ""
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(16); vbox.set_margin_bottom(16)
        vbox.set_margin_start(20); vbox.set_margin_end(20)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Barcode Generator", css_classes=["title"]))

        type_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        type_box.set_halign(Gtk.Align.CENTER)
        type_box.append(Gtk.Label(label="Type:"))
        self.type_combo = Gtk.ComboBoxText()
        for t in ["Code 128", "EAN-8 (digits)", "EAN-13 (digits)", "Binary (0s and 1s)"]:
            self.type_combo.append_text(t)
        self.type_combo.set_active(0)
        type_box.append(self.type_combo)
        vbox.append(type_box)

        input_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        input_box.set_halign(Gtk.Align.FILL)
        input_box.append(Gtk.Label(label="Data:"))
        self.data_entry = Gtk.Entry()
        self.data_entry.set_text("Hello World 123")
        self.data_entry.set_hexpand(True)
        self.data_entry.connect("changed", self.on_generate)
        input_box.append(self.data_entry)
        gen_btn = Gtk.Button(label="Generate")
        gen_btn.connect("clicked", self.on_generate)
        input_box.append(gen_btn)
        vbox.append(input_box)

        scale_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        scale_box.set_halign(Gtk.Align.CENTER)
        scale_box.append(Gtk.Label(label="Scale:"))
        self.scale_spin = Gtk.SpinButton.new_with_range(1, 8, 1)
        self.scale_spin.set_value(2)
        self.scale_spin.connect("value-changed", self.on_generate)
        scale_box.append(self.scale_spin)
        scale_box.append(Gtk.Label(label="Height:"))
        self.height_spin = Gtk.SpinButton.new_with_range(30, 200, 5)
        self.height_spin.set_value(80)
        self.height_spin.connect("value-changed", self.on_generate)
        scale_box.append(self.height_spin)
        vbox.append(scale_box)

        barcode_frame = Gtk.Frame(label="Barcode")
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(120)
        self.barcode_area = Gtk.DrawingArea()
        self.barcode_area.set_draw_func(self.draw_barcode)
        scroll.set_child(self.barcode_area)
        barcode_frame.set_child(scroll)
        vbox.append(barcode_frame)

        self.info_label = Gtk.Label(label="", xalign=0)
        vbox.append(self.info_label)

        save_btn = Gtk.Button(label="Save as PNG")
        save_btn.set_halign(Gtk.Align.CENTER)
        save_btn.connect("clicked", self.on_save)
        vbox.append(save_btn)

        self.on_generate(None)

    def on_generate(self, widget):
        text = self.data_entry.get_text()
        barcode_type = self.type_combo.get_active_text()
        if barcode_type == "Binary (0s and 1s)":
            self.barcode_data = ''.join('1' if c == '1' else '0' for c in text if c in '01')
        elif barcode_type in ("EAN-8 (digits)", "EAN-13 (digits)"):
            digits = ''.join(c for c in text if c.isdigit())
            if barcode_type == "EAN-8 (digits)":
                digits = digits[:7].zfill(7)
                check = (3 * sum(int(digits[i]) for i in range(0, 7, 2)) +
                         sum(int(digits[i]) for i in range(1, 7, 2))) % 10
                check = (10 - check) % 10
                digits = digits + str(check)
            self.barcode_data = encode_code128(digits)
        else:
            self.barcode_data = encode_code128(text)
        scale = int(self.scale_spin.get_value())
        w = len(self.barcode_data) * scale + 40
        h = int(self.height_spin.get_value()) + 40
        self.barcode_area.set_size_request(w, h)
        self.info_label.set_text(f"Bars: {len(self.barcode_data)}  |  Width: {w}px")
        self.barcode_area.queue_draw()

    def draw_barcode(self, area, cr, w, h):
        cr.set_source_rgb(1, 1, 1); cr.rectangle(0, 0, w, h); cr.fill()
        if not self.barcode_data:
            return
        scale = int(self.scale_spin.get_value())
        bar_h = int(self.height_spin.get_value())
        x_start = 20
        y_start = 10
        for i, bit in enumerate(self.barcode_data):
            x = x_start + i * scale
            if bit == '1':
                cr.set_source_rgb(0, 0, 0)
                cr.rectangle(x, y_start, scale, bar_h)
                cr.fill()
        cr.set_source_rgb(0, 0, 0); cr.set_font_size(11)
        text = self.data_entry.get_text()[:50]
        cr.move_to(x_start, y_start + bar_h + 16)
        cr.show_text(text)

    def on_save(self, btn):
        dialog = Gtk.FileDialog()
        dialog.save(self, None, self.do_save)

    def do_save(self, dialog, result):
        try:
            f = dialog.save_finish(result)
            if f:
                path = f.get_path()
                if not path.endswith('.png'):
                    path += '.png'
                import cairo
                scale = int(self.scale_spin.get_value())
                bar_h = int(self.height_spin.get_value())
                w = len(self.barcode_data) * scale + 40
                h = bar_h + 40
                surface = cairo.ImageSurface(cairo.FORMAT_RGB24, w, h)
                cr = cairo.Context(surface)
                self.draw_barcode(None, cr, w, h)
                surface.write_to_png(path)
        except Exception as e:
            pass

class BarcodeGenApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.BarcodeGen")
    def do_activate(self):
        win = BarcodeGenWindow(self); win.present()

def main():
    app = BarcodeGenApp(); app.run(None)

if __name__ == "__main__":
    main()
