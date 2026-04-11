#!/usr/bin/env python3
import gi
import json
import threading
import urllib.request
import urllib.error

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib

WEATHER_ICONS = {
    "113": "☀️",   # Sunny/Clear
    "116": "⛅",   # Partly Cloudy
    "119": "☁️",   # Cloudy
    "122": "☁️",   # Overcast
    "143": "🌫️",  # Mist
    "176": "🌦️",  # Patchy rain
    "179": "🌨️",  # Patchy snow
    "182": "🌧️",  # Patchy sleet
    "185": "🌧️",  # Patchy freezing drizzle
    "200": "⛈️",  # Thundery outbreaks
    "227": "🌨️",  # Blowing snow
    "230": "❄️",   # Blizzard
    "248": "🌫️",  # Fog
    "260": "🌫️",  # Freezing fog
    "263": "🌧️",  # Patchy light drizzle
    "266": "🌧️",  # Light drizzle
    "281": "🌧️",  # Freezing drizzle
    "284": "🌧️",  # Heavy freezing drizzle
    "293": "🌦️",  # Patchy light rain
    "296": "🌧️",  # Light rain
    "299": "🌧️",  # Moderate rain at times
    "302": "🌧️",  # Moderate rain
    "305": "🌧️",  # Heavy rain at times
    "308": "🌧️",  # Heavy rain
    "311": "🌧️",  # Light freezing rain
    "314": "🌧️",  # Moderate or heavy freezing rain
    "317": "🌧️",  # Light sleet
    "320": "🌨️",  # Moderate or heavy sleet
    "323": "🌨️",  # Patchy light snow
    "326": "🌨️",  # Light snow
    "329": "❄️",   # Patchy moderate snow
    "332": "❄️",   # Moderate snow
    "335": "❄️",   # Patchy heavy snow
    "338": "❄️",   # Heavy snow
    "350": "🌨️",  # Ice pellets
    "353": "🌦️",  # Light rain shower
    "356": "🌧️",  # Moderate or heavy rain shower
    "359": "🌧️",  # Torrential rain shower
    "362": "🌨️",  # Light sleet showers
    "365": "🌨️",  # Moderate or heavy sleet showers
    "368": "🌨️",  # Light snow showers
    "371": "❄️",   # Moderate or heavy snow showers
    "374": "🌨️",  # Light showers of ice pellets
    "377": "🌨️",  # Moderate or heavy showers of ice pellets
    "386": "⛈️",  # Patchy light rain with thunder
    "389": "⛈️",  # Moderate or heavy rain with thunder
    "392": "⛈️",  # Patchy light snow with thunder
    "395": "⛈️",  # Moderate or heavy snow with thunder
}


class WeatherViewerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Weather Viewer")
        self.set_default_size(480, 560)

        css_provider = Gtk.CssProvider()
        css = b"""
        .title-label { font-size: 22px; font-weight: bold; }
        .city-result { font-size: 20px; font-weight: bold; }
        .weather-icon { font-size: 64px; }
        .weather-desc { font-size: 16px; color: #444; }
        .metric-label { font-size: 14px; color: #222; }
        .metric-value { font-size: 14px; font-weight: bold; color: #1565C0; }
        .error-label { font-size: 14px; color: #c0392b; }
        """
        css_provider.load_from_data(css)
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        outer.set_margin_top(20)
        outer.set_margin_bottom(20)
        outer.set_margin_start(30)
        outer.set_margin_end(30)
        self.set_child(outer)

        title = Gtk.Label(label="Weather Viewer")
        title.add_css_class("title-label")
        title.set_halign(Gtk.Align.CENTER)
        outer.append(title)

        # Search row
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.city_entry = Gtk.Entry()
        self.city_entry.set_placeholder_text("Enter city name (e.g. Jakarta)")
        self.city_entry.set_hexpand(True)
        self.city_entry.connect("activate", self.on_fetch_clicked)
        search_box.append(self.city_entry)

        self.fetch_btn = Gtk.Button(label="Fetch")
        self.fetch_btn.set_size_request(80, -1)
        self.fetch_btn.connect("clicked", self.on_fetch_clicked)
        search_box.append(self.fetch_btn)
        outer.append(search_box)

        outer.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # Spinner
        self.spinner = Gtk.Spinner()
        self.spinner.set_size_request(40, 40)
        self.spinner.set_halign(Gtk.Align.CENTER)
        self.spinner.set_visible(False)
        outer.append(self.spinner)

        # Error label
        self.error_label = Gtk.Label(label="")
        self.error_label.add_css_class("error-label")
        self.error_label.set_halign(Gtk.Align.CENTER)
        self.error_label.set_wrap(True)
        outer.append(self.error_label)

        # Result area
        self.result_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.result_box.set_visible(False)
        outer.append(self.result_box)

        # City name
        self.city_label = Gtk.Label(label="")
        self.city_label.add_css_class("city-result")
        self.city_label.set_halign(Gtk.Align.CENTER)
        self.result_box.append(self.city_label)

        # Weather icon
        self.icon_label = Gtk.Label(label="")
        self.icon_label.add_css_class("weather-icon")
        self.icon_label.set_halign(Gtk.Align.CENTER)
        self.result_box.append(self.icon_label)

        # Description
        self.desc_label = Gtk.Label(label="")
        self.desc_label.add_css_class("weather-desc")
        self.desc_label.set_halign(Gtk.Align.CENTER)
        self.result_box.append(self.desc_label)

        self.result_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # Metrics grid
        metrics_grid = Gtk.Grid()
        metrics_grid.set_row_spacing(8)
        metrics_grid.set_column_spacing(20)
        metrics_grid.set_margin_top(6)
        metrics_grid.set_halign(Gtk.Align.CENTER)
        self.result_box.append(metrics_grid)

        self.metric_widgets = {}
        metrics = [
            ("temp_c", "Temperature (C)"),
            ("temp_f", "Temperature (F)"),
            ("feels_like_c", "Feels Like (C)"),
            ("humidity", "Humidity"),
            ("wind_speed", "Wind Speed"),
        ]
        for row, (key, display_name) in enumerate(metrics):
            lbl = Gtk.Label(label=display_name + ":")
            lbl.add_css_class("metric-label")
            lbl.set_halign(Gtk.Align.END)
            metrics_grid.attach(lbl, 0, row, 1, 1)

            val = Gtk.Label(label="—")
            val.add_css_class("metric-value")
            val.set_halign(Gtk.Align.START)
            metrics_grid.attach(val, 1, row, 1, 1)
            self.metric_widgets[key] = val

    def on_fetch_clicked(self, _widget):
        city = self.city_entry.get_text().strip()
        if not city:
            self.error_label.set_label("Please enter a city name.")
            return

        self.error_label.set_label("")
        self.result_box.set_visible(False)
        self.spinner.set_visible(True)
        self.spinner.start()
        self.fetch_btn.set_sensitive(False)

        thread = threading.Thread(target=self._fetch_weather, args=(city,), daemon=True)
        thread.start()

    def _fetch_weather(self, city):
        url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1"
        try:
            import urllib.parse
            url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1"
            req = urllib.request.Request(url, headers={"User-Agent": "WeatherViewer/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            GLib.idle_add(self._on_weather_received, data, city)
        except urllib.error.URLError as e:
            GLib.idle_add(self._on_fetch_error, f"Network error: {e.reason}")
        except json.JSONDecodeError:
            GLib.idle_add(self._on_fetch_error, "City not found or invalid response.")
        except Exception as e:
            GLib.idle_add(self._on_fetch_error, f"Error: {str(e)}")

    def _on_weather_received(self, data, city):
        self.spinner.stop()
        self.spinner.set_visible(False)
        self.fetch_btn.set_sensitive(True)

        try:
            current = data["current_condition"][0]
            nearest = data.get("nearest_area", [{}])[0]
            area_name = nearest.get("areaName", [{}])[0].get("value", city)
            country = nearest.get("country", [{}])[0].get("value", "")
            display_city = f"{area_name}, {country}" if country else area_name

            temp_c = current.get("temp_C", "—")
            temp_f = current.get("temp_F", "—")
            feels_c = current.get("FeelsLikeC", "—")
            humidity = current.get("humidity", "—")
            wind_kmph = current.get("windspeedKmph", "—")
            desc = current.get("weatherDesc", [{}])[0].get("value", "Unknown")
            weather_code = current.get("weatherCode", "113")
            icon = WEATHER_ICONS.get(str(weather_code), "🌡️")

            self.city_label.set_label(display_city)
            self.icon_label.set_label(icon)
            self.desc_label.set_label(desc)
            self.metric_widgets["temp_c"].set_label(f"{temp_c}°C")
            self.metric_widgets["temp_f"].set_label(f"{temp_f}°F")
            self.metric_widgets["feels_like_c"].set_label(f"{feels_c}°C")
            self.metric_widgets["humidity"].set_label(f"{humidity}%")
            self.metric_widgets["wind_speed"].set_label(f"{wind_kmph} km/h")

            self.result_box.set_visible(True)
            self.error_label.set_label("")
        except (KeyError, IndexError, TypeError) as e:
            self._on_fetch_error(f"Failed to parse weather data: {e}")

        return False

    def _on_fetch_error(self, message):
        self.spinner.stop()
        self.spinner.set_visible(False)
        self.fetch_btn.set_sensitive(True)
        self.error_label.set_label(message)
        self.result_box.set_visible(False)
        return False


def on_activate(app):
    win = WeatherViewerWindow(app)
    win.present()


if __name__ == "__main__":
    import urllib.parse
    app = Gtk.Application(application_id="com.pens.WeatherViewer")
    app.connect("activate", on_activate)
    app.run(None)
