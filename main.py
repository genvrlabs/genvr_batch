"""
GenVR Batch Processing Desktop Application
A modern desktop application for batch processing with GenVR API
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import requests
import json
import threading
import queue
import time
from pathlib import Path
from datetime import datetime
import os

class GenVRBatchProcessor:
    def __init__(self, root):
        self.root = root
        self.root.title("GenVR Batch Processor - Modern AI Model Processing")
        self.root.geometry("1800x1100")
        self.root.minsize(1600, 1000)
        
        # Set window icon if available
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
        
        # API Configuration
        self.api_base = "https://api.genvrresearch.com"
        self.api_key = tk.StringVar()
        self.uid = tk.StringVar()
        
        # Can be overridden for local testing
        # self.api_base = "http://localhost:3000"
        
        # Data storage
        self.models = []
        self.categories = {}
        self.current_schema = None
        self.batch_queue = queue.Queue()
        self.results = []
        
        # Setup UI
        self.setup_styles()
        self.create_ui()
        
        # Load models on startup
        self.load_models()
    
    def setup_styles(self):
        """Setup custom styles for the application"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Modern color palette
        self.colors = {
            'bg': '#1e1e2e',
            'bg_light': '#2a2a3e',
            'bg_card': '#313244',
            'accent': '#89b4fa',
            'accent_hover': '#74c7ec',
            'text': '#cdd6f4',
            'text_dim': '#9399b2',
            'success': '#a6e3a1',
            'error': '#f38ba8',
            'warning': '#fab387',
            'border': '#45475a',
            'white': '#ffffff'
        }
        
        # Configure root window
        self.root.configure(bg=self.colors['bg'])
        
        # Title styles
        style.configure("Title.TLabel", 
                       font=("Segoe UI", 24, "bold"), 
                       foreground=self.colors['accent'],
                       background=self.colors['bg'])
        
        style.configure("Subtitle.TLabel", 
                       font=("Segoe UI", 11, "bold"),
                       foreground=self.colors['text'],
                       background=self.colors['bg_card'])
        
        style.configure("Header.TLabel",
                       font=("Segoe UI", 10, "bold"),
                       foreground=self.colors['text'],
                       background=self.colors['bg_light'])
        
        # Frame styles
        style.configure("TFrame", background=self.colors['bg'])
        style.configure("Card.TFrame", background=self.colors['bg_card'], relief="flat")
        
        # LabelFrame styles
        style.configure("TLabelframe", 
                       background=self.colors['bg_card'],
                       bordercolor=self.colors['border'],
                       relief="solid",
                       borderwidth=1)
        style.configure("TLabelframe.Label",
                       font=("Segoe UI", 10, "bold"),
                       foreground=self.colors['accent'],
                       background=self.colors['bg_card'])
        
        # Button styles
        style.configure("TButton",
                       font=("Segoe UI", 10),
                       borderwidth=0,
                       relief="flat",
                       padding=(20, 10))
        
        style.configure("Accent.TButton",
                       font=("Segoe UI", 10, "bold"),
                       foreground=self.colors['white'],
                       background=self.colors['accent'],
                       borderwidth=0,
                       relief="flat",
                       padding=(20, 12))
        
        style.map("Accent.TButton",
                 background=[("active", self.colors['accent_hover']),
                           ("pressed", self.colors['accent'])],
                 relief=[("pressed", "flat")])
        
        style.configure("Success.TButton",
                       background=self.colors['success'],
                       foreground=self.colors['bg'])
        
        # Entry and Combobox styles
        style.configure("TEntry",
                       fieldbackground=self.colors['bg_light'],
                       foreground=self.colors['text'],
                       bordercolor=self.colors['border'],
                       lightcolor=self.colors['border'],
                       darkcolor=self.colors['border'],
                       insertcolor=self.colors['text'])
        
        style.configure("TCombobox",
                       fieldbackground=self.colors['bg_light'],
                       background=self.colors['bg_card'],
                       foreground=self.colors['text'],
                       bordercolor=self.colors['border'],
                       arrowcolor=self.colors['accent'],
                       selectbackground=self.colors['accent'],
                       selectforeground=self.colors['white'])
        
        # Notebook styles
        style.configure("TNotebook",
                       background=self.colors['bg'],
                       borderwidth=0)
        style.configure("TNotebook.Tab",
                       font=("Segoe UI", 10),
                       padding=(20, 10),
                       background=self.colors['bg_light'],
                       foreground=self.colors['text_dim'])
        style.map("TNotebook.Tab",
                 background=[("selected", self.colors['bg_card'])],
                 foreground=[("selected", self.colors['accent'])],
                 expand=[("selected", [1, 1, 1, 0])])
        
        # Progressbar
        style.configure("TProgressbar",
                       background=self.colors['accent'],
                       troughcolor=self.colors['bg_light'],
                       bordercolor=self.colors['border'],
                       lightcolor=self.colors['accent'],
                       darkcolor=self.colors['accent'])
        
        # Label styles
        style.configure("TLabel",
                       background=self.colors['bg_card'],
                       foreground=self.colors['text'],
                       font=("Segoe UI", 9))
        
        style.configure("Dim.TLabel",
                       foreground=self.colors['text_dim'],
                       background=self.colors['bg_card'],
                       font=("Segoe UI", 9))
        
        # Checkbutton
        style.configure("TCheckbutton",
                       background=self.colors['bg_card'],
                       foreground=self.colors['text'])
        
        # Separator
        style.configure("TSeparator", background=self.colors['border'])
        
    def create_ui(self):
        """Create the main UI layout"""
        # Main container with padding
        main_container = ttk.Frame(self.root, padding="20")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Title bar
        title_frame = ttk.Frame(main_container)
        title_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # App title and subtitle
        title_container = ttk.Frame(title_frame)
        title_container.pack(side=tk.LEFT)
        ttk.Label(title_container, text="GenVR Batch Processor", style="Title.TLabel").pack(anchor=tk.W)
        ttk.Label(title_container, text="Process 300+ AI models in batch", 
                 style="Dim.TLabel").pack(anchor=tk.W, pady=(2, 0))
        
        # API Configuration - Modern card style
        api_frame = ttk.LabelFrame(title_frame, text=" 🔑 API Configuration ", padding="15")
        api_frame.pack(side=tk.RIGHT, padx=20)
        
        # UID field
        uid_container = ttk.Frame(api_frame)
        uid_container.pack(fill=tk.X, pady=5)
        ttk.Label(uid_container, text="User ID", style="Dim.TLabel").pack(anchor=tk.W)
        ttk.Entry(uid_container, textvariable=self.uid, width=30, font=("Segoe UI", 10)).pack(fill=tk.X, pady=(2, 0))
        
        # API Key field
        key_container = ttk.Frame(api_frame)
        key_container.pack(fill=tk.X, pady=5)
        ttk.Label(key_container, text="API Key", style="Dim.TLabel").pack(anchor=tk.W)
        ttk.Entry(key_container, textvariable=self.api_key, width=30, show="●", font=("Segoe UI", 10)).pack(fill=tk.X, pady=(2, 0))
        
        # Left Panel - Model Selection
        left_panel = ttk.LabelFrame(main_container, text=" 📁 Model Selection ", padding="15")
        left_panel.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 15))
        
        # Category Selection
        category_container = ttk.Frame(left_panel)
        category_container.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(category_container, text="Category", style="Subtitle.TLabel").pack(anchor=tk.W, pady=(0, 5))
        
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(category_container, textvariable=self.category_var, 
                                           state="readonly", font=("Segoe UI", 10), height=15)
        self.category_combo.pack(fill=tk.X)
        self.category_combo.bind("<<ComboboxSelected>>", self.on_category_selected)
        
        # Model Selection - takes most of the space
        model_container = ttk.Frame(left_panel)
        model_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        ttk.Label(model_container, text="Available Models", style="Subtitle.TLabel").pack(anchor=tk.W, pady=(0, 5))
        
        # Model listbox with scrollbar - expands to fill available space
        model_list_frame = ttk.Frame(model_container)
        model_list_frame.pack(fill=tk.BOTH, expand=True)
        
        model_scroll = ttk.Scrollbar(model_list_frame)
        model_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.model_listbox = tk.Listbox(model_list_frame, 
                                        yscrollcommand=model_scroll.set,
                                        font=("Segoe UI", 11), 
                                        selectmode=tk.SINGLE,
                                        bg=self.colors['bg_light'],
                                        fg=self.colors['text'],
                                        selectbackground=self.colors['accent'],
                                        selectforeground=self.colors['white'],
                                        borderwidth=0,
                                        highlightthickness=1,
                                        highlightbackground=self.colors['border'],
                                        highlightcolor=self.colors['accent'],
                                        activestyle='none')
        # No fixed height - let it expand!
        self.model_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        model_scroll.config(command=self.model_listbox.yview)
        self.model_listbox.bind("<<ListboxSelect>>", self.on_model_selected)
        
        # Model info - fixed size at bottom, doesn't expand
        info_frame = ttk.Frame(left_panel)
        info_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(info_frame, text="ℹ️ Description", style="Dim.TLabel").pack(anchor=tk.W, pady=(0, 5))
        
        # Wrap info in a frame with fixed height
        info_container = ttk.Frame(info_frame, height=80)
        info_container.pack(fill=tk.X)
        info_container.pack_propagate(False)  # Don't let it expand
        
        self.model_info = ttk.Label(info_container, text="Select a model to see details", 
                                    wraplength=380, 
                                    justify=tk.LEFT,
                                    style="TLabel")
        self.model_info.pack(fill=tk.BOTH, expand=True)
        
        # Right Panel - Parameters and Batch Processing
        right_panel = ttk.Frame(main_container)
        right_panel.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Single Request
        self.single_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.single_frame, text="Single Request")
        
        # Scrollable parameters frame
        canvas = tk.Canvas(self.single_frame, 
                          bg=self.colors['bg_card'],
                          highlightthickness=0,
                          borderwidth=0)
        scrollbar = ttk.Scrollbar(self.single_frame, orient="vertical", command=canvas.yview)
        self.params_frame = ttk.Frame(canvas)
        
        self.params_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.params_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Tab 2: Batch Processing
        self.batch_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.batch_frame, text="Batch Processing")
        
        # Batch input area
        ttk.Label(self.batch_frame, text="📝 Batch Input (JSON format - one request per line):", 
                 style="Subtitle.TLabel").pack(anchor=tk.W, pady=(0, 10))
        
        self.batch_input = scrolledtext.ScrolledText(self.batch_frame, height=15, 
                                                     font=("Consolas", 10),
                                                     bg=self.colors['bg_light'],
                                                     fg=self.colors['text'],
                                                     insertbackground=self.colors['accent'],
                                                     selectbackground=self.colors['accent'],
                                                     selectforeground=self.colors['white'],
                                                     borderwidth=0,
                                                     highlightthickness=1,
                                                     highlightbackground=self.colors['border'],
                                                     highlightcolor=self.colors['accent'])
        self.batch_input.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Batch controls
        batch_control_frame = ttk.Frame(self.batch_frame)
        batch_control_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Generate examples button (highlighted)
        generate_btn = ttk.Button(batch_control_frame, text="✨ Generate 10 Examples", 
                  command=self.generate_batch_examples)
        generate_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(batch_control_frame, text="📄 Load CSV", 
                  command=self.load_csv).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(batch_control_frame, text="📋 Load JSON", 
                  command=self.load_json).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(batch_control_frame, text="🗑️ Clear", 
                  command=lambda: self.batch_input.delete(1.0, tk.END)).pack(side=tk.LEFT)
        
        # Concurrent requests setting
        concurrent_frame = ttk.Frame(batch_control_frame)
        concurrent_frame.pack(side=tk.RIGHT)
        ttk.Label(concurrent_frame, text="⚡ Concurrent Requests:", 
                 style="TLabel").pack(side=tk.LEFT, padx=(0, 10))
        self.concurrent_var = tk.IntVar(value=3)
        ttk.Spinbox(concurrent_frame, from_=1, to=10, textvariable=self.concurrent_var, 
                   width=15, font=("Segoe UI", 10)).pack(side=tk.LEFT)
        
        # Tab 3: Results
        self.results_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.results_frame, text="Results")
        
        # Results display
        ttk.Label(self.results_frame, text="📊 Generation Results:", 
                 style="Subtitle.TLabel").pack(anchor=tk.W, pady=(0, 10))
        
        self.results_text = scrolledtext.ScrolledText(self.results_frame, height=25, 
                                                      font=("Consolas", 10),
                                                      bg=self.colors['bg_light'],
                                                      fg=self.colors['text'],
                                                      insertbackground=self.colors['accent'],
                                                      selectbackground=self.colors['accent'],
                                                      selectforeground=self.colors['white'],
                                                      borderwidth=0,
                                                      highlightthickness=1,
                                                      highlightbackground=self.colors['border'],
                                                      highlightcolor=self.colors['accent'])
        self.results_text.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Results controls
        results_control_frame = ttk.Frame(self.results_frame)
        results_control_frame.pack(fill=tk.X)
        
        ttk.Button(results_control_frame, text="💾 Export Results", 
                  command=self.export_results).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(results_control_frame, text="🗑️ Clear Results", 
                  command=self.clear_results).pack(side=tk.LEFT)
        
        # Bottom panel - Action buttons and status
        bottom_panel = ttk.LabelFrame(main_container, text=" ⚡ Actions ", padding="15")
        bottom_panel.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(20, 0))
        
        # Action buttons
        button_frame = ttk.Frame(bottom_panel)
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.generate_btn = ttk.Button(button_frame, text="▶️  Generate Single", 
                                       command=self.generate_single, 
                                       style="Accent.TButton")
        self.generate_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.batch_btn = ttk.Button(button_frame, text="🚀  Start Batch Processing", 
                                    command=self.start_batch, 
                                    style="Accent.TButton")
        self.batch_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(button_frame, text="⏹️  Stop", 
                                   command=self.stop_processing, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)
        
        # Status section
        status_container = ttk.Frame(bottom_panel)
        status_container.pack(fill=tk.X)
        
        ttk.Label(status_container, text="Status", style="Dim.TLabel").pack(anchor=tk.W, pady=(0, 5))
        
        # Status bar
        self.status_var = tk.StringVar(value="🟢 Ready to process")
        status_bar = ttk.Label(status_container, textvariable=self.status_var,
                              font=("Segoe UI", 10),
                              foreground=self.colors['success'],
                              background=self.colors['bg_card'],
                              padding=(10, 8),
                              relief="solid",
                              borderwidth=1)
        status_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(status_container, variable=self.progress_var, 
                                       maximum=100, mode='determinate')
        self.progress.pack(fill=tk.X)
        
        # Configure grid weights for proper resizing
        main_container.columnconfigure(0, weight=1, minsize=400)
        main_container.columnconfigure(1, weight=2, minsize=600)
        main_container.rowconfigure(1, weight=1)
        
        # Make root window resizable
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
    
    def load_models(self):
        """Load available models from GenVR API"""
        self.status_var.set("Loading models...")
        
        def fetch():
            try:
                # Get model details directly from /api/models
                response = requests.get(f"{self.api_base}/api/models", timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if not data.get("success"):
                    raise Exception("Failed to load models")
                
                self.models = data.get("data", [])
                
                self.organize_models()
                self.root.after(0, self.populate_categories)
                self.root.after(0, lambda: self.status_var.set(
                    f"🟢 Loaded {len(self.models)} models successfully"))
                    
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(
                    "Error", f"Failed to load models: {str(e)}"))
                self.root.after(0, lambda: self.status_var.set("❌ Error loading models"))
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def organize_models(self):
        """Organize models by category"""
        self.categories = {}
        for model in self.models:
            category = model.get("category", "other")
            if category not in self.categories:
                self.categories[category] = []
            self.categories[category].append(model)
    
    def populate_categories(self):
        """Populate category dropdown"""
        categories = sorted(self.categories.keys())
        self.category_combo['values'] = categories
        if categories:
            self.category_combo.current(0)
            self.on_category_selected(None)
    
    def on_category_selected(self, event):
        """Handle category selection"""
        category = self.category_var.get()
        if category in self.categories:
            self.model_listbox.delete(0, tk.END)
            for model in self.categories[category]:
                self.model_listbox.insert(tk.END, model.get("name", "Unknown"))
            
            if self.categories[category]:
                self.model_listbox.selection_set(0)
                self.on_model_selected(None)
    
    def on_model_selected(self, event):
        """Handle model selection"""
        selection = self.model_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        category = self.category_var.get()
        if category not in self.categories:
            return
        
        model = self.categories[category][idx]
        self.model_info.config(text=model.get("description", ""))
        
        # Load schema for this model
        self.load_schema(model.get("category"), model.get("subcategory"))
    
    def load_schema(self, category, subcategory):
        """Load schema for selected model"""
        self.status_var.set(f"Loading schema for {category}/{subcategory}...")
        
        def fetch():
            try:
                url = f"{self.api_base}/api/schema/{category}/{subcategory}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if data.get("success"):
                    self.current_schema = data.get("data", {})
                    self.root.after(0, self.build_parameter_form)
                    self.root.after(0, lambda: self.status_var.set(
                        f"Schema loaded for {category}/{subcategory}"))
                else:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Error", f"Failed to load schema"))
            except Exception as e:
                self.root.after(0, lambda: self.status_var.set(
                    f"Error loading schema: {str(e)}"))
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def build_parameter_form(self):
        """Build dynamic form based on schema"""
        # Clear existing form
        for widget in self.params_frame.winfo_children():
            widget.destroy()
        
        self.param_widgets = {}
        
        if not self.current_schema:
            ttk.Label(self.params_frame, text="No schema available").pack(pady=20)
            return
        
        parameters = self.current_schema.get("parameters", {})
        
        row = 0
        
        # Required parameters
        if parameters.get("required"):
            ttk.Label(self.params_frame, text="Required Parameters", 
                     style="Subtitle.TLabel").grid(row=row, column=0, columnspan=2, 
                                                   sticky=tk.W, pady=(10, 5))
            row += 1
            
            for param in parameters["required"]:
                row = self.create_parameter_widget(param, row, required=True)
        
        # Optional parameters
        if parameters.get("optional"):
            ttk.Label(self.params_frame, text="Optional Parameters", 
                     style="Subtitle.TLabel").grid(row=row, column=0, columnspan=2, 
                                                   sticky=tk.W, pady=(20, 5))
            row += 1
            
            for param in parameters["optional"]:
                row = self.create_parameter_widget(param, row, required=False)
    
    def create_parameter_widget(self, param, row, required=False):
        """Create a widget for a parameter"""
        name = param.get("name", "")
        param_type = param.get("type", "string")
        description = param.get("description", "")
        default = param.get("default")
        allowed_values = param.get("allowedValues", [])
        # Support both 'min'/'max' and 'minimum'/'maximum'
        min_val = param.get("min") or param.get("minimum")
        max_val = param.get("max") or param.get("maximum")
        step = param.get("step", 1)
        
        # Label with range info
        label_text = f"{name}{'*' if required else ''}"
        if min_val is not None and max_val is not None:
            label_text += f" ({min_val}-{max_val})"
        label = ttk.Label(self.params_frame, text=label_text,
                         font=("Segoe UI", 10, "bold" if required else "normal"),
                         foreground=self.colors['accent'] if required else self.colors['text'])
        label.grid(row=row, column=0, sticky=tk.W, padx=10, pady=8)
        
        # Create appropriate widget
        widget_var = None
        widget = None
        
        if param_type == "enum" and allowed_values:
            widget_var = tk.StringVar(value=str(default) if default else "")
            widget = ttk.Combobox(self.params_frame, textvariable=widget_var, 
                                 values=allowed_values, state="readonly", width=40)
            if default:
                widget.set(str(default))
        elif param_type == "boolean":
            widget_var = tk.BooleanVar(value=default if default is not None else False)
            widget = ttk.Checkbutton(self.params_frame, variable=widget_var)
        elif param_type in ["integer", "number"] and min_val is not None and max_val is not None:
            # Use slider + spinbox for numeric values with min/max
            slider_frame = ttk.Frame(self.params_frame)
            
            if param_type == "integer":
                widget_var = tk.IntVar(value=int(default) if default else int(min_val))
                
                # Slider
                slider = ttk.Scale(slider_frame, from_=min_val, to=max_val, 
                                  variable=widget_var, orient=tk.HORIZONTAL, length=300)
                slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
                
                # Spinbox
                spinbox = ttk.Spinbox(slider_frame, from_=min_val, to=max_val, 
                                     textvariable=widget_var, width=10, increment=step)
                spinbox.pack(side=tk.LEFT)
            else:
                # Float values
                widget_var = tk.DoubleVar(value=float(default) if default else float(min_val))
                
                # Slider
                slider = ttk.Scale(slider_frame, from_=min_val, to=max_val, 
                                  variable=widget_var, orient=tk.HORIZONTAL, length=300)
                slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
                
                # Spinbox
                spinbox = ttk.Spinbox(slider_frame, from_=min_val, to=max_val, 
                                     textvariable=widget_var, width=10, increment=step if step else 0.01,
                                     format="%.2f")
                spinbox.pack(side=tk.LEFT)
            
            widget = slider_frame
        elif param_type == "integer":
            widget_var = tk.StringVar(value=str(default) if default else "")
            widget = ttk.Entry(self.params_frame, textvariable=widget_var, width=42)
            # Add validation for integers
            vcmd = (self.root.register(self.validate_integer), '%P')
            widget.config(validate='key', validatecommand=vcmd)
        else:  # string or text
            if len(description) > 100 or "detail" in description.lower():
                # Multi-line text for long descriptions
                widget = scrolledtext.ScrolledText(self.params_frame, height=5, width=50, 
                                                  font=("Segoe UI", 10),
                                                  bg=self.colors['bg_light'],
                                                  fg=self.colors['text'],
                                                  insertbackground=self.colors['accent'],
                                                  selectbackground=self.colors['accent'],
                                                  selectforeground=self.colors['white'],
                                                  borderwidth=0,
                                                  highlightthickness=1,
                                                  highlightbackground=self.colors['border'])
            else:
                widget_var = tk.StringVar(value=str(default) if default else "")
                widget = ttk.Entry(self.params_frame, textvariable=widget_var, width=50, 
                                  font=("Segoe UI", 10))
        
        widget.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5, pady=8)
        
        # Store widget reference
        self.param_widgets[name] = {
            "widget": widget,
            "var": widget_var,
            "type": param_type,
            "required": required,
            "min": min_val,
            "max": max_val,
            "step": step
        }
        
        row += 1
        
        # Description with better spacing
        if description:
            desc_label = ttk.Label(self.params_frame, text=description, 
                                  wraplength=500, font=("Segoe UI", 9), 
                                  foreground=self.colors['text_dim'],
                                  style="Dim.TLabel")
            desc_label.grid(row=row, column=1, sticky=tk.W, padx=10, pady=(5, 10))
            row += 1
            
            # Add separator
            separator = ttk.Separator(self.params_frame, orient=tk.HORIZONTAL)
            separator.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 15))
            row += 1
        
        return row
    
    def validate_integer(self, value):
        """Validate integer input"""
        if value == "":
            return True
        try:
            int(value)
            return True
        except ValueError:
            return False
    
    def get_parameters(self):
        """Get parameters from form"""
        params = {}
        
        for name, widget_info in self.param_widgets.items():
            widget = widget_info["widget"]
            var = widget_info["var"]
            param_type = widget_info["type"]
            required = widget_info["required"]
            
            # Get value
            value = None
            if isinstance(widget, scrolledtext.ScrolledText):
                value = widget.get(1.0, tk.END).strip()
            elif var:
                value = var.get()
                # For IntVar and DoubleVar, get() returns the numeric value
                if isinstance(var, (tk.IntVar, tk.DoubleVar)):
                    value = var.get()
            else:
                continue
            
            # Check required fields
            if required and (value is None or value == ""):
                raise ValueError(f"Required field '{name}' is empty")
            
            # Convert types
            if value is not None and value != "":
                if param_type == "integer":
                    value = int(value)
                elif param_type == "number":
                    value = float(value)
                elif param_type == "boolean":
                    value = bool(value)
                
                params[name] = value
        
        return params
    
    def generate_single(self):
        """Generate single request"""
        try:
            params = self.get_parameters()
            
            if not self.api_key.get():
                messagebox.showwarning("Warning", "Please enter your API key")
                return
            
            if not self.uid.get():
                messagebox.showwarning("Warning", "Please enter your UID")
                return
            
            category = self.current_schema.get("category")
            subcategory = self.current_schema.get("subcategory")
            
            self.status_var.set("Generating...")
            self.generate_btn.config(state=tk.DISABLED)
            
            def process():
                try:
                    result = self.call_api(category, subcategory, params)
                    self.root.after(0, lambda: self.display_result(result))
                    self.root.after(0, lambda: self.status_var.set("Generation complete"))
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Error", f"Generation failed: {str(e)}"))
                    self.root.after(0, lambda: self.status_var.set("Generation failed"))
                finally:
                    self.root.after(0, lambda: self.generate_btn.config(state=tk.NORMAL))
            
            threading.Thread(target=process, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Invalid parameters: {str(e)}")
    
    def call_api(self, category, subcategory, params):
        """Call GenVR API with 3-step workflow: generate -> poll -> response"""
        headers = {
            "Authorization": f"Bearer {self.api_key.get()}",
            "Content-Type": "application/json"
        }
        
        # Step 1: Generate - Submit the task
        generate_payload = {
            "uid": self.uid.get(),
            "category": category,
            "subcategory": subcategory,
            **params  # Spread the parameters directly
        }
        
        self.root.after(0, lambda: self.status_var.set("Submitting task..."))
        
        generate_response = requests.post(
            f"{self.api_base}/v2/generate",
            json=generate_payload,
            headers=headers,
            timeout=120  # Increased timeout for slow models
        )
        generate_response.raise_for_status()
        generate_data = generate_response.json()
        
        if not generate_data.get("success"):
            raise Exception(f"Generate failed: {generate_data.get('message', 'Unknown error')}")
        
        task_id = generate_data["data"]["id"]
        
        # Step 2: Poll for status
        poll_count = 0
        max_polls = 300  # 5 minutes with 1 second intervals
        
        while poll_count < max_polls:
            self.root.after(0, lambda c=poll_count: self.status_var.set(
                f"Processing... ({c}s elapsed)"))
            
            status_payload = {
                "id": task_id,
                "uid": self.uid.get(),
                "category": category,
                "subcategory": subcategory
            }
            
            status_response = requests.post(
                f"{self.api_base}/v2/status",
                json=status_payload,
                headers=headers,
                timeout=10
            )
            status_response.raise_for_status()
            status_data = status_response.json()
            
            if not status_data.get("success"):
                raise Exception(f"Status check failed: {status_data.get('message', 'Unknown error')}")
            
            status = status_data["data"]["status"]
            
            if status == "completed":
                # Step 3: Get final response
                self.root.after(0, lambda: self.status_var.set("Retrieving results..."))
                
                result_payload = {
                    "id": task_id,
                    "uid": self.uid.get(),
                    "category": category,
                    "subcategory": subcategory
                }
                
                result_response = requests.post(
                    f"{self.api_base}/v2/response",
                    json=result_payload,
                    headers=headers,
                    timeout=60  # Increased timeout for large responses
                )
                result_response.raise_for_status()
                result_data = result_response.json()
                
                if not result_data.get("success"):
                    raise Exception(f"Result fetch failed: {result_data.get('message', 'Unknown error')}")
                
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "output": result_data["data"]["output"],
                    "processing_time": f"{poll_count}s"
                }
            
            elif status == "failed":
                error_msg = status_data["data"].get("error", "Unknown error")
                raise Exception(f"Task failed: {error_msg}")
            
            # Status is still processing/queued
            time.sleep(1)
            poll_count += 1
        
        raise Exception(f"Timeout: Task did not complete within {max_polls} seconds")
    
    def display_result(self, result):
        """Display result in results tab"""
        self.notebook.select(self.results_frame)
        
        result_text = json.dumps(result, indent=2)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.results_text.insert(tk.END, f"\n{'='*80}\n")
        self.results_text.insert(tk.END, f"Result at {timestamp}\n")
        self.results_text.insert(tk.END, f"{'='*80}\n")
        self.results_text.insert(tk.END, f"{result_text}\n")
        self.results_text.see(tk.END)
        
        self.results.append({"timestamp": timestamp, "result": result})
    
    def generate_batch_examples(self):
        """Generate 10 example JSON entries based on current schema"""
        if not self.current_schema:
            messagebox.showwarning("No Schema", "Please select a model first to load its schema.")
            return
        
        parameters = self.current_schema.get("parameters", {})
        required_params = parameters.get("required", [])
        optional_params = parameters.get("optional", [])
        
        # Example variations for different parameter types
        example_prompts = [
            "a beautiful sunset over mountains",
            "a futuristic city with flying cars",
            "a cute cat playing with yarn",
            "an astronaut floating in space",
            "a serene lake surrounded by trees",
            "a dragon flying over a castle",
            "a robot serving coffee in a cafe",
            "a magical forest with glowing mushrooms",
            "a vintage car on a desert highway",
            "a cozy library with warm lighting"
        ]
        
        examples = []
        
        for i in range(10):
            example = {}
            
            # Add required parameters
            for param in required_params:
                name = param.get("name")
                param_type = param.get("type")
                
                if "prompt" in name.lower():
                    example[name] = example_prompts[i]
                elif param_type == "string":
                    example[name] = f"example_{name}_{i+1}"
                elif param_type == "integer":
                    min_val = param.get("min") or param.get("minimum", 1)
                    max_val = param.get("max") or param.get("maximum", 10)
                    example[name] = min_val + (i % (max_val - min_val + 1))
                elif param_type == "boolean":
                    example[name] = i % 2 == 0
            
            # Add some optional parameters
            for param in optional_params[:3]:  # Add first 3 optional params
                name = param.get("name")
                param_type = param.get("type")
                default = param.get("default")
                allowed_values = param.get("allowedValues", [])
                
                if param_type == "enum" and allowed_values:
                    example[name] = allowed_values[i % len(allowed_values)]
                elif "aspect_ratio" in name.lower() and allowed_values:
                    example[name] = allowed_values[i % len(allowed_values)]
                elif param_type == "integer":
                    min_val = param.get("min") or param.get("minimum")
                    max_val = param.get("max") or param.get("maximum")
                    if min_val is not None and max_val is not None:
                        example[name] = min_val + (i % (max_val - min_val + 1))
                    elif default is not None:
                        example[name] = default
                elif param_type == "string" and "negative" in name.lower():
                    # Skip negative prompts for variety
                    if i % 3 == 0:
                        example[name] = "blurry, low quality"
                elif default is not None and i % 2 == 0:
                    example[name] = default
            
            examples.append(json.dumps(example))
        
        # Set the text
        self.batch_input.delete(1.0, tk.END)
        self.batch_input.insert(1.0, "\n".join(examples))
        self.status_var.set(f"✅ Generated 10 example entries based on {self.current_schema.get('subcategory')} schema")
    
    def load_csv(self):
        """Load batch data from CSV"""
        filename = filedialog.askopenfilename(
            title="Load CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            try:
                import csv
                with open(filename, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    self.batch_input.delete(1.0, tk.END)
                    for row in reader:
                        self.batch_input.insert(tk.END, json.dumps(row) + "\n")
                self.status_var.set(f"Loaded CSV: {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load CSV: {str(e)}")
    
    def load_json(self):
        """Load batch data from JSON"""
        filename = filedialog.askopenfilename(
            title="Load JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.batch_input.delete(1.0, tk.END)
                    if isinstance(data, list):
                        for item in data:
                            self.batch_input.insert(tk.END, json.dumps(item) + "\n")
                    else:
                        self.batch_input.insert(tk.END, json.dumps(data) + "\n")
                self.status_var.set(f"Loaded JSON: {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load JSON: {str(e)}")
    
    def start_batch(self):
        """Start batch processing"""
        if not self.api_key.get():
            messagebox.showwarning("Warning", "Please enter your API key")
            return
        
        if not self.uid.get():
            messagebox.showwarning("Warning", "Please enter your UID")
            return
        
        if not self.current_schema:
            messagebox.showwarning("Warning", "Please select a model first")
            return
        
        # Parse batch input
        batch_text = self.batch_input.get(1.0, tk.END).strip()
        if not batch_text:
            messagebox.showwarning("Warning", "No batch data provided")
            return
        
        try:
            batch_items = []
            for line in batch_text.split('\n'):
                line = line.strip()
                if line:
                    batch_items.append(json.loads(line))
            
            if not batch_items:
                messagebox.showwarning("Warning", "No valid batch items found")
                return
            
            self.status_var.set(f"Starting batch processing: {len(batch_items)} items")
            self.batch_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.progress_var.set(0)
            
            # Start batch processing in thread
            self.processing = True
            threading.Thread(target=self.process_batch, 
                           args=(batch_items,), daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse batch data: {str(e)}")
    
    def process_batch(self, batch_items):
        """Process batch items with concurrent execution"""
        import concurrent.futures
        from datetime import datetime
        
        category = self.current_schema.get("category")
        subcategory = self.current_schema.get("subcategory")
        total = len(batch_items)
        completed = [0]  # Use list to allow modification in nested function
        successful = [0]
        failed = [0]
        
        # Clear results at start
        self.root.after(0, lambda: self.results_text.delete(1.0, tk.END))
        self.root.after(0, lambda: self.results_text.insert(tk.END, 
            f"🚀 Starting batch processing: {total} requests\n"))
        self.root.after(0, lambda: self.results_text.insert(tk.END, 
            f"Model: {category}/{subcategory}\n"))
        self.root.after(0, lambda: self.results_text.insert(tk.END, 
            f"Concurrent requests: {self.concurrent_var.get()}\n"))
        self.root.after(0, lambda: self.results_text.insert(tk.END, "="*80 + "\n\n"))
        
        def process_single(idx, params):
            if not self.processing:
                return
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            try:
                result = self.call_api(category, subcategory, params)
                
                completed[0] += 1
                successful[0] += 1
                progress = (completed[0] / total) * 100
                
                # Update UI
                self.root.after(0, lambda: self.status_var.set(
                    f"⏳ Processing: {completed[0]}/{total} (✅ {successful[0]} | ❌ {failed[0]})"))
                self.root.after(0, lambda p=progress: self.progress_var.set(p))
                
                # Display result
                self.root.after(0, lambda: self.results_text.insert(tk.END, 
                    f"\n{'='*80}\n"))
                self.root.after(0, lambda: self.results_text.insert(tk.END, 
                    f"✅ Request #{idx + 1} completed at {timestamp}\n"))
                self.root.after(0, lambda: self.results_text.insert(tk.END, 
                    f"{'='*80}\n\n"))
                self.root.after(0, lambda: self.results_text.insert(tk.END, 
                    f"📝 Parameters:\n{json.dumps(params, indent=2)}\n\n"))
                self.root.after(0, lambda: self.results_text.insert(tk.END, 
                    f"📊 Result:\n{json.dumps(result, indent=2)}\n\n"))
                self.root.after(0, lambda: self.results_text.see(tk.END))
                
            except Exception as e:
                completed[0] += 1
                failed[0] += 1
                progress = (completed[0] / total) * 100
                
                # Update UI
                self.root.after(0, lambda: self.status_var.set(
                    f"⏳ Processing: {completed[0]}/{total} (✅ {successful[0]} | ❌ {failed[0]})"))
                self.root.after(0, lambda p=progress: self.progress_var.set(p))
                
                # Display error
                self.root.after(0, lambda: self.results_text.insert(tk.END, 
                    f"\n{'='*80}\n"))
                self.root.after(0, lambda: self.results_text.insert(tk.END, 
                    f"❌ Request #{idx + 1} failed at {timestamp}\n"))
                self.root.after(0, lambda: self.results_text.insert(tk.END, 
                    f"{'='*80}\n\n"))
                self.root.after(0, lambda: self.results_text.insert(tk.END, 
                    f"📝 Parameters:\n{json.dumps(params, indent=2)}\n\n"))
                self.root.after(0, lambda: self.results_text.insert(tk.END, 
                    f"❌ Error: {str(e)}\n\n"))
                self.root.after(0, lambda: self.results_text.see(tk.END))
        
        # Process with thread pool
        max_workers = self.concurrent_var.get()
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for idx, params in enumerate(batch_items):
                if not self.processing:
                    break
                future = executor.submit(process_single, idx, params)
                futures.append(future)
            
            # Wait for all to complete
            concurrent.futures.wait(futures)
        
        # Show final summary
        self.root.after(0, lambda: self.results_text.insert(tk.END, 
            f"\n{'='*80}\n"))
        self.root.after(0, lambda: self.results_text.insert(tk.END, 
            f"🎉 Batch processing completed!\n"))
        self.root.after(0, lambda: self.results_text.insert(tk.END, 
            f"{'='*80}\n"))
        self.root.after(0, lambda: self.results_text.insert(tk.END, 
            f"Total: {total} | Successful: {successful[0]} | Failed: {failed[0]}\n"))
        
        self.root.after(0, self.batch_complete)
    
    def batch_complete(self):
        """Handle batch processing completion"""
        self.processing = False
        self.status_var.set("Batch processing complete")
        self.batch_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress_var.set(100)
    
    def stop_processing(self):
        """Stop batch processing"""
        self.processing = False
        self.status_var.set("Stopping batch processing...")
    
    def clear_results(self):
        """Clear results display"""
        self.results_text.delete(1.0, tk.END)
        self.results = []
        self.status_var.set("Results cleared")
    
    def export_results(self):
        """Export results to file"""
        if not self.results:
            messagebox.showinfo("Info", "No results to export")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Export Results",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.results, f, indent=2)
                self.status_var.set(f"Results exported to {filename}")
                messagebox.showinfo("Success", f"Results exported successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export results: {str(e)}")


def main():
    root = tk.Tk()
    app = GenVRBatchProcessor(root)
    root.mainloop()


if __name__ == "__main__":
    main()

