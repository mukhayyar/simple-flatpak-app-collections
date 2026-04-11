#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk
import datetime

class InvoiceMakerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app); self.set_title("Invoice Maker"); self.set_default_size(900,720)
        self.line_items = []
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        hbox.set_margin_top(8); hbox.set_margin_bottom(8); hbox.set_margin_start(8); hbox.set_margin_end(8)
        self.set_child(hbox)
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); left.set_size_request(400,-1)
        
        for label, key in [("Business Name","biz_name"),("Business Address","biz_addr"),("Client Name","client_name"),("Client Address","client_addr"),("Invoice #","invoice_num"),("Due Date","due_date")]:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            row.append(Gtk.Label(label=f"{label}:", width_chars=16, xalign=1))
            e = Gtk.Entry(); e.set_hexpand(True); row.append(e)
            setattr(self, f"field_{key}", e); left.append(row)
        self.field_invoice_num.set_text(f"INV-{datetime.date.today().strftime('%Y%m%d')}-001")
        self.field_due_date.set_text((datetime.date.today() + datetime.timedelta(days=30)).isoformat())

        left.append(Gtk.Label(label="Line Items:", xalign=0))
        items_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2); self.items_box = items_box; left.append(items_box)
        add_item_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.item_desc = Gtk.Entry(); self.item_desc.set_placeholder_text("Description"); self.item_desc.set_hexpand(True)
        self.item_qty = Gtk.SpinButton.new_with_range(1,999,1); self.item_qty.set_value(1)
        self.item_rate = Gtk.Entry(); self.item_rate.set_placeholder_text("Rate"); self.item_rate.set_width_chars(8)
        add_item_btn = Gtk.Button(label="Add"); add_item_btn.connect("clicked", self.on_add_item)
        add_item_row.append(self.item_desc); add_item_row.append(self.item_qty); add_item_row.append(self.item_rate); add_item_row.append(add_item_btn)
        left.append(add_item_row)
        
        tax_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        tax_row.append(Gtk.Label(label="Tax %:"))
        self.tax_spin = Gtk.SpinButton.new_with_range(0,100,0.5); self.tax_spin.set_value(0)
        self.tax_spin.connect("value-changed", self.update_preview); tax_row.append(self.tax_spin)
        left.append(tax_row)
        
        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        preview_btn = Gtk.Button(label="Update Preview"); preview_btn.connect("clicked", self.update_preview)
        copy_btn = Gtk.Button(label="Copy Text"); copy_btn.connect("clicked", self.on_copy)
        btn_row.append(preview_btn); btn_row.append(copy_btn)
        left.append(btn_row)
        hbox.append(left)
        
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4); right.set_hexpand(True)
        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        self.preview_view = Gtk.TextView(); self.preview_view.set_monospace(True); self.preview_view.set_editable(False)
        scroll.set_child(self.preview_view); right.append(scroll); hbox.append(right)

    def on_add_item(self, btn):
        desc = self.item_desc.get_text().strip()
        if not desc: return
        try: rate = float(self.item_rate.get_text())
        except ValueError: return
        qty = int(self.item_qty.get_value())
        item = {"desc": desc, "qty": qty, "rate": rate}
        self.line_items.append(item)
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        lbl = Gtk.Label(label=f"{qty}x {desc}: ${rate*qty:.2f}", xalign=0, hexpand=True); row.append(lbl)
        del_btn = Gtk.Button(label="×"); del_btn.connect("clicked", lambda b, i=item, r=row: self.remove_item(i, r)); row.append(del_btn)
        self.items_box.append(row)
        self.item_desc.set_text(""); self.item_rate.set_text(""); self.item_qty.set_value(1)
        self.update_preview(None)

    def remove_item(self, item, row):
        self.line_items.remove(item); self.items_box.remove(row); self.update_preview(None)

    def update_preview(self, *a):
        subtotal = sum(i["qty"]*i["rate"] for i in self.line_items)
        tax_rate = self.tax_spin.get_value() / 100
        tax = subtotal * tax_rate; total = subtotal + tax
        lines = []
        lines.append("=" * 50)
        lines.append(f"  INVOICE")
        lines.append("=" * 50)
        lines.append(f"FROM: {self.field_biz_name.get_text()}")
        lines.append(f"      {self.field_biz_addr.get_text()}")
        lines.append(f"TO:   {self.field_client_name.get_text()}")
        lines.append(f"      {self.field_client_addr.get_text()}")
        lines.append(f"Invoice #: {self.field_invoice_num.get_text()}")
        lines.append(f"Due Date:  {self.field_due_date.get_text()}")
        lines.append("-" * 50)
        lines.append(f"{'Description':<25} {'Qty':>5} {'Rate':>8} {'Total':>8}")
        lines.append("-" * 50)
        for item in self.line_items:
            lines.append(f"{item['desc'][:25]:<25} {item['qty']:>5} ${item['rate']:>7.2f} ${item['qty']*item['rate']:>7.2f}")
        lines.append("-" * 50)
        lines.append(f"{'Subtotal':>42} ${subtotal:>7.2f}")
        if tax_rate > 0: lines.append(f"{'Tax ({:.1f}%)'.format(tax_rate*100):>42} ${tax:>7.2f}")
        lines.append(f"{'TOTAL':>42} ${total:>7.2f}")
        lines.append("=" * 50)
        self.preview_view.get_buffer().set_text("\n".join(lines))

    def on_copy(self, btn):
        buf = self.preview_view.get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
        Gdk.Display.get_default().get_clipboard().set(text)

class InvoiceMakerApp(Gtk.Application):
    def __init__(self): super().__init__(application_id="com.pens.InvoiceMaker")
    def do_activate(self): InvoiceMakerWindow(self).present()

def main(): InvoiceMakerApp().run(None)
if __name__ == "__main__": main()
