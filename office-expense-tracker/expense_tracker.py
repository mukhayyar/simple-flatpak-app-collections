#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import json, os, datetime, math

DATA_DIR = os.path.expanduser("~/.local/share/com.pens.ExpenseTracker")
DATA_FILE = os.path.join(DATA_DIR, "expenses.json")
CATEGORIES = ["Food", "Transport", "Housing", "Health", "Entertainment", "Shopping", "Other"]

class ExpenseTrackerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Expense Tracker")
        self.set_default_size(900, 700)
        os.makedirs(DATA_DIR, exist_ok=True)
        self.expenses = self.load_expenses()
        self.build_ui()
        self.refresh()

    def load_expenses(self):
        try:
            with open(DATA_FILE) as f:
                return json.load(f)
        except Exception:
            return []

    def save_expenses(self):
        with open(DATA_FILE, "w") as f:
            json.dump(self.expenses, f)

    def build_ui(self):
        paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(paned)

        top = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        top.set_margin_top(8); top.set_margin_start(8); top.set_margin_end(8); top.set_margin_bottom(4)
        top.set_size_request(-1, 280)

        form = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        form.append(Gtk.Label(label="Date:"))
        self.date_entry = Gtk.Entry(); self.date_entry.set_text(datetime.date.today().isoformat())
        form.append(self.date_entry)
        form.append(Gtk.Label(label="Amount:"))
        self.amount_entry = Gtk.Entry(); self.amount_entry.set_placeholder_text("0.00")
        form.append(self.amount_entry)
        form.append(Gtk.Label(label="Category:"))
        self.cat_combo = Gtk.ComboBoxText()
        for c in CATEGORIES: self.cat_combo.append_text(c)
        self.cat_combo.set_active(0)
        form.append(self.cat_combo)
        form.append(Gtk.Label(label="Description:"))
        self.desc_entry = Gtk.Entry(); self.desc_entry.set_hexpand(True)
        form.append(self.desc_entry)
        add_btn = Gtk.Button(label="Add"); add_btn.connect("clicked", self.on_add)
        form.append(add_btn)
        top.append(form)

        self.total_label = Gtk.Label(label="Total: $0.00")
        top.append(self.total_label)

        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        self.list_view = Gtk.TextView(); self.list_view.set_monospace(True); self.list_view.set_editable(False)
        scroll.set_child(self.list_view)
        top.append(scroll)

        export_btn = Gtk.Button(label="Export CSV"); export_btn.connect("clicked", self.on_export)
        top.append(export_btn)
        paned.set_start_child(top)

        charts_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        charts_box.set_margin_top(4); charts_box.set_margin_start(8); charts_box.set_margin_end(8); charts_box.set_margin_bottom(8)

        bar_frame = Gtk.Frame(label="Monthly Summary")
        self.bar_chart = Gtk.DrawingArea(); self.bar_chart.set_draw_func(self.draw_bar)
        self.bar_chart.set_hexpand(True); self.bar_chart.set_vexpand(True)
        bar_frame.set_child(self.bar_chart)
        charts_box.append(bar_frame)

        pie_frame = Gtk.Frame(label="By Category")
        self.pie_chart = Gtk.DrawingArea(); self.pie_chart.set_draw_func(self.draw_pie)
        self.pie_chart.set_hexpand(True); self.pie_chart.set_vexpand(True)
        pie_frame.set_child(self.pie_chart)
        charts_box.append(pie_frame)
        paned.set_end_child(charts_box)

    def on_add(self, btn):
        try:
            amount = float(self.amount_entry.get_text())
        except ValueError:
            return
        exp = {"date": self.date_entry.get_text(), "amount": amount,
               "category": self.cat_combo.get_active_text(), "description": self.desc_entry.get_text()}
        self.expenses.append(exp)
        self.save_expenses()
        self.amount_entry.set_text(""); self.desc_entry.set_text("")
        self.refresh()

    def refresh(self):
        lines = ["Date        Amount   Category     Description"]
        lines.append("-" * 60)
        total = 0
        sorted_exp = sorted(self.expenses, key=lambda x: x["date"], reverse=True)
        for e in sorted_exp:
            lines.append(f"{e["date"]}  ${e["amount"]:7.2f}  {e["category"]:<12} {e["description"][:30]}")
            total += e["amount"]
        self.list_view.get_buffer().set_text("\n".join(lines))
        self.total_label.set_text(f"Total: ${total:.2f}")
        self.bar_chart.queue_draw(); self.pie_chart.queue_draw()

    def draw_bar(self, area, cr, w, h):
        cr.set_source_rgb(0.1,0.1,0.15); cr.rectangle(0,0,w,h); cr.fill()
        monthly = {}
        for e in self.expenses:
            m = e["date"][:7]
            monthly[m] = monthly.get(m, 0) + e["amount"]
        if not monthly: return
        months = sorted(monthly.keys())[-6:]
        mx = max(monthly.values()) or 1
        bw = w / (len(months) + 1)
        for i, m in enumerate(months):
            bh = (monthly[m] / mx) * (h - 40)
            cr.set_source_rgb(0.3, 0.6, 0.9)
            cr.rectangle(i*bw + bw*0.2, h-30-bh, bw*0.6, bh); cr.fill()
            cr.set_source_rgb(0.8,0.8,0.8); cr.set_font_size(9)
            cr.move_to(i*bw+2, h-10); cr.show_text(m[5:])
            cr.move_to(i*bw+2, h-30-bh-2); cr.show_text(f"${monthly[m]:.0f}")

    def draw_pie(self, area, cr, w, h):
        cr.set_source_rgb(0.1,0.1,0.15); cr.rectangle(0,0,w,h); cr.fill()
        by_cat = {}
        for e in self.expenses:
            by_cat[e["category"]] = by_cat.get(e["category"], 0) + e["amount"]
        if not by_cat: return
        total = sum(by_cat.values()) or 1
        cx, cy, r = w/2, h/2, min(w,h)*0.35
        colors = [(0.9,0.2,0.2),(0.2,0.8,0.2),(0.2,0.2,0.9),(0.9,0.9,0.2),(0.9,0.2,0.9),(0.2,0.9,0.9),(0.8,0.5,0.2)]
        angle = -math.pi/2
        for i, (cat, val) in enumerate(by_cat.items()):
            sweep = (val / total) * 2 * math.pi
            cr.set_source_rgb(*colors[i % len(colors)])
            cr.move_to(cx, cy); cr.arc(cx, cy, r, angle, angle+sweep); cr.close_path(); cr.fill()
            mid = angle + sweep/2
            tx = cx + r*0.7*math.cos(mid); ty = cy + r*0.7*math.sin(mid)
            cr.set_source_rgb(1,1,1); cr.set_font_size(9)
            cr.move_to(tx-10, ty); cr.show_text(f"{cat[:6]}")
            angle += sweep

    def on_export(self, btn):
        dialog = Gtk.FileDialog(); dialog.save(self, None, self.do_export)

    def do_export(self, dialog, result):
        try:
            f = dialog.save_finish(result)
            if f:
                with open(f.get_path(), "w") as fp:
                    fp.write("Date,Amount,Category,Description\n")
                    for e in self.expenses:
                        fp.write(f"{e["date"]},{e["amount"]},{e["category"]},{e["description"]}\n")
        except Exception: pass

class ExpenseTrackerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.ExpenseTracker")
    def do_activate(self):
        win = ExpenseTrackerWindow(self); win.present()

def main():
    app = ExpenseTrackerApp(); app.run(None)

if __name__ == "__main__":
    main()
