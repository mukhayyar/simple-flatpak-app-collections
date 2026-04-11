#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk
import json, base64, time, datetime

def b64url_decode(s):
    s = s.replace("-", "+").replace("_", "/")
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.b64decode(s)

class JwtDecoderWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("JWT Decoder")
        self.set_default_size(800, 700)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="JWT Decoder (DOES NOT verify signature)", css_classes=["title"]))

        input_frame = Gtk.Frame(label="JWT Token")
        input_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        input_vbox.set_margin_top(4); input_vbox.set_margin_start(4)
        input_vbox.set_margin_bottom(4); input_vbox.set_margin_end(4)
        self.token_entry = Gtk.Entry()
        self.token_entry.set_placeholder_text("Paste JWT token here...")
        self.token_entry.connect("changed", self.on_decode)
        input_vbox.append(self.token_entry)
        decode_btn = Gtk.Button(label="Decode")
        decode_btn.connect("clicked", self.on_decode)
        input_vbox.append(decode_btn)
        input_frame.set_child(input_vbox)
        vbox.append(input_frame)

        self.warning_label = Gtk.Label(label="")
        self.warning_label.set_markup('<span foreground="#f39c12">⚠ Signature is NOT verified — do not trust claims without verification</span>')
        self.warning_label.set_xalign(0)
        vbox.append(self.warning_label)

        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_vexpand(True)

        header_frame = Gtk.Frame(label="Header")
        h_scroll = Gtk.ScrolledWindow()
        self.header_view = Gtk.TextView()
        self.header_view.set_monospace(True)
        self.header_view.set_editable(False)
        h_scroll.set_child(self.header_view)
        header_frame.set_child(h_scroll)
        paned.set_start_child(header_frame)

        payload_frame = Gtk.Frame(label="Payload")
        p_scroll = Gtk.ScrolledWindow()
        self.payload_view = Gtk.TextView()
        self.payload_view.set_monospace(True)
        self.payload_view.set_editable(False)
        p_scroll.set_child(self.payload_view)
        payload_frame.set_child(p_scroll)
        paned.set_end_child(payload_frame)
        vbox.append(paned)

        info_frame = Gtk.Frame(label="Claims Analysis")
        self.info_view = Gtk.TextView()
        self.info_view.set_editable(False)
        self.info_view.set_monospace(True)
        info_scroll = Gtk.ScrolledWindow()
        info_scroll.set_min_content_height(120)
        info_scroll.set_child(self.info_view)
        info_frame.set_child(info_scroll)
        vbox.append(info_frame)

        self.status_label = Gtk.Label(label="Paste a JWT token above")
        self.status_label.set_xalign(0)
        vbox.append(self.status_label)

    def on_decode(self, *args):
        token = self.token_entry.get_text().strip()
        if not token:
            return
        parts = token.split(".")
        if len(parts) != 3:
            self.status_label.set_markup('<span foreground="#e74c3c">Invalid JWT: must have 3 parts separated by dots</span>')
            return
        try:
            header_raw = b64url_decode(parts[0])
            header = json.loads(header_raw)
            self.header_view.get_buffer().set_text(json.dumps(header, indent=2))
        except Exception as e:
            self.header_view.get_buffer().set_text(f"Error: {e}")
            header = {}

        try:
            payload_raw = b64url_decode(parts[1])
            payload = json.loads(payload_raw)
            self.payload_view.get_buffer().set_text(json.dumps(payload, indent=2))
        except Exception as e:
            self.payload_view.get_buffer().set_text(f"Error: {e}")
            payload = {}

        info_lines = []
        now = int(time.time())
        alg = header.get("alg", "?")
        typ = header.get("typ", "?")
        info_lines.append(f"Algorithm: {alg}  |  Type: {typ}")

        if "exp" in payload:
            exp = payload["exp"]
            exp_dt = datetime.datetime.utcfromtimestamp(exp)
            expired = now > exp
            status = "EXPIRED" if expired else f"valid for {exp - now}s"
            info_lines.append(f"exp (expires): {exp_dt.isoformat()}Z — {status}")

        if "iat" in payload:
            iat = payload["iat"]
            iat_dt = datetime.datetime.utcfromtimestamp(iat)
            info_lines.append(f"iat (issued at): {iat_dt.isoformat()}Z ({now - iat}s ago)")

        if "nbf" in payload:
            nbf = payload["nbf"]
            nbf_dt = datetime.datetime.utcfromtimestamp(nbf)
            valid = now >= nbf
            info_lines.append(f"nbf (not before): {nbf_dt.isoformat()}Z — {'OK' if valid else 'NOT YET VALID'}")

        for claim in ["iss", "sub", "aud", "jti"]:
            if claim in payload:
                info_lines.append(f"{claim}: {payload[claim]}")

        self.info_view.get_buffer().set_text("\n".join(info_lines))
        self.status_label.set_markup('<span foreground="#2ecc71">Decoded successfully (signature NOT verified)</span>')

class JwtDecoderApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.JwtDecoder")
    def do_activate(self):
        win = JwtDecoderWindow(self)
        win.present()

def main():
    app = JwtDecoderApp()
    app.run(None)

if __name__ == "__main__":
    main()
