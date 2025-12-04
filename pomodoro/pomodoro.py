#!/usr/bin/env python3
import sys
import math
import gi
import cairo

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk, Pango

class PomodoroWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Focus Timer")
        self.set_default_size(500, 700)
        
        # --- State ---
        self.total_seconds = 25 * 60
        self.current_seconds = self.total_seconds
        self.is_running = False
        self.timer_id = None
        self.mode_color = (1.0, 0.6, 0.0) # Orange (Focus) by default

        # --- Styling ---
        self.apply_css()
        self.add_css_class("app-window")

        # --- Layout ---
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=30)
        main_box.set_valign(Gtk.Align.CENTER)
        main_box.set_halign(Gtk.Align.CENTER)
        self.set_child(main_box)

        # 1. Mode Picker
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        mode_box.set_halign(Gtk.Align.CENTER)
        main_box.append(mode_box)

        self.btn_focus = self.create_mode_btn("Focus", 25, "mode-btn-active")
        self.btn_short = self.create_mode_btn("Short Break", 5, "mode-btn")
        self.btn_long = self.create_mode_btn("Long Break", 15, "mode-btn")
        
        mode_box.append(self.btn_focus)
        mode_box.append(self.btn_short)
        mode_box.append(self.btn_long)

        # 2. The Ring & Timer Display (Using Overlay)
        # We use Gtk.Overlay to put Labels ON TOP of the DrawingArea
        self.overlay = Gtk.Overlay()
        self.overlay.set_halign(Gtk.Align.CENTER)
        main_box.append(self.overlay)

        # Layer 1: Background (Drawing Area for Rings)
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_content_width(300)
        self.drawing_area.set_content_height(300)
        self.drawing_area.set_draw_func(self.on_draw)
        self.overlay.set_child(self.drawing_area)

        # Layer 2: Foreground (Time Text)
        center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        center_box.set_valign(Gtk.Align.CENTER)
        center_box.set_halign(Gtk.Align.CENTER)
        # Pass-through input so clicks go through to background if needed
        center_box.set_can_target(False) 
        
        self.time_label = Gtk.Label(label="25:00")
        self.time_label.add_css_class("timer-text")
        center_box.append(self.time_label)
        
        self.bell_label = Gtk.Label(label="🔔")
        self.bell_label.add_css_class("bell-icon")
        center_box.append(self.bell_label)

        self.overlay.add_overlay(center_box)

        # 3. Time Adjusters
        adj_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        adj_box.set_halign(Gtk.Align.CENTER)
        main_box.append(adj_box)

        btn_minus = Gtk.Button(label="-1m")
        btn_minus.add_css_class("adj-btn")
        btn_minus.connect("clicked", self.adjust_time, -60)
        adj_box.append(btn_minus)

        btn_plus = Gtk.Button(label="+1m")
        btn_plus.add_css_class("adj-btn")
        btn_plus.connect("clicked", self.adjust_time, 60)
        adj_box.append(btn_plus)

        # 4. Control Buttons (Circle style)
        ctrl_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=60)
        ctrl_box.set_halign(Gtk.Align.CENTER)
        main_box.append(ctrl_box)

        self.btn_cancel = Gtk.Button(label="Cancel")
        self.btn_cancel.add_css_class("circle-btn-gray")
        self.btn_cancel.set_size_request(80, 80)
        self.btn_cancel.connect("clicked", self.on_cancel)
        ctrl_box.append(self.btn_cancel)

        self.btn_start = Gtk.Button(label="Start")
        self.btn_start.add_css_class("circle-btn-green")
        self.btn_start.set_size_request(80, 80)
        self.btn_start.connect("clicked", self.on_toggle_start)
        ctrl_box.append(self.btn_start)

    def create_mode_btn(self, label, mins, css_class):
        btn = Gtk.Button(label=label)
        btn.add_css_class(css_class)
        btn.connect("clicked", self.set_mode, mins)
        return btn

    def update_display(self):
        # Update Text
        mins = self.current_seconds // 60
        secs = self.current_seconds % 60
        self.time_label.set_label(f"{mins:02d}:{secs:02d}")
        
        # Update Ring
        self.drawing_area.queue_draw()

    def set_mode(self, btn, mins):
        self.on_cancel(None) # Reset first
        self.total_seconds = mins * 60
        self.current_seconds = self.total_seconds
        
        # Reset styles
        self.btn_focus.remove_css_class("mode-btn-active")
        self.btn_short.remove_css_class("mode-btn-active")
        self.btn_long.remove_css_class("mode-btn-active")
        self.btn_focus.add_css_class("mode-btn")
        self.btn_short.add_css_class("mode-btn")
        self.btn_long.add_css_class("mode-btn")
        
        btn.remove_css_class("mode-btn")
        btn.add_css_class("mode-btn-active")

        # Set Color
        if mins == 5: self.mode_color = (0.2, 0.6, 1.0) # Blue
        elif mins == 15: self.mode_color = (0.6, 0.2, 1.0) # Purple
        else: self.mode_color = (1.0, 0.6, 0.0) # Orange

        self.update_display()

    def adjust_time(self, btn, amount):
        if self.is_running: return
        new_time = self.current_seconds + amount
        if new_time > 0:
            self.total_seconds = new_time
            self.current_seconds = new_time
            self.update_display()

    def on_toggle_start(self, btn):
        if self.is_running:
            # Pause
            self.is_running = False
            if self.timer_id:
                GLib.source_remove(self.timer_id)
                self.timer_id = None
            self.btn_start.set_label("Resume")
            self.btn_start.remove_css_class("circle-btn-orange")
            self.btn_start.add_css_class("circle-btn-green")
        else:
            # Start
            self.is_running = True
            self.timer_id = GLib.timeout_add(1000, self.tick)
            self.btn_start.set_label("Pause")
            self.btn_start.remove_css_class("circle-btn-green")
            self.btn_start.add_css_class("circle-btn-orange")

    def on_cancel(self, btn):
        self.is_running = False
        if self.timer_id:
            GLib.source_remove(self.timer_id)
            self.timer_id = None
        self.current_seconds = self.total_seconds
        self.btn_start.set_label("Start")
        self.btn_start.remove_css_class("circle-btn-orange")
        self.btn_start.add_css_class("circle-btn-green")
        self.update_display()

    def tick(self):
        if self.current_seconds > 0:
            self.current_seconds -= 1
            self.update_display()
            return True
        else:
            self.on_cancel(None)
            return False

    def on_draw(self, area, cr, width, height, data):
        # We ONLY draw the circles here now. Text is handled by GtkLabel.
        cx = width / 2
        cy = height / 2
        radius = min(width, height) / 2 - 20
        
        # 1. Background Ring (Grey)
        cr.set_line_width(12) # Thicker for modern look
        cr.set_source_rgba(0.2, 0.2, 0.2, 1)
        cr.arc(cx, cy, radius, 0, 2 * math.pi)
        cr.stroke()

        # 2. Progress Ring (Colored)
        if self.total_seconds > 0:
            progress = self.current_seconds / self.total_seconds
        else:
            progress = 0
            
        start_angle = -math.pi / 2
        end_angle = start_angle + (2 * math.pi * progress)
        
        cr.set_line_width(12)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        r, g, b = self.mode_color
        cr.set_source_rgba(r, g, b, 1)
        
        cr.arc(cx, cy, radius, start_angle, end_angle)
        cr.stroke()
        # No text drawing here! Safest method.

    def apply_css(self):
        css_provider = Gtk.CssProvider()
        css = b"""
        .app-window { background-color: #000000; color: white; }
        
        /* New Text Styles */
        .timer-text {
            font-size: 80px;
            font-family: "Sans";
            font-weight: 200; /* Ultra Thin */
            color: white;
            margin-bottom: -10px;
        }
        .bell-icon {
            font-size: 24px;
            color: #636366;
        }

        .mode-btn { 
            background: #1c1c1e; 
            color: #8e8e93; 
            border-radius: 20px; 
            padding: 8px 16px; 
            font-weight: bold; 
            border: none;
        }
        .mode-btn:hover { background: #2c2c2e; }
        .mode-btn-active { 
            background: #3a3a3c; 
            color: white; 
            border-radius: 20px; 
            padding: 8px 16px; 
            font-weight: bold; 
            border: none;
        }

        .adj-btn {
            background: #1c1c1e;
            color: white;
            border-radius: 10px;
            font-weight: bold;
        }

        /* Circular Buttons */
        .circle-btn-gray {
            background: #3a3a3c;
            color: white;
            border-radius: 9999px; /* Full circle */
            font-size: 16px;
            font-weight: bold;
            border: 2px solid #3a3a3c;
        }
        .circle-btn-green {
            background: #1b4b28; /* Dark Green bg */
            color: #61d982; /* Light Green text */
            border-radius: 9999px;
            font-size: 16px;
            font-weight: bold;
            border: 2px solid #1b4b28;
        }
        .circle-btn-orange {
            background: #4b3210; /* Dark Orange bg */
            color: #ffaa55; /* Light Orange text */
            border-radius: 9999px;
            font-size: 16px;
            font-weight: bold;
            border: 2px solid #4b3210;
        }
        """
        css_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

def on_activate(app):
    win = PomodoroWindow(app)
    win.present()
    win.maximize()

if __name__ == "__main__":
    app = Gtk.Application(application_id='com.pens.Pomodoro')
    app.connect('activate', on_activate)
    app.run(None)