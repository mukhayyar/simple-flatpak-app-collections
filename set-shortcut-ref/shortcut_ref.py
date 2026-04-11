#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

SHORTCUTS = {
    "GNOME Desktop": [
        ("Super", "Activities overview"),
        ("Super+Tab", "Switch applications"),
        ("Super+Left/Right", "Snap window to side"),
        ("Super+Up/Down", "Maximize / restore window"),
        ("Super+H", "Hide window"),
        ("Super+L", "Lock screen"),
        ("Super+D", "Show desktop"),
        ("Super+A", "Application grid"),
        ("Alt+F4", "Close window"),
        ("Alt+F2", "Run command"),
        ("Ctrl+Alt+T", "Open terminal"),
        ("Ctrl+Alt+Delete", "Log out dialog"),
        ("PrtSc", "Screenshot"),
        ("Shift+PrtSc", "Screenshot region"),
        ("Super+PrtSc", "Screenshot window"),
    ],
    "Text Editing": [
        ("Ctrl+A", "Select all"),
        ("Ctrl+C", "Copy"),
        ("Ctrl+X", "Cut"),
        ("Ctrl+V", "Paste"),
        ("Ctrl+Z", "Undo"),
        ("Ctrl+Y / Ctrl+Shift+Z", "Redo"),
        ("Ctrl+F", "Find"),
        ("Ctrl+H", "Find & Replace"),
        ("Ctrl+S", "Save"),
        ("Ctrl+W", "Close document/tab"),
        ("Ctrl+Home", "Go to beginning"),
        ("Ctrl+End", "Go to end"),
        ("Ctrl+Left/Right", "Word by word navigation"),
        ("Shift+Ctrl+Left/Right", "Select word by word"),
        ("Home / End", "Line start / end"),
    ],
    "File Manager (Nautilus)": [
        ("Ctrl+L", "Focus location bar"),
        ("Alt+Left", "Go back"),
        ("Alt+Right", "Go forward"),
        ("Alt+Up", "Go to parent folder"),
        ("Alt+Home", "Go to home folder"),
        ("F2", "Rename file"),
        ("Delete", "Move to trash"),
        ("Shift+Delete", "Delete permanently"),
        ("Ctrl+N", "New window"),
        ("Ctrl+Shift+N", "New folder"),
        ("Ctrl+H", "Show hidden files"),
        ("F9", "Toggle side panel"),
        ("Ctrl+1 / Ctrl+2", "Icon / List view"),
    ],
    "Browser (Firefox/Chrome)": [
        ("Ctrl+T", "New tab"),
        ("Ctrl+W", "Close tab"),
        ("Ctrl+Shift+T", "Reopen closed tab"),
        ("Ctrl+Tab", "Next tab"),
        ("Ctrl+Shift+Tab", "Previous tab"),
        ("Ctrl+L / F6", "Focus address bar"),
        ("Ctrl+D", "Bookmark page"),
        ("Ctrl+R / F5", "Reload"),
        ("Ctrl+Shift+R", "Hard reload"),
        ("Ctrl+Plus/Minus", "Zoom in/out"),
        ("Ctrl+0", "Reset zoom"),
        ("F11", "Toggle fullscreen"),
        ("Ctrl+Shift+I", "Developer tools"),
        ("Ctrl+U", "View source"),
    ],
    "Terminal": [
        ("Ctrl+C", "Interrupt/kill process"),
        ("Ctrl+Z", "Suspend process"),
        ("Ctrl+D", "EOF / close shell"),
        ("Ctrl+L", "Clear screen"),
        ("Ctrl+A", "Go to beginning of line"),
        ("Ctrl+E", "Go to end of line"),
        ("Ctrl+U", "Delete to beginning of line"),
        ("Ctrl+K", "Delete to end of line"),
        ("Ctrl+W", "Delete previous word"),
        ("Ctrl+R", "Search history"),
        ("Up/Down", "History navigation"),
        ("Tab", "Autocomplete"),
        ("Ctrl+Shift+C", "Copy (terminal)"),
        ("Ctrl+Shift+V", "Paste (terminal)"),
        ("Ctrl+Shift+T", "New tab (GNOME Terminal)"),
    ],
    "Vim": [
        ("i / a", "Insert mode (before/after cursor)"),
        ("Esc", "Normal mode"),
        (":", "Command mode"),
        ("h j k l", "Move left/down/up/right"),
        ("w / b", "Next / previous word"),
        ("0 / $", "Line start / end"),
        ("gg / G", "File start / end"),
        ("dd", "Delete (cut) line"),
        ("yy", "Yank (copy) line"),
        ("p / P", "Paste after/before"),
        ("u / Ctrl+R", "Undo / Redo"),
        ("/pattern", "Search forward"),
        (":wq / :q!", "Save+quit / Force quit"),
        ("v / V", "Visual char / line mode"),
        ("Ctrl+V", "Visual block mode"),
    ],
}

class ShortcutRefWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Keyboard Shortcut Reference")
        self.set_default_size(880, 640)
        self.build_ui()

    def build_ui(self):
        hpaned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_child(hpaned)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        left.set_margin_top(8); left.set_margin_bottom(8)
        left.set_margin_start(8); left.set_margin_end(4)
        left.set_size_request(200, -1)

        left.append(Gtk.Label(label="Categories", css_classes=["title"]))

        search = Gtk.SearchEntry()
        search.set_placeholder_text("Search shortcuts...")
        search.connect("search-changed", self.on_search)
        left.append(search)

        scroll_left = Gtk.ScrolledWindow()
        scroll_left.set_vexpand(True)
        self.cat_store = Gtk.ListStore(str)
        for cat in SHORTCUTS:
            self.cat_store.append([cat])
        cat_view = Gtk.TreeView(model=self.cat_store)
        cat_view.set_headers_visible(False)
        col = Gtk.TreeViewColumn("Cat", Gtk.CellRendererText(), text=0)
        cat_view.append_column(col)
        cat_view.get_selection().connect("changed", self.on_cat_selected)
        scroll_left.set_child(cat_view)
        left.append(scroll_left)
        hpaned.set_start_child(left)

        self.right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.right.set_margin_top(8); self.right.set_margin_bottom(8)
        self.right.set_margin_start(4); self.right.set_margin_end(8)

        self.right_title = Gtk.Label(label="Select a category", css_classes=["title"])
        self.right_title.set_halign(Gtk.Align.START)
        self.right.append(self.right_title)

        scroll_right = Gtk.ScrolledWindow()
        scroll_right.set_vexpand(True)
        self.shortcut_store = Gtk.ListStore(str, str)
        self.shortcut_view = Gtk.TreeView(model=self.shortcut_store)
        for i, title in enumerate(["Keys", "Action"]):
            r = Gtk.CellRendererText()
            if i == 0:
                r.set_property("family", "Monospace")
                r.set_property("weight", 700)
            col = Gtk.TreeViewColumn(title, r, text=i)
            col.set_resizable(True)
            col.set_fixed_width(220 if i == 0 else 400)
            self.shortcut_view.append_column(col)
        scroll_right.set_child(self.shortcut_view)
        self.right.append(scroll_right)

        self.count_label = Gtk.Label(label="", xalign=0)
        self.count_label.set_css_classes(["dim-label"])
        self.right.append(self.count_label)

        hpaned.set_end_child(self.right)

        # Select first category
        cat_view.get_selection().select_path(Gtk.TreePath.new_first())
        self.cat_view = cat_view
        self.search_text = ""

    def on_cat_selected(self, selection):
        model, iter_ = selection.get_selected()
        if not iter_:
            return
        cat = model.get_value(iter_, 0)
        self.right_title.set_label(cat)
        self.populate_shortcuts(cat, self.search_text)

    def populate_shortcuts(self, cat, search=""):
        self.shortcut_store.clear()
        items = SHORTCUTS.get(cat, [])
        count = 0
        for keys, action in items:
            if search and search.lower() not in keys.lower() and search.lower() not in action.lower():
                continue
            self.shortcut_store.append([keys, action])
            count += 1
        self.count_label.set_text(f"{count} shortcuts")

    def on_search(self, entry):
        self.search_text = entry.get_text()
        # Search across all categories
        if self.search_text:
            self.shortcut_store.clear()
            count = 0
            for cat, items in SHORTCUTS.items():
                for keys, action in items:
                    if self.search_text.lower() in keys.lower() or self.search_text.lower() in action.lower():
                        self.shortcut_store.append([keys, f"[{cat}] {action}"])
                        count += 1
            self.right_title.set_label(f"Search: {self.search_text}")
            self.count_label.set_text(f"{count} results")
        else:
            model, iter_ = self.cat_view.get_selection().get_selected()
            if iter_:
                cat = model.get_value(iter_, 0)
                self.populate_shortcuts(cat)

class ShortcutRefApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.ShortcutRef")
    def do_activate(self):
        win = ShortcutRefWindow(self); win.present()

def main():
    app = ShortcutRefApp(); app.run(None)

if __name__ == "__main__":
    main()
