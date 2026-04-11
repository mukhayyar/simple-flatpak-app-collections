#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import urllib.request, threading, time

class UrlCheckerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("URL Checker")
        self.set_default_size(800, 600)
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="URL Checker", css_classes=["title"]))

        input_frame = Gtk.Frame(label="URLs to check (one per line)")
        input_scroll = Gtk.ScrolledWindow()
        input_scroll.set_min_content_height(100)
        self.url_view = Gtk.TextView()
        self.url_view.set_monospace(True)
        self.url_view.get_buffer().set_text("https://www.google.com\nhttps://github.com\nhttps://httpbin.org/status/404\nhttps://httpbin.org/delay/1")
        input_scroll.set_child(self.url_view)
        input_frame.set_child(input_scroll)
        vbox.append(input_frame)

        ctrl = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.check_btn = Gtk.Button(label="Check All URLs")
        self.check_btn.connect("clicked", self.on_check)
        ctrl.append(self.check_btn)
        self.progress = Gtk.ProgressBar()
        self.progress.set_hexpand(True)
        ctrl.append(self.progress)
        vbox.append(ctrl)

        self.status_label = Gtk.Label(label="Paste URLs above and click Check")
        self.status_label.set_xalign(0)
        vbox.append(self.status_label)

        results_frame = Gtk.Frame(label="Results")
        results_scroll = Gtk.ScrolledWindow()
        results_scroll.set_vexpand(True)
        self.results_view = Gtk.TextView()
        self.results_view.set_monospace(True)
        self.results_view.set_editable(False)
        results_scroll.set_child(self.results_view)
        self.results_buf = self.results_view.get_buffer()
        tt = self.results_buf.get_tag_table()
        for name, color in [("ok", "#2ecc71"), ("warn", "#f39c12"), ("error", "#e74c3c")]:
            tag = Gtk.TextTag.new(name)
            tag.set_property("foreground", color)
            tt.add(tag)
        results_frame.set_child(results_scroll)
        vbox.append(results_frame)

    def on_check(self, btn):
        buf = self.url_view.get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
        urls = [u.strip() for u in text.splitlines() if u.strip()]
        if not urls: return
        self.check_btn.set_sensitive(False)
        self.results_buf.set_text("")
        self.progress.set_fraction(0)
        self.status_label.set_text(f"Checking {len(urls)} URL(s)...")
        threading.Thread(target=self.check_urls, args=(urls,), daemon=True).start()

    def check_urls(self, urls):
        results = [None] * len(urls)
        lock = threading.Lock()
        done = [0]

        def check_one(i, url):
            t0 = time.time()
            try:
                req = urllib.request.Request(url, method="HEAD",
                    headers={"User-Agent": "URL-Checker/1.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    elapsed = time.time() - t0
                    ct = resp.headers.get("Content-Type", "")
                    results[i] = (url, resp.status, elapsed, ct, [])
            except urllib.error.HTTPError as e:
                elapsed = time.time() - t0
                results[i] = (url, e.code, elapsed, "", [])
            except Exception as e:
                elapsed = time.time() - t0
                results[i] = (url, 0, elapsed, "", [str(e)])
            with lock:
                done[0] += 1
                GLib.idle_add(self.update_progress, done[0] / len(urls))
            if all(r is not None for r in results):
                GLib.idle_add(self.show_results, results)

        threads = [threading.Thread(target=check_one, args=(i, url), daemon=True)
                   for i, url in enumerate(urls)]
        for t in threads:
            t.start()

    def update_progress(self, frac):
        self.progress.set_fraction(frac)
        return False

    def show_results(self, results):
        self.results_buf.set_text("")
        ok_count = warn_count = error_count = 0
        for url, status, elapsed, ct, errors in results:
            end = self.results_buf.get_end_iter()
            if 200 <= status < 300:
                tag = "ok"; ok_count += 1; indicator = "OK  "
            elif 400 <= status < 600:
                tag = "warn" if status < 500 else "error"
                if status < 500: warn_count += 1
                else: error_count += 1
                indicator = "FAIL"
            else:
                tag = "error"; error_count += 1; indicator = "ERR "
            line = f"{indicator} {status:3d}  {elapsed*1000:.0f}ms  {url[:60]}\n"
            self.results_buf.insert_with_tags_by_name(end, line, tag)
            if errors:
                end = self.results_buf.get_end_iter()
                self.results_buf.insert_with_tags_by_name(end, f"       {errors[0]}\n", "error")
        self.status_label.set_text(f"Done: {ok_count} OK, {warn_count} warnings, {error_count} errors")
        self.check_btn.set_sensitive(True)
        return False

class UrlCheckerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.UrlChecker")
    def do_activate(self):
        win = UrlCheckerWindow(self)
        win.present()

def main():
    app = UrlCheckerApp()
    app.run(None)

if __name__ == "__main__":
    main()
