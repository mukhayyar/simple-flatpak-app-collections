#!/usr/bin/env python3
"""PensHub Store Client -- com.pens.PensHubClient
Browse and discover apps from the AGL PENS App Store.
Connects to https://api.agl-store.cyou and lists available Flatpak apps.
"""
import gi, threading, json, urllib.request, urllib.error
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

API = "https://api.agl-store.cyou"

def fetch_apps(query="", limit=60):
    url = f"{API}/apps?limit={limit}" + (f"&search={query}" if query else "")
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        return []

def fetch_stats():
    try:
        with urllib.request.urlopen(f"{API}/stats", timeout=6) as r:
            return json.loads(r.read())
    except:
        return {}

class PensHubClientApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='com.pens.PensHubClient')

    def do_activate(self):
        self.win = Gtk.ApplicationWindow(application=self, title='PensHub — AGL App Store')
        self.win.set_default_size(700, 540)

        hdr = Gtk.HeaderBar()
        title_lbl = Gtk.Label()
        title_lbl.set_markup("<b>PensHub Store</b>")
        hdr.set_title_widget(title_lbl)
        self.search = Gtk.SearchEntry(placeholder_text="Search apps…", hexpand=True)
        self.search.set_size_request(200, -1)
        self.search.connect("search-changed", self._on_search)
        hdr.pack_end(self.search)
        self.win.set_titlebar(hdr)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.win.set_child(root)

        self.status = Gtk.Label(label="Connecting to PensHub…", margin_top=10, margin_bottom=6)
        root.append(self.status)

        scroll = Gtk.ScrolledWindow(vexpand=True)
        root.append(scroll)

        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.list_box.set_margin_start(8); self.list_box.set_margin_end(8)
        scroll.set_child(self.list_box)

        self.win.present()
        threading.Thread(target=self._load_apps, args=("",), daemon=True).start()

    def _on_search(self, entry):
        GLib.idle_add(self._clear)
        GLib.idle_add(self.status.set_text, "Searching…")
        threading.Thread(target=self._load_apps, args=(entry.get_text(),), daemon=True).start()

    def _clear(self):
        child = self.list_box.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self.list_box.remove(child)
            child = nxt

    def _load_apps(self, q):
        apps = fetch_apps(q)
        GLib.idle_add(self._populate, apps)

    def _populate(self, apps):
        self._clear()
        n = len(apps)
        self.status.set_text(f"{n} app{'s' if n != 1 else ''} available in PensHub store")
        for app in apps:
            row = Gtk.ListBoxRow()
            row.set_margin_top(2); row.set_margin_bottom(2)
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12,
                           margin_top=10, margin_bottom=10,
                           margin_start=12, margin_end=12)
            row.set_child(hbox)

            badge = Gtk.Label(label=(app.get('name') or app.get('id','?'))[:2].upper())
            badge.set_size_request(44, 44); badge.set_valign(Gtk.Align.CENTER)
            badge.set_markup(f"<span weight='bold' size='large' color='#4f7fff'>"
                             f"{GLib.markup_escape_text((app.get('name') or '?')[:2].upper())}</span>")
            hbox.append(badge)

            info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3, hexpand=True)
            name = Gtk.Label(halign=Gtk.Align.START)
            name.set_markup(f"<b>{GLib.markup_escape_text(app.get('name') or app.get('id','?'))}</b>")
            info.append(name)
            if summary := (app.get('summary') or '')[:90]:
                sl = Gtk.Label(label=summary, halign=Gtk.Align.START, ellipsize=3)
                sl.add_css_class('dim-label')
                info.append(sl)
            cats = ', '.join((app.get('categories') or [])[:3])
            if cats:
                cl = Gtk.Label(label=cats, halign=Gtk.Align.START)
                cl.set_markup(f"<span size='small' color='#888'>{GLib.markup_escape_text(cats)}</span>")
                info.append(cl)
            hbox.append(info)

            app_id_lbl = Gtk.Label()
            app_id_lbl.set_markup(f"<span size='small' color='#aaa'>{GLib.markup_escape_text(app.get('id',''))}</span>")
            app_id_lbl.set_valign(Gtk.Align.CENTER)
            hbox.append(app_id_lbl)

            self.list_box.append(row)

if __name__ == '__main__':
    PensHubClientApp().run()
