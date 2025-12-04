#!/usr/bin/env python3
import sys
import datetime
import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk

class ClockWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Retro Flip Clock")
        self.set_default_size(800, 500)
        
        # Add a specific class to the window to ensure background styling works
        self.add_css_class("app-window")
        
        # Default state: Show seconds
        self.show_seconds = True

        # --- Layout ---
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.main_box.set_valign(Gtk.Align.CENTER)
        self.main_box.set_halign(Gtk.Align.CENTER)
        self.set_child(self.main_box)

        # Clock Container (Horizontal row)
        self.clock_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        self.clock_box.set_halign(Gtk.Align.CENTER)
        self.clock_box.set_valign(Gtk.Align.CENTER)
        self.main_box.append(self.clock_box)
        
        # AM/PM Label (Integrated aesthetic)
        self.ampm_label = Gtk.Label(label="AM")
        self.ampm_label.add_css_class("ampm-label")
        self.ampm_label.set_valign(Gtk.Align.START) # Align to top
        self.clock_box.append(self.ampm_label)

        # Hours Card
        self.hour_label = Gtk.Label(label="00")
        self.hour_label.add_css_class("flip-card")
        self.clock_box.append(self.hour_label)

        # Minutes Card
        self.min_label = Gtk.Label(label="00")
        self.min_label.add_css_class("flip-card")
        self.clock_box.append(self.min_label)

        # Seconds Card (Smaller, optional)
        self.sec_label = Gtk.Label(label="00")
        self.sec_label.add_css_class("flip-card")
        self.clock_box.append(self.sec_label)

        # Date Label
        self.date_label = Gtk.Label()
        self.date_label.add_css_class("date-label")
        self.main_box.append(self.date_label)
        
        # Hint text
        hint = Gtk.Label(label="(Click to toggle seconds)")
        hint.add_css_class("hint-label")
        self.main_box.append(hint)

        # --- Interaction ---
        gesture = Gtk.GestureClick()
        gesture.connect("pressed", self.on_click)
        self.add_controller(gesture)

        # Start Clock
        self.update_clock()
        GLib.timeout_add(1000, self.update_clock)

    def load_css(self):
        """Loads the CSS provider. Called after window creation to ensure display exists."""
        css_provider = Gtk.CssProvider()
        # CSS designed to match the Apple 'StandBy' mechanical clock look
        css = b"""
        .app-window {
            background-color: #000000;
        }
        
        .flip-card {
            background-color: #1a1a1a;
            color: #e0e0e0;
            border-radius: 12px;
            padding: 5px 25px;
            margin: 0 4px;
            
            /* The Mechanical Split Line */
            background-image: linear-gradient(
                to bottom,
                #222222 0%,
                #222222 50%,
                #000000 50%,
                #000000 52%,
                #222222 52%,
                #222222 100%
            );
            
            font-family: "Sans";
            font-weight: 800;
            font-size: 160px;
            letter-spacing: -4px;
            
            /* Animation Transition Setup */
            transition: transform 200ms ease-in-out;
            transform: scaleY(1.0);
        }
        
        /* The 'Flipped' state (Compressed) */
        .flipping {
            transform: scaleY(0.0);
        }

        .ampm-label {
            color: #555555;
            font-family: "Sans";
            font-weight: 700;
            font-size: 30px;
            margin-right: 10px;
            margin-top: 25px;
        }

        .date-label {
            color: #FE9F0C; /* Apple amber/orange accent for date */
            font-size: 22px;
            font-family: "Sans";
            font-weight: 600;
            margin-top: 20px;
            letter-spacing: 1px;
        }

        .hint-label {
            color: #333333;
            font-size: 11px;
            margin-top: 10px;
        }
        """
        
        try:
            css_provider.load_from_data(css)
            # Apply to the specific display of this window
            display = self.get_display() 
            if display:
                Gtk.StyleContext.add_provider_for_display(
                    display, 
                    css_provider, 
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )
            else:
                print("Warning: No display found for CSS.")
        except Exception as e:
            print(f"CSS Loading Error: {e}")

    def on_click(self, gesture, n_press, x, y):
        self.show_seconds = not self.show_seconds
        self.sec_label.set_visible(self.show_seconds)
    
    def update_card(self, label_widget, new_value):
        """Checks if value changed and triggers animation if so."""
        current_value = label_widget.get_label()
        
        if current_value != new_value:
            # 1. Trigger Flip Out (Scale -> 0)
            label_widget.add_css_class("flipping")
            
            # 2. Wait 200ms (halfway), update text, then Flip In
            GLib.timeout_add(200, self._finish_flip, label_widget, new_value)
            
    def _finish_flip(self, label_widget, new_value):
        # Update text while invisible (scaled to 0)
        label_widget.set_label(new_value)
        # Remove class to trigger Flip In (Scale -> 1)
        label_widget.remove_css_class("flipping")
        return False # Stop timeout

    def update_clock(self):
        now = datetime.datetime.now()
        
        # We now use the helper method to animate changes
        self.update_card(self.hour_label, now.strftime("%I"))
        self.update_card(self.min_label, now.strftime("%M"))
        self.update_card(self.sec_label, now.strftime("%S"))
        
        self.ampm_label.set_label(now.strftime("%p"))
        self.date_label.set_label(now.strftime("%A, %B %d").upper())
        return True

def on_activate(app):
    win = ClockWindow(app)
    # Load CSS BEFORE showing the window to ensure styles apply immediately
    win.load_css()
    win.present()
    win.maximize()

if __name__ == "__main__":
    app = Gtk.Application(application_id='com.pens.DigitalClock')
    app.connect('activate', on_activate)
    app.run(None)