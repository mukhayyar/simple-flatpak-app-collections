#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import socket, threading

class SocketTesterWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Socket Tester")
        self.set_default_size(780, 640)
        self.server_sock = None
        self.client_sock = None
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Socket Tester", css_classes=["title"]))

        conn_frame = Gtk.Frame(label="Connection")
        conn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        conn_box.set_margin_top(6); conn_box.set_margin_start(6); conn_box.set_margin_bottom(6); conn_box.set_margin_end(6)

        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.client_radio = Gtk.CheckButton(label="TCP Client")
        self.client_radio.set_active(True)
        self.server_radio = Gtk.CheckButton(label="TCP Listener")
        self.server_radio.set_group(self.client_radio)
        self.udp_radio = Gtk.CheckButton(label="UDP Client")
        self.udp_radio.set_group(self.client_radio)
        mode_box.append(self.client_radio)
        mode_box.append(self.server_radio)
        mode_box.append(self.udp_radio)
        conn_box.append(mode_box)

        host_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        host_box.append(Gtk.Label(label="Host:"))
        self.host_entry = Gtk.Entry(); self.host_entry.set_text("localhost"); self.host_entry.set_hexpand(True)
        host_box.append(self.host_entry)
        host_box.append(Gtk.Label(label="Port:"))
        self.port_spin = Gtk.SpinButton.new_with_range(1, 65535, 1)
        self.port_spin.set_value(8080)
        host_box.append(self.port_spin)
        conn_box.append(host_box)

        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.connect_btn = Gtk.Button(label="Connect")
        self.connect_btn.connect("clicked", self.on_connect)
        self.disconnect_btn = Gtk.Button(label="Disconnect")
        self.disconnect_btn.connect("clicked", self.on_disconnect)
        self.disconnect_btn.set_sensitive(False)
        btn_row.append(self.connect_btn); btn_row.append(self.disconnect_btn)
        conn_box.append(btn_row)
        conn_frame.set_child(conn_box)
        vbox.append(conn_frame)

        self.status_label = Gtk.Label(label="Not connected")
        self.status_label.set_xalign(0)
        vbox.append(self.status_label)

        recv_frame = Gtk.Frame(label="Received Data")
        recv_scroll = Gtk.ScrolledWindow()
        recv_scroll.set_min_content_height(180)
        self.recv_view = Gtk.TextView()
        self.recv_view.set_monospace(True); self.recv_view.set_editable(False)
        recv_scroll.set_child(self.recv_view)
        recv_frame.set_child(recv_scroll)
        vbox.append(recv_frame)

        send_frame = Gtk.Frame(label="Send Data")
        send_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        send_box.set_margin_top(4); send_box.set_margin_start(4); send_box.set_margin_bottom(4); send_box.set_margin_end(4)

        self.hex_toggle = Gtk.CheckButton(label="Hex display")
        send_box.append(self.hex_toggle)

        msg_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.msg_entry = Gtk.Entry()
        self.msg_entry.set_placeholder_text("Enter message to send...")
        self.msg_entry.set_hexpand(True)
        self.msg_entry.connect("activate", self.on_send)
        msg_box.append(self.msg_entry)
        send_btn = Gtk.Button(label="Send")
        send_btn.connect("clicked", self.on_send)
        msg_box.append(send_btn)
        send_box.append(msg_box)
        send_frame.set_child(send_box)
        vbox.append(send_frame)

    def on_connect(self, btn):
        host = self.host_entry.get_text().strip()
        port = int(self.port_spin.get_value())

        if self.server_radio.get_active():
            threading.Thread(target=self.start_listener, args=(port,), daemon=True).start()
        elif self.udp_radio.get_active():
            threading.Thread(target=self.connect_udp, args=(host, port), daemon=True).start()
        else:
            threading.Thread(target=self.connect_tcp, args=(host, port), daemon=True).start()

    def connect_tcp(self, host, port):
        try:
            self.client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_sock.connect((host, port))
            GLib.idle_add(self.set_connected, f"TCP connected to {host}:{port}")
            while True:
                data = self.client_sock.recv(4096)
                if not data: break
                GLib.idle_add(self.append_recv, data)
        except Exception as e:
            GLib.idle_add(self.set_status, f"Error: {e}")

    def connect_udp(self, host, port):
        self.client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_sock.settimeout(5)
        self._udp_target = (host, port)
        GLib.idle_add(self.set_connected, f"UDP ready → {host}:{port}")

    def start_listener(self, port):
        try:
            self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_sock.bind(("0.0.0.0", port))
            self.server_sock.listen(1)
            GLib.idle_add(self.set_status, f"Listening on port {port}...")
            conn, addr = self.server_sock.accept()
            self.client_sock = conn
            GLib.idle_add(self.set_connected, f"Client connected: {addr}")
            while True:
                data = conn.recv(4096)
                if not data: break
                GLib.idle_add(self.append_recv, data)
        except Exception as e:
            GLib.idle_add(self.set_status, f"Listener error: {e}")

    def on_disconnect(self, btn):
        if self.client_sock:
            try: self.client_sock.close()
            except Exception: pass
            self.client_sock = None
        if self.server_sock:
            try: self.server_sock.close()
            except Exception: pass
            self.server_sock = None
        self.set_status("Disconnected")
        self.connect_btn.set_sensitive(True)
        self.disconnect_btn.set_sensitive(False)

    def on_send(self, *args):
        msg = self.msg_entry.get_text()
        if not msg or not self.client_sock: return
        data = msg.encode("utf-8")
        try:
            if self.udp_radio.get_active() and hasattr(self, '_udp_target'):
                self.client_sock.sendto(data, self._udp_target)
            else:
                self.client_sock.send(data)
            display = data.hex() if self.hex_toggle.get_active() else msg
            end = self.recv_view.get_buffer().get_end_iter()
            self.recv_view.get_buffer().insert(end, f"→ {display}\n")
            self.msg_entry.set_text("")
        except Exception as e:
            self.set_status(f"Send error: {e}")

    def set_connected(self, msg):
        self.set_status(msg)
        self.connect_btn.set_sensitive(False)
        self.disconnect_btn.set_sensitive(True)
        return False

    def set_status(self, msg):
        self.status_label.set_text(msg)
        return False

    def append_recv(self, data):
        text = data.hex() if self.hex_toggle.get_active() else data.decode("utf-8", errors="replace")
        end = self.recv_view.get_buffer().get_end_iter()
        self.recv_view.get_buffer().insert(end, f"← {text}\n")
        self.recv_view.scroll_to_iter(self.recv_view.get_buffer().get_end_iter(), 0, False, 0, 1)
        return False

class SocketTesterApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.SocketTester")
    def do_activate(self):
        win = SocketTesterWindow(self)
        win.present()

def main():
    app = SocketTesterApp()
    app.run(None)

if __name__ == "__main__":
    main()
