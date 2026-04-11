#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk
import json, os

DATA_DIR = os.path.expanduser("~/.local/share/com.pens.ContactBook")
DATA_FILE = os.path.join(DATA_DIR, "contacts.json")

class ContactBookWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app); self.set_title("Contact Book"); self.set_default_size(860,640)
        os.makedirs(DATA_DIR, exist_ok=True)
        self.contacts = self.load(); self.selected = None
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0); self.set_child(hbox)
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4); left.set_size_request(260,-1)
        left.set_margin_top(6); left.set_margin_start(6); left.set_margin_bottom(6)
        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        new_btn = Gtk.Button(label="+ New"); new_btn.connect("clicked", self.on_new); btn_row.append(new_btn)
        del_btn = Gtk.Button(label="Delete"); del_btn.connect("clicked", self.on_delete); btn_row.append(del_btn)
        left.append(btn_row)
        self.search = Gtk.SearchEntry(); self.search.set_placeholder_text("Search..."); self.search.connect("search-changed", self.refresh_list); left.append(self.search)
        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        self.clist = Gtk.ListBox(); self.clist.connect("row-selected", self.on_selected); scroll.set_child(self.clist); left.append(scroll)
        hbox.append(left); hbox.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        right.set_hexpand(True); right.set_margin_top(8); right.set_margin_start(8); right.set_margin_end(8); right.set_margin_bottom(8)
        self.avatar = Gtk.DrawingArea(); self.avatar.set_size_request(80,80); self.avatar.set_halign(Gtk.Align.CENTER)
        self.avatar.set_draw_func(self.draw_avatar); right.append(self.avatar)
        self.fields = {}
        for label, key in [("Name","name"),("Phone","phone"),("Email","email"),("Address","address"),("Groups","groups")]:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            row.append(Gtk.Label(label=f"{label}:", width_chars=8, xalign=1))
            e = Gtk.Entry(); e.set_hexpand(True); e.connect("changed", self.on_field_changed, key)
            row.append(e); self.fields[key] = e; right.append(row)
        btn_row2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        save_btn = Gtk.Button(label="Save"); save_btn.connect("clicked", self.on_save); btn_row2.append(save_btn)
        export_btn = Gtk.Button(label="Export VCard"); export_btn.connect("clicked", self.on_export); btn_row2.append(export_btn)
        right.append(btn_row2); hbox.append(right)
        self.refresh_list(None)

    def load(self):
        try:
            with open(DATA_FILE) as f: return json.load(f)
        except Exception: return []
    def save_all(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(DATA_FILE, "w") as f: json.dump(self.contacts, f)

    def refresh_list(self, *a):
        q = self.search.get_text().lower() if self.search else ""
        while self.clist.get_row_at_index(0): self.clist.remove(self.clist.get_row_at_index(0))
        for i, c in enumerate(self.contacts):
            if q and q not in c.get("name","").lower() and q not in c.get("phone","").lower(): continue
            row = Gtk.ListBoxRow()
            lbl = Gtk.Label(label=c.get("name","(no name)"), xalign=0); lbl.set_margin_start(6); lbl.set_margin_top(3); lbl.set_margin_bottom(3)
            row.set_child(lbl); row._idx = i; self.clist.append(row)

    def on_selected(self, listbox, row):
        if not row: return
        self.selected = row._idx; c = self.contacts[self.selected]
        for key, entry in self.fields.items(): entry.set_text(c.get(key,""))
        self.avatar.queue_draw()

    def on_new(self, btn):
        self.contacts.append({"name":"New Contact","phone":"","email":"","address":"","groups":""}); self.save_all(); self.refresh_list(None)

    def on_delete(self, btn):
        if self.selected is not None:
            self.contacts.pop(self.selected); self.selected = None; self.save_all(); self.refresh_list(None)

    def on_field_changed(self, entry, key):
        if self.selected is not None: self.contacts[self.selected][key] = entry.get_text()

    def on_save(self, btn):
        self.save_all(); self.refresh_list(None)

    def on_export(self, btn):
        if self.selected is None: return
        c = self.contacts[self.selected]
        vcard = f"BEGIN:VCARD\nVERSION:3.0\nFN:{c.get('name','')}\nTEL:{c.get('phone','')}\nEMAIL:{c.get('email','')}\nADR:{c.get('address','')}\nEND:VCARD"
        Gdk.Display.get_default().get_clipboard().set(vcard)

    def draw_avatar(self, area, cr, w, h):
        name = ""
        if self.selected is not None: name = self.contacts[self.selected].get("name","?")
        initials = "".join(p[0].upper() for p in name.split()[:2]) if name else "?"
        colors = [(0.3,0.6,0.9),(0.9,0.4,0.3),(0.3,0.8,0.5),(0.8,0.5,0.9)]
        color = colors[hash(name) % len(colors)]
        cr.set_source_rgb(*color); cr.arc(w/2,h/2,min(w,h)/2-2,0,6.28); cr.fill()
        cr.set_source_rgb(1,1,1); cr.set_font_size(24); cr.move_to(w/2-len(initials)*8, h/2+9); cr.show_text(initials)

class ContactBookApp(Gtk.Application):
    def __init__(self): super().__init__(application_id="com.pens.ContactBook")
    def do_activate(self): ContactBookWindow(self).present()

def main(): ContactBookApp().run(None)
if __name__ == "__main__": main()
