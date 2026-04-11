#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GdkPixbuf
import math

# Simple QR code generator - Version 1 (21x21), ECC Level M
# Implements core QR algorithm in pure Python

def get_gf256_tables():
    exp = [0] * 512
    log = [0] * 256
    x = 1
    for i in range(255):
        exp[i] = x
        log[x] = i
        x = x << 1
        if x & 0x100:
            x ^= 0x11d
    for i in range(255, 512):
        exp[i] = exp[i - 255]
    return exp, log

GF_EXP, GF_LOG = get_gf256_tables()

def gf_mul(a, b):
    if a == 0 or b == 0: return 0
    return GF_EXP[(GF_LOG[a] + GF_LOG[b]) % 255]

def gf_poly_mul(p, q):
    r = [0] * (len(p) + len(q) - 1)
    for j, qj in enumerate(q):
        for i, pi in enumerate(p):
            r[i + j] ^= gf_mul(pi, qj)
    return r

def gen_poly(n):
    g = [1]
    for i in range(n):
        g = gf_poly_mul(g, [1, GF_EXP[i]])
    return g

def rs_encode(data, n_ec):
    g = gen_poly(n_ec)
    padded = data + [0] * n_ec
    for i in range(len(data)):
        coeff = padded[i]
        if coeff != 0:
            for j, gj in enumerate(g):
                padded[i + j] ^= gf_mul(gj, coeff)
    return padded[len(data):]

def bits_to_bytes(bits):
    result = []
    for i in range(0, len(bits), 8):
        byte = int("".join(str(b) for b in bits[i:i+8]), 2)
        result.append(byte)
    return result

def make_qr_v1(text):
    # Version 1 QR: 21x21, max 17 alphanumeric or 25 numeric chars
    # Use numeric mode for digits-only, else byte mode
    size = 21
    matrix = [[None] * size for _ in range(size)]

    def set_module(r, c, val):
        if 0 <= r < size and 0 <= c < size:
            matrix[r][c] = val

    def add_finder(r, c):
        for dr in range(-1, 8):
            for dc in range(-1, 8):
                if 0 <= r+dr < size and 0 <= c+dc < size:
                    if (dr in (-1, 7) or dc in (-1, 7) or
                            (1 <= dr <= 5 and 1 <= dc <= 5 and (dr in (1,5) or dc in (1,5)))):
                        val = False
                    elif 2 <= dr <= 4 and 2 <= dc <= 4:
                        val = True
                    elif dr in (0, 6) or dc in (0, 6):
                        val = True
                    else:
                        val = False
                    matrix[r+dr][c+dc] = val

    add_finder(0, 0); add_finder(0, 14); add_finder(14, 0)

    for i in range(8, 13):
        matrix[6][i] = (i % 2 == 0)
        matrix[i][6] = (i % 2 == 0)

    matrix[13][8] = True

    # Encode data (byte mode)
    data_bits = [0, 1, 0, 0]  # byte mode
    byte_count = len(text.encode('iso-8859-1', errors='replace'))
    for b in format(byte_count, '08b'):
        data_bits.append(int(b))
    for ch in text.encode('iso-8859-1', errors='replace'):
        for b in format(ch, '08b'):
            data_bits.append(int(b))
    data_bits.extend([0, 0, 0, 0])  # terminator
    while len(data_bits) % 8:
        data_bits.append(0)
    data_bytes = bits_to_bytes(data_bits)
    pad_bytes = [0xEC, 0x11]
    while len(data_bytes) < 16:
        data_bytes.append(pad_bytes[len(data_bytes) % 2])
    data_bytes = data_bytes[:16]
    ec_bytes = rs_encode(data_bytes, 10)
    all_bytes = data_bytes + ec_bytes

    all_bits = []
    for byte in all_bytes:
        for b in format(byte, '08b'):
            all_bits.append(int(b))

    # Place data bits
    col = size - 1
    going_up = True
    bit_idx = 0
    while col > 0:
        if col == 6: col -= 1
        rows = range(size - 1, -1, -1) if going_up else range(size)
        for r in rows:
            for dc in [0, -1]:
                c = col + dc
                if matrix[r][c] is None:
                    if bit_idx < len(all_bits):
                        matrix[r][c] = bool(all_bits[bit_idx])
                    else:
                        matrix[r][c] = False
                    bit_idx += 1
        going_up = not going_up
        col -= 2

    # Apply mask pattern 0
    for r in range(size):
        for c in range(size):
            if matrix[r][c] is None:
                matrix[r][c] = False
            elif (r + c) % 2 == 0 and matrix[r][c] is not None:
                # Skip finder/timing areas
                in_finder = (r <= 8 and (c <= 8 or c >= 13)) or (r >= 13 and c <= 8)
                if not in_finder:
                    matrix[r][c] = not matrix[r][c]

    # Format info (mask 0, ECL M = 10)
    fmt = 0b100000011001110
    for i in range(6):
        matrix[8][i] = bool((fmt >> (14 - i)) & 1)
    matrix[8][7] = bool((fmt >> 8) & 1)
    matrix[8][8] = bool((fmt >> 7) & 1)
    matrix[7][8] = bool((fmt >> 6) & 1)
    for i in range(6):
        matrix[5 - i][8] = bool((fmt >> i) & 1)

    return matrix

class QrGeneratorWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("QR Code Generator")
        self.set_default_size(500, 560)
        self.qr_matrix = None
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(12); vbox.set_margin_bottom(12)
        vbox.set_margin_start(12); vbox.set_margin_end(12)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="QR Code Generator", css_classes=["title"]))

        input_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.text_entry = Gtk.Entry()
        self.text_entry.set_placeholder_text("Enter text or URL (max ~17 chars for v1)...")
        self.text_entry.set_hexpand(True)
        self.text_entry.connect("changed", self.on_generate)
        input_box.append(self.text_entry)
        gen_btn = Gtk.Button(label="Generate")
        gen_btn.connect("clicked", self.on_generate)
        input_box.append(gen_btn)
        vbox.append(input_box)

        self.status_label = Gtk.Label(label="Type text above to generate QR code")
        vbox.append(self.status_label)

        self.qr_area = Gtk.DrawingArea()
        self.qr_area.set_size_request(420, 420)
        self.qr_area.set_draw_func(self.on_draw)
        vbox.append(self.qr_area)

        save_btn = Gtk.Button(label="Export PNG")
        save_btn.connect("clicked", self.on_export)
        vbox.append(save_btn)

    def on_generate(self, *args):
        text = self.text_entry.get_text()
        if not text:
            self.qr_matrix = None
            self.qr_area.queue_draw()
            return
        try:
            self.qr_matrix = make_qr_v1(text)
            self.status_label.set_text(f"Generated QR code for: {text!r} (Version 1, 21×21)")
        except Exception as e:
            self.status_label.set_text(f"Error: {e} (text may be too long)")
            self.qr_matrix = None
        self.qr_area.queue_draw()

    def on_draw(self, area, cr, w, h):
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(0, 0, w, h)
        cr.fill()
        if not self.qr_matrix:
            cr.set_source_rgb(0.5, 0.5, 0.5)
            cr.set_font_size(18)
            cr.move_to(60, h/2)
            cr.show_text("Enter text to generate QR code")
            return
        size = len(self.qr_matrix)
        cell = min(w, h) / (size + 8)
        offset_x = (w - size * cell) / 2
        offset_y = (h - size * cell) / 2
        for r, row in enumerate(self.qr_matrix):
            for c, val in enumerate(row):
                if val:
                    cr.set_source_rgb(0, 0, 0)
                else:
                    cr.set_source_rgb(1, 1, 1)
                cr.rectangle(offset_x + c * cell, offset_y + r * cell, cell, cell)
                cr.fill()

    def on_export(self, btn):
        if not self.qr_matrix: return
        dialog = Gtk.FileDialog(); dialog.set_title("Save QR Code PNG")
        dialog.save(self, None, self.on_save_file)

    def on_save_file(self, dialog, result):
        try:
            f = dialog.save_finish(result)
            if f:
                size = len(self.qr_matrix)
                cell = 20
                img_size = (size + 8) * cell
                data = bytearray([255] * img_size * img_size * 3)
                offset = 4 * cell
                for r, row in enumerate(self.qr_matrix):
                    for c, val in enumerate(row):
                        color = 0 if val else 255
                        for dy in range(cell):
                            for dx in range(cell):
                                px = offset + c*cell + dx
                                py = offset + r*cell + dy
                                idx = (py * img_size + px) * 3
                                data[idx] = data[idx+1] = data[idx+2] = color
                pb = GdkPixbuf.Pixbuf.new_from_data(bytes(data), GdkPixbuf.Colorspace.RGB, False, 8, img_size, img_size, img_size*3)
                path = f.get_path()
                if not path.endswith(".png"): path += ".png"
                pb.savev(path, "png", [], [])
                self.status_label.set_text(f"Saved to {path}")
        except Exception as e:
            self.status_label.set_text(f"Save error: {e}")

class QrGeneratorApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.QrGenerator")
    def do_activate(self):
        win = QrGeneratorWindow(self)
        win.present()

def main():
    app = QrGeneratorApp()
    app.run(None)

if __name__ == "__main__":
    main()
