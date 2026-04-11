#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import math, threading

class PrimeSieveWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Prime Number Sieve")
        self.set_default_size(780, 580)
        self.primes = []
        self.limit = 200
        self.sieve_data = []
        self.build_ui()
        self.run_sieve(200)

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(12); vbox.set_margin_bottom(12)
        vbox.set_margin_start(12); vbox.set_margin_end(12)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Prime Number Sieve (Sieve of Eratosthenes)", css_classes=["title"]))

        ctrl_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        ctrl_box.set_halign(Gtk.Align.CENTER)
        ctrl_box.append(Gtk.Label(label="Find primes up to:"))
        self.limit_spin = Gtk.SpinButton.new_with_range(10, 1000000, 10)
        self.limit_spin.set_value(200)
        ctrl_box.append(self.limit_spin)
        go_btn = Gtk.Button(label="Run Sieve")
        go_btn.connect("clicked", self.on_run)
        ctrl_box.append(go_btn)
        vbox.append(ctrl_box)

        self.status_label = Gtk.Label(label="")
        vbox.append(self.status_label)

        grid_frame = Gtk.Frame(label="Sieve Grid (green=prime, dark=composite)")
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        self.grid_area = Gtk.DrawingArea()
        self.grid_area.set_size_request(740, 300)
        self.grid_area.set_draw_func(self.draw_grid)
        scroll.set_child(self.grid_area)
        grid_frame.set_child(scroll)
        vbox.append(grid_frame)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        stats_frame = Gtk.Frame(label="Statistics")
        scroll2 = Gtk.ScrolledWindow()
        scroll2.set_min_content_height(120)
        self.stats_view = Gtk.TextView()
        self.stats_view.set_editable(False)
        self.stats_view.set_monospace(True)
        scroll2.set_child(self.stats_view)
        stats_frame.set_child(scroll2)
        hbox.append(stats_frame)

        check_frame = Gtk.Frame(label="Check Number")
        check_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        check_vbox.set_margin_top(6); check_vbox.set_margin_start(6); check_vbox.set_margin_end(6); check_vbox.set_margin_bottom(6)
        check_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.check_entry = Gtk.Entry()
        self.check_entry.set_placeholder_text("Enter a number...")
        self.check_entry.set_hexpand(True)
        check_btn = Gtk.Button(label="Check")
        check_btn.connect("clicked", self.on_check)
        check_hbox.append(self.check_entry); check_hbox.append(check_btn)
        check_vbox.append(check_hbox)
        self.check_result = Gtk.Label(label="", xalign=0)
        self.check_result.set_wrap(True)
        check_vbox.append(self.check_result)
        check_frame.set_child(check_vbox)
        hbox.append(check_frame)
        vbox.append(hbox)

    def run_sieve(self, limit):
        self.limit = limit
        n = limit + 1
        sieve = [True] * n
        sieve[0] = sieve[1] = False
        for i in range(2, int(math.sqrt(limit)) + 1):
            if sieve[i]:
                for j in range(i*i, n, i):
                    sieve[j] = False
        self.sieve_data = sieve
        self.primes = [i for i, v in enumerate(sieve) if v]

        n_primes = len(self.primes)
        density = n_primes / limit * 100 if limit > 0 else 0
        twin = sum(1 for i in range(len(self.primes)-1) if self.primes[i+1] - self.primes[i] == 2)
        mersenne = [p for p in self.primes if (p + 1) & p == 0 and p > 1]
        gaps = [self.primes[i+1] - self.primes[i] for i in range(min(len(self.primes)-1, 1000))]
        max_gap = max(gaps) if gaps else 0

        lines = [
            f"Primes found:     {n_primes}",
            f"Largest prime:    {self.primes[-1] if self.primes else 'N/A'}",
            f"Prime density:    {density:.2f}%",
            f"Twin prime pairs: {twin}",
            f"Max prime gap:    {max_gap}",
            f"Mersenne primes:  {mersenne[:8]}",
            f"\nFirst 20: {self.primes[:20]}",
        ]
        self.stats_view.get_buffer().set_text("\n".join(lines))
        self.status_label.set_text(f"Found {n_primes} primes up to {limit}")
        size = min(limit + 1, 1000)
        cell = max(4, 740 // min(size, 100))
        self.grid_area.set_size_request(cell * min(size, 100) + 2, cell * ((size + 99) // 100) + 20)
        self.grid_area.queue_draw()

    def on_run(self, btn):
        limit = int(self.limit_spin.get_value())
        self.status_label.set_text("Computing...")
        threading.Thread(target=lambda: GLib.idle_add(self.run_sieve, limit), daemon=True).start()

    def draw_grid(self, area, cr, w, h):
        cr.set_source_rgb(0.08, 0.08, 0.12); cr.rectangle(0, 0, w, h); cr.fill()
        if not self.sieve_data:
            return
        size = min(len(self.sieve_data), 1001)
        cols = 100
        cell = max(4, (w - 2) // cols)
        for n in range(2, size):
            row = (n - 2) // cols
            col = (n - 2) % cols
            x = col * cell
            y = row * cell + 18
            if self.sieve_data[n]:
                cr.set_source_rgb(0.2, 0.7, 0.3)
            else:
                cr.set_source_rgb(0.18, 0.18, 0.22)
            cr.rectangle(x + 1, y + 1, cell - 2, cell - 2)
            cr.fill()
            if cell >= 14:
                cr.set_source_rgb(0.9, 0.9, 0.9)
                cr.set_font_size(8)
                cr.move_to(x + 2, y + cell - 2)
                cr.show_text(str(n))

    def on_check(self, btn):
        txt = self.check_entry.get_text().strip()
        try:
            n = int(txt)
        except ValueError:
            self.check_result.set_text("Enter a valid integer")
            return

        def is_prime_miller(n):
            if n < 2: return False
            if n == 2: return True
            if n % 2 == 0: return False
            d, r = n - 1, 0
            while d % 2 == 0:
                d //= 2; r += 1
            for a in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]:
                if a >= n: continue
                x = pow(a, d, n)
                if x == 1 or x == n - 1: continue
                for _ in range(r - 1):
                    x = pow(x, 2, n)
                    if x == n - 1: break
                else:
                    return False
            return True

        prime = is_prime_miller(n)
        if prime:
            lines = [f"{n} IS PRIME"]
        else:
            factors = []
            temp = n
            d = 2
            while d * d <= temp:
                while temp % d == 0:
                    factors.append(d)
                    temp //= d
                d += 1
            if temp > 1:
                factors.append(temp)
            lines = [f"{n} is NOT prime", f"Factors: {' × '.join(map(str, factors))}"]

        if n > 0:
            prev_prime = max((p for p in self.primes if p < n), default=None)
            next_prime = min((p for p in self.primes if p > n), default=None)
            if prev_prime:
                lines.append(f"Previous prime: {prev_prime}")
            if next_prime:
                lines.append(f"Next prime: {next_prime}")

        self.check_result.set_text("\n".join(lines))

class PrimeSieveApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.PrimeSieve")
    def do_activate(self):
        win = PrimeSieveWindow(self); win.present()

def main():
    app = PrimeSieveApp(); app.run(None)

if __name__ == "__main__":
    main()
