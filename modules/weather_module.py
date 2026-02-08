"""
Weather Module for Thunderz Assistant
Version: 1.0.0

This module provides weather checking functionality.
It uses the wttr.in service to fetch weather data without requiring an API key.
"""

import tkinter as tk
from tkinter import messagebox
import requests
import json


class WeatherModule:
    """
    Weather checking module.
    
    This class creates the UI for checking weather and handles fetching
    weather data from the wttr.in service.
    """
    
    def __init__(self, parent_frame, colors):
        """
        Initialize the weather module.
        
        Args:
            parent_frame: The tkinter frame where this module will be displayed
            colors: Dictionary containing the application's color scheme
        """
        self.parent = parent_frame
        self.colors = colors
        
        # Create the UI
        self.create_ui()
        
    def create_ui(self):
        """
        Create the user interface for the weather module.
        
        This sets up input fields, buttons, and display areas for weather information.
        """
        # Title
        title_label = tk.Label(
            self.parent,
            text="Weather Checker",
            font=("Arial", 18, "bold"),
            bg="white",
            fg=self.colors['primary']
        )
        title_label.pack(pady=20)
        
        # Input frame
        input_frame = tk.Frame(self.parent, bg="white")
        input_frame.pack(pady=10)
        
        # City label and entry
        city_label = tk.Label(
            input_frame,
            text="Enter City:",
            font=("Arial", 12),
            bg="white",
            fg=self.colors['text']
        )
        city_label.grid(row=0, column=0, padx=10, pady=5)
        
        self.city_entry = tk.Entry(
            input_frame,
            font=("Arial", 12),
            width=25,
            relief=tk.SOLID,
            borderwidth=1
        )
        self.city_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # Bind Enter key to search
        self.city_entry.bind('<Return>', lambda event: self.get_weather())
        
        # Search button
        search_btn = tk.Button(
            input_frame,
            text="Get Weather",
            font=("Arial", 12, "bold"),
            bg=self.colors['secondary'],
            fg="white",
            activebackground=self.colors['button_hover'],
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.get_weather,
            padx=20,
            pady=5
        )
        search_btn.grid(row=0, column=2, padx=10, pady=5)
        
        # Result frame (hidden initially)
        self.result_frame = tk.Frame(self.parent, bg="white")
        self.result_frame.pack(pady=20, fill=tk.BOTH, expand=True)
        
        # Info label
        info_label = tk.Label(
            self.parent,
            text="Tip: You can also press Enter to search",
            font=("Arial", 9, "italic"),
            bg="white",
            fg=self.colors['text']
        )
        info_label.pack(pady=5)
        
    def get_weather(self):
        """
        Fetch and display weather data for the entered city.
        
        This method:
        1. Gets the city name from the input field
        2. Makes an API request to wttr.in
        3. Parses the JSON response
        4. Displays the weather information
        """
        city = self.city_entry.get().strip()
        
        # Validate input
        if not city:
            messagebox.showwarning("Input Required", "Please enter a city name.")
            return
        
        try:
            # Show loading message
            self.clear_results()
            loading_label = tk.Label(
                self.result_frame,
                text="Loading weather data...",
                font=("Arial", 12),
                bg="white",
                fg=self.colors['text']
            )
            loading_label.pack(pady=20)
            self.parent.update()
            
            # Fetch weather data from wttr.in (free, no API key needed)
            # Using format parameter to get JSON response
            url = f"https://wttr.in/{city}?format=j1"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Raise exception for bad status codes
            
            data = response.json()
            
            # Display the weather
            self.display_weather(data, city)
            
        except requests.exceptions.RequestException as e:
            # Handle network errors
            self.clear_results()
            error_label = tk.Label(
                self.result_frame,
                text=f"Error fetching weather data.\nPlease check your internet connection\nand try again.",
                font=("Arial", 12),
                bg="white",
                fg="red",
                justify=tk.CENTER
            )
            error_label.pack(pady=20)
            
        except (KeyError, json.JSONDecodeError) as e:
            # Handle parsing errors
            self.clear_results()
            error_label = tk.Label(
                self.result_frame,
                text=f"City not found or invalid response.\nPlease check the city name and try again.",
                font=("Arial", 12),
                bg="white",
                fg="red",
                justify=tk.CENTER
            )
            error_label.pack(pady=20)
    
    def display_weather(self, data, city):
        """
        Display the weather information in a formatted way.
        
        Args:
            data: Dictionary containing weather data from the API
            city: Name of the city (for display purposes)
        """
        self.clear_results()
        
        try:
            # Extract current conditions
            current = data['current_condition'][0]
            
            # Create a card-style display
            card_frame = tk.Frame(
                self.result_frame,
                bg=self.colors['accent'],
                relief=tk.RAISED,
                borderwidth=3
            )
            card_frame.pack(pady=20, padx=50, fill=tk.BOTH, expand=True)
            
            # City name header
            city_label = tk.Label(
                card_frame,
                text=f"📍 {city.title()}",
                font=("Arial", 20, "bold"),
                bg=self.colors['accent'],
                fg="white"
            )
            city_label.pack(pady=15)
            
            # Temperature (large display)
            temp_label = tk.Label(
                card_frame,
                text=f"{current['temp_C']}°C / {current['temp_F']}°F",
                font=("Arial", 32, "bold"),
                bg=self.colors['accent'],
                fg="white"
            )
            temp_label.pack(pady=10)
            
            # Weather description
            desc_label = tk.Label(
                card_frame,
                text=current['weatherDesc'][0]['value'],
                font=("Arial", 16),
                bg=self.colors['accent'],
                fg="white"
            )
            desc_label.pack(pady=5)
            
            # Details frame
            details_frame = tk.Frame(card_frame, bg=self.colors['accent'])
            details_frame.pack(pady=15, padx=20)
            
            # Feels like temperature
            feels_label = tk.Label(
                details_frame,
                text=f"Feels like: {current['FeelsLikeC']}°C / {current['FeelsLikeF']}°F",
                font=("Arial", 11),
                bg=self.colors['accent'],
                fg="white"
            )
            feels_label.pack()
            
            # Humidity
            humidity_label = tk.Label(
                details_frame,
                text=f"💧 Humidity: {current['humidity']}%",
                font=("Arial", 11),
                bg=self.colors['accent'],
                fg="white"
            )
            humidity_label.pack()
            
            # Wind speed
            wind_label = tk.Label(
                details_frame,
                text=f"💨 Wind: {current['windspeedKmph']} km/h ({current['windspeedMiles']} mph)",
                font=("Arial", 11),
                bg=self.colors['accent'],
                fg="white"
            )
            wind_label.pack()
            
            # Visibility
            visibility_label = tk.Label(
                details_frame,
                text=f"👁️ Visibility: {current['visibility']} km",
                font=("Arial", 11),
                bg=self.colors['accent'],
                fg="white"
            )
            visibility_label.pack()
            
            # UV Index
            uv_label = tk.Label(
                details_frame,
                text=f"☀️ UV Index: {current['uvIndex']}",
                font=("Arial", 11),
                bg=self.colors['accent'],
                fg="white"
            )
            uv_label.pack()
            
        except KeyError as e:
            # Handle missing data fields
            error_label = tk.Label(
                self.result_frame,
                text=f"Error parsing weather data.\nSome information may be unavailable.",
                font=("Arial", 12),
                bg="white",
                fg="red"
            )
            error_label.pack(pady=20)
    
    def clear_results(self):
        """
        Clear all widgets from the results display area.
        
        This is called before displaying new weather data or error messages.
        """
        for widget in self.result_frame.winfo_children():
            widget.destroy()
