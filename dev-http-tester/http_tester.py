#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import urllib.request, urllib.error, json, threading, time

class HttpTesterWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("HTTP Tester")
        self.set_default_size(900, 700)
        self.headers_rows = []

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        # Request area
        req_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.method_combo = Gtk.ComboBoxText()
        for m in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]:
            self.method_combo.append_text(m)
        self.method_combo.set_active(0)
        req_box.append(self.method_combo)
        self.url_entry = Gtk.Entry()
        self.url_entry.set_placeholder_text("https://api.example.com/endpoint")
        self.url_entry.set_hexpand(True)
        req_box.append(self.url_entry)
        send_btn = Gtk.Button(label="Send")
        send_btn.connect("clicked", self.on_send)
        req_box.append(send_btn)
        vbox.append(req_box)

        paned_h = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned_h.set_vexpand(True)

        # Left: request config
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        left.set_size_request(380, -1)

        headers_frame = Gtk.Frame(label="Headers")
        hdr_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        hdr_vbox.set_margin_top(4); hdr_vbox.set_margin_start(4)
        hdr_vbox.set_margin_bottom(4); hdr_vbox.set_margin_end(4)
        self.headers_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        hdr_vbox.append(self.headers_box)
        add_hdr_btn = Gtk.Button(label="+ Add Header")
        add_hdr_btn.connect("clicked", self.on_add_header)
        hdr_vbox.append(add_hdr_btn)
        headers_frame.set_child(hdr_vbox)
        left.append(headers_frame)
        self.add_header_row("Content-Type", "application/json")

        body_frame = Gtk.Frame(label="Request Body")
        body_scroll = Gtk.ScrolledWindow()
        body_scroll.set_min_content_height(120)
        self.body_view = Gtk.TextView()
        self.body_view.set_monospace(True)
        body_scroll.set_child(self.body_view)
        body_frame.set_child(body_scroll)
        left.append(body_frame)

        paned_h.set_start_child(left)

        # Right: response
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.status_label = Gtk.Label(label="Ready")
        self.status_label.set_xalign(0)
        right.append(self.status_label)

        resp_hdr_frame = Gtk.Frame(label="Response Headers")
        resp_hdr_scroll = Gtk.ScrolledWindow()
        resp_hdr_scroll.set_min_content_height(120)
        self.resp_headers_view = Gtk.TextView()
        self.resp_headers_view.set_editable(False)
        self.resp_headers_view.set_monospace(True)
        resp_hdr_scroll.set_child(self.resp_headers_view)
        resp_hdr_frame.set_child(resp_hdr_scroll)
        right.append(resp_hdr_frame)

        resp_body_frame = Gtk.Frame(label="Response Body")
        resp_body_scroll = Gtk.ScrolledWindow()
        resp_body_scroll.set_vexpand(True)
        self.resp_body_view = Gtk.TextView()
        self.resp_body_view.set_editable(False)
        self.resp_body_view.set_monospace(True)
        resp_body_scroll.set_child(self.resp_body_view)
        resp_body_frame.set_child(resp_body_scroll)
        right.append(resp_body_frame)

        paned_h.set_end_child(right)
        vbox.append(paned_h)

    def add_header_row(self, key="", value=""):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        key_entry = Gtk.Entry(); key_entry.set_placeholder_text("Key"); key_entry.set_hexpand(True)
        val_entry = Gtk.Entry(); val_entry.set_placeholder_text("Value"); val_entry.set_hexpand(True)
        key_entry.set_text(key); val_entry.set_text(value)
        del_btn = Gtk.Button(label="×")
        del_btn.connect("clicked", lambda b, r=row: self.remove_header(r))
        row.append(key_entry); row.append(val_entry); row.append(del_btn)
        self.headers_box.append(row)
        self.headers_rows.append((row, key_entry, val_entry))

    def remove_header(self, row):
        self.headers_box.remove(row)
        self.headers_rows = [(r, k, v) for r, k, v in self.headers_rows if r != row]

    def on_add_header(self, btn):
        self.add_header_row()

    def on_send(self, btn):
        url = self.url_entry.get_text().strip()
        method = self.method_combo.get_active_text()
        headers = {k.get_text(): v.get_text() for _, k, v in self.headers_rows if k.get_text()}
        body_buf = self.body_view.get_buffer()
        body = body_buf.get_text(body_buf.get_start_iter(), body_buf.get_end_iter(), True).encode("utf-8")
        self.status_label.set_text("Sending...")
        threading.Thread(target=self.do_request, args=(url, method, headers, body), daemon=True).start()

    def do_request(self, url, method, headers, body):
        t0 = time.time()
        try:
            req = urllib.request.Request(url, data=body if body else None, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=15) as resp:
                elapsed = time.time() - t0
                status = resp.status
                resp_headers = dict(resp.headers)
                resp_body = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            elapsed = time.time() - t0
            status = e.code
            resp_headers = dict(e.headers)
            resp_body = e.read().decode("utf-8", errors="replace")
        except Exception as e:
            elapsed = time.time() - t0
            status = 0
            resp_headers = {}
            resp_body = str(e)
        GLib.idle_add(self.show_response, status, resp_headers, resp_body, elapsed)

    def show_response(self, status, headers, body, elapsed):
        color = "#2ecc71" if 200 <= status < 300 else "#f39c12" if 400 <= status < 500 else "#e74c3c"
        self.status_label.set_markup(f'<span foreground="{color}">Status: {status}</span>  {elapsed*1000:.0f}ms')
        hdr_text = "\n".join(f"{k}: {v}" for k, v in headers.items())
        self.resp_headers_view.get_buffer().set_text(hdr_text)
        try:
            parsed = json.loads(body)
            body = json.dumps(parsed, indent=2)
        except Exception:
            pass
        self.resp_body_view.get_buffer().set_text(body)
        return False

class HttpTesterApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.HttpTester")
    def do_activate(self):
        win = HttpTesterWindow(self)
        win.present()

def main():
    app = HttpTesterApp()
    app.run(None)

if __name__ == "__main__":
    main()
