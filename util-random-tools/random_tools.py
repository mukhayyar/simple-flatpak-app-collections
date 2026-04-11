#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import random, string, uuid, os

class RandomToolsWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Random Tools")
        self.set_default_size(660, 580)
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(12); vbox.set_margin_bottom(12)
        vbox.set_margin_start(16); vbox.set_margin_end(16)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Random Tools", css_classes=["title"]))

        notebook = Gtk.Notebook()
        vbox.append(notebook)

        # Number page
        num_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        num_page.set_margin_top(12); num_page.set_margin_start(12); num_page.set_margin_end(12); num_page.set_margin_bottom(12)

        range_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        range_box.set_halign(Gtk.Align.CENTER)
        range_box.append(Gtk.Label(label="Min:"))
        self.num_min = Gtk.SpinButton.new_with_range(-1000000, 1000000, 1)
        self.num_min.set_value(1)
        range_box.append(self.num_min)
        range_box.append(Gtk.Label(label="Max:"))
        self.num_max = Gtk.SpinButton.new_with_range(-1000000, 1000000, 1)
        self.num_max.set_value(100)
        range_box.append(self.num_max)
        range_box.append(Gtk.Label(label="Count:"))
        self.num_count = Gtk.SpinButton.new_with_range(1, 1000, 1)
        self.num_count.set_value(1)
        range_box.append(self.num_count)
        num_page.append(range_box)

        float_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        float_box.set_halign(Gtk.Align.CENTER)
        self.float_check = Gtk.CheckButton(label="Float")
        self.unique_check = Gtk.CheckButton(label="Unique")
        self.sorted_check = Gtk.CheckButton(label="Sorted")
        float_box.append(self.float_check); float_box.append(self.unique_check); float_box.append(self.sorted_check)
        num_page.append(float_box)

        gen_num_btn = Gtk.Button(label="Generate Numbers")
        gen_num_btn.set_halign(Gtk.Align.CENTER)
        gen_num_btn.connect("clicked", self.on_gen_numbers)
        num_page.append(gen_num_btn)

        num_scroll = Gtk.ScrolledWindow(); num_scroll.set_vexpand(True)
        self.num_view = Gtk.TextView(); self.num_view.set_editable(False); self.num_view.set_monospace(True)
        num_scroll.set_child(self.num_view)
        num_page.append(num_scroll)
        notebook.append_page(num_page, Gtk.Label(label="Numbers"))

        # Password page
        pw_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        pw_page.set_margin_top(12); pw_page.set_margin_start(12); pw_page.set_margin_end(12); pw_page.set_margin_bottom(12)

        pw_len_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        pw_len_box.append(Gtk.Label(label="Length:"))
        self.pw_len = Gtk.SpinButton.new_with_range(4, 256, 1); self.pw_len.set_value(16)
        pw_len_box.append(self.pw_len)
        pw_len_box.append(Gtk.Label(label="Count:"))
        self.pw_count = Gtk.SpinButton.new_with_range(1, 50, 1); self.pw_count.set_value(5)
        pw_len_box.append(self.pw_count)
        pw_page.append(pw_len_box)

        pw_chars_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.use_upper = Gtk.CheckButton(label="Uppercase"); self.use_upper.set_active(True)
        self.use_lower = Gtk.CheckButton(label="Lowercase"); self.use_lower.set_active(True)
        self.use_digits = Gtk.CheckButton(label="Digits"); self.use_digits.set_active(True)
        self.use_special = Gtk.CheckButton(label="Special"); self.use_special.set_active(True)
        for w in [self.use_upper, self.use_lower, self.use_digits, self.use_special]:
            pw_chars_box.append(w)
        pw_page.append(pw_chars_box)

        custom_chars_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        custom_chars_box.append(Gtk.Label(label="Custom chars:"))
        self.custom_chars = Gtk.Entry(); self.custom_chars.set_placeholder_text("(optional extra chars)")
        self.custom_chars.set_hexpand(True)
        custom_chars_box.append(self.custom_chars)
        pw_page.append(custom_chars_box)

        gen_pw_btn = Gtk.Button(label="Generate Passwords")
        gen_pw_btn.set_halign(Gtk.Align.CENTER)
        gen_pw_btn.connect("clicked", self.on_gen_passwords)
        pw_page.append(gen_pw_btn)

        pw_scroll = Gtk.ScrolledWindow(); pw_scroll.set_vexpand(True)
        self.pw_view = Gtk.TextView(); self.pw_view.set_editable(False); self.pw_view.set_monospace(True)
        pw_scroll.set_child(self.pw_view)
        pw_page.append(pw_scroll)
        notebook.append_page(pw_page, Gtk.Label(label="Passwords"))

        # UUIDs page
        uid_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        uid_page.set_margin_top(12); uid_page.set_margin_start(12); uid_page.set_margin_end(12); uid_page.set_margin_bottom(12)

        uid_ctrl = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        uid_ctrl.set_halign(Gtk.Align.CENTER)
        uid_ctrl.append(Gtk.Label(label="Format:"))
        self.uid_format = Gtk.ComboBoxText()
        for f in ["UUID v4", "UUID v1", "UUID uppercase", "No hyphens", "Hex (32 chars)"]:
            self.uid_format.append_text(f)
        self.uid_format.set_active(0)
        uid_ctrl.append(self.uid_format)
        uid_ctrl.append(Gtk.Label(label="Count:"))
        self.uid_count = Gtk.SpinButton.new_with_range(1, 100, 1); self.uid_count.set_value(10)
        uid_ctrl.append(self.uid_count)
        uid_page.append(uid_ctrl)

        gen_uid_btn = Gtk.Button(label="Generate UUIDs")
        gen_uid_btn.set_halign(Gtk.Align.CENTER)
        gen_uid_btn.connect("clicked", self.on_gen_uuids)
        uid_page.append(gen_uid_btn)

        uid_scroll = Gtk.ScrolledWindow(); uid_scroll.set_vexpand(True)
        self.uid_view = Gtk.TextView(); self.uid_view.set_editable(False); self.uid_view.set_monospace(True)
        uid_scroll.set_child(self.uid_view)
        uid_page.append(uid_scroll)
        notebook.append_page(uid_page, Gtk.Label(label="UUIDs"))

        # Dice/picker page
        dice_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        dice_page.set_margin_top(12); dice_page.set_margin_start(12); dice_page.set_margin_end(12); dice_page.set_margin_bottom(12)

        dice_ctrl = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        dice_ctrl.set_halign(Gtk.Align.CENTER)
        dice_ctrl.append(Gtk.Label(label="Roll:"))
        self.dice_count_spin = Gtk.SpinButton.new_with_range(1, 100, 1); self.dice_count_spin.set_value(2)
        dice_ctrl.append(self.dice_count_spin)
        dice_ctrl.append(Gtk.Label(label="d"))
        self.dice_sides_spin = Gtk.SpinButton.new_with_range(2, 1000, 1); self.dice_sides_spin.set_value(6)
        dice_ctrl.append(self.dice_sides_spin)
        roll_btn = Gtk.Button(label="Roll Dice")
        roll_btn.connect("clicked", self.on_roll_dice)
        dice_ctrl.append(roll_btn)
        dice_page.append(dice_ctrl)

        self.dice_result = Gtk.Label(label="", css_classes=["heading"])
        self.dice_result.set_markup("<span font='24'>Roll the dice!</span>")
        dice_page.append(self.dice_result)

        coin_btn = Gtk.Button(label="Flip Coin")
        coin_btn.set_halign(Gtk.Align.CENTER)
        coin_btn.connect("clicked", self.on_flip_coin)
        dice_page.append(coin_btn)
        self.coin_label = Gtk.Label(label="")
        dice_page.append(self.coin_label)

        pick_frame = Gtk.Frame(label="Random Picker")
        pick_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        pick_vbox.set_margin_top(4); pick_vbox.set_margin_start(4); pick_vbox.set_margin_end(4); pick_vbox.set_margin_bottom(4)
        self.pick_entry = Gtk.Entry(); self.pick_entry.set_placeholder_text("Option 1, Option 2, Option 3")
        pick_vbox.append(self.pick_entry)
        pick_btn = Gtk.Button(label="Pick Random")
        pick_btn.connect("clicked", self.on_pick)
        pick_vbox.append(pick_btn)
        self.pick_result = Gtk.Label(label="", css_classes=["heading"])
        pick_vbox.append(self.pick_result)
        pick_frame.set_child(pick_vbox)
        dice_page.append(pick_frame)
        notebook.append_page(dice_page, Gtk.Label(label="Dice/Picker"))

    def on_gen_numbers(self, btn):
        mn = int(self.num_min.get_value())
        mx = int(self.num_max.get_value())
        count = int(self.num_count.get_value())
        use_float = self.float_check.get_active()
        unique = self.unique_check.get_active()
        sorted_out = self.sorted_check.get_active()
        if use_float:
            nums = [random.uniform(mn, mx) for _ in range(count)]
            nums_str = [f"{n:.4f}" for n in nums]
        else:
            if unique and count <= (mx - mn + 1):
                nums = random.sample(range(mn, mx + 1), count)
            else:
                nums = [random.randint(mn, mx) for _ in range(count)]
            nums_str = [str(n) for n in nums]
        if sorted_out:
            nums_str = sorted(nums_str, key=float)
        text = ", ".join(nums_str) if count <= 20 else "\n".join(nums_str)
        if count <= 1000:
            try:
                vals = [float(n) for n in nums_str]
                text += f"\n\nSum: {sum(vals):.4f}\nMean: {sum(vals)/len(vals):.4f}\nMin: {min(vals):.4f}\nMax: {max(vals):.4f}"
            except Exception:
                pass
        self.num_view.get_buffer().set_text(text)

    def on_gen_passwords(self, btn):
        chars = ""
        if self.use_upper.get_active(): chars += string.ascii_uppercase
        if self.use_lower.get_active(): chars += string.ascii_lowercase
        if self.use_digits.get_active(): chars += string.digits
        if self.use_special.get_active(): chars += string.punctuation
        chars += self.custom_chars.get_text()
        if not chars:
            self.pw_view.get_buffer().set_text("Select at least one character set")
            return
        length = int(self.pw_len.get_value())
        count = int(self.pw_count.get_value())
        passwords = [''.join(random.choice(chars) for _ in range(length)) for _ in range(count)]
        self.pw_view.get_buffer().set_text("\n".join(passwords))

    def on_gen_uuids(self, btn):
        fmt = self.uid_format.get_active_text()
        count = int(self.uid_count.get_value())
        uids = []
        for _ in range(count):
            if fmt == "UUID v4": u = str(uuid.uuid4())
            elif fmt == "UUID v1": u = str(uuid.uuid1())
            elif fmt == "UUID uppercase": u = str(uuid.uuid4()).upper()
            elif fmt == "No hyphens": u = str(uuid.uuid4()).replace("-", "")
            elif fmt == "Hex (32 chars)": u = uuid.uuid4().hex
            else: u = str(uuid.uuid4())
            uids.append(u)
        self.uid_view.get_buffer().set_text("\n".join(uids))

    def on_roll_dice(self, btn):
        count = int(self.dice_count_spin.get_value())
        sides = int(self.dice_sides_spin.get_value())
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls)
        rolls_str = " + ".join(map(str, rolls)) if count <= 10 else f"{count} dice"
        self.dice_result.set_markup(f"<span font='24'>🎲 {rolls_str} = <b>{total}</b></span>")

    def on_flip_coin(self, btn):
        result = random.choice(["Heads", "Tails"])
        emoji = "🪙 Heads!" if result == "Heads" else "🪙 Tails!"
        self.coin_label.set_markup(f"<span font='20'>{emoji}</span>")

    def on_pick(self, btn):
        text = self.pick_entry.get_text()
        options = [o.strip() for o in text.split(",") if o.strip()]
        if options:
            chosen = random.choice(options)
            self.pick_result.set_markup(f"<span font='18'>→ <b>{GLib.markup_escape_text(chosen)}</b></span>")

class RandomToolsApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.RandomTools")
    def do_activate(self):
        win = RandomToolsWindow(self); win.present()

def main():
    app = RandomToolsApp(); app.run(None)

if __name__ == "__main__":
    main()
