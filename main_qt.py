"""
GenVR Batch Processing Desktop Application - PyQt6 Version
A modern desktop application for batch processing with GenVR API
"""

import sys
import requests
import json
import time
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QListWidget, QTextEdit,
    QTabWidget, QProgressBar, QSpinBox, QCheckBox, QScrollArea,
    QFrame, QSplitter, QFileDialog, QMessageBox, QGroupBox, QSizePolicy,
    QSlider, QDoubleSpinBox, QDialog
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QIcon


class APIWorker(QThread):
    """Worker thread for API calls"""
    status_update = Signal(str)
    progress_update = Signal(int)
    result_ready = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, api_base, uid, api_key, category, subcategory, params):
        super().__init__()
        self.api_base = api_base
        self.uid = uid
        self.api_key = api_key
        self.category = category
        self.subcategory = subcategory
        self.params = params
        self.is_running = True
    
    def run(self):
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Step 1: Generate
            self.status_update.emit("⏳ Submitting task...")
            generate_payload = {
                "uid": self.uid,
                "category": self.category,
                "subcategory": self.subcategory,
                **self.params
            }
            
            response = requests.post(
                f"{self.api_base}/api/v1/generate",
                json=generate_payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("success"):
                raise Exception(f"Generate failed: {data.get('message', 'Unknown error')}")
            
            task_id = data["data"]["id"]
            
            # Step 2: Poll status
            poll_count = 0
            max_polls = 300
            
            while poll_count < max_polls and self.is_running:
                self.status_update.emit(f"⏳ Processing... ({poll_count}s)")
                
                status_response = requests.post(
                    f"{self.api_base}/api/v1/status",
                    json={
                        "id": task_id,
                        "uid": self.uid,
                        "category": self.category,
                        "subcategory": self.subcategory
                    },
                    headers=headers,
                    timeout=10
                )
                status_response.raise_for_status()
                status_data = status_response.json()
                
                if not status_data.get("success"):
                    raise Exception(f"Status check failed: {status_data.get('message')}")
                
                status = status_data["data"]["status"]
                
                if status == "completed":
                    # Step 3: Get result
                    self.status_update.emit("✅ Retrieving results...")
                    
                    result_response = requests.post(
                        f"{self.api_base}/api/v1/response",
                        json={
                            "id": task_id,
                            "uid": self.uid,
                            "category": self.category,
                            "subcategory": self.subcategory
                        },
                        headers=headers,
                        timeout=30
                    )
                    result_response.raise_for_status()
                    result_data = result_response.json()
                    
                    if not result_data.get("success"):
                        raise Exception(f"Result fetch failed: {result_data.get('message')}")
                    
                    result = {
                        "task_id": task_id,
                        "status": "completed",
                        "output": result_data["data"]["output"],
                        "processing_time": f"{poll_count}s"
                    }
                    self.result_ready.emit(result)
                    return
                
                elif status == "failed":
                    error_msg = status_data["data"].get("error", "Unknown error")
                    raise Exception(f"Task failed: {error_msg}")
                
                time.sleep(1)
                poll_count += 1
                self.progress_update.emit(int((poll_count / max_polls) * 100))
            
            if not self.is_running:
                self.status_update.emit("⏹️ Stopped by user")
            else:
                raise Exception(f"Timeout: Task did not complete within {max_polls} seconds")
                
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def stop(self):
        self.is_running = False


class BatchWorker(QThread):
    """Worker thread for batch processing"""
    progress_update = Signal(str)
    result_ready = Signal(int, dict, dict)  # index, params, result
    error = Signal(int, dict, str)  # index, params, error_message
    finished = Signal(int, int, int)  # total, successful, failed
    
    def __init__(self, api_base, uid, api_key, category, subcategory, batch_data, max_concurrent):
        super().__init__()
        self.api_base = api_base
        self.uid = uid
        self.api_key = api_key
        self.category = category
        self.subcategory = subcategory
        self.batch_data = batch_data
        self.max_concurrent = max_concurrent
        self.is_running = True
        
    def run(self):
        """Process batch with concurrency"""
        import concurrent.futures
        import threading
        
        total = len(self.batch_data)
        successful = 0
        failed = 0
        completed = 0
        lock = threading.Lock()
        
        def process_single(index, params):
            nonlocal successful, failed, completed
            
            if not self.is_running:
                return
            
            try:
                # Call API with 3-step workflow
                result = self.call_api(params)
                
                with lock:
                    successful += 1
                    completed += 1
                    self.progress_update.emit(f"⏳ Processing: {completed}/{total} (✅ {successful} | ❌ {failed})")
                
                self.result_ready.emit(index, params, result)
                
            except Exception as e:
                with lock:
                    failed += 1
                    completed += 1
                    self.progress_update.emit(f"⏳ Processing: {completed}/{total} (✅ {successful} | ❌ {failed})")
                
                self.error.emit(index, params, str(e))
        
        # Process with thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            futures = []
            for i, params in enumerate(self.batch_data):
                if not self.is_running:
                    break
                future = executor.submit(process_single, i, params)
                futures.append(future)
            
            # Wait for all to complete
            concurrent.futures.wait(futures)
        
        self.finished.emit(total, successful, failed)
    
    def call_api(self, params):
        """Call GenVR API with 3-step workflow"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Step 1: Generate
        generate_payload = {
            "uid": self.uid,
            "category": self.category,
            "subcategory": self.subcategory,
            **params
        }
        
        generate_response = requests.post(
            f"{self.api_base}/api/v1/generate",
            json=generate_payload,
            headers=headers,
            timeout=30
        )
        generate_response.raise_for_status()
        generate_data = generate_response.json()
        
        if not generate_data.get("success"):
            raise Exception(f"Generate failed: {generate_data.get('message', 'Unknown error')}")
        
        task_id = generate_data["data"]["id"]
        
        # Step 2: Poll for status
        max_polls = 300
        for poll_count in range(max_polls):
            if not self.is_running:
                raise Exception("Stopped by user")
            
            status_payload = {
                "id": task_id,
                "uid": self.uid,
                "category": self.category,
                "subcategory": self.subcategory
            }
            
            status_response = requests.post(
                f"{self.api_base}/api/v1/status",
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
                # Step 3: Get response
                result_payload = {
                    "id": task_id,
                    "uid": self.uid,
                    "category": self.category,
                    "subcategory": self.subcategory
                }
                
                result_response = requests.post(
                    f"{self.api_base}/api/v1/response",
                    json=result_payload,
                    headers=headers,
                    timeout=10
                )
                result_response.raise_for_status()
                result_data = result_response.json()
                
                if not result_data.get("success"):
                    raise Exception(f"Response retrieval failed: {result_data.get('message', 'Unknown error')}")
                
                return result_data["data"]
            
            elif status == "failed":
                raise Exception("Task failed on server")
            
            time.sleep(1)
        
        raise Exception("Timeout waiting for completion")
    
    def stop(self):
        self.is_running = False


class GenVRBatchProcessor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GenVR Batch Processor - Modern AI Processing")
        self.setGeometry(100, 100, 1600, 1000)
        self.setMinimumSize(1400, 900)
        
        # Fix layout issues when maximizing
        self.setSizePolicy(self.sizePolicy().horizontalPolicy(), self.sizePolicy().verticalPolicy())
        
        # API Configuration
        self.api_base = "https://api.genvrresearch.com"
        
        # Data storage
        self.models = []
        self.categories = {}
        self.current_model = None
        self.current_schema = None
        self.param_widgets = {}
        self.results = []
        self.batch_results = []  # Store batch results with outputs
        self.batch_json_data = None  # Store actual JSON with base64
        self.worker = None
        self.batch_worker = None
        
        # Setup UI
        self.setup_ui()
        self.apply_styles()
        
        # Load models
        QTimer.singleShot(100, self.load_models)
    
    def setup_ui(self):
        """Setup the main UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main scroll area to contain everything
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Content widget inside scroll area
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)
        
        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        header_layout = self.create_header()
        main_layout.addLayout(header_layout)
        
        # Main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        splitter.setMinimumHeight(600)  # Ensure minimum height
        
        # Left panel - Model selection
        left_panel = self.create_left_panel()
        left_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        splitter.addWidget(left_panel)
        
        # Right panel - Tabs
        right_panel = self.create_right_panel()
        right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([400, 800])  # Set initial sizes
        
        main_layout.addWidget(splitter, 1)
        
        # Bottom panel - Actions
        bottom_panel = self.create_bottom_panel()
        main_layout.addWidget(bottom_panel)
        
        # Set scroll area as central widget
        wrapper_layout = QVBoxLayout(central_widget)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.addWidget(scroll_area)
    
    def create_header(self):
        """Create header with title and API config"""
        layout = QHBoxLayout()
        
        # Title section
        title_container = QVBoxLayout()
        title_label = QLabel("GenVR Batch Processor")
        title_label.setObjectName("titleLabel")
        title_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        
        subtitle_label = QLabel("Process all available AI models in batch")
        subtitle_label.setObjectName("subtitleLabel")
        
        title_container.addWidget(title_label)
        title_container.addWidget(subtitle_label)
        title_container.addStretch()
        
        layout.addLayout(title_container)
        layout.addStretch()
        
        # API Configuration
        api_group = QGroupBox("🔑 API Configuration")
        api_group.setObjectName("apiGroup")
        api_layout = QVBoxLayout()
        
        # UID
        uid_label = QLabel("User ID")
        uid_label.setObjectName("dimLabel")
        self.uid_input = QLineEdit()
        self.uid_input.setPlaceholderText("Enter your GenVR User ID")
        self.uid_input.setMinimumWidth(300)
        
        api_layout.addWidget(uid_label)
        api_layout.addWidget(self.uid_input)
        
        # API Key
        key_label = QLabel("API Key")
        key_label.setObjectName("dimLabel")
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your API Key")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setMinimumWidth(300)
        
        api_layout.addWidget(key_label)
        api_layout.addWidget(self.api_key_input)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        return layout
    
    def create_left_panel(self):
        """Create left panel with model selection"""
        panel = QGroupBox("📁 Model Selection")
        panel.setObjectName("cardGroup")
        layout = QVBoxLayout()
        
        # Category selection
        cat_label = QLabel("Category")
        cat_label.setObjectName("sectionLabel")
        layout.addWidget(cat_label)
        
        self.category_combo = QComboBox()
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        layout.addWidget(self.category_combo)
        
        layout.addSpacing(15)
        
        # Model selection
        model_label = QLabel("Available Models")
        model_label.setObjectName("sectionLabel")
        layout.addWidget(model_label)
        
        self.model_list = QListWidget()
        self.model_list.setMinimumHeight(400)  # Good minimum size
        # Remove max height - let it expand when window is maximized
        self.model_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.model_list.currentRowChanged.connect(self.on_model_selected)
        layout.addWidget(self.model_list, 1)  # Stretch factor 1 - takes available space
        
        layout.addSpacing(10)
        
        # Model info - fixed size container that doesn't expand
        info_container = QFrame()
        info_container.setFixedHeight(120)  # Fixed height prevents overlap
        info_container_layout = QVBoxLayout(info_container)
        info_container_layout.setContentsMargins(0, 0, 0, 0)
        
        info_label = QLabel("ℹ️ Description")
        info_label.setObjectName("dimLabel")
        info_container_layout.addWidget(info_label)
        
        self.model_info = QLabel("Select a model to see details")
        self.model_info.setWordWrap(True)
        self.model_info.setObjectName("infoLabel")
        self.model_info.setAlignment(Qt.AlignmentFlag.AlignTop)
        info_container_layout.addWidget(self.model_info, 1)
        
        layout.addWidget(info_container)  # No stretch factor - stays fixed
        
        panel.setLayout(layout)
        return panel
    
    def create_right_panel(self):
        """Create right panel with tabs"""
        self.tabs = QTabWidget()
        self.tabs.setObjectName("mainTabs")
        
        # Tab 1: Single Request
        single_tab = self.create_single_tab()
        self.tabs.addTab(single_tab, "Single Request")
        
        # Tab 2: Batch Processing
        batch_tab = self.create_batch_tab()
        self.tabs.addTab(batch_tab, "Batch Processing")
        
        # Tab 3: Results
        results_tab = self.create_results_tab()
        self.tabs.addTab(results_tab, "Results")
        
        return self.tabs
    
    def create_single_tab(self):
        """Create single request tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Scrollable parameters area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.params_widget = QWidget()
        self.params_widget.setMinimumWidth(500)
        self.params_layout = QVBoxLayout(self.params_widget)
        self.params_layout.setSpacing(0)
        self.params_layout.setContentsMargins(15, 15, 15, 15)
        self.params_layout.addWidget(QLabel("Select a model to see parameters"))
        self.params_layout.addStretch()
        
        scroll.setWidget(self.params_widget)
        layout.addWidget(scroll, 1)  # Give it stretch factor
        
        return widget
    
    def create_batch_tab(self):
        """Create batch processing tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Label
        label = QLabel("📝 Batch Input (JSON format - one request per line)")
        label.setObjectName("sectionLabel")
        layout.addWidget(label)
        
        # Text input
        self.batch_input = QTextEdit()
        self.batch_input.setPlaceholderText('{"prompt": "example", "aspect_ratio": "16:9"}\n{"prompt": "another example", "aspect_ratio": "1:1"}')
        self.batch_input.textChanged.connect(self.on_batch_text_changed)
        layout.addWidget(self.batch_input)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        generate_examples_btn = QPushButton("✨ Generate 10 Examples")
        generate_examples_btn.clicked.connect(self.generate_batch_examples)
        generate_examples_btn.setStyleSheet("background-color: #89b4fa; color: #1e1e2e; font-weight: bold;")
        controls_layout.addWidget(generate_examples_btn)
        
        generate_from_folder_btn = QPushButton("📁 Generate from Folder")
        generate_from_folder_btn.clicked.connect(self.generate_from_folder)
        generate_from_folder_btn.setStyleSheet("background-color: #f9e2af; color: #1e1e2e; font-weight: bold;")
        controls_layout.addWidget(generate_from_folder_btn)
        
        load_csv_btn = QPushButton("📄 Load CSV")
        load_csv_btn.clicked.connect(self.load_csv)
        controls_layout.addWidget(load_csv_btn)
        
        load_json_btn = QPushButton("📋 Load JSON")
        load_json_btn.clicked.connect(self.load_json)
        controls_layout.addWidget(load_json_btn)
        
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self.clear_batch_input)
        controls_layout.addWidget(clear_btn)
        
        controls_layout.addStretch()
        
        # Concurrent requests
        controls_layout.addWidget(QLabel("⚡ Concurrent Requests:"))
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, 10)
        self.concurrent_spin.setValue(3)
        self.concurrent_spin.setMinimumWidth(100)
        controls_layout.addWidget(self.concurrent_spin)
        
        layout.addLayout(controls_layout)
        
        return widget
    
    def create_results_tab(self):
        """Create results tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Label
        label = QLabel("📊 Generation Results")
        label.setObjectName("sectionLabel")
        layout.addWidget(label)
        
        # Results text
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.results_text)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        save_outputs_btn = QPushButton("📥 Save All Outputs")
        save_outputs_btn.clicked.connect(self.save_all_outputs)
        save_outputs_btn.setStyleSheet("background-color: #a6e3a1; color: #1e1e2e; font-weight: bold;")
        controls_layout.addWidget(save_outputs_btn)
        
        export_btn = QPushButton("💾 Export Results JSON")
        export_btn.clicked.connect(self.export_results)
        controls_layout.addWidget(export_btn)
        
        clear_btn = QPushButton("🗑️ Clear Results")
        clear_btn.clicked.connect(self.clear_results)
        controls_layout.addWidget(clear_btn)
        
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        return widget
    
    def create_bottom_panel(self):
        """Create bottom action panel"""
        panel = QGroupBox("⚡ Actions")
        panel.setObjectName("cardGroup")
        layout = QVBoxLayout()
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("▶️  Generate Single")
        self.generate_btn.setObjectName("accentButton")
        self.generate_btn.clicked.connect(self.generate_single)
        buttons_layout.addWidget(self.generate_btn)
        
        self.batch_btn = QPushButton("🚀  Start Batch Processing")
        self.batch_btn.setObjectName("accentButton")
        self.batch_btn.clicked.connect(self.start_batch)
        buttons_layout.addWidget(self.batch_btn)
        
        self.stop_btn = QPushButton("⏹️  Stop")
        self.stop_btn.clicked.connect(self.stop_processing)
        self.stop_btn.setEnabled(False)
        buttons_layout.addWidget(self.stop_btn)
        
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        # Status
        status_label = QLabel("Status")
        status_label.setObjectName("dimLabel")
        layout.addWidget(status_label)
        
        self.status_label = QLabel("🟢 Ready to process")
        self.status_label.setObjectName("statusLabel")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        panel.setLayout(layout)
        return panel
    
    def apply_styles(self):
        """Apply modern dark theme styles"""
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 10pt;
            }
            
            #titleLabel {
                color: #89b4fa;
                font-size: 24pt;
                font-weight: bold;
            }
            
            #subtitleLabel {
                color: #9399b2;
                font-size: 10pt;
            }
            
            #sectionLabel {
                color: #cdd6f4;
                font-size: 11pt;
                font-weight: bold;
                padding: 5px 0;
            }
            
            #dimLabel {
                color: #9399b2;
                font-size: 9pt;
            }
            
            #infoLabel {
                color: #cdd6f4;
                padding: 8px;
                background-color: #2a2a3e;
                border-radius: 6px;
            }
            
            #statusLabel {
                color: #a6e3a1;
                font-size: 10pt;
                padding: 10px;
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 6px;
            }
            
            QGroupBox {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
                color: #89b4fa;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
            
            #cardGroup {
                background-color: #313244;
            }
            
            #apiGroup {
                background-color: #313244;
                padding: 15px;
            }
            
            QLineEdit, QTextEdit {
                background-color: #2a2a3e;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 8px;
                color: #cdd6f4;
                selection-background-color: #89b4fa;
                selection-color: #ffffff;
            }
            
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #89b4fa;
            }
            
            QComboBox {
                background-color: #2a2a3e;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 8px;
                color: #cdd6f4;
            }
            
            QComboBox:hover {
                border: 1px solid #89b4fa;
            }
            
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #89b4fa;
                margin-right: 5px;
            }
            
            QComboBox QAbstractItemView {
                background-color: #2a2a3e;
                border: 1px solid #45475a;
                selection-background-color: #89b4fa;
                selection-color: #ffffff;
                color: #cdd6f4;
            }
            
            QListWidget {
                background-color: #2a2a3e;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 5px;
                color: #cdd6f4;
                outline: none;
            }
            
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            
            QListWidget::item:selected {
                background-color: #89b4fa;
                color: #ffffff;
            }
            
            QListWidget::item:hover {
                background-color: #45475a;
            }
            
            QPushButton {
                background-color: #45475a;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                color: #cdd6f4;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #585b70;
            }
            
            QPushButton:pressed {
                background-color: #45475a;
            }
            
            QPushButton:disabled {
                background-color: #313244;
                color: #6c7086;
            }
            
            #accentButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                padding: 12px 24px;
                font-size: 10pt;
            }
            
            #accentButton:hover {
                background-color: #74c7ec;
            }
            
            #accentButton:pressed {
                background-color: #89b4fa;
            }
            
            QProgressBar {
                background-color: #2a2a3e;
                border: 1px solid #45475a;
                border-radius: 6px;
                text-align: center;
                color: #cdd6f4;
                height: 20px;
            }
            
            QProgressBar::chunk {
                background-color: #89b4fa;
                border-radius: 5px;
            }
            
            QTabWidget::pane {
                border: 1px solid #45475a;
                border-radius: 8px;
                background-color: #313244;
                top: -1px;
            }
            
            QTabBar::tab {
                background-color: #2a2a3e;
                color: #9399b2;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            
            QTabBar::tab:selected {
                background-color: #313244;
                color: #89b4fa;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #45475a;
            }
            
            QSpinBox {
                background-color: #2a2a3e;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 5px;
                color: #cdd6f4;
            }
            
            QSpinBox:focus {
                border: 1px solid #89b4fa;
            }
            
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #45475a;
                border: none;
                width: 20px;
            }
            
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #585b70;
            }
            
            QCheckBox {
                color: #cdd6f4;
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #45475a;
                background-color: #2a2a3e;
            }
            
            QCheckBox::indicator:checked {
                background-color: #89b4fa;
                border-color: #89b4fa;
            }
            
            QScrollBar:vertical {
                background-color: #1e1e2e;
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #45475a;
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #585b70;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar:horizontal {
                background-color: #1e1e2e;
                height: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:horizontal {
                background-color: #45475a;
                border-radius: 6px;
                min-width: 20px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background-color: #585b70;
            }
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            
            QScrollArea {
                border: none;
            }
            
            QSplitter::handle {
                background-color: #45475a;
                width: 2px;
            }
            
            QSplitter::handle:hover {
                background-color: #89b4fa;
            }
        """)
    
    def load_models(self):
        """Load models from API"""
        self.status_label.setText("⏳ Loading models...")
        
        class ModelLoader(QThread):
            finished_signal = Signal(list)
            error_signal = Signal(str)
            
            def __init__(self, api_base):
                super().__init__()
                self.api_base = api_base
            
            def run(self):
                try:
                    response = requests.get(f"{self.api_base}/api/models", timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    if not data.get("success"):
                        self.error_signal.emit("Failed to load models")
                        return
                    
                    models = data.get("data", [])
                    self.finished_signal.emit(models)
                    
                except Exception as e:
                    self.error_signal.emit(str(e))
        
        def on_loaded(models):
            self.models = models
            
            # Organize by category
            self.categories = {}
            for model in self.models:
                category = model.get("category", "other")
                if category not in self.categories:
                    self.categories[category] = []
                self.categories[category].append(model)
            
            self.populate_categories()
            self.status_label.setText(f"✅ Loaded {len(self.models)} models")
        
        def on_error(error_msg):
            QMessageBox.critical(self, "Error", f"Failed to load models: {error_msg}")
            self.status_label.setText("❌ Error loading models")
        
        self.model_loader = ModelLoader(self.api_base)
        self.model_loader.finished_signal.connect(on_loaded)
        self.model_loader.error_signal.connect(on_error)
        self.model_loader.start()
    
    def populate_categories(self):
        """Populate category dropdown"""
        self.category_combo.clear()
        categories = sorted(self.categories.keys())
        self.category_combo.addItems(categories)
    
    def on_category_changed(self, category):
        """Handle category change"""
        self.model_list.clear()
        if category in self.categories:
            for model in self.categories[category]:
                self.model_list.addItem(model.get("name", "Unknown"))
    
    def on_model_selected(self, index):
        """Handle model selection"""
        if index < 0:
            return
        
        category = self.category_combo.currentText()
        if category not in self.categories:
            return
        
        model = self.categories[category][index]
        self.current_model = model  # Store the selected model
        self.model_info.setText(model.get("description", "No description available"))
        
        # Load schema
        self.load_schema(model.get("category"), model.get("subcategory"))
    
    def load_schema(self, category, subcategory):
        """Load schema for selected model"""
        self.status_label.setText(f"⏳ Loading schema for {category}/{subcategory}...")
        
        class SchemaLoader(QThread):
            finished_signal = Signal(dict)
            error_signal = Signal(str)
            
            def __init__(self, api_base, category, subcategory):
                super().__init__()
                self.api_base = api_base
                self.category = category
                self.subcategory = subcategory
            
            def run(self):
                try:
                    url = f"{self.api_base}/api/schema/{self.category}/{self.subcategory}"
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    if data.get("success"):
                        self.finished_signal.emit(data.get("data", {}))
                    else:
                        self.error_signal.emit("Failed to load schema")
                        
                except Exception as e:
                    self.error_signal.emit(str(e))
        
        def on_schema_loaded(schema):
            self.current_schema = schema
            self.build_parameter_form()
            self.status_label.setText("✅ Schema loaded")
        
        def on_schema_error(error_msg):
            self.status_label.setText(f"❌ Error: {error_msg}")
        
        self.schema_loader = SchemaLoader(self.api_base, category, subcategory)
        self.schema_loader.finished_signal.connect(on_schema_loaded)
        self.schema_loader.error_signal.connect(on_schema_error)
        self.schema_loader.start()
    
    def build_parameter_form(self):
        """Build dynamic form based on schema"""
        # Clear existing widgets
        while self.params_layout.count():
            item = self.params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.param_widgets = {}
        
        if not self.current_schema:
            self.params_layout.addWidget(QLabel("No schema available"))
            self.params_layout.addStretch()
            return
        
        parameters = self.current_schema.get("parameters", {})
        
        # Required parameters
        if parameters.get("required"):
            req_label = QLabel("Required Parameters")
            req_label.setObjectName("sectionLabel")
            self.params_layout.addWidget(req_label)
            
            for param in parameters["required"]:
                self.create_parameter_widget(param, required=True)
        
        # Optional parameters
        if parameters.get("optional"):
            opt_label = QLabel("Optional Parameters")
            opt_label.setObjectName("sectionLabel")
            self.params_layout.addWidget(opt_label)
            
            for param in parameters["optional"]:
                self.create_parameter_widget(param, required=False)
        
        self.params_layout.addStretch()
    
    def create_parameter_widget(self, param, required=False):
        """Create a widget for a parameter"""
        name = param.get("name", "")
        param_type = param.get("type", "string")
        description = param.get("description", "")
        default = param.get("default")
        allowed_values = param.get("allowedValues", [])
        # Support both 'min'/'max' and 'minimum'/'maximum'
        min_val = param.get("min") or param.get("minimum")
        max_val = param.get("max") or param.get("maximum")
        step = param.get("step")
        
        # Check if this is an array of files
        items = param.get("items", {})
        max_items = param.get("maxItems")
        is_array_of_files = (param_type == "array" and 
                            items.get("format") == "uri" and 
                            items.get("fileType") in ["image", "video", "audio"])
        
        # Container with fixed spacing
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 15)
        layout.setSpacing(8)
        
        # Label with range info
        label_text = f"{name}{'*' if required else ''}"
        if min_val is not None and max_val is not None:
            label_text += f" ({min_val} - {max_val})"
        label = QLabel(label_text)
        label.setMinimumHeight(20)
        if required:
            label.setStyleSheet("color: #89b4fa; font-weight: bold; min-height: 20px;")
        layout.addWidget(label)
        
        # Widget
        widget = None
        value_label = None
        
        if is_array_of_files:
            # Array of file uploads (e.g., maxItems: 4)
            array_container = QWidget()
            array_layout = QVBoxLayout(array_container)
            array_layout.setContentsMargins(0, 0, 0, 0)
            array_layout.setSpacing(5)
            
            file_inputs = []
            num_inputs = max_items if max_items else 4  # Default to 4 if not specified
            
            for i in range(num_inputs):
                file_row = QHBoxLayout()
                
                file_input = QLineEdit()
                file_input.setPlaceholderText(f"File {i+1} (optional)" if i > 0 else f"File {i+1}")
                file_row.addWidget(file_input, 3)
                
                browse_btn = QPushButton("📁")
                browse_btn.setMaximumWidth(40)
                browse_btn.clicked.connect(lambda checked, fi=file_input: self.browse_file(fi))
                file_row.addWidget(browse_btn)
                
                array_layout.addLayout(file_row)
                file_inputs.append(file_input)
            
            widget = array_container
            # Store reference to all file inputs for this array parameter
            self.param_widgets[name] = {
                "widget": widget,
                "type": param_type,
                "required": required,
                "is_array": True,
                "file_inputs": file_inputs
            }
            
        elif param_type == "enum" and allowed_values:
            widget = QComboBox()
            widget.addItems([str(v) for v in allowed_values])
            if default:
                widget.setCurrentText(str(default))
        elif param_type == "boolean":
            widget = QCheckBox("Enable")
            if default is not None:
                widget.setChecked(default)
        elif param_type in ["integer", "number"] and min_val is not None and max_val is not None:
            # Use slider + spinbox for numeric values with min/max
            slider_container = QWidget()
            slider_layout = QHBoxLayout(slider_container)
            slider_layout.setContentsMargins(0, 0, 0, 0)
            
            if param_type == "integer":
                # Integer slider
                slider = QSlider(Qt.Orientation.Horizontal)
                slider.setMinimum(int(min_val))
                slider.setMaximum(int(max_val))
                if step:
                    slider.setSingleStep(int(step))
                if default:
                    slider.setValue(int(default))
                else:
                    slider.setValue(int(min_val))
                
                spinbox = QSpinBox()
                spinbox.setMinimum(int(min_val))
                spinbox.setMaximum(int(max_val))
                if step:
                    spinbox.setSingleStep(int(step))
                if default:
                    spinbox.setValue(int(default))
                else:
                    spinbox.setValue(int(min_val))
                
                # Connect slider and spinbox
                slider.valueChanged.connect(spinbox.setValue)
                spinbox.valueChanged.connect(slider.setValue)
                
            else:
                # Float slider (using QSlider with scaling)
                slider = QSlider(Qt.Orientation.Horizontal)
                scale = 100  # Scale for float precision
                slider.setMinimum(int(min_val * scale))
                slider.setMaximum(int(max_val * scale))
                if step:
                    slider.setSingleStep(int(step * scale))
                if default:
                    slider.setValue(int(default * scale))
                else:
                    slider.setValue(int(min_val * scale))
                
                spinbox = QDoubleSpinBox()
                spinbox.setMinimum(float(min_val))
                spinbox.setMaximum(float(max_val))
                if step:
                    spinbox.setSingleStep(float(step))
                else:
                    spinbox.setSingleStep(0.01)
                spinbox.setDecimals(2)
                if default:
                    spinbox.setValue(float(default))
                else:
                    spinbox.setValue(float(min_val))
                
                # Connect slider and spinbox with scaling
                slider.valueChanged.connect(lambda v: spinbox.setValue(v / scale))
                spinbox.valueChanged.connect(lambda v: slider.setValue(int(v * scale)))
            
            slider_layout.addWidget(slider, 3)
            slider_layout.addWidget(spinbox, 1)
            widget = slider_container
            
        elif param_type == "integer":
            widget = QSpinBox()
            widget.setMaximum(999999)
            if default:
                widget.setValue(int(default))
            widget.setMinimumWidth(150)
        else:
            # Check if this is a file upload field (format: uri)
            param_format = param.get("format")
            file_type = param.get("fileType")
            is_file_field = param_format == "uri" or file_type in ["image", "video", "audio"]
            
            if is_file_field:
                # Create file upload widget
                file_container = QWidget()
                file_layout = QHBoxLayout(file_container)
                file_layout.setContentsMargins(0, 0, 0, 0)
                
                file_input = QLineEdit()
                file_input.setPlaceholderText("Select file or enter URL...")
                if default:
                    file_input.setText(str(default))
                file_layout.addWidget(file_input, 3)
                
                browse_btn = QPushButton("📁 Browse")
                browse_btn.clicked.connect(lambda checked, fi=file_input: self.browse_file(fi))
                file_layout.addWidget(browse_btn, 1)
                
                widget = file_container
            elif len(description) > 100:
                widget = QTextEdit()
                widget.setMaximumHeight(100)
                if default:
                    widget.setText(str(default))
            else:
                widget = QLineEdit()
                if default:
                    widget.setText(str(default))
                widget.setPlaceholderText(f"Enter {name}")
        
        layout.addWidget(widget)
        
        # Description with proper spacing
        if description:
            desc = QLabel(description)
            desc.setObjectName("dimLabel")
            desc.setWordWrap(True)
            desc.setMinimumHeight(30)
            desc.setMaximumWidth(600)
            layout.addWidget(desc)
            layout.addSpacing(5)
        
        # Add separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setMaximumHeight(1)
        layout.addWidget(separator)
        
        self.params_layout.addWidget(container)
        
        # Only store if not already stored (array files store themselves earlier)
        if name not in self.param_widgets:
            self.param_widgets[name] = {
                "widget": widget,
                "type": param_type,
                "required": required,
                "min": min_val,
                "max": max_val,
                "step": step
            }
    
    def browse_file(self, line_edit):
        """Browse for file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, 
            "Select File",
            "",
            "All Files (*);;Images (*.png *.jpg *.jpeg *.webp *.gif);;Videos (*.mp4 *.webm *.mov)"
        )
        if filename:
            line_edit.setText(filename)
    
    def get_parameters(self):
        """Get parameters from form"""
        params = {}
        
        for name, info in self.param_widgets.items():
            widget = info["widget"]
            param_type = info["type"]
            required = info["required"]
            is_array = info.get("is_array", False)
            
            # Get value
            value = None
            
            if is_array:
                # Handle array of files
                file_inputs = info.get("file_inputs", [])
                array_values = []
                for file_input in file_inputs:
                    file_path = file_input.text().strip()
                    if file_path:  # Only add non-empty values
                        array_values.append(file_path)
                
                if array_values:
                    value = array_values
                elif required:
                    raise ValueError(f"Required array field '{name}' must have at least one file")
                    
            elif isinstance(widget, QComboBox):
                value = widget.currentText()
            elif isinstance(widget, QCheckBox):
                value = widget.isChecked()
            elif isinstance(widget, QSpinBox):
                value = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                value = widget.value()
            elif isinstance(widget, QWidget):
                # Check if it's a file upload container or slider container
                widget_layout = widget.layout()
                if widget_layout and widget_layout.count() >= 2:
                    first_widget = widget_layout.itemAt(0).widget()
                    if isinstance(first_widget, QLineEdit):
                        # File upload container
                        value = first_widget.text().strip()
                    else:
                        # Slider container
                        spinbox = widget_layout.itemAt(1).widget()
                        if isinstance(spinbox, (QSpinBox, QDoubleSpinBox)):
                            value = spinbox.value()
            elif isinstance(widget, QTextEdit):
                value = widget.toPlainText().strip()
            elif isinstance(widget, QLineEdit):
                value = widget.text().strip()
            
            # Check required
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
            
            uid = self.uid_input.text().strip()
            api_key = self.api_key_input.text().strip()
            
            if not uid:
                QMessageBox.warning(self, "Warning", "Please enter your UID")
                return
            
            if not api_key:
                QMessageBox.warning(self, "Warning", "Please enter your API key")
                return
            
            if not self.current_schema:
                QMessageBox.warning(self, "Warning", "Please select a model first")
                return
            
            category = self.current_schema.get("category")
            subcategory = self.current_schema.get("subcategory")
            
            # Disable buttons
            self.generate_btn.setEnabled(False)
            self.batch_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            
            # Create worker
            self.worker = APIWorker(self.api_base, uid, api_key, category, subcategory, params)
            self.worker.status_update.connect(self.status_label.setText)
            self.worker.progress_update.connect(self.progress_bar.setValue)
            self.worker.result_ready.connect(self.display_result)
            self.worker.error_occurred.connect(self.on_error)
            self.worker.finished.connect(self.on_worker_finished)
            self.worker.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Invalid parameters: {str(e)}")
    
    def display_result(self, result):
        """Display result"""
        self.tabs.setCurrentIndex(2)
        
        result_text = json.dumps(result, indent=2)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.results_text.append(f"\n{'='*80}\n")
        self.results_text.append(f"Result at {timestamp}\n")
        self.results_text.append(f"{'='*80}\n")
        self.results_text.append(f"{result_text}\n")
        
        self.results.append({"timestamp": timestamp, "result": result})
        self.status_label.setText("✅ Generation complete")
    
    def on_error(self, error_msg):
        """Handle error"""
        QMessageBox.critical(self, "Error", f"Generation failed: {error_msg}")
        self.status_label.setText(f"❌ Error: {error_msg}")
    
    def on_worker_finished(self):
        """Handle worker completion"""
        self.generate_btn.setEnabled(True)
        self.batch_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.worker = None
    
    def stop_processing(self):
        """Stop processing"""
        if self.worker:
            self.worker.stop()
            self.status_label.setText("⏹️ Stopping single request...")
        
        if self.batch_worker:
            self.batch_worker.stop()
            self.status_label.setText("⏹️ Stopping batch processing...")
            self.stop_btn.setEnabled(False)
    
    def start_batch(self):
        """Start batch processing"""
        try:
            # Check if we have stored batch data with base64 (from folder generation)
            if self.batch_json_data:
                # Use the stored data with actual base64
                batch_data = []
                for line in self.batch_json_data:
                    try:
                        data = json.loads(line)
                        batch_data.append(data)
                    except json.JSONDecodeError as e:
                        QMessageBox.warning(self, "Invalid JSON", f"Error parsing stored data: {str(e)}")
                        return
            else:
                # Parse from text input (manual entry)
                batch_text = self.batch_input.toPlainText().strip()
                if not batch_text:
                    QMessageBox.warning(self, "No Input", "Please enter batch data (one JSON per line)")
                    return
                
                # Try to parse as JSON array first
                batch_data = []
                try:
                    # Check if it's a JSON array
                    if batch_text.startswith('['):
                        batch_data = json.loads(batch_text)
                        if not isinstance(batch_data, list):
                            raise ValueError("Expected JSON array")
                        # Convert file placeholders for each item
                        batch_data = [self.convert_file_placeholders_to_base64(item) for item in batch_data]
                    else:
                        # Parse as newline-delimited JSON
                        # Use a smarter approach: collect complete JSON objects
                        import re
                        # Find all complete JSON objects
                        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                        matches = re.findall(json_pattern, batch_text, re.DOTALL)
                        
                        for match in matches:
                            try:
                                data = json.loads(match)
                                # Convert [FILE: ...] placeholders to base64
                                data = self.convert_file_placeholders_to_base64(data)
                                batch_data.append(data)
                            except json.JSONDecodeError:
                                pass
                        
                        if not batch_data:
                            # Fallback: try line by line
                            lines = batch_text.split('\n')
                            for i, line in enumerate(lines):
                                line = line.strip()
                                if not line or not line.startswith('{'):
                                    continue
                                try:
                                    data = json.loads(line)
                                    data = self.convert_file_placeholders_to_base64(data)
                                    batch_data.append(data)
                                except json.JSONDecodeError:
                                    pass
                    
                except Exception as e:
                    QMessageBox.warning(self, "Invalid JSON", f"Failed to parse batch data: {str(e)}")
                    return
            
            if not batch_data:
                QMessageBox.warning(self, "No Data", "No valid JSON entries found")
                return
            
            # Check credentials
            uid = self.uid_input.text().strip()
            api_key = self.api_key_input.text().strip()
            
            if not uid:
                QMessageBox.warning(self, "Missing UID", "Please enter your UID")
                return
            
            if not api_key:
                QMessageBox.warning(self, "Missing API Key", "Please enter your API Key")
                return
            
            # Check model selected
            if not self.current_model:
                QMessageBox.warning(self, "No Model", "Please select a model first")
                return
            
            category = self.current_model.get("category")
            subcategory = self.current_model.get("subcategory")
            
            # Clear results
            self.batch_results = []  # Clear previous batch results
            self.results_text.clear()
            self.results_text.append(f"🚀 Starting batch processing: {len(batch_data)} requests\n")
            self.results_text.append(f"Model: {category}/{subcategory}\n")
            self.results_text.append(f"Concurrent requests: {self.concurrent_spin.value()}\n")
            self.results_text.append("="*80 + "\n")
            
            # Start batch worker
            self.batch_worker = BatchWorker(
                self.api_base,
                uid,
                api_key,
                category,
                subcategory,
                batch_data,
                self.concurrent_spin.value()
            )
            
            self.batch_worker.progress_update.connect(self.on_batch_progress)
            self.batch_worker.result_ready.connect(self.on_batch_result)
            self.batch_worker.finished.connect(self.on_batch_finished)
            self.batch_worker.error.connect(self.on_batch_error)
            
            self.batch_worker.start()
            self.status_label.setText("⏳ Batch processing in progress...")
            
            # Enable stop button
            self.stop_btn.setEnabled(True)
            self.batch_btn.setEnabled(False)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start batch: {str(e)}")
    
    def on_batch_progress(self, message):
        """Handle batch progress updates"""
        self.status_label.setText(message)
    
    def on_batch_result(self, index, params, result):
        """Handle individual batch result"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Store result for later download
        self.batch_results.append({
            "index": index,
            "params": params,
            "result": result,
            "timestamp": timestamp
        })
        
        self.results_text.append(f"\n{'='*80}")
        self.results_text.append(f"✅ Request #{index + 1} completed at {timestamp}")
        self.results_text.append(f"{'='*80}")
        
        # Show clean parameters (hide base64)
        clean_params = self.clean_params_for_display(params)
        self.results_text.append(f"\n📝 Parameters:")
        self.results_text.append(json.dumps(clean_params, indent=2))
        
        # Show clean result (hide base64, show output URLs)
        self.results_text.append(f"\n📊 Result:")
        if "output" in result:
            outputs = result.get("output", [])
            if isinstance(outputs, list):
                self.results_text.append(f"  Generated {len(outputs)} output(s):")
                for i, url in enumerate(outputs):
                    self.results_text.append(f"    {i+1}. {url}")
            else:
                self.results_text.append(f"  Output: {outputs}")
        
        # Show other important fields
        for key in ["id", "status", "message"]:
            if key in result:
                self.results_text.append(f"  {key}: {result[key]}")
        
        self.results_text.append("\n")
        
        # Auto-scroll to bottom
        self.results_text.verticalScrollBar().setValue(
            self.results_text.verticalScrollBar().maximum()
        )
    
    def on_batch_finished(self, total, successful, failed):
        """Handle batch completion"""
        self.results_text.append(f"\n{'='*80}")
        self.results_text.append(f"🎉 Batch processing completed!")
        self.results_text.append(f"{'='*80}")
        self.results_text.append(f"Total: {total} | Successful: {successful} | Failed: {failed}")
        self.status_label.setText(f"✅ Batch complete: {successful}/{total} successful")
        
        # Re-enable buttons
        self.stop_btn.setEnabled(False)
        self.batch_btn.setEnabled(True)
    
    def on_batch_error(self, index, params, error):
        """Handle batch error"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.results_text.append(f"\n{'='*80}")
        self.results_text.append(f"❌ Request #{index + 1} failed at {timestamp}")
        self.results_text.append(f"{'='*80}")
        
        # Show clean parameters (hide base64)
        clean_params = self.clean_params_for_display(params)
        self.results_text.append(f"\n📝 Parameters:")
        self.results_text.append(json.dumps(clean_params, indent=2))
        
        self.results_text.append(f"\n❌ Error: {error}")
        self.results_text.append("\n")
        
        # Auto-scroll to bottom
        self.results_text.verticalScrollBar().setValue(
            self.results_text.verticalScrollBar().maximum()
        )
    
    def generate_from_folder(self):
        """Generate batch JSON from all files in folder(s)"""
        if not self.current_schema:
            QMessageBox.warning(self, "No Schema", "Please select a model first to load its schema.")
            return
        
        # Get schema parameters FIRST
        parameters = self.current_schema.get("parameters", {})
        required_params = parameters.get("required", [])
        optional_params = parameters.get("optional", [])
        
        # Find ALL file upload fields (format: uri or array of uri)
        file_fields = []
        for param in required_params + optional_params:
            param_format = param.get("format")
            file_type = param.get("fileType")
            param_type = param.get("type")
            
            # Check if single file field
            if param_format == "uri" or file_type in ["image", "video", "audio"]:
                file_fields.append({
                    "name": param.get("name"),
                    "type": file_type,
                    "description": param.get("description", ""),
                    "is_array": False,
                    "max_items": None
                })
            # Check if array of files
            elif param_type == "array":
                items = param.get("items", {})
                if items.get("format") == "uri" or items.get("fileType") in ["image", "video", "audio"]:
                    file_fields.append({
                        "name": param.get("name"),
                        "type": items.get("fileType"),
                        "description": param.get("description", ""),
                        "is_array": True,
                        "max_items": param.get("maxItems", 4)
                    })
        
        if not file_fields:
            QMessageBox.warning(self, "No File Field", 
                              "This model doesn't have a file upload field.\n\n" +
                              "This feature is for models that accept image/video inputs.")
            return
        
        # If multiple file fields, show selection dialog
        if len(file_fields) > 1:
            self.generate_from_multiple_folders(file_fields)
        else:
            self.generate_from_single_folder(file_fields[0])
    
    def clean_params_for_display(self, params):
        """Clean parameters for display - replace base64 with [BASE64_DATA] or filename"""
        import os
        
        def clean_value(value):
            if isinstance(value, str):
                if value.startswith("data:"):
                    # It's a base64 data URI
                    mime_part = value.split(';')[0].split(':')[1] if ':' in value and ';' in value else "unknown"
                    return f"[BASE64: {mime_part}]"
                return value
            elif isinstance(value, list):
                return [clean_value(item) for item in value]
            elif isinstance(value, dict):
                return {k: clean_value(v) for k, v in value.items()}
            return value
        
        return clean_value(params)
    
    def convert_file_placeholders_to_base64(self, data):
        """Convert [FILE: path] placeholders to base64 in a dict"""
        import re
        
        def convert_value(value):
            if isinstance(value, str) and value.startswith("[FILE: ") and value.endswith("]"):
                # Extract file path
                filepath = value[7:-1]  # Remove "[FILE: " and "]"
                try:
                    return self.file_to_base64(filepath)
                except Exception as e:
                    return value  # Return as-is if conversion fails
            elif isinstance(value, list):
                # Recursively convert list items
                return [convert_value(item) for item in value]
            elif isinstance(value, dict):
                # Recursively convert dict values
                return {k: convert_value(v) for k, v in value.items()}
            return value
        
        return convert_value(data)
    
    def file_to_base64(self, filepath):
        """Convert file to base64 data URI"""
        import base64
        import mimetypes
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(filepath)
        if not mime_type:
            # Default based on extension
            ext = filepath.lower().split('.')[-1]
            mime_map = {
                'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
                'webp': 'image/webp', 'gif': 'image/gif',
                'mp4': 'video/mp4', 'webm': 'video/webm', 'mov': 'video/quicktime',
                'mp3': 'audio/mpeg', 'wav': 'audio/wav', 'ogg': 'audio/ogg'
            }
            mime_type = mime_map.get(ext, 'application/octet-stream')
        
        # Read and encode file
        with open(filepath, 'rb') as f:
            file_data = f.read()
            base64_data = base64.b64encode(file_data).decode('utf-8')
        
        # Return data URI
        return f"data:{mime_type};base64,{base64_data}"
    
    def get_files_from_folder(self, folder, file_type):
        """Get all files of specified type from folder (cross-platform, no duplicates)"""
        import os
        import glob
        
        # Find ALL files based on fileType
        if file_type == "image":
            extensions = ['png', 'jpg', 'jpeg', 'webp', 'gif']
        elif file_type == "video":
            extensions = ['mp4', 'webm', 'mov', 'avi']
        elif file_type == "audio":
            extensions = ['mp3', 'wav', 'ogg', 'm4a']
        else:
            # Default: all media types
            extensions = ['png', 'jpg', 'jpeg', 'webp', 'gif', 'mp4', 'webm', 'mov', 'mp3', 'wav']
        
        all_files = set()  # Use set to avoid duplicates (Windows case-insensitivity)
        
        for ext in extensions:
            # Search for both lowercase and uppercase variants
            for pattern in [f'*.{ext}', f'*.{ext.upper()}']:
                all_files.update(glob.glob(os.path.join(folder, pattern)))
        
        # Convert back to sorted list
        all_files = sorted(list(all_files))
        return all_files
    
    def generate_from_single_folder(self, file_field):
        """Generate from single or multiple folders for one file field"""
        if file_field['is_array'] and file_field['max_items']:
            # Array field: select multiple folders (one per array element)
            self.select_folders_for_array_field(file_field)
        else:
            # Single file field: select one folder
            folder = QFileDialog.getExistingDirectory(self, f"Select Folder with {file_field['type'] or 'Media'} Files")
            if not folder:
                return
            
            all_files = self.get_files_from_folder(folder, file_field['type'])
            
            if not all_files:
                QMessageBox.warning(self, "No Files", f"No {file_field['type'] or 'media'} files found in the selected folder.")
                return
            
            self.status_label.setText(f"⏳ Converting {len(all_files)} files to base64...")
            
            # Generate JSON entries with base64
            field_info = {
                file_field['name']: {
                    'files': all_files,
                    'is_array': False,
                    'max_items': None
                }
            }
            self.generate_json_from_files(field_info)
    
    def select_folders_for_array_field(self, file_field):
        """Select separate folders for each element of array field"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Select Folders for {file_field['name']} Array")
        dialog.setMinimumWidth(700)
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel(f"This field accepts an array of up to {file_field['max_items']} {file_field['type']} files.\n" +
                               "Select a folder for each element:"))
        layout.addSpacing(10)
        
        folder_inputs = []
        for i in range(file_field['max_items']):
            field_layout = QHBoxLayout()
            
            label = QLabel(f"Element {i+1}:")
            label.setMinimumWidth(100)
            field_layout.addWidget(label)
            
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(f"Folder for element {i+1} (optional)" if i > 0 else f"Folder for element {i+1}")
            line_edit.setReadOnly(True)
            field_layout.addWidget(line_edit, 1)
            
            browse_btn = QPushButton("📁 Browse")
            browse_btn.clicked.connect(lambda checked, le=line_edit, ft=file_field['type']: self.browse_folder_for_field(le, ft))
            field_layout.addWidget(browse_btn)
            
            layout.addLayout(field_layout)
            folder_inputs.append(line_edit)
        
        layout.addSpacing(20)
        
        buttons = QHBoxLayout()
        ok_btn = QPushButton("✅ Generate JSON")
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get files from each folder (each represents one array element)
            element_files = []  # List of file lists
            for line_edit in folder_inputs:
                folder = line_edit.text()
                if folder:
                    files = self.get_files_from_folder(folder, file_field['type'])
                    if files:
                        element_files.append(files)
            
            if not element_files:
                QMessageBox.warning(self, "No Files", "No files found in any selected folder.")
                return
            
            # Generate JSON with array structure
            self.generate_json_from_array_folders(file_field, element_files)
    
    def generate_json_from_array_folders(self, file_field, element_files):
        """Generate JSON from array field with separate folders per element
        
        Args:
            file_field: Field metadata {'name', 'type', 'max_items', ...}
            element_files: List of file lists, e.g., [[folder1_files], [folder2_files], ...]
        """
        # Get schema parameters
        parameters = self.current_schema.get("parameters", {})
        required_params = parameters.get("required", [])
        optional_params = parameters.get("optional", [])
        
        # Determine number of entries (minimum files across all folders)
        num_entries = min(len(files) for files in element_files)
        
        if num_entries == 0:
            QMessageBox.warning(self, "No Files", "No files to process.")
            return
        
        example_prompts = [
            "enhance this", "improve the quality", "make it more vibrant",
            "add more details", "enhance colors", "improve lighting",
            "make it sharper", "enhance the scene", "improve composition",
            "add artistic style"
        ]
        
        examples = []
        display_examples = []
        
        for i in range(num_entries):
            example = {}
            display_example = {}
            
            # Build array from each folder's i-th file
            base64_array = []
            display_array = []
            
            for folder_files in element_files:
                if i < len(folder_files):
                    try:
                        base64_data = self.file_to_base64(folder_files[i])
                        base64_array.append(base64_data)
                        display_array.append(f"[FILE: {folder_files[i]}]")
                    except Exception as e:
                        QMessageBox.warning(self, "Error", f"Failed to convert {folder_files[i]}: {str(e)}")
                        return
            
            example[file_field['name']] = base64_array
            display_example[file_field['name']] = display_array
            
            # Add required parameters
            for param in required_params:
                name = param.get("name")
                if name == file_field['name']:
                    continue
                
                param_type = param.get("type")
                value = None
                if "prompt" in name.lower():
                    value = example_prompts[i % len(example_prompts)]
                elif param_type == "string":
                    value = f"example_{i+1}"
                elif param_type == "integer":
                    min_val = param.get("min") or param.get("minimum", 1)
                    max_val = param.get("max") or param.get("maximum", 10)
                    value = min_val + (i % (max_val - min_val + 1))
                
                if value is not None:
                    example[name] = value
                    display_example[name] = value
            
            # Add optional parameters
            for param in optional_params[:2]:
                name = param.get("name")
                if name == file_field['name']:
                    continue
                
                param_type = param.get("type")
                default = param.get("default")
                allowed_values = param.get("allowedValues", [])
                value = None
                
                if param_type == "enum" and allowed_values:
                    value = allowed_values[i % len(allowed_values)]
                elif default is not None:
                    value = default
                
                if value is not None:
                    example[name] = value
                    display_example[name] = value
            
            examples.append(json.dumps(example))
            display_examples.append(json.dumps(display_example))
            
            # Update progress
            if (i + 1) % 10 == 0:
                self.status_label.setText(f"⏳ Processing {i+1}/{num_entries}...")
        
        # Store and display
        self.batch_json_data = examples
        display_text = "\n".join(display_examples)
        self.batch_input.setPlainText(display_text)
        self.status_label.setText(f"✅ Generated {len(examples)} entries with base64 arrays")
        
        QMessageBox.information(
            self,
            "Success",
            f"Generated {len(examples)} batch entries!\n\n" +
            f"Array field: {file_field['name']}\n" +
            f"Elements per entry: {len(element_files)}\n" +
            f"Files per element: {num_entries}\n\n" +
            "Files converted to base64 arrays (shown as filenames).\n" +
            "Review the JSON and click 'Start Batch Processing' when ready."
        )
    
    def generate_from_multiple_folders(self, file_fields):
        """Generate from multiple folders for multiple file fields"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Folders for Each File Field")
        dialog.setMinimumWidth(600)
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel("This model has multiple file input fields.\nSelect a folder for each:"))
        layout.addSpacing(10)
        
        folder_inputs = {}
        for field in file_fields:
            field_layout = QHBoxLayout()
            
            label = QLabel(f"{field['name']} ({field['type'] or 'file'}):")
            label.setMinimumWidth(200)
            field_layout.addWidget(label)
            
            line_edit = QLineEdit()
            line_edit.setPlaceholderText("No folder selected")
            line_edit.setReadOnly(True)
            field_layout.addWidget(line_edit, 1)
            
            browse_btn = QPushButton("📁 Browse")
            browse_btn.clicked.connect(lambda checked, le=line_edit, ft=field['type']: self.browse_folder_for_field(le, ft))
            field_layout.addWidget(browse_btn)
            
            layout.addLayout(field_layout)
            folder_inputs[field['name']] = {
                'line_edit': line_edit,
                'type': field['type']
            }
        
        layout.addSpacing(20)
        
        buttons = QHBoxLayout()
        ok_btn = QPushButton("✅ Generate JSON")
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get files from all folders
            field_info = {}
            for field_name, inp_info in folder_inputs.items():
                folder = inp_info['line_edit'].text()
                if folder:
                    files = self.get_files_from_folder(folder, inp_info['type'])
                    if files:
                        # Find the field metadata
                        field_metadata = next((f for f in file_fields if f['name'] == field_name), None)
                        if field_metadata:
                            field_info[field_name] = {
                                'files': files,
                                'is_array': field_metadata['is_array'],
                                'max_items': field_metadata['max_items']
                            }
            
            if not field_info:
                QMessageBox.warning(self, "No Files", "No files found in any selected folder.")
                return
            
            self.status_label.setText(f"⏳ Converting files to base64...")
            self.generate_json_from_files(field_info)
    
    def browse_folder_for_field(self, line_edit, file_type):
        """Browse folder for a specific file field"""
        folder = QFileDialog.getExistingDirectory(self, f"Select Folder with {file_type or 'Media'} Files")
        if folder:
            line_edit.setText(folder)
    
    def generate_json_from_files(self, field_info):
        """Generate JSON from files dict {field_name: {'files': [], 'is_array': bool, 'max_items': int}}"""
        # Get schema parameters
        parameters = self.current_schema.get("parameters", {})
        required_params = parameters.get("required", [])
        optional_params = parameters.get("optional", [])
        
        # Determine number of entries based on field type
        # For array fields: divide files by max_items
        # For single fields: one entry per file
        min_entries = float('inf')
        for field_name, info in field_info.items():
            files = info['files']
            is_array = info['is_array']
            max_items = info['max_items']
            
            if is_array and max_items:
                # Array field: each entry can have up to max_items files
                num_possible = len(files) // max_items
                if num_possible < min_entries:
                    min_entries = num_possible
            else:
                # Single field: one file per entry
                if len(files) < min_entries:
                    min_entries = len(files)
        
        num_entries = int(min_entries) if min_entries != float('inf') else 0
        
        if num_entries == 0:
            QMessageBox.warning(self, "No Files", "No files to process.")
            return
        
        example_prompts = [
            "enhance this", "improve the quality", "make it more vibrant",
            "add more details", "enhance colors", "improve lighting",
            "make it sharper", "enhance the scene", "improve composition",
            "add artistic style"
        ]
        
        examples = []
        display_examples = []  # For UI display with filenames
        
        for i in range(num_entries):
            example = {}
            display_example = {}
            
            # Add file fields as base64
            for field_name, info in field_info.items():
                files = info['files']
                is_array = info['is_array']
                max_items = info['max_items']
                
                if is_array and max_items:
                    # Array field: take max_items files starting from i * max_items
                    start_idx = i * max_items
                    end_idx = start_idx + max_items
                    chunk_files = files[start_idx:end_idx]
                    
                    try:
                        base64_array = []
                        display_array = []
                        for file_path in chunk_files:
                            base64_data = self.file_to_base64(file_path)
                            base64_array.append(base64_data)
                            display_array.append(f"[FILE: {file_path}]")
                        
                        example[field_name] = base64_array
                        display_example[field_name] = display_array
                    except Exception as e:
                        QMessageBox.warning(self, "Error", f"Failed to convert files: {str(e)}")
                        return
                else:
                    # Single file field
                    if i < len(files):
                        try:
                            base64_data = self.file_to_base64(files[i])
                            example[field_name] = base64_data
                            display_example[field_name] = f"[FILE: {files[i]}]"
                        except Exception as e:
                            QMessageBox.warning(self, "Error", f"Failed to convert {files[i]}: {str(e)}")
                            return
            
            # Add required parameters
            for param in required_params:
                name = param.get("name")
                if name in field_info:
                    continue  # Already added as file
                
                param_type = param.get("type")
                value = None
                if "prompt" in name.lower():
                    value = example_prompts[i % len(example_prompts)]
                elif param_type == "string":
                    value = f"example_{i+1}"
                elif param_type == "integer":
                    min_val = param.get("min") or param.get("minimum", 1)
                    max_val = param.get("max") or param.get("maximum", 10)
                    value = min_val + (i % (max_val - min_val + 1))
                
                if value is not None:
                    example[name] = value
                    display_example[name] = value
            
            # Add some optional parameters
            for param in optional_params[:2]:
                name = param.get("name")
                if name in field_info:
                    continue
                
                param_type = param.get("type")
                default = param.get("default")
                allowed_values = param.get("allowedValues", [])
                value = None
                
                if param_type == "enum" and allowed_values:
                    value = allowed_values[i % len(allowed_values)]
                elif default is not None:
                    value = default
                
                if value is not None:
                    example[name] = value
                    display_example[name] = value
            
            # Store actual data as single-line JSON
            examples.append(json.dumps(example))
            # Display as single-line JSON too (not pretty-printed to avoid confusion)
            display_examples.append(json.dumps(display_example))
            
            # Update progress
            if (i + 1) % 10 == 0:
                self.status_label.setText(f"⏳ Processing {i+1}/{num_entries}...")
        
        # Store actual examples with base64 for processing
        self.batch_json_data = examples
        
        # Display examples with filenames for readability
        display_text = "\n".join(display_examples)
        self.batch_input.setPlainText(display_text)
        self.status_label.setText(f"✅ Generated {len(examples)} entries with base64 data")
        
        field_names = ", ".join(field_info.keys())
        
        # Build summary message
        summary_lines = [f"Generated {len(examples)} batch entries!\n"]
        for field_name, info in field_info.items():
            if info['is_array']:
                summary_lines.append(f"{field_name}: Array field (max {info['max_items']} files per entry)")
                summary_lines.append(f"  Total files: {len(info['files'])}")
            else:
                summary_lines.append(f"{field_name}: Single file field")
                summary_lines.append(f"  Total files: {len(info['files'])}")
        
        QMessageBox.information(
            self,
            "Success",
            "\n".join(summary_lines) + "\n\n" +
            "Files converted to base64 (shown as filenames for readability).\n" +
            "Review the JSON and click 'Start Batch Processing' when ready."
        )
    
    def generate_batch_examples(self):
        """Generate 10 example JSON entries based on current schema"""
        if not self.current_schema:
            QMessageBox.warning(self, "No Schema", "Please select a model first to load its schema.")
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
        
        aspect_ratios = ["1:1", "16:9", "9:16", "4:3", "3:4"]
        
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
        self.batch_input.setPlainText("\n".join(examples))
        self.status_label.setText(f"✅ Generated 10 example entries based on {self.current_schema.get('subcategory')} schema")
    
    def load_csv(self):
        """Load CSV file"""
        filename, _ = QFileDialog.getOpenFileName(self, "Load CSV", "", "CSV Files (*.csv)")
        if filename:
            try:
                import csv
                with open(filename, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    self.batch_input.clear()
                    for row in reader:
                        self.batch_input.append(json.dumps(row))
                self.status_label.setText(f"✅ Loaded CSV: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load CSV: {str(e)}")
    
    def load_json(self):
        """Load JSON file"""
        filename, _ = QFileDialog.getOpenFileName(self, "Load JSON", "", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.batch_input.clear()
                    if isinstance(data, list):
                        for item in data:
                            self.batch_input.append(json.dumps(item))
                    else:
                        self.batch_input.append(json.dumps(data))
                self.status_label.setText(f"✅ Loaded JSON: {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load JSON: {str(e)}")
    
    def export_results(self):
        """Export results"""
        if not self.results:
            QMessageBox.information(self, "Info", "No results to export")
            return
        
        filename, _ = QFileDialog.getSaveFileName(self, "Export Results", "", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.results, f, indent=2)
                self.status_label.setText(f"✅ Results exported")
                QMessageBox.information(self, "Success", "Results exported successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")
    
    def save_all_outputs(self):
        """Save all output files from batch results"""
        if not self.batch_results:
            QMessageBox.information(self, "No Results", "No batch results to save. Run batch processing first.")
            return
        
        # Select directory
        directory = QFileDialog.getExistingDirectory(self, "Select Directory to Save Outputs")
        if not directory:
            return
        
        # Count total outputs
        total_outputs = 0
        for result_item in self.batch_results:
            result = result_item.get("result", {})
            outputs = result.get("output", [])
            if isinstance(outputs, list):
                total_outputs += len(outputs)
            elif outputs:  # Single output
                total_outputs += 1
        
        if total_outputs == 0:
            QMessageBox.information(self, "No Outputs", "No output URLs found in results.")
            return
        
        # Confirm download
        reply = QMessageBox.question(
            self, 
            "Confirm Download",
            f"Found {total_outputs} output files from {len(self.batch_results)} requests.\n\nDownload all to:\n{directory}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Start download in thread
        self.status_label.setText(f"📥 Downloading {total_outputs} files...")
        
        class DownloadWorker(QThread):
            progress = Signal(int, int, str)  # current, total, filename
            finished_signal = Signal(int, int)  # successful, failed
            
            def __init__(self, batch_results, directory):
                super().__init__()
                self.batch_results = batch_results
                self.directory = directory
                
            def run(self):
                import os
                import urllib.request
                
                successful = 0
                failed = 0
                file_index = 0
                
                for result_item in self.batch_results:
                    request_index = result_item.get("index", 0)
                    result = result_item.get("result", {})
                    outputs = result.get("output", [])
                    
                    # Handle both list and single output
                    if not isinstance(outputs, list):
                        outputs = [outputs] if outputs else []
                    
                    for output_idx, output_url in enumerate(outputs):
                        if not output_url:
                            continue
                        
                        try:
                            # Determine file extension from URL
                            ext = ".png"  # default
                            if ".jpg" in output_url or ".jpeg" in output_url:
                                ext = ".jpg"
                            elif ".mp4" in output_url:
                                ext = ".mp4"
                            elif ".gif" in output_url:
                                ext = ".gif"
                            elif ".webm" in output_url:
                                ext = ".webm"
                            
                            # Create filename
                            filename = f"request_{request_index + 1}_output_{output_idx + 1}{ext}"
                            filepath = os.path.join(self.directory, filename)
                            
                            # Download
                            self.progress.emit(file_index + 1, len(self.batch_results) * len(outputs), filename)
                            urllib.request.urlretrieve(output_url, filepath)
                            
                            successful += 1
                            
                        except Exception as e:
                            failed += 1
                        
                        file_index += 1
                
                self.finished_signal.emit(successful, failed)
        
        def on_download_progress(current, total, filename):
            self.status_label.setText(f"📥 Downloading {current}/{total}: {filename}")
        
        def on_download_finished(successful, failed):
            self.status_label.setText(f"✅ Download complete: {successful} successful, {failed} failed")
            QMessageBox.information(
                self, 
                "Download Complete",
                f"Successfully downloaded: {successful}\nFailed: {failed}\n\nSaved to: {directory}"
            )
        
        self.download_worker = DownloadWorker(self.batch_results, directory)
        self.download_worker.progress.connect(on_download_progress)
        self.download_worker.finished_signal.connect(on_download_finished)
        self.download_worker.start()
    
    def on_batch_text_changed(self):
        """Handle batch text changes - clear stored base64 data"""
        # When user manually edits, clear the stored base64 data
        # It will be regenerated from the text when batch starts
        self.batch_json_data = None
    
    def clear_batch_input(self):
        """Clear batch input and stored data"""
        self.batch_input.clear()
        self.batch_json_data = None
        self.status_label.setText("✅ Batch input cleared")
    
    def clear_results(self):
        """Clear results"""
        self.results_text.clear()
        self.results = []
        self.batch_results = []
        self.status_label.setText("✅ Results cleared")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = GenVRBatchProcessor()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

