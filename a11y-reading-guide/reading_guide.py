#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk, Pango
import math

SAMPLE_TEXTS = {
    "Dyslexia guide": (
        "Reading guides help focus your eyes on the current line of text.\n"
        "The highlighted band follows your mouse or can be scrolled manually.\n"
        "This tool is especially helpful for people with dyslexia or attention difficulties.\n"
        "OpenDyslexic font uses heavier bottoms on letters to indicate direction.\n"
        "Increased letter spacing and line height also improve readability.\n"
        "The ruler provides a visual anchor to prevent skipping lines.\n"
        "Color overlays (tinted lenses effect) can reduce visual stress.\n"
        "Studies show colored overlays help some readers with Meares-Irlen syndrome.\n"
        "Try different tint colors to find what works best for you.\n"
        "Regular breaks (every 20 minutes) also reduce reading fatigue."
    ),
    "Long article": (
        "Accessibility in software design means creating applications that can be used\n"
        "by people with a wide range of disabilities and abilities. This includes visual\n"
        "impairments such as blindness or low vision, auditory impairments, motor\n"
        "impairments that limit keyboard or mouse use, and cognitive impairments.\n\n"
        "The Web Content Accessibility Guidelines (WCAG) provide a framework for making\n"
        "digital content more accessible. These guidelines are organized around four\n"
        "principles: Perceivable, Operable, Understandable, and Robust.\n\n"
        "For desktop applications, similar principles apply. GTK provides built-in\n"
        "accessibility support through the ATK (Accessibility Toolkit) interface,\n"
        "which allows screen readers like Orca to describe interface elements to users."
    ),
}

TINT_COLORS = {
    "None": None,
    "Yellow": (1.0, 1.0, 0.0, 0.15),
    "Blue": (0.0, 0.4, 1.0, 0.12),
    "Green": (0.0, 0.8, 0.0, 0.12),
    "Rose": (1.0, 0.3, 0.5, 0.12),
    "Peach": (1.0, 0.7, 0.4, 0.15),
}

class ReadingGuideWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Reading Guide")
        self.set_default_size(800, 600)
        self.guide_y = 0
        self.guide_height = 28
        self.follow_mouse = True
        self.tint = None
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Reading Guide", css_classes=["title"]))

        # Controls
        ctrl_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        ctrl_box.set_halign(Gtk.Align.CENTER)

        ctrl_box.append(Gtk.Label(label="Guide height:"))
        self.height_spin = Gtk.SpinButton.new_with_range(16, 80, 2)
        self.height_spin.set_value(self.guide_height)
        self.height_spin.connect("value-changed", lambda s: self.set_guide_height(int(s.get_value())))
        ctrl_box.append(self.height_spin)

        follow_btn = Gtk.ToggleButton(label="Follow mouse")
        follow_btn.set_active(True)
        follow_btn.connect("toggled", lambda b: self.set_follow(b.get_active()))
        ctrl_box.append(follow_btn)

        ctrl_box.append(Gtk.Label(label="Tint:"))
        self.tint_combo = Gtk.ComboBoxText()
        for t in TINT_COLORS:
            self.tint_combo.append_text(t)
        self.tint_combo.set_active(0)
        self.tint_combo.connect("changed", self.on_tint_changed)
        ctrl_box.append(self.tint_combo)
        vbox.append(ctrl_box)

        # Font controls
        font_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        font_box.set_halign(Gtk.Align.CENTER)
        font_box.append(Gtk.Label(label="Font size:"))
        self.font_size_spin = Gtk.SpinButton.new_with_range(8, 36, 1)
        self.font_size_spin.set_value(14)
        self.font_size_spin.connect("value-changed", self.on_font_changed)
        font_box.append(self.font_size_spin)

        font_box.append(Gtk.Label(label="Line spacing:"))
        self.line_spin = Gtk.SpinButton.new_with_range(1.0, 3.0, 0.1)
        self.line_spin.set_value(1.5)
        self.line_spin.connect("value-changed", self.on_font_changed)
        font_box.append(self.line_spin)

        font_box.append(Gtk.Label(label="Text:"))
        self.text_combo = Gtk.ComboBoxText()
        for t in SAMPLE_TEXTS:
            self.text_combo.append_text(t)
        self.text_combo.set_active(0)
        self.text_combo.connect("changed", self.on_text_changed)
        font_box.append(self.text_combo)
        vbox.append(font_box)

        # Reading area (overlay with canvas)
        reading_frame = Gtk.Frame(label="Reading Area (move mouse over text)")
        reading_overlay = Gtk.Overlay()

        self.text_view = Gtk.TextView()
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.text_view.set_editable(False)
        self.text_view.set_left_margin(12)
        self.text_view.set_right_margin(12)
        self.text_view.set_top_margin(8)
        self.text_view.set_bottom_margin(8)

        # Load first text
        first_text = list(SAMPLE_TEXTS.values())[0]
        self.text_view.get_buffer().set_text(first_text)
        self.on_font_changed(None)

        text_scroll = Gtk.ScrolledWindow()
        text_scroll.set_vexpand(True)
        text_scroll.set_child(self.text_view)

        self.guide_canvas = Gtk.DrawingArea()
        self.guide_canvas.set_draw_func(self.draw_guide)

        reading_overlay.set_child(text_scroll)
        reading_overlay.add_overlay(self.guide_canvas)
        reading_frame.set_child(reading_overlay)
        vbox.append(reading_frame)

        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self.on_motion)
        self.guide_canvas.add_controller(motion)
        reading_overlay.add_controller(Gtk.EventControllerMotion())
        self.text_view.add_controller(Gtk.EventControllerMotion())

        motion2 = Gtk.EventControllerMotion()
        motion2.connect("motion", self.on_motion)
        self.text_view.add_controller(motion2)

        self.status_label = Gtk.Label(
            label="Move mouse over text to position guide | Use scrollwheel or keyboard in text area",
            xalign=0)
        self.status_label.set_css_classes(["dim-label"])
        vbox.append(self.status_label)

    def set_guide_height(self, h):
        self.guide_height = h
        self.guide_canvas.queue_draw()

    def set_follow(self, val):
        self.follow_mouse = val

    def on_tint_changed(self, combo):
        name = combo.get_active_text()
        self.tint = TINT_COLORS.get(name)
        self.guide_canvas.queue_draw()

    def on_font_changed(self, widget):
        size = int(self.font_size_spin.get_value())
        spacing = self.line_spin.get_value()
        fd = Pango.FontDescription.from_string(f"Sans {size}")
        self.text_view.set_font(fd)
        self.guide_height = max(20, int(size * spacing * 1.5))
        self.height_spin.set_value(self.guide_height)
        self.guide_canvas.queue_draw()

    def on_text_changed(self, combo):
        name = combo.get_active_text()
        if name in SAMPLE_TEXTS:
            self.text_view.get_buffer().set_text(SAMPLE_TEXTS[name])

    def on_motion(self, ctrl, x, y):
        if self.follow_mouse:
            self.guide_y = y - self.guide_height // 2
            self.guide_canvas.queue_draw()

    def draw_guide(self, area, cr, w, h):
        gy = self.guide_y
        gh = self.guide_height

        # Apply tint overlay
        if self.tint:
            r, g, b, a = self.tint
            cr.set_source_rgba(r, g, b, a)
            cr.rectangle(0, 0, w, h)
            cr.fill()

        # Darken above guide
        cr.set_source_rgba(0, 0, 0, 0.3)
        cr.rectangle(0, 0, w, gy)
        cr.fill()

        # Highlight band (semi-transparent yellow)
        cr.set_source_rgba(1.0, 1.0, 0.0, 0.2)
        cr.rectangle(0, gy, w, gh)
        cr.fill()

        # Guide border lines
        cr.set_source_rgba(0.8, 0.6, 0.0, 0.8)
        cr.set_line_width(1.5)
        cr.move_to(0, gy); cr.line_to(w, gy); cr.stroke()
        cr.move_to(0, gy + gh); cr.line_to(w, gy + gh); cr.stroke()

        # Darken below guide
        cr.set_source_rgba(0, 0, 0, 0.3)
        cr.rectangle(0, gy + gh, w, h - gy - gh)
        cr.fill()

class ReadingGuideApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.ReadingGuide")
    def do_activate(self):
        win = ReadingGuideWindow(self); win.present()

def main():
    app = ReadingGuideApp(); app.run(None)

if __name__ == "__main__":
    main()
