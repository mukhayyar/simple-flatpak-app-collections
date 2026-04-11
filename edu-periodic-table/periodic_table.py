#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

ELEMENTS = [
    (1,"H","Hydrogen",1.008,"nonmetal",1,1),
    (2,"He","Helium",4.003,"noble gas",1,18),
    (3,"Li","Lithium",6.941,"alkali metal",2,1),
    (4,"Be","Beryllium",9.012,"alkaline earth",2,2),
    (5,"B","Boron",10.81,"metalloid",2,13),
    (6,"C","Carbon",12.01,"nonmetal",2,14),
    (7,"N","Nitrogen",14.01,"nonmetal",2,15),
    (8,"O","Oxygen",16.00,"nonmetal",2,16),
    (9,"F","Fluorine",19.00,"halogen",2,17),
    (10,"Ne","Neon",20.18,"noble gas",2,18),
    (11,"Na","Sodium",22.99,"alkali metal",3,1),
    (12,"Mg","Magnesium",24.31,"alkaline earth",3,2),
    (13,"Al","Aluminum",26.98,"post-transition",3,13),
    (14,"Si","Silicon",28.09,"metalloid",3,14),
    (15,"P","Phosphorus",30.97,"nonmetal",3,15),
    (16,"S","Sulfur",32.07,"nonmetal",3,16),
    (17,"Cl","Chlorine",35.45,"halogen",3,17),
    (18,"Ar","Argon",39.95,"noble gas",3,18),
    (19,"K","Potassium",39.10,"alkali metal",4,1),
    (20,"Ca","Calcium",40.08,"alkaline earth",4,2),
    (21,"Sc","Scandium",44.96,"transition",4,3),
    (22,"Ti","Titanium",47.87,"transition",4,4),
    (23,"V","Vanadium",50.94,"transition",4,5),
    (24,"Cr","Chromium",52.00,"transition",4,6),
    (25,"Mn","Manganese",54.94,"transition",4,7),
    (26,"Fe","Iron",55.85,"transition",4,8),
    (27,"Co","Cobalt",58.93,"transition",4,9),
    (28,"Ni","Nickel",58.69,"transition",4,10),
    (29,"Cu","Copper",63.55,"transition",4,11),
    (30,"Zn","Zinc",65.38,"transition",4,12),
    (31,"Ga","Gallium",69.72,"post-transition",4,13),
    (32,"Ge","Germanium",72.63,"metalloid",4,14),
    (33,"As","Arsenic",74.92,"metalloid",4,15),
    (34,"Se","Selenium",78.97,"nonmetal",4,16),
    (35,"Br","Bromine",79.90,"halogen",4,17),
    (36,"Kr","Krypton",83.80,"noble gas",4,18),
    (37,"Rb","Rubidium",85.47,"alkali metal",5,1),
    (38,"Sr","Strontium",87.62,"alkaline earth",5,2),
    (39,"Y","Yttrium",88.91,"transition",5,3),
    (40,"Zr","Zirconium",91.22,"transition",5,4),
    (41,"Nb","Niobium",92.91,"transition",5,5),
    (42,"Mo","Molybdenum",95.96,"transition",5,6),
    (43,"Tc","Technetium",98.0,"transition",5,7),
    (44,"Ru","Ruthenium",101.1,"transition",5,8),
    (45,"Rh","Rhodium",102.9,"transition",5,9),
    (46,"Pd","Palladium",106.4,"transition",5,10),
    (47,"Ag","Silver",107.9,"transition",5,11),
    (48,"Cd","Cadmium",112.4,"transition",5,12),
    (49,"In","Indium",114.8,"post-transition",5,13),
    (50,"Sn","Tin",118.7,"post-transition",5,14),
    (51,"Sb","Antimony",121.8,"metalloid",5,15),
    (52,"Te","Tellurium",127.6,"metalloid",5,16),
    (53,"I","Iodine",126.9,"halogen",5,17),
    (54,"Xe","Xenon",131.3,"noble gas",5,18),
    (55,"Cs","Cesium",132.9,"alkali metal",6,1),
    (56,"Ba","Barium",137.3,"alkaline earth",6,2),
    (57,"La","Lanthanum",138.9,"lanthanide",8,3),
    (72,"Hf","Hafnium",178.5,"transition",6,4),
    (73,"Ta","Tantalum",180.9,"transition",6,5),
    (74,"W","Tungsten",183.8,"transition",6,6),
    (75,"Re","Rhenium",186.2,"transition",6,7),
    (76,"Os","Osmium",190.2,"transition",6,8),
    (77,"Ir","Iridium",192.2,"transition",6,9),
    (78,"Pt","Platinum",195.1,"transition",6,10),
    (79,"Au","Gold",197.0,"transition",6,11),
    (80,"Hg","Mercury",200.6,"transition",6,12),
    (81,"Tl","Thallium",204.4,"post-transition",6,13),
    (82,"Pb","Lead",207.2,"post-transition",6,14),
    (83,"Bi","Bismuth",208.9,"post-transition",6,15),
    (84,"Po","Polonium",209.0,"metalloid",6,16),
    (85,"At","Astatine",210.0,"halogen",6,17),
    (86,"Rn","Radon",222.0,"noble gas",6,18),
    (87,"Fr","Francium",223.0,"alkali metal",7,1),
    (88,"Ra","Radium",226.0,"alkaline earth",7,2),
    (89,"Ac","Actinium",227.0,"actinide",9,3),
    (104,"Rf","Rutherfordium",267.0,"transition",7,4),
    (105,"Db","Dubnium",270.0,"transition",7,5),
    (106,"Sg","Seaborgium",271.0,"transition",7,6),
    (107,"Bh","Bohrium",270.0,"transition",7,7),
    (108,"Hs","Hassium",277.0,"transition",7,8),
    (109,"Mt","Meitnerium",278.0,"transition",7,9),
    (110,"Ds","Darmstadtium",281.0,"transition",7,10),
    (111,"Rg","Roentgenium",282.0,"transition",7,11),
    (112,"Cn","Copernicium",285.0,"transition",7,12),
    (113,"Nh","Nihonium",286.0,"post-transition",7,13),
    (114,"Fl","Flerovium",289.0,"post-transition",7,14),
    (115,"Mc","Moscovium",290.0,"post-transition",7,15),
    (116,"Lv","Livermorium",293.0,"post-transition",7,16),
    (117,"Ts","Tennessine",294.0,"halogen",7,17),
    (118,"Og","Oganesson",294.0,"noble gas",7,18),
]

