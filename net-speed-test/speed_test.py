#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import urllib.request, threading, time, collections

TEST_URLS = [
    "http://speed.cloudflare.com/__down?bytes=10000000",
    "http://ipv4.download.thinkbroadband.com/10MB.zip",
    "http://proof.ovh.net/files/10Mb.dat",
]

MAX_HISTORY = 20

class SpeedTestWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Speed Test")
        self.set_default_size(700, 520)
        self.history = collections.deque(maxlen=MAX_HISTORY)
        self.testing = False
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(16); vbox.set_margin_bottom(16)
        vbox.set_margin_start(16); vbox.set_margin_end(16)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Network Speed Test", css_classes=["title"]))

        self.speed_label = Gtk.Label(label="--")
        css = Gtk.CssProvider()
        css.load_from_data(b".speed-display { font-size: 48px; font-weight: bold; }")
        Gtk.StyleContext.add_provider_for_display(self.get_display(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.speed_label.set_css_classes(["speed-display"])
        vbox.append(self.speed_label)

        self.unit_label = Gtk.Label(label="MB/s")
        vbox.append(self.unit_label)

        self.progress = Gtk.ProgressBar()
        self.progress.set_show_text(True)
        vbox.append(self.progress)

        ctrl = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        ctrl.set_halign(Gtk.Align.CENTER)
        self.test_btn = Gtk.Button(label="Start Speed Test")
        self.test_btn.connect("clicked", self.on_test)
        ctrl.append(self.test_btn)
        vbox.append(ctrl)

        self.status_label = Gtk.Label(label="Click 'Start Speed Test' to begin")
        vbox.append(self.status_label)

        graph_frame = Gtk.Frame(label="Speed History")
        self.graph = Gtk.DrawingArea()
        self.graph.set_size_request(640, 150)
        self.graph.set_draw_func(self.on_draw_graph)
        graph_frame.set_child(self.graph)
        vbox.append(graph_frame)

        self.history_label = Gtk.Label(label="No tests run yet")
        vbox.append(self.history_label)

    def on_test(self, btn):
        if self.testing: return
        self.testing = True
        self.test_btn.set_sensitive(False)
        self.progress.set_fraction(0)
        self.status_label.set_text("Testing download speed...")
        threading.Thread(target=self.do_test, daemon=True).start()

    def do_test(self):
        best_speed = 0
        for url in TEST_URLS:
            try:
                GLib.idle_add(self.update_status, f"Trying: {url[:60]}...")
                start = time.time()
                with urllib.request.urlopen(url, timeout=15) as resp:
                    total = 0
                    chunk_size = 65536
                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk: break
                        total += len(chunk)
                        elapsed = time.time() - start
                        if elapsed > 0:
                            speed = total / elapsed / 1e6
                            GLib.idle_add(self.update_live, speed, total)
                    elapsed = time.time() - start
                    if elapsed > 0 and total > 0:
                        speed = total / elapsed / 1e6
                        best_speed = max(best_speed, speed)
                        break
            except Exception as e:
                GLib.idle_add(self.update_status, f"Failed: {e}")
                continue
        GLib.idle_add(self.test_done, best_speed)

    def update_live(self, speed, total):
        self.speed_label.set_text(f"{speed:.2f}")
        self.progress.set_fraction(min(1.0, total / 10e6))
        self.progress.set_text(f"{total/1e6:.1f} MB downloaded")
        return False

    def update_status(self, text):
        self.status_label.set_text(text)
        return False

    def test_done(self, speed):
        self.testing = False
        self.test_btn.set_sensitive(True)
        if speed > 0:
            self.history.append(speed)
            self.speed_label.set_text(f"{speed:.2f}")
            self.status_label.set_text(f"Download: {speed:.2f} MB/s ({speed*8:.1f} Mbps)")
            avg = sum(self.history) / len(self.history)
            mx = max(self.history)
            self.history_label.set_text(f"Tests: {len(self.history)} | Avg: {avg:.2f} MB/s | Max: {mx:.2f} MB/s")
        else:
            self.speed_label.set_text("--")
            self.status_label.set_text("Speed test failed — check internet connection")
        self.progress.set_fraction(1.0)
        self.graph.queue_draw()
        return False

    def on_draw_graph(self, area, cr, w, h):
        cr.set_source_rgb(0.1, 0.1, 0.15)
        cr.rectangle(0, 0, w, h); cr.fill()
        if len(self.history) < 2: return
        mx = max(self.history) or 1
        step = w / (MAX_HISTORY - 1)
        hist = list(self.history)
        cr.set_source_rgb(0.2, 0.7, 0.9)
        cr.set_line_width(2)
        pts = [(i * step, h - (v / mx) * (h - 20) - 10) for i, v in enumerate(hist)]
        cr.move_to(*pts[0])
        for pt in pts[1:]:
            cr.line_to(*pt)
        cr.stroke()
        for x, y in pts:
            cr.arc(x, y, 3, 0, 6.28); cr.fill()

class SpeedTestApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.SpeedTest")
    def do_activate(self):
        win = SpeedTestWindow(self)
        win.present()

def main():
    app = SpeedTestApp()
    app.run(None)

if __name__ == "__main__":
    main()
