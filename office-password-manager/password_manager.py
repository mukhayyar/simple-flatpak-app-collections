#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk
import json, os, hashlib, secrets, base64

DATA_DIR = os.path.expanduser("~/.local/share/com.pens.PasswordManager")
DATA_FILE = os.path.join(DATA_DIR, "vault.json")

def xor_encrypt(data: bytes, key: bytes) -> bytes:
    extended_key = (key * (len(data) // len(key) + 1))[:len(data)]
    return bytes(a ^ b for a, b in zip(data, extended_key))

def derive_key(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000, 32)

def encrypt(plaintext: str, password: str, salt: bytes) -> str:
    key = derive_key(password, salt)
    enc = xor_encrypt(plaintext.encode(), key)
    return base64.b64encode(enc).decode()

def decrypt(ciphertext: str, password: str, salt: bytes) -> str:
    key = derive_key(password, salt)
    enc = base64.b64decode(ciphertext.encode())
    return xor_encrypt(enc, key).decode()

class PasswordManagerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app); self.set_title("Password Manager"); self.set_default_size(800,640)
        os.makedirs(DATA_DIR, exist_ok=True)
        self.master_key = None; self.salt = None; self.entries = []
        self.build_login_ui()

    def build_login_ui(self):
        self.set_child(None)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_top(80); vbox.set_margin_bottom(80); vbox.set_margin_start(80); vbox.set_margin_end(80)
        vbox.set_halign(Gtk.Align.CENTER); self.set_child(vbox)
        vbox.append(Gtk.Label(label="Password Manager", css_classes=["title"]))
        self.master_entry = Gtk.Entry(); self.master_entry.set_visibility(False); self.master_entry.set_placeholder_text("Master password")
        vbox.append(self.master_entry)
        unlock_btn = Gtk.Button(label="Unlock Vault"); unlock_btn.connect("clicked", self.on_unlock); vbox.append(unlock_btn)
        new_btn = Gtk.Button(label="Create New Vault"); new_btn.connect("clicked", self.on_new_vault); vbox.append(new_btn)
        self.login_status = Gtk.Label(label=""); vbox.append(self.login_status)

    def on_new_vault(self, btn):
        self.salt = secrets.token_bytes(16)
        self.master_key = self.master_entry.get_text()
        if not self.master_key: self.login_status.set_text("Enter a master password"); return
        self.entries = []
        vault_data = {"salt": base64.b64encode(self.salt).decode(), "entries_enc": encrypt("[]", self.master_key, self.salt)}
        with open(DATA_FILE, "w") as f: json.dump(vault_data, f)
        self.login_status.set_text("New vault created!"); self.build_main_ui()

    def on_unlock(self, btn):
        if not os.path.exists(DATA_FILE): self.login_status.set_text("No vault found. Create one first."); return
        pw = self.master_entry.get_text()
        try:
            with open(DATA_FILE) as f: vault = json.load(f)
            self.salt = base64.b64decode(vault["salt"])
            decrypted = decrypt(vault["entries_enc"], pw, self.salt)
            self.entries = json.loads(decrypted)
            self.master_key = pw; self.build_main_ui()
        except Exception: self.login_status.set_text("Wrong master password or corrupted vault")

    def build_main_ui(self):
        self.set_child(None)
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0); self.set_child(hbox)
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4); left.set_size_request(250,-1)
        left.set_margin_top(6); left.set_margin_start(6); left.set_margin_bottom(6)
        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        new_btn = Gtk.Button(label="+ New"); new_btn.connect("clicked", self.on_new_entry); btn_row.append(new_btn)
        del_btn = Gtk.Button(label="Delete"); del_btn.connect("clicked", self.on_delete); btn_row.append(del_btn)
        left.append(btn_row)
        search = Gtk.SearchEntry(); search.set_placeholder_text("Search..."); search.connect("search-changed", self.refresh); left.append(search)
        self.search_entry = search
        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        self.entry_list = Gtk.ListBox(); self.entry_list.connect("row-selected", self.on_entry_selected); scroll.set_child(self.entry_list); left.append(scroll)
        hbox.append(left); hbox.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        right.set_hexpand(True); right.set_margin_top(8); right.set_margin_start(8); right.set_margin_end(8); right.set_margin_bottom(8)
        self.fields = {}
        for label, key, vis in [("Title","title",True),("Username","username",True),("Password","password",False),("URL","url",True),("Notes","notes",True)]:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            row.append(Gtk.Label(label=f"{label}:", width_chars=10, xalign=1))
            e = Gtk.Entry(); e.set_hexpand(True); e.set_visibility(vis)
            e.connect("changed", self.on_field_changed, key)
            row.append(e)
            if key == "password":
                gen_btn = Gtk.Button(label="Generate"); gen_btn.connect("clicked", self.on_generate); row.append(gen_btn)
                copy_btn = Gtk.Button(label="Copy"); copy_btn.connect("clicked", lambda b, k=key: self.copy_field(k)); row.append(copy_btn)
            self.fields[key] = e; right.append(row)
        save_btn = Gtk.Button(label="Save"); save_btn.connect("clicked", self.on_save_entry); right.append(save_btn)
        lock_btn = Gtk.Button(label="Lock Vault"); lock_btn.connect("clicked", lambda b: self.build_login_ui()); right.append(lock_btn)
        hbox.append(right); self.selected_idx = None
        self.refresh(None)

    def refresh(self, *a):
        q = self.search_entry.get_text().lower() if hasattr(self, "search_entry") else ""
        while self.entry_list.get_row_at_index(0): self.entry_list.remove(self.entry_list.get_row_at_index(0))
        for i, e in enumerate(self.entries):
            if q and q not in e.get("title","").lower(): continue
            row = Gtk.ListBoxRow()
            lbl = Gtk.Label(label=e.get("title","(no title)"), xalign=0); lbl.set_margin_start(6); lbl.set_margin_top(3); lbl.set_margin_bottom(3)
            row.set_child(lbl); row._idx = i; self.entry_list.append(row)

    def on_entry_selected(self, listbox, row):
        if not row: return
        self.selected_idx = row._idx; e = self.entries[self.selected_idx]
        for key, entry in self.fields.items(): entry.set_text(e.get(key,""))

    def on_new_entry(self, btn):
        self.entries.append({"title":"New Entry","username":"","password":"","url":"","notes":""}); self.save_vault(); self.refresh(None)

    def on_delete(self, btn):
        if self.selected_idx is not None:
            self.entries.pop(self.selected_idx); self.selected_idx = None; self.save_vault(); self.refresh(None)

    def on_field_changed(self, entry, key):
        if self.selected_idx is not None: self.entries[self.selected_idx][key] = entry.get_text()

    def on_generate(self, btn):
        import string; chars = string.ascii_letters + string.digits + "!@#$%^&*"
        pw = "".join(secrets.choice(chars) for _ in range(20))
        self.fields["password"].set_text(pw)
        if self.selected_idx is not None: self.entries[self.selected_idx]["password"] = pw

    def copy_field(self, key):
        text = self.fields[key].get_text()
        Gdk.Display.get_default().get_clipboard().set(text)

    def on_save_entry(self, btn):
        self.save_vault(); self.refresh(None)

    def save_vault(self):
        enc = encrypt(json.dumps(self.entries), self.master_key, self.salt)
        vault = {"salt": base64.b64encode(self.salt).decode(), "entries_enc": enc}
        with open(DATA_FILE, "w") as f: json.dump(vault, f)

class PasswordManagerApp(Gtk.Application):
    def __init__(self): super().__init__(application_id="com.pens.PasswordManager")
    def do_activate(self): PasswordManagerWindow(self).present()

def main(): PasswordManagerApp().run(None)
if __name__ == "__main__": main()
