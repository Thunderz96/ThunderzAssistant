"""
Glizzy (hotdog) Module for Thunderz Assistant
Version: 1.0.0

This module rolls a 20-sided dice. Based on the roll:
- 1: Plays a hot dog contest video.
- 2-10: Throws a hotdog at your face (fun message).
- 11-19: Celebrates with confetti.
- 20: Shows a special prompt and confetti.
"""

import tkinter as tk
from tkinter import messagebox
import random
import os
from PIL import Image, ImageTk
import cv2  # OpenCV for video playback
import threading


class GlizzyModule:
    """
    Glizzy module for Thunderz Assistant.
    """
    ICON = "🌭"
    PRIORITY = 90  


    def __init__(self, parent_frame, colors):
        """
        Initialize the module.

        Args:
            parent_frame: The tkinter frame where this module will be displayed
                         (This is the content area passed from main.py).
            colors: Dictionary containing the application's color scheme
                   (This keeps your module matching the app's theme).
        """
        self.parent = parent_frame
        self.colors = colors

        # No extra data needed for this simple module
        self.data = None

        # Create the user interface
        self.create_ui()

    def create_ui(self):
        """
        Create the user interface for this module.

        This sets up the title, instructions, roll button, and results area.
        No input field needed since we just roll on button click.
        """
        # Title for the module
        title_label = tk.Label(
            self.parent,
            text="Glizzy Module 🌭",
            font=("Arial", 18, "bold"),
            bg=self.colors['content_bg'],  # Use theme color
            fg=self.colors['text']
        )
        title_label.pack(pady=20)

        # Description of what the module does
        info_label = tk.Label(
            self.parent,
            text="Click the button to roll a 20-sided dice and see what happens!",
            font=("Arial", 12),
            bg=self.colors['content_bg'],
            fg=self.colors['text']
        )
        info_label.pack(pady=10)

        # Frame for the action button (no input entry needed)
        input_frame = tk.Frame(self.parent, bg=self.colors['content_bg'])
        input_frame.pack(pady=20)

        # Action button to roll the dice
        action_button = tk.Button(
            input_frame,
            text="Roll For Glizzy",
            font=("Arial", 12),
            bg=self.colors['secondary'],
            fg="white",
            command=self.perform_action,  # Calls the roll logic when clicked
            padx=20,
            pady=5
        )
        action_button.pack(padx=5)

        # Create a label for the video display (outside results_frame so it doesn't get destroyed)
        self.video_label = tk.Label(self.parent, bg=self.colors['content_bg'])
        self.video_label.pack_forget()  # Hide it initially
        
        # Video playback state
        self.video_playing = False
        self.video_thread = None

        # Results frame where output (messages, confetti) is shown
        self.results_frame = tk.Frame(self.parent, bg=self.colors['content_bg'])
        self.results_frame.pack(pady=20, fill=tk.BOTH, expand=True)

    def roll_dice(self):
        """
        Roll a 20-sided dice and return the result.
        """
        return random.randint(1, 20)

    def perform_action(self):
        """
        This method is called when the user clicks the roll button.
    
        It rolls the dice, decides what to do based on the roll,
        and displays the result. Handles errors like file not found.
        """
        try:
            # Stop any currently playing video
            self.stop_video()
            
            # Roll the dice
            roll = self.roll_dice()
    
            # Clear any old results before showing new ones
            self.clear_results()
    
            # Handle different roll cases
            if roll == 1:
                # Play the hot dog contest video inside the app
                # Look for video in media folder
                video_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "media", "hot_dog_contest.mp4")
                
                # Check if video exists
                if not os.path.exists(video_path):
                    result = f"You rolled a {roll}. Video file not found!\n\nPlace 'hot_dog_contest.mp4' in:\n{os.path.dirname(video_path)}"
                    self.display_result(result)
                    messagebox.showinfo("Setup Required", 
                                      f"Create a 'media' folder and add 'hot_dog_contest.mp4'\n\n"
                                      f"Location: {os.path.dirname(video_path)}")
                    return
                
                result = f"You rolled a {roll}. 🎬 Playing hot dog contest video!"
                self.display_result(result)
                
                # Play video using OpenCV
                self.play_video(video_path)
                
            elif 2 <= roll <= 10:
                # Glizzy to the face message
                result = f"You rolled a {roll}. Glizzy to the face! 🌭"
                self.display_result(result)
            elif 11 <= roll <= 19:
                # Confetti celebration
                result = f"You rolled a {roll}. 🎉"
                self.display_result(result)
                self.show_confetti()
            elif roll == 20:
                # Special prompt and confetti
                messagebox.showinfo("Special Door", "Hey buddy I think you got the wrong door. 🚪")
                result = f"You rolled a {roll}. 🎊 CRITICAL SUCCESS!"
                self.display_result(result)
                self.show_confetti()
        except Exception as e:
            # Handle any errors
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def play_video(self, video_path):
        """
        Play a video using OpenCV in a separate thread.
        
        Args:
            video_path: Path to the video file
        """
        # Show the video label
        self.video_label.pack(pady=10)
        
        # Start video playback in a separate thread so it doesn't freeze the GUI
        self.video_playing = True
        self.video_thread = threading.Thread(target=self._video_loop, args=(video_path,))
        self.video_thread.daemon = True
        self.video_thread.start()
    
    def _video_loop(self, video_path):
        """
        Internal method to handle video playback loop.
        Loops the video continuously until stopped.
        
        Args:
            video_path: Path to the video file
        """
        try:
            # Open video file
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                # Only show error if widget still exists
                if self._widget_exists():
                    self.video_label.after(0, lambda: messagebox.showerror("Error", "Failed to open video file"))
                return
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            delay = int(1000 / fps) if fps > 0 else 33  # milliseconds per frame
            
            # LOOP CONTINUOUSLY until video_playing is set to False
            while self.video_playing and cap.isOpened():
                ret, frame = cap.read()
                
                if not ret:
                    # Video ended - restart from beginning!
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to first frame
                    continue  # Continue looping
                
                # Check if widget still exists before processing frame
                if not self._widget_exists():
                    break
                
                # Convert frame from BGR (OpenCV) to RGB (tkinter)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Resize to fit window (640x480)
                frame = cv2.resize(frame, (640, 480))
                
                # Convert to PIL Image then to ImageTk
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                
                # Update label with new frame (only if widget exists)
                if self._widget_exists():
                    self.video_label.after(0, lambda img=imgtk: self._update_frame(img))
                
                # Wait for next frame
                threading.Event().wait(delay / 1000.0)
            
            # Cleanup
            cap.release()
            
            # Hide video label when done (only if widget exists)
            if self._widget_exists():
                self.video_label.after(0, self.video_label.pack_forget)
            self.video_playing = False
            
        except Exception as e:
            # Only show error if widget still exists
            if self._widget_exists():
                self.video_label.after(0, lambda: messagebox.showerror("Video Error", f"Error playing video: {str(e)}"))
            self.video_playing = False
    
    def _widget_exists(self):
        """
        Check if the video label widget still exists.
        
        Returns:
            bool: True if widget exists and is valid
        """
        try:
            return self.video_label.winfo_exists()
        except:
            return False
    
    def _update_frame(self, imgtk):
        """
        Update the video label with a new frame.
        
        Args:
            imgtk: ImageTk.PhotoImage object
        """
        # Only update if widget still exists
        if self._widget_exists():
            self.video_label.imgtk = imgtk  # Keep a reference
            self.video_label.configure(image=imgtk)
    
    def stop_video(self):
        """Stop any currently playing video."""
        self.video_playing = False
        if self.video_thread and self.video_thread.is_alive():
            self.video_thread.join(timeout=1.0)
        # Only try to hide label if it still exists
        if self._widget_exists():
            self.video_label.pack_forget()
    
    def __del__(self):
        """Cleanup when module is destroyed."""
        try:
            self.stop_video()
        except:
            pass  # Ignore errors during cleanup

    def show_confetti(self):
        """
        Display a simple confetti celebration in the results area.

        This adds a label with fun emojis. We can make it fancier later!
        """
        confetti_label = tk.Label(
            self.results_frame,
            text="🎉🎉🎉 Confetti celebration! 🎉🎉🎉",
            font=("Arial", 14, "bold"),
            bg=self.colors['card_bg'],
            fg=self.colors['secondary']
        )
        confetti_label.pack(pady=10)

    def display_result(self, result):
        """
        Display the main result message to the user.

        Args:
            result: The text to display.
        """
        result_label = tk.Label(
            self.results_frame,
            text=result,
            font=("Arial", 14),
            bg=self.colors['card_bg'],
            fg=self.colors['text']
        )
        result_label.pack(pady=20)

    def clear_results(self):
        """
        Clear all widgets from the results display area.

        This keeps things clean for the next roll.
        Also stops any playing video.
        """
        # Stop video before clearing
        self.stop_video()
        
        # Clear all widgets
        for widget in self.results_frame.winfo_children():
            widget.destroy()