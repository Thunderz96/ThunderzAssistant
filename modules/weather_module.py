"""
Weather Module for Thunderz Assistant
Version: 1.2.0

This module provides weather checking functionality.
It uses the wttr.in service to fetch weather data without requiring an API key.
Now with automatic location detection and non-blocking network calls!
"""

import tkinter as tk
from tkinter import messagebox
import requests
import json
import threading


class WeatherModule:
    """
    Weather checking module.

    This class creates the UI for checking weather and handles fetching
    weather data from the wttr.in service. It can auto-detect your location!
    """

    def __init__(self, parent_frame, colors):
        self.parent = parent_frame
        self.colors = colors
        self._destroyed = False
        self.create_ui()
        self.auto_detect_and_show_weather()

    def _is_alive(self):
        """Check if our widgets still exist (haven't been destroyed by navigation)."""
        if self._destroyed:
            return False
        try:
            self.parent.winfo_exists()
            return True
        except tk.TclError:
            self._destroyed = True
            return False

    def _safe_update(self, callback):
        """Schedule a UI update on the main thread, only if widgets are alive."""
        def _wrapped():
            if not self._is_alive():
                return
            try:
                callback()
            except tk.TclError:
                self._destroyed = True
        if self._is_alive():
            try:
                self.parent.after(0, _wrapped)
            except tk.TclError:
                self._destroyed = True

    def create_ui(self):
        title_label = tk.Label(
            self.parent, text="Weather Checker",
            font=("Arial", 18, "bold"), bg="white", fg=self.colors['primary']
        )
        title_label.pack(pady=20)

        input_frame = tk.Frame(self.parent, bg="white")
        input_frame.pack(pady=10)

        tk.Label(
            input_frame, text="Enter City:",
            font=("Arial", 12), bg="white", fg=self.colors['text']
        ).grid(row=0, column=0, padx=10, pady=5)

        self.city_entry = tk.Entry(
            input_frame, font=("Arial", 12), width=25,
            relief=tk.SOLID, borderwidth=1
        )
        self.city_entry.grid(row=0, column=1, padx=10, pady=5)
        self.city_entry.bind('<Return>', lambda event: self.get_weather())

        tk.Button(
            input_frame, text="Get Weather", font=("Arial", 12, "bold"),
            bg=self.colors['secondary'], fg="white",
            activebackground=self.colors['button_hover'], activeforeground="white",
            relief=tk.FLAT, cursor="hand2", command=self.get_weather, padx=20, pady=5
        ).grid(row=0, column=2, padx=10, pady=5)

        tk.Button(
            input_frame, text="📍 My Location", font=("Arial", 12, "bold"),
            bg=self.colors['accent'], fg="white",
            activebackground=self.colors['button_hover'], activeforeground="white",
            relief=tk.FLAT, cursor="hand2", command=self.auto_detect_and_show_weather,
            padx=15, pady=5
        ).grid(row=0, column=3, padx=10, pady=5)

        self.result_frame = tk.Frame(self.parent, bg="white")
        self.result_frame.pack(pady=20, fill=tk.BOTH, expand=True)

        tk.Label(
            self.parent,
            text="Tip: Weather for your location loads automatically, or enter any city name",
            font=("Arial", 9, "italic"), bg="white", fg=self.colors['text']
        ).pack(pady=5)

    def _try_ipapi_co(self):
        location_url = "https://ipapi.co/json/"
        resp = requests.get(location_url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if data.get('error'):
            raise Exception(f"ipapi.co error: {data.get('reason', 'Unknown error')}")
        city = data.get('city', '')
        if not city:
            city = data.get('region', data.get('country_name', ''))
        return city

    def _try_ip_api_com(self):
        location_url = "http://ip-api.com/json/?fields=status,message,city,regionName,country"
        resp = requests.get(location_url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if data.get('status') == 'fail':
            raise Exception(f"ip-api.com error: {data.get('message', 'Unknown error')}")
        city = data.get('city', '')
        if not city:
            city = data.get('regionName', data.get('country', ''))
        return city

    def auto_detect_and_show_weather(self):
        """Show loading message, then detect location in a background thread."""
        self.clear_results()
        tk.Label(
            self.result_frame, text="🌍 Detecting your location...",
            font=("Arial", 12), bg="white", fg=self.colors['text']
        ).pack(pady=20)

        def _detect():
            city = ''
            error_details = []
            try:
                city = self._try_ipapi_co()
            except Exception as e:
                error_details.append(f"Primary (ipapi.co): {e}")
            if not city:
                try:
                    city = self._try_ip_api_com()
                except Exception as e:
                    error_details.append(f"Fallback (ip-api.com): {e}")

            # Schedule UI update on the main thread
            self._safe_update(lambda: self._on_location_detected(city, error_details))

        threading.Thread(target=_detect, daemon=True).start()

    def _on_location_detected(self, city, error_details):
        """Called on the main thread after location detection finishes."""
        if not self._is_alive():
            return
        if city:
            self.city_entry.delete(0, tk.END)
            self.city_entry.insert(0, city)
            self.get_weather(auto_detected=True)
        else:
            self.clear_results()
            error_msg = "Could not detect your location.\nPlease enter a city manually."
            if error_details:
                error_msg += "\n\nDetails:\n" + "\n".join(error_details)
            tk.Label(
                self.result_frame, text=error_msg,
                font=("Arial", 12), bg="white", fg="orange", justify=tk.CENTER
            ).pack(pady=20)

    def get_weather(self, auto_detected=False):
        """Show loading message, then fetch weather in a background thread."""
        city = self.city_entry.get().strip()
        if not city:
            messagebox.showwarning("Input Required", "Please enter a city name.")
            return

        self.clear_results()
        loading_text = (f"Loading weather for your location ({city})..."
                        if auto_detected else f"Loading weather for {city}...")
        tk.Label(
            self.result_frame, text=loading_text,
            font=("Arial", 12), bg="white", fg=self.colors['text']
        ).pack(pady=20)

        def _fetch():
            try:
                url = f"https://wttr.in/{city}?format=j1"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                self._safe_update(lambda: self.display_weather(data, city))
            except requests.exceptions.RequestException:
                self._safe_update(lambda: self._show_error(
                    "Error fetching weather data.\nPlease check your internet connection\nand try again."))
            except (KeyError, json.JSONDecodeError):
                self._safe_update(lambda: self._show_error(
                    "City not found or invalid response.\nPlease check the city name and try again."))

        threading.Thread(target=_fetch, daemon=True).start()

    def _show_error(self, message):
        """Display an error message in the results area."""
        if not self._is_alive():
            return
        self.clear_results()
        tk.Label(
            self.result_frame, text=message,
            font=("Arial", 12), bg="white", fg="red", justify=tk.CENTER
        ).pack(pady=20)

    def display_weather(self, data, city):
        if not self._is_alive():
            return
        self.clear_results()
        try:
            current = data['current_condition'][0]

            card_frame = tk.Frame(
                self.result_frame, bg=self.colors['accent'],
                relief=tk.RAISED, borderwidth=3
            )
            card_frame.pack(pady=20, padx=50, fill=tk.BOTH, expand=True)

            tk.Label(
                card_frame, text=f"📍 {city.title()}",
                font=("Arial", 20, "bold"), bg=self.colors['accent'], fg="white"
            ).pack(pady=15)

            tk.Label(
                card_frame, text=f"{current['temp_C']}°C / {current['temp_F']}°F",
                font=("Arial", 32, "bold"), bg=self.colors['accent'], fg="white"
            ).pack(pady=10)

            tk.Label(
                card_frame, text=current['weatherDesc'][0]['value'],
                font=("Arial", 16), bg=self.colors['accent'], fg="white"
            ).pack(pady=5)

            details_frame = tk.Frame(card_frame, bg=self.colors['accent'])
            details_frame.pack(pady=15, padx=20)

            details = [
                f"Feels like: {current['FeelsLikeC']}°C / {current['FeelsLikeF']}°F",
                f"💧 Humidity: {current['humidity']}%",
                f"💨 Wind: {current['windspeedKmph']} km/h ({current['windspeedMiles']} mph)",
                f"👁️ Visibility: {current['visibility']} km",
                f"☀️ UV Index: {current['uvIndex']}",
            ]
            for detail in details:
                tk.Label(
                    details_frame, text=detail,
                    font=("Arial", 11), bg=self.colors['accent'], fg="white"
                ).pack()

        except KeyError:
            tk.Label(
                self.result_frame,
                text="Error parsing weather data.\nSome information may be unavailable.",
                font=("Arial", 12), bg="white", fg="red"
            ).pack(pady=20)

    def clear_results(self):
        if not self._is_alive():
            return
        try:
            for widget in self.result_frame.winfo_children():
                widget.destroy()
        except tk.TclError:
            self._destroyed = True
