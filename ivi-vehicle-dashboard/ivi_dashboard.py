#!/usr/bin/env python3
"""IVI Vehicle Dashboard -- com.pens.IVIVehicleDashboard
A simulated automotive instrument cluster for AGL IVI systems.
Shows speed, RPM, fuel level and coolant temperature gauges.
"""
import gi, math, random
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import cairo

state = {'speed': 0.0, 'rpm': 800.0, 'fuel': 0.72, 'coolant': 82.0,
         'tgt_speed': 0.0, 'tgt_rpm': 800.0}

def tick_state():
    if random.random() < 0.025:
        state['tgt_speed'] = random.uniform(0, 185)
        state['tgt_rpm']   = 800 + state['tgt_speed'] / 185 * 6800 + random.uniform(-300, 300)
    for k, t in [('speed','tgt_speed'),('rpm','tgt_rpm')]:
        state[k] += (state[t] - state[k]) * 0.06
    state['coolant'] = 78 + 14*(state['speed']/185) + random.uniform(-0.3,0.3)
    state['fuel']    = max(0.05, state['fuel'] - 0.00002)

def draw_gauge(cr, cx, cy, r, val, vmin, vmax, title, unit, rgb,
               a0=210, sweep=300):
    cr.arc(cx, cy, r, 0, 2*math.pi)
    cr.set_source_rgb(0.07, 0.07, 0.09); cr.fill()
    cr.arc(cx, cy, r, 0, 2*math.pi)
    cr.set_source_rgb(0.18, 0.18, 0.22); cr.set_line_width(2.5); cr.stroke()

    for i in range(11):
        ang = math.radians(a0 + sweep*i/10)
        major = (i % 2 == 0)
        r1 = r*(0.73 if major else 0.82); r2 = r*0.91
        cr.move_to(cx+r1*math.cos(ang), cy+r1*math.sin(ang))
        cr.line_to(cx+r2*math.cos(ang), cy+r2*math.sin(ang))
        cr.set_source_rgb(0.45, 0.45, 0.5)
        cr.set_line_width(2.0 if major else 1.0); cr.stroke()

    frac = max(0.0, min(1.0, (val-vmin)/(vmax-vmin)))
    end  = math.radians(a0 + sweep*frac)
    cr.arc(cx, cy, r*0.84, math.radians(a0), end)
    cr.set_source_rgb(*rgb); cr.set_line_width(5); cr.stroke()

    nang = end
    cr.move_to(cx, cy)
    cr.line_to(cx + r*0.70*math.cos(nang), cy + r*0.70*math.sin(nang))
    cr.set_source_rgb(1, 0.28, 0.08); cr.set_line_width(2.8); cr.stroke()
    cr.arc(cx, cy, 7, 0, 2*math.pi)
    cr.set_source_rgb(0.85, 0.85, 0.85); cr.fill()

    cr.select_font_face("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_source_rgb(0.95, 0.95, 0.95); cr.set_font_size(r*0.27)
    txt = f"{val:.0f}"
    te = cr.text_extents(txt)
    cr.move_to(cx - te.width/2, cy + r*0.34); cr.show_text(txt)
    cr.set_font_size(r*0.13); cr.set_source_rgb(0.55,0.55,0.6)
    te = cr.text_extents(unit)
    cr.move_to(cx - te.width/2, cy + r*0.5); cr.show_text(unit)
    te = cr.text_extents(title)
    cr.move_to(cx - te.width/2, cy - r*0.62); cr.show_text(title)

def draw_bar(cr, x, y, w, h, val, lo, hi, lbl, rgb):
    cr.rectangle(x, y, w, h)
    cr.set_source_rgb(0.12,0.12,0.14); cr.fill()
    cr.rectangle(x, y, w, h)
    cr.set_source_rgb(0.22,0.22,0.27); cr.set_line_width(1); cr.stroke()
    f = max(0.0, min(1.0, (val-lo)/(hi-lo)))
    cr.rectangle(x+2, y+2, (w-4)*f, h-4)
    cr.set_source_rgb(*rgb); cr.fill()
    cr.select_font_face("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cr.set_source_rgb(0.9, 0.9, 0.9); cr.set_font_size(11)
    cr.move_to(x+7, y+h/2+4.5); cr.show_text(f"{lbl}: {val:.1f}")

class VehicleDashboard(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='com.pens.IVIVehicleDashboard')

    def do_activate(self):
        win = Gtk.ApplicationWindow(application=self, title='AGL IVI — Vehicle Dashboard')
        win.set_default_size(780, 460)
        css = Gtk.CssProvider()
        css.load_from_data(b'window { background-color: #0b0b0e; }')
        win.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        da = Gtk.DrawingArea()
        da.set_draw_func(self._draw)
        win.set_child(da)
        win.present()
        GLib.timeout_add(50, self._tick, da)

    def _tick(self, da):
        tick_state(); da.queue_draw(); return True

    def _draw(self, da, cr, w, h):
        cr.set_source_rgb(0.04,0.04,0.06); cr.paint()
        r = min(w*0.34, h*0.42)
        draw_gauge(cr, w*0.28, h*0.5,  r, state['speed'], 0, 200, 'SPEED', 'km/h', (0.15,0.75,1.0))
        draw_gauge(cr, w*0.72, h*0.5,  r, state['rpm'],   0, 8000, 'RPM',  'rpm',  (1.0,0.55,0.05))
        bw, bh = w*0.32, 30
        draw_bar(cr, w*0.34, h-52, bw, bh, state['fuel']*100,  0,  100, 'FUEL %',  (0.15,0.85,0.35))
        draw_bar(cr, w*0.34+bw+12, h-52, bw, bh, state['coolant'], 50, 130, 'TEMP °C', (1.0,0.38,0.18))
        cr.select_font_face("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_source_rgb(0.35,0.75,1.0); cr.set_font_size(13)
        cr.move_to(w/2-120, 26); cr.show_text('AGL IVI  ·  PensHub Vehicle Dashboard')

if __name__ == '__main__':
    VehicleDashboard().run()
