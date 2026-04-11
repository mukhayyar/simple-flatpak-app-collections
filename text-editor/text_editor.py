#!/usr/bin/env python3
import gi
import os

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, Gio, GLib


class TextEditorWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_default_size(800, 600)

        self._current_file = None
        self._modified = False

        css_provider = Gtk.CssProvider()
        css = b"""
        textview {
            font-family: monospace;
            font-size: 14px;
            padding: 8px;
        }
        """
        css_provider.load_from_data(css)
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

        self._update_title()

        # Main layout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(vbox)

        # Menu bar
        menubar = self._build_menubar()
        vbox.append(menubar)

        # Scrolled text view
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.textview = Gtk.TextView()
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.textview.set_monospace(True)
        self.textview.set_hexpand(True)
        self.textview.set_vexpand(True)
        scrolled.set_child(self.textview)
        vbox.append(scrolled)

        # Status bar
        self.status_bar = Gtk.Label(label="Ready")
        self.status_bar.set_halign(Gtk.Align.START)
        self.status_bar.set_margin_start(8)
        self.status_bar.set_margin_end(8)
        self.status_bar.set_margin_top(4)
        self.status_bar.set_margin_bottom(4)
        vbox.append(self.status_bar)

        # Connect buffer change signal
        self.buffer = self.textview.get_buffer()
        self.buffer.connect("changed", self.on_buffer_changed)

    def _build_menubar(self):
        menubar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        menubar.add_css_class("menubar")

        # File menu
        file_menu_btn = Gtk.MenuButton(label="File")
        file_menu = Gio.Menu()
        file_menu.append("New", "win.new")
        file_menu.append("Open", "win.open")
        file_menu.append("Save", "win.save")
        file_menu.append("Save As", "win.save_as")
        file_menu.append("Quit", "win.quit")
        file_menu_btn.set_menu_model(file_menu)
        menubar.append(file_menu_btn)

        # Edit menu
        edit_menu_btn = Gtk.MenuButton(label="Edit")
        edit_menu = Gio.Menu()
        edit_menu.append("Undo", "win.undo")
        edit_menu.append("Redo", "win.redo")
        edit_menu.append("Cut", "win.cut")
        edit_menu.append("Copy", "win.copy")
        edit_menu.append("Paste", "win.paste")
        edit_menu.append("Select All", "win.select_all")
        edit_menu_btn.set_menu_model(edit_menu)
        menubar.append(edit_menu_btn)

        # Register actions
        actions = [
            ("new", self.action_new),
            ("open", self.action_open),
            ("save", self.action_save),
            ("save_as", self.action_save_as),
            ("quit", self.action_quit),
            ("undo", self.action_undo),
            ("redo", self.action_redo),
            ("cut", self.action_cut),
            ("copy", self.action_copy),
            ("paste", self.action_paste),
            ("select_all", self.action_select_all),
        ]
        for name, handler in actions:
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", handler)
            self.add_action(action)

        return menubar

    def _update_title(self):
        if self._current_file:
            basename = os.path.basename(self._current_file)
            marker = " *" if self._modified else ""
            self.set_title(f"{basename}{marker} — Text Editor")
        else:
            marker = " *" if self._modified else ""
            self.set_title(f"Untitled{marker} — Text Editor")

    def on_buffer_changed(self, _buffer):
        if not self._modified:
            self._modified = True
            self._update_title()

    # --- File actions ---

    def action_new(self, _action, _param):
        if self._modified:
            if not self._confirm_discard():
                return
        self.buffer.set_text("")
        self._current_file = None
        self._modified = False
        self._update_title()
        self.status_bar.set_label("New file created.")

    def action_open(self, _action, _param):
        if self._modified:
            if not self._confirm_discard():
                return
        dialog = Gtk.FileChooserDialog(
            title="Open File",
            transient_for=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Open", Gtk.ResponseType.ACCEPT)
        dialog.connect("response", self._on_open_response)
        dialog.present()

    def _on_open_response(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            path = dialog.get_file().get_path()
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.buffer.set_text(content)
                self._current_file = path
                self._modified = False
                self._update_title()
                self.status_bar.set_label(f"Opened: {path}")
            except Exception as e:
                self._show_error(f"Could not open file: {e}")
        dialog.destroy()

    def action_save(self, _action, _param):
        if self._current_file:
            self._write_file(self._current_file)
        else:
            self.action_save_as(None, None)

    def action_save_as(self, _action, _param):
        dialog = Gtk.FileChooserDialog(
            title="Save File As",
            transient_for=self,
            action=Gtk.FileChooserAction.SAVE,
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Save", Gtk.ResponseType.ACCEPT)
        dialog.set_current_name("untitled.txt")
        dialog.connect("response", self._on_save_as_response)
        dialog.present()

    def _on_save_as_response(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            path = dialog.get_file().get_path()
            self._write_file(path)
            self._current_file = path
        dialog.destroy()

    def _write_file(self, path):
        try:
            start = self.buffer.get_start_iter()
            end = self.buffer.get_end_iter()
            text = self.buffer.get_text(start, end, True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self._current_file = path
            self._modified = False
            self._update_title()
            self.status_bar.set_label(f"Saved: {path}")
        except Exception as e:
            self._show_error(f"Could not save file: {e}")

    def action_quit(self, _action, _param):
        if self._modified:
            if not self._confirm_discard():
                return
        self.get_application().quit()

    # --- Edit actions ---

    def action_undo(self, _action, _param):
        if self.buffer.can_undo():
            self.buffer.undo()
            self.status_bar.set_label("Undo.")

    def action_redo(self, _action, _param):
        if self.buffer.can_redo():
            self.buffer.redo()
            self.status_bar.set_label("Redo.")

    def action_cut(self, _action, _param):
        display = Gdk.Display.get_default()
        if display:
            clipboard = display.get_clipboard()
            self.buffer.cut_clipboard(clipboard, self.textview.get_editable())

    def action_copy(self, _action, _param):
        display = Gdk.Display.get_default()
        if display:
            clipboard = display.get_clipboard()
            self.buffer.copy_clipboard(clipboard)

    def action_paste(self, _action, _param):
        display = Gdk.Display.get_default()
        if display:
            clipboard = display.get_clipboard()
            self.buffer.paste_clipboard(clipboard, None, self.textview.get_editable())

    def action_select_all(self, _action, _param):
        start = self.buffer.get_start_iter()
        end = self.buffer.get_end_iter()
        self.buffer.select_range(start, end)

    # --- Helpers ---

    def _confirm_discard(self):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="You have unsaved changes.",
        )
        dialog.format_secondary_text("Do you want to discard them?")
        response = dialog.run()
        dialog.destroy()
        return response == Gtk.ResponseType.YES

    def _show_error(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message,
        )
        dialog.run()
        dialog.destroy()
        self.status_bar.set_label(f"Error: {message}")


def on_activate(app):
    win = TextEditorWindow(app)
    win.present()


if __name__ == "__main__":
    app = Gtk.Application(application_id="com.pens.TextEditor")
    app.connect("activate", on_activate)
    app.run(None)
