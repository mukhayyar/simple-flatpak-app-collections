#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import math, statistics

class StatisticsCalcWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Statistics Calculator")
        self.set_default_size(800, 600)
        self.build_ui()

    def build_ui(self):
        hpaned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_child(hpaned)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        left.set_size_request(300, -1)
        left.set_margin_top(8); left.set_margin_start(8); left.set_margin_bottom(8)

        left.append(Gtk.Label(label="Enter data (one value per line or comma-separated):", xalign=0))
        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        self.data_view = Gtk.TextView()
        self.data_view.set_monospace(True)
        sample = "4\n7\n13\n2\n1\n8\n15\n6\n3\n9\n11\n7\n5\n14\n2\n8"
        self.data_view.get_buffer().set_text(sample)
        scroll.set_child(self.data_view)
        left.append(scroll)

        calc_btn = Gtk.Button(label="Calculate Statistics")
        calc_btn.connect("clicked", self.on_calculate)
        left.append(calc_btn)
        hpaned.set_start_child(left)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        right.set_margin_top(8); right.set_margin_end(8); right.set_margin_bottom(8); right.set_margin_start(4)

        stats_frame = Gtk.Frame(label="Descriptive Statistics")
        scroll2 = Gtk.ScrolledWindow()
        scroll2.set_min_content_height(200)
        self.stats_view = Gtk.TextView()
        self.stats_view.set_editable(False)
        self.stats_view.set_monospace(True)
        scroll2.set_child(self.stats_view)
        stats_frame.set_child(scroll2)
        right.append(stats_frame)

        chart_frame = Gtk.Frame(label="Histogram & Box Plot")
        self.chart = Gtk.DrawingArea()
        self.chart.set_vexpand(True)
        self.chart.set_draw_func(self.draw_chart)
        chart_frame.set_child(self.chart)
        right.append(chart_frame)

        hpaned.set_end_child(right)

        self.data = []
        self.on_calculate(None)

    def parse_data(self):
        buf = self.data_view.get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
        values = []
        for part in text.replace(',', '\n').split('\n'):
            part = part.strip()
            if part:
                try:
                    values.append(float(part))
                except ValueError:
                    pass
        return values

    def on_calculate(self, btn):
        data = self.parse_data()
        if not data:
            self.stats_view.get_buffer().set_text("No valid data")
            return
        self.data = sorted(data)
        n = len(data)
        mean = statistics.mean(data)
        median = statistics.median(data)
        try:
            mode = statistics.mode(data)
        except Exception:
            mode = "multimodal"
        std = statistics.stdev(data) if n > 1 else 0
        var = statistics.variance(data) if n > 1 else 0
        mn, mx = min(data), max(data)
        rng = mx - mn
        q1 = statistics.quantiles(data, n=4)[0] if n >= 4 else mn
        q3 = statistics.quantiles(data, n=4)[2] if n >= 4 else mx
        iqr = q3 - q1
        skew = sum((x - mean)**3 for x in data) / (n * std**3) if std > 0 else 0
        kurt = sum((x - mean)**4 for x in data) / (n * std**4) - 3 if std > 0 else 0
        cv = (std / mean * 100) if mean != 0 else 0

        lines = [
            f"{'Count':<25} {n}",
            f"{'Sum':<25} {sum(data):.4f}",
            f"{'Mean':<25} {mean:.4f}",
            f"{'Median':<25} {median:.4f}",
            f"{'Mode':<25} {mode}",
            f"{'Std Dev (sample)':<25} {std:.4f}",
            f"{'Variance (sample)':<25} {var:.4f}",
            f"{'Min':<25} {mn:.4f}",
            f"{'Max':<25} {mx:.4f}",
            f"{'Range':<25} {rng:.4f}",
            f"{'Q1 (25th pct)':<25} {q1:.4f}",
            f"{'Q3 (75th pct)':<25} {q3:.4f}",
            f"{'IQR':<25} {iqr:.4f}",
            f"{'Skewness':<25} {skew:.4f}",
            f"{'Kurtosis (excess)':<25} {kurt:.4f}",
            f"{'Coeff of Variation':<25} {cv:.2f}%",
        ]
        self.stats_view.get_buffer().set_text("\n".join(lines))
        self.chart.queue_draw()

    def draw_chart(self, area, cr, w, h):
        cr.set_source_rgb(0.08, 0.08, 0.12)
        cr.rectangle(0, 0, w, h); cr.fill()
        if not self.data:
            return
        half_h = h // 2

        # Histogram (top half)
        mn, mx = min(self.data), max(self.data)
        bins = 10
        bin_w = (mx - mn) / bins if mx != mn else 1
        counts = [0] * bins
        for v in self.data:
            idx = min(int((v - mn) / bin_w), bins - 1)
            counts[idx] += 1
        max_count = max(counts) or 1
        cell_w = w / bins
        for i, c in enumerate(counts):
            bh = int(c / max_count * (half_h - 20))
            cr.set_source_rgb(0.3, 0.6, 0.9)
            cr.rectangle(i * cell_w + 1, half_h - 15 - bh, cell_w - 2, bh)
            cr.fill()
            cr.set_source_rgb(0.7, 0.7, 0.7)
            cr.set_font_size(8)
            xv = mn + i * bin_w
            cr.move_to(i * cell_w + 2, half_h - 2); cr.show_text(f"{xv:.1f}")
            cr.move_to(i * cell_w + 2, half_h - 18 - bh); cr.show_text(str(c))

        # Box plot (bottom half)
        y_base = half_h + 10
        box_h = half_h - 30
        padding = 30
        plot_w = w - 2 * padding

        def px(v):
            return padding + (v - mn) / (mx - mn) * plot_w if mx != mn else padding

        q1 = statistics.quantiles(self.data, n=4)[0] if len(self.data) >= 4 else mn
        q3 = statistics.quantiles(self.data, n=4)[2] if len(self.data) >= 4 else mx
        med = statistics.median(self.data)
        iqr = q3 - q1
        whisker_low = max(mn, q1 - 1.5 * iqr)
        whisker_high = min(mx, q3 + 1.5 * iqr)

        mid_y = y_base + box_h // 2
        bh = box_h // 3

        cr.set_source_rgb(0.3, 0.6, 0.9)
        cr.set_line_width(1)
        cr.move_to(px(whisker_low), mid_y); cr.line_to(px(q1), mid_y); cr.stroke()
        cr.move_to(px(q3), mid_y); cr.line_to(px(whisker_high), mid_y); cr.stroke()
        cr.rectangle(px(q1), mid_y - bh, px(q3) - px(q1), bh * 2)
        cr.set_source_rgba(0.3, 0.6, 0.9, 0.4); cr.fill()
        cr.set_source_rgb(0.3, 0.6, 0.9); cr.rectangle(px(q1), mid_y - bh, px(q3) - px(q1), bh * 2); cr.stroke()
        cr.set_source_rgb(0.9, 0.5, 0.3); cr.set_line_width(2)
        cr.move_to(px(med), mid_y - bh); cr.line_to(px(med), mid_y + bh); cr.stroke()

        mean_v = statistics.mean(self.data)
        cr.set_source_rgb(0.9, 0.9, 0.3)
        cr.arc(px(mean_v), mid_y, 4, 0, math.tau); cr.fill()

        outliers = [v for v in self.data if v < whisker_low or v > whisker_high]
        cr.set_source_rgb(0.9, 0.3, 0.3)
        for v in outliers:
            cr.arc(px(v), mid_y, 3, 0, math.tau); cr.fill()

        cr.set_source_rgb(0.7, 0.7, 0.7); cr.set_font_size(9)
        cr.move_to(padding, y_base + box_h + 14); cr.show_text(f"{mn:.1f}")
        cr.move_to(px(med) - 10, y_base + box_h + 14); cr.show_text(f"M:{med:.1f}")
        cr.move_to(w - padding - 30, y_base + box_h + 14); cr.show_text(f"{mx:.1f}")

class StatisticsCalcApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.StatisticsCalc")
    def do_activate(self):
        win = StatisticsCalcWindow(self); win.present()

def main():
    app = StatisticsCalcApp(); app.run(None)

if __name__ == "__main__":
    main()
