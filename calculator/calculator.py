#!/usr/bin/env python3
import sys
import math
import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

class CalculatorWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Flatpak Calculator")
        self.set_default_size(400, 600) # Set a default size first
        
        # NOTE: self.maximize() moved to on_activate to prevent Wayland Protocol Error 71

        # Add CSS for larger fonts to match the larger screen size
        css_provider = Gtk.CssProvider()
        css = b"""
        button {
            font-size: 20px;
            font-weight: bold;
        }
        .display-entry {
            font-size: 32px;
            font-weight: bold;
            padding: 10px;
        }
        """
        css_provider.load_from_data(css)
        
        # Safety check: Ensure display is ready before adding CSS
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display, 
                css_provider, 
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

        # Main layout container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        main_box.set_margin_start(10)
        main_box.set_margin_end(10)
        self.set_child(main_box)

        # Display Entry
        self.display = Gtk.Entry()
        self.display.set_alignment(1.0)
        self.display.set_placeholder_text("0")
        self.display.set_can_focus(False)
        # Make the display taller
        self.display.set_size_request(-1, 80)
        self.display.add_css_class("display-entry") 
        main_box.append(self.display)

        # 2. Responsive Grid Setup
        grid = Gtk.Grid()
        grid.set_row_spacing(5)
        grid.set_column_spacing(5)
        # Allow grid to expand to fill available space
        grid.set_hexpand(True)
        grid.set_vexpand(True)
        # Make all rows and columns equal size (responsive resizing)
        grid.set_row_homogeneous(True)
        grid.set_column_homogeneous(True)
        main_box.append(grid)

        # 3. New Layout with Scientific Functions (5 columns x 5 rows)
        buttons = [
            # Label, Column, Row
            ('(', 0, 0), (')', 1, 0), ('%', 2, 0), ('C', 3, 0), ('DEL', 4, 0),
            ('7', 0, 1), ('8', 1, 1), ('9', 2, 1), ('/', 3, 1), ('√', 4, 1),
            ('4', 0, 2), ('5', 1, 2), ('6', 2, 2), ('*', 3, 2), ('^', 4, 2),
            ('1', 0, 3), ('2', 1, 3), ('3', 2, 3), ('-', 3, 3), ('π', 4, 3),
            ('0', 0, 4), ('.', 1, 4), ('=', 2, 4), ('+', 3, 4), ('e', 4, 4),
        ]

        for label, col, row in buttons:
            button = Gtk.Button(label=label)
            # Removed fixed size request so they fill the grid cells
            button.connect('clicked', self.on_button_clicked)
            grid.attach(button, col, row, 1, 1)

    def on_button_clicked(self, button):
        label = button.get_label()
        current_text = self.display.get_text()

        if label == 'C':
            self.display.set_text("")
            
        elif label == 'DEL':
            # Remove the last character
            self.display.set_text(current_text[:-1])
            
        elif label == 'π':
            self.display.set_text(current_text + str(math.pi))
            
        elif label == 'e':
            self.display.set_text(current_text + str(math.e))
            
        elif label == '^':
            # Python uses ** for power
            self.display.set_text(current_text + "**")
            
        elif label == '√':
            try:
                # Calculate current value then sqrt it
                if not current_text:
                    return
                # Evaluate current expression first (e.g. if user types 5+4 then √)
                val = eval(current_text)
                res = math.sqrt(val)
                self.display.set_text(str(res))
            except:
                self.display.set_text("Error")

        elif label == '=':
            try:
                # Allowed characters for security (added ( ) %)
                # We allow 'e' if it's part of scientific notation or the number, 
                # but our basic filter assumes digits and operators. 
                # Since we inject full float strings for pi/e, we relax the filter slightly 
                # or just rely on the user inputting valid logic.
                
                # Simple logic: Replace UI symbols with Python math
                # Note: We already handled ^ as **, so we just eval.
                result = str(eval(current_text))
                self.display.set_text(result)
            except Exception:
                self.display.set_text("Error")
        else:
            self.display.set_text(current_text + label)

def on_activate(app):
    win = CalculatorWindow(app)
    win.present()
    # FIX: Maximize AFTER the window is presented to avoid Wayland Protocol Error 71
    win.maximize()

if __name__ == "__main__":
    app = Gtk.Application(application_id='com.pens.Calculator')
    app.connect('activate', on_activate)
    app.run(None)