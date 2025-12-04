#!/usr/bin/env python3
import sys
import gi
import random

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk

class HelloWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Hello World Creative")
        self.set_default_size(800, 600)
        
        # --- Data ---
        self.greetings = [
            "Hello World",         # English
            "Hola Mundo",          # Spanish
            "Bonjour le Monde",    # French
            "Hallo Welt",          # German
            "Ciao Mondo",          # Italian
            "Halo Dunia",        # Japanese
            "Olá Mundo",           # Portuguese
            "Привет мир",          # Russian
            "你好，世界",           # Chinese
            "नमस्ते दुनिया"          # Hindi
        ]
        
        self.bg_colors = [
            "#FF6B6B", # Pastel Red
            "#4ECDC4", # Teal
            "#45B7D1", # Sky Blue
            "#96CEB4", # Mint
            "#FFEEAD", # Pale Yellow
            "#D4A5A5", # Dusty Rose
            "#9B59B6", # Purple
            "#3498DB", # Blue
            "#E67E22", # Orange
            "#1ABC9C"  # Green
        ]

        # --- State ---
        self.lang_index = 0
        self.char_index = 0
        self.is_deleting = False
        self.wait_counter = 0
        
        # --- UI Setup ---
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_box.set_halign(Gtk.Align.FILL)
        self.main_box.set_valign(Gtk.Align.FILL)
        self.set_child(self.main_box)

        self.label = Gtk.Label(label="")
        self.label.set_halign(Gtk.Align.CENTER)
        self.label.set_valign(Gtk.Align.CENTER)
        self.label.set_hexpand(True)
        self.label.set_vexpand(True)
        self.main_box.append(self.label)

        # --- Styling ---
        self.bg_provider = Gtk.CssProvider()
        self.base_provider = Gtk.CssProvider()
        
        # Base styles for text
        css = b"""
        .hello-label {
            font-size: 90px;
            font-weight: 800;
            color: white;
            text-shadow: 0px 5px 15px rgba(0,0,0,0.3);
            font-family: "Sans";
        }
        window {
            transition: background-color 1s ease;
        }
        """
        self.base_provider.load_from_data(css)
        
        # Apply Base CSS
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display, 
                self.base_provider, 
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            # Add the dynamic provider with higher priority
            Gtk.StyleContext.add_provider_for_display(
                display, 
                self.bg_provider, 
                Gtk.STYLE_PROVIDER_PRIORITY_USER
            )

        self.label.add_css_class("hello-label")
        
        # Initialize Background
        self.update_background_color()

        # Start Animation Loop (Runs every 100ms)
        GLib.timeout_add(100, self.tick)

    def update_background_color(self):
        """Updates the CSS provider with a new background color."""
        color = self.bg_colors[self.lang_index % len(self.bg_colors)]
        css_string = f"""
        window {{
            background-color: {color};
        }}
        """
        self.bg_provider.load_from_data(css_string.encode('utf-8'))

    def tick(self):
        """Main animation loop handling the Typewriter effect."""
        current_text = self.greetings[self.lang_index]
        
        if not self.is_deleting:
            # TYPING PHASE
            if self.char_index < len(current_text):
                self.char_index += 1
                self.label.set_label(current_text[:self.char_index] + "|") # Add cursor
            else:
                # Finished typing, wait a bit
                self.wait_counter += 1
                if self.wait_counter > 20: # Wait 2 seconds (20 * 100ms)
                    self.is_deleting = True
                    self.wait_counter = 0
                elif self.wait_counter % 5 < 3:
                     # Blink cursor while waiting
                    self.label.set_label(current_text + "|")
                else:
                    self.label.set_label(current_text)
                    
        else:
            # DELETING PHASE
            if self.char_index > 0:
                self.char_index -= 1
                self.label.set_label(current_text[:self.char_index] + "|")
            else:
                # Finished deleting, switch language
                self.is_deleting = False
                self.lang_index = (self.lang_index + 1) % len(self.greetings)
                self.update_background_color()

        return True # Keep timer running

def on_activate(app):
    win = HelloWindow(app)
    win.present()
    win.maximize()

if __name__ == "__main__":
    # Ensure this ID matches your manifest!
    app = Gtk.Application(application_id='com.pens.HelloWorld')
    app.connect('activate', on_activate)
    app.run(None)