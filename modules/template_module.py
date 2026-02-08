"""
Template Module for Thunderz Assistant
Version: 1.0.0

This is a template file showing how to create a new module for the application.
Copy this file and modify it to create your own features!

STEPS TO CREATE A NEW MODULE:
1. Copy this file and rename it (e.g., calculator_module.py)
2. Rename the class (e.g., CalculatorModule)
3. Modify the create_ui() method to design your interface
4. Add your functionality methods
5. Import your module in main.py
6. Add a button in the sidebar to access your module
"""

import tkinter as tk
from tkinter import messagebox


class TemplateModule:
    """
    Template module for Thunderz Assistant.
    
    This class demonstrates the basic structure needed for any module.
    All modules should follow this pattern for consistency.
    """
    
    def __init__(self, parent_frame, colors):
        """
        Initialize the module.
        
        Args:
            parent_frame: The tkinter frame where this module will be displayed
                         (This is the content area passed from main.py)
            colors: Dictionary containing the application's color scheme
                   (This keeps your module matching the app's theme)
        """
        self.parent = parent_frame
        self.colors = colors
        
        # Store any data or state your module needs here
        self.data = None
        
        # Create the user interface
        self.create_ui()
        
    def create_ui(self):
        """
        Create the user interface for this module.
        
        This method sets up all the visual elements (labels, buttons, entry fields, etc.)
        that the user will interact with.
        
        TIP: Break this into smaller methods if your UI becomes complex!
        """
        # Title for your module
        title_label = tk.Label(
            self.parent,
            text="Your Module Name Here",
            font=("Arial", 18, "bold"),
            bg="white",
            fg=self.colors['primary']
        )
        title_label.pack(pady=20)
        
        # Description or instructions
        info_label = tk.Label(
            self.parent,
            text="Describe what your module does here",
            font=("Arial", 12),
            bg="white",
            fg=self.colors['text']
        )
        info_label.pack(pady=10)
        
        # Input frame (if you need user input)
        input_frame = tk.Frame(self.parent, bg="white")
        input_frame.pack(pady=20)
        
        # Example: Text entry field
        self.input_entry = tk.Entry(
            input_frame,
            font=("Arial", 12),
            width=30
        )
        self.input_entry.pack(side=tk.LEFT, padx=5)
        
        # Example: Action button
        action_button = tk.Button(
            input_frame,
            text="Do Something",
            font=("Arial", 12),
            bg=self.colors['secondary'],
            fg="white",
            command=self.perform_action,  # This calls your method when clicked
            padx=20,
            pady=5
        )
        action_button.pack(side=tk.LEFT, padx=5)
        
        # Results frame (where output is displayed)
        self.results_frame = tk.Frame(self.parent, bg="white")
        self.results_frame.pack(pady=20, fill=tk.BOTH, expand=True)
        
    def perform_action(self):
        """
        This method is called when the user clicks the action button.
        
        Add your main functionality here!
        
        COMMON PATTERNS:
        - Get input from entry fields
        - Process/calculate something
        - Display results
        - Handle errors with try/except
        """
        # Example: Get input
        user_input = self.input_entry.get().strip()
        
        # Example: Validate input
        if not user_input:
            messagebox.showwarning("Input Required", "Please enter something!")
            return
        
        # Example: Do something with the input
        try:
            # Your logic here
            result = f"You entered: {user_input}"
            
            # Display result
            self.display_result(result)
            
        except Exception as e:
            # Handle errors gracefully
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def display_result(self, result):
        """
        Display results to the user.
        
        Args:
            result: The data/text to display
        """
        # Clear previous results
        self.clear_results()
        
        # Show new result
        result_label = tk.Label(
            self.results_frame,
            text=result,
            font=("Arial", 14),
            bg="white",
            fg=self.colors['text']
        )
        result_label.pack(pady=20)
    
    def clear_results(self):
        """
        Clear all widgets from the results display area.
        
        This is useful before showing new results to avoid clutter.
        """
        for widget in self.results_frame.winfo_children():
            widget.destroy()


# HOW TO ADD THIS MODULE TO THE MAIN APP:
# 
# 1. In main.py, add this import at the top:
#    from your_module_name import YourClassName
#
# 2. In the create_ui() method of ThunderzAssistant class, add a button:
#    your_module_btn = tk.Button(
#        sidebar,
#        text="🔧  Your Module",
#        font=("Arial", 12),
#        bg=self.colors['accent'],
#        fg="white",
#        command=self.show_your_module
#    )
#    your_module_btn.pack(fill=tk.X, padx=10, pady=5)
#
# 3. Add a method to display your module:
#    def show_your_module(self):
#        self.clear_content()
#        your_module = YourClassName(self.content_frame, self.colors)
#
# That's it! Your module is now integrated into the app!
