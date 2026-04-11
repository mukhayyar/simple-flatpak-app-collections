#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk
import json, os, time

NOTES_DIR = os.path.expanduser("~/.local/share/com.pens.Notes")

class NotesWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Notes")
        self.set_default_size(900, 640)
        self.notes = {}
        self.current_id = None
        os.makedirs(NOTES_DIR, exist_ok=True)
        self.build_ui()
        self.load_all_notes()

    def build_ui(self):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.set_child(hbox)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        left.set_size_request(240, -1)
        left.set_margin_top(6); left.set_margin_start(6); left.set_margin_bottom(6)

        top_btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        new_btn = Gtk.Button(label="+ New Note")
        new_btn.connect("clicked", self.on_new)
        del_btn = Gtk.Button(label="Delete")
        del_btn.connect("clicked", self.on_delete)
        top_btn_row.append(new_btn); top_btn_row.append(del_btn)
        left.append(top_btn_row)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search notes...")
        self.search_entry.connect("search-changed", self.on_search)
        left.append(self.search_entry)

        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        self.note_list = Gtk.ListBox()
        self.note_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.note_list.connect("row-selected", self.on_note_selected)
        scroll.set_child(self.note_list)
        left.append(scroll)
        hbox.append(left)

        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        hbox.append(sep)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        right.set_hexpand(True)
        right.set_margin_top(6); right.set_margin_end(6); right.set_margin_bottom(6); right.set_margin_start(6)

        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        title_box.append(Gtk.Label(label="Title:"))
        self.title_entry = Gtk.Entry()
        self.title_entry.set_hexpand(True)
        self.title_entry.connect("changed", self.on_title_changed)
        title_box.append(self.title_entry)
        right.append(title_box)

        tag_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        tag_box.append(Gtk.Label(label="Tags:"))
        self.tags_entry = Gtk.Entry()
        self.tags_entry.set_placeholder_text("Comma-separated tags...")
        self.tags_entry.set_hexpand(True)
        self.tags_entry.connect("changed", self.on_content_changed)
        tag_box.append(self.tags_entry)
        right.append(tag_box)

        fmt_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        for label, tag_pair in [("Bold", ("bold", "bold")), ("Italic", ("italic", "italic"))]:
            btn = Gtk.Button(label=label)
            btn.connect("clicked", self.on_format, tag_pair[0])
            fmt_bar.append(btn)
        right.append(fmt_bar)

        scroll2 = Gtk.ScrolledWindow(); scroll2.set_vexpand(True)
        self.content_view = Gtk.TextView()
        self.content_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.content_buf = self.content_view.get_buffer()
        tt = self.content_buf.get_tag_table()
        bold_tag = Gtk.TextTag.new("bold"); bold_tag.set_property("weight", 700); tt.add(bold_tag)
        italic_tag = Gtk.TextTag.new("italic"); italic_tag.set_property("style", 2); tt.add(italic_tag)
        self.content_buf.connect("changed", self.on_content_changed)
        scroll2.set_child(self.content_view)
        right.append(scroll2)

        self.status_label = Gtk.Label(label="Select or create a note")
        self.status_label.set_xalign(0)
        right.append(self.status_label)
        hbox.append(right)

    def on_format(self, btn, tag_name):
        buf = self.content_buf
        if buf.get_has_selection():
            start, end = buf.get_selection_bounds()
            buf.apply_tag_by_name(tag_name, start, end)

    def load_all_notes(self):
        for fn in os.listdir(NOTES_DIR):
            if fn.endswith(".json"):
                try:
                    with open(os.path.join(NOTES_DIR, fn)) as f:
                        note = json.load(f)
                        self.notes[note["id"]] = note
                except Exception:
                    pass
        self.refresh_list()

    def save_note(self):
        if not self.current_id: return
        note = self.notes.get(self.current_id, {})
        buf = self.content_buf
        note["content"] = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
        note["title"] = self.title_entry.get_text() or "Untitled"
        note["tags"] = [t.strip() for t in self.tags_entry.get_text().split(",") if t.strip()]
        note["modified"] = time.time()
        self.notes[self.current_id] = note
        path = os.path.join(NOTES_DIR, f"{self.current_id}.json")
        with open(path, "w") as f:
            json.dump(note, f)
        self.refresh_list()

    def on_new(self, btn):
        import uuid
        nid = str(uuid.uuid4())[:8]
        note = {"id": nid, "title": "New Note", "content": "", "tags": [], "created": time.time(), "modified": time.time()}
        self.notes[nid] = note
        path = os.path.join(NOTES_DIR, f"{nid}.json")
        with open(path, "w") as f:
            json.dump(note, f)
        self.refresh_list()
        self.load_note(nid)

    def on_delete(self, btn):
        if not self.current_id: return
        path = os.path.join(NOTES_DIR, f"{self.current_id}.json")
        try: os.remove(path)
        except Exception: pass
        del self.notes[self.current_id]
        self.current_id = None
        self.title_entry.set_text("")
        self.content_buf.set_text("")
        self.refresh_list()

    def refresh_list(self):
        q = self.search_entry.get_text().lower()
        while self.note_list.get_row_at_index(0):
            self.note_list.remove(self.note_list.get_row_at_index(0))
        for nid, note in sorted(self.notes.items(), key=lambda x: -x[1].get("modified", 0)):
            if q and q not in note["title"].lower() and q not in note["content"].lower():
                continue
            row = Gtk.ListBoxRow()
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            vbox.set_margin_top(4); vbox.set_margin_start(6); vbox.set_margin_bottom(4)
            title_lbl = Gtk.Label(label=note["title"], xalign=0)
            title_lbl.set_markup(f"<b>{note['title'][:30]}</b>")
            preview = note["content"][:50].replace("\n", " ")
            preview_lbl = Gtk.Label(label=preview, xalign=0)
            vbox.append(title_lbl); vbox.append(preview_lbl)
            row.set_child(vbox)
            row._note_id = nid
            self.note_list.append(row)

    def on_search(self, entry):
        self.refresh_list()

    def on_note_selected(self, listbox, row):
        if row:
            self.save_note()
            self.load_note(row._note_id)

    def load_note(self, nid):
        self.current_id = nid
        note = self.notes[nid]
        self.title_entry.set_text(note["title"])
        self.content_buf.set_text(note["content"])
        self.tags_entry.set_text(", ".join(note.get("tags", [])))
        self.status_label.set_text(f"Note: {nid}")

    def on_title_changed(self, entry):
        GLib.timeout_add(500, self.save_note)

    def on_content_changed(self, *args):
        GLib.timeout_add(1000, self.save_note)

class NotesApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.Notes")
    def do_activate(self):
        win = NotesWindow(self)
        win.present()

def main():
    app = NotesApp()
    app.run(None)

if __name__ == "__main__":
    main()
