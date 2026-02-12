"""
News Module for Thunderz Assistant
Version: 1.3.0  # Updated for Tkinter integration

This module provides Breaking News checking functionality.
It uses NewsAPI.org to fetch real breaking news data and processes it to provide relevant information to the user.
Now integrated with Tkinter for displaying in a GUI.
Author: OpenAI (updated by SuperGrok suggestions)

"""

import tkinter as tk
import requests
import logging

class NewsModule:
    """
    A class to fetch and process breaking news from a real API, and display it in a Tkinter frame.
    """
    ICON = "📰"
    PRIORITY = 6
    
    def __init__(self, api_key, content_frame, colors):
        """
        Initialize the NewsModule with API key, Tkinter frame, and colors.
        
        Args:
            api_key (str): Your free API key from NewsAPI.org.
            content_frame (tk.Frame): The Tkinter frame where news will be displayed.
            colors (dict): A dictionary of colors, e.g., {'bg': 'white', 'fg': 'black'}.
        """
        try:
            # Set up the real NewsAPI.org endpoint for top headlines (e.g., US news)
            # You can change 'country=us' to other countries like 'gb' for UK.
            self.api_url = "https://newsapi.org/v2/top-headlines?country=us&apiKey=" + api_key
            self.content_frame = content_frame  # Store the frame for displaying news
            self.colors = colors  # Store colors for customizing the display
            self.logger = logging.getLogger(__name__)
        except Exception as e:
            logging.error(f"Error initializing NewsModule: {e}")
            self.api_url = None

    def fetch_breaking_news(self):
        """
        Fetch raw news data from the API.
        
        Returns:
            list: A list of news articles (or empty if there's an error).
        """
        try:
            response = requests.get(self.api_url)
            response.raise_for_status()  # Raises an error if the request fails
            news_data = response.json().get("articles", [])  # Get the 'articles' list from JSON
            return news_data[:5]  # Return the top 5 news items
        except requests.RequestException as e:
            self.logger.error(f"Error fetching breaking news: {e}")
            return []

    def process_news_data(self, news_data):
        """
        Process the raw news data into a simple format.
        
        Args:
            news_data (list): Raw articles from the API.
        
        Returns:
            list: Processed news items with title and description.
        """
        processed_news = []
        for item in news_data:
            processed_news.append({
                "title": item.get("title"),  # NewsAPI uses 'title'
                "body": item.get("description")  # Use 'description' instead of 'body' (it's like a summary)
            })
        return processed_news

    def get_breaking_news(self):
        """
        Get formatted breaking news as a string.
        
        Returns:
            str: A summary of the news or an error message.
        """
        news_data = self.fetch_breaking_news()
        if not news_data:
            return "Unable to fetch breaking news at the moment."
        
        processed_news = self.process_news_data(news_data)
        news_summary = "\n".join([f"{news['title']}: {news['body']}" for news in processed_news])
        return f"Here are the latest breaking news:\n{news_summary}"

    def display_news(self):
        """
        Display the breaking news in the stored Tkinter content_frame.
        This creates a nicely formatted display with proper styling.
        """
        # Clear any existing content in the frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Title
        title_label = tk.Label(
            self.content_frame,
            text="📰 Breaking News",
            font=("Arial", 18, "bold"),
            bg=self.colors.get('content_bg', '#1E293B'),
            fg=self.colors.get('primary', '#1E3A8A')
        )
        title_label.pack(pady=20)
        
        # Loading message
        loading_label = tk.Label(
            self.content_frame,
            text="Loading latest headlines...",
            font=("Arial", 12),
            bg=self.colors.get('content_bg', '#1E293B'),
            fg=self.colors.get('text', '#1E293B')
        )
        loading_label.pack(pady=10)
        self.content_frame.update()
        
        # Fetch news
        news_data = self.fetch_breaking_news()
        
        # Remove loading message
        loading_label.destroy()
        
        if not news_data:
            error_label = tk.Label(
                self.content_frame,
                text="Unable to fetch breaking news at the moment.\nPlease check your internet connection and try again.",
                font=("Arial", 12),
                bg=self.colors.get('content_bg', '#1E293B'),
                fg="red",
                justify=tk.CENTER
            )
            error_label.pack(pady=20)
            return
        
        # Create scrollable frame for news
        canvas = tk.Canvas(self.content_frame, bg=self.colors.get('content_bg', '#1E293B'), highlightthickness=0)
        scrollbar = tk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors.get('content_bg', '#1E293B'))
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Display each news article
        for i, article in enumerate(news_data, 1):
            # Article frame (card style)
            article_frame = tk.Frame(
                scrollable_frame,
                bg=self.colors.get('accent', '#60A5FA'),
                relief=tk.RAISED,
                borderwidth=2
            )
            article_frame.pack(fill=tk.X, padx=20, pady=10)
            
            # Article number
            number_label = tk.Label(
                article_frame,
                text=f"#{i}",
                font=("Arial", 14, "bold"),
                bg=self.colors.get('accent', '#60A5FA'),
                fg="white"
            )
            number_label.pack(anchor="w", padx=10, pady=(10, 5))
            
            # Article title
            title = article.get("title", "No title")
            title_label = tk.Label(
                article_frame,
                text=title,
                font=("Arial", 13, "bold"),
                bg=self.colors.get('accent', '#60A5FA'),
                fg="white",
                wraplength=520,
                justify=tk.LEFT
            )
            title_label.pack(anchor="w", padx=10, pady=5)
            
            # Article description
            description = article.get("description", "No description available.")
            if description:
                desc_label = tk.Label(
                    article_frame,
                    text=description,
                    font=("Arial", 11),
                    bg=self.colors.get('accent', '#60A5FA'),
                    fg="white",
                    wraplength=520,
                    justify=tk.LEFT
                )
                desc_label.pack(anchor="w", padx=10, pady=(0, 10))
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