CATEGORY_COLORS = {
    "alkali metal": "#ff6b6b",
    "alkaline earth": "#ffa07a",
    "transition": "#87ceeb",
    "post-transition": "#98fb98",
    "metalloid": "#dda0dd",
    "nonmetal": "#f0e68c",
    "halogen": "#90ee90",
    "noble gas": "#add8e6",
    "lanthanide": "#ffb6c1",
    "actinide": "#ffd700",
}

class PeriodicTableWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Periodic Table")
        self.set_default_size(1200, 680)
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(vbox)

        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        search_box.set_margin_top(6); search_box.set_margin_start(8); search_box.set_margin_end(8)
        search_box.set_margin_bottom(4)
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search element name or symbol...")
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("search-changed", self.on_search)
        search_box.append(self.search_entry)
        vbox.append(search_box)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        grid = Gtk.Grid()
        grid.set_row_spacing(2)
        grid.set_column_spacing(2)
        grid.set_margin_top(4); grid.set_margin_start(8); grid.set_margin_end(8)

        self.buttons = {}
        for elem in ELEMENTS:
            num, sym, name, mass, cat, row, col = elem
            btn = Gtk.Button()
            btn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            num_lbl = Gtk.Label(label=str(num))
            num_lbl.set_css_classes(["caption"])
            sym_lbl = Gtk.Label(label=sym)
            sym_lbl.set_markup(f"<b>{sym}</b>")
            btn_box.append(num_lbl)
            btn_box.append(sym_lbl)
            btn.set_child(btn_box)
            btn.set_size_request(52, 42)
            color = CATEGORY_COLORS.get(cat, "#cccccc")
            css = Gtk.CssProvider()
            css.load_from_data(f"button {{ background: {color}; color: #111; font-size: 9px; }}".encode())
            btn.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            btn.connect("clicked", self.on_element_clicked, elem)
            grid.attach(btn, col - 1, row - 1, 1, 1)
            self.buttons[num] = (btn, elem)

        scroll.set_child(grid)
        vbox.append(scroll)

        self.info_label = Gtk.Label(label="Click an element to see details")
        self.info_label.set_margin_top(6); self.info_label.set_margin_bottom(6)
        self.info_label.set_wrap(True)
        vbox.append(self.info_label)

        legend = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        legend.set_margin_start(8); legend.set_margin_bottom(4)
        for cat, color in list(CATEGORY_COLORS.items())[:6]:
            swatch = Gtk.Label(label=f" {cat} ")
            css = Gtk.CssProvider()
            css.load_from_data(f"label {{ background: {color}; color: #111; border-radius: 4px; font-size: 9px; }}".encode())
            swatch.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            legend.append(swatch)
        vbox.append(legend)

    def on_element_clicked(self, btn, elem):
        num, sym, name, mass, cat, row, col = elem
        self.info_label.set_text(
            f"Element {num}: {name} ({sym})  |  Atomic Mass: {mass}  |  Category: {cat}  |  Period: {row}  |  Group: {col}"
        )

    def on_search(self, entry):
        q = entry.get_text().lower()
        for num, (btn, elem) in self.buttons.items():
            _, sym, name, *_ = elem
            visible = not q or q in name.lower() or q in sym.lower()
            btn.set_opacity(1.0 if visible else 0.2)

class PeriodicTableApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.PeriodicTable")
    def do_activate(self):
        win = PeriodicTableWindow(self); win.present()

def main():
    app = PeriodicTableApp(); app.run(None)

if __name__ == "__main__":
    main()
