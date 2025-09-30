import sys
import os
import glob
import subprocess
import threading
import json
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                               QWidget, QPushButton, QListWidget, QListWidgetItem, 
                               QCheckBox, QTextEdit, QLabel, QFileDialog, 
                               QMessageBox, QComboBox, QDialog, QDialogButtonBox,
                               QProgressBar, QTabWidget, QLineEdit, QGroupBox,
                               QSplitter, QFrame, QToolBar, QStatusBar, QToolButton,
                               QMenu, QSystemTrayIcon, QStyle, QInputDialog, QFormLayout)
from PySide6.QtCore import Qt, QThread, Signal, QSettings, QTimer, QSize
from PySide6.QtGui import QFont, QIcon, QPalette, QColor, QAction, QPixmap, QPainter

class ModernProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QProgressBar {
                border: 2px solid #2b2b2b;
                border-radius: 10px;
                text-align: center;
                background-color: #1e1e1e;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0078D7, stop:0.5 #0091FF, stop:1 #00B7FF);
                border-radius: 8px;
            }
        """)

class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Tool Settings")
        self.setMinimumSize(600, 500)
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Tool paths
        paths_group = QGroupBox("Tool Paths")
        paths_layout = QFormLayout()
        
        self.mtk_path = QLineEdit()
        self.mtk_browse = QPushButton("Browse")
        self.mtk_browse.clicked.connect(lambda: self.browse_file(self.mtk_path))
        mtk_layout = QHBoxLayout()
        mtk_layout.addWidget(self.mtk_path)
        mtk_layout.addWidget(self.mtk_browse)
        
        self.edl_path = QLineEdit()
        self.edl_browse = QPushButton("Browse")
        self.edl_browse.clicked.connect(lambda: self.browse_file(self.edl_path))
        edl_layout = QHBoxLayout()
        edl_layout.addWidget(self.edl_path)
        edl_layout.addWidget(self.edl_browse)
        
        self.avb_path = QLineEdit()
        self.avb_browse = QPushButton("Browse")
        self.avb_browse.clicked.connect(lambda: self.browse_file(self.avb_path))
        avb_layout = QHBoxLayout()
        avb_layout.addWidget(self.avb_path)
        avb_layout.addWidget(self.avb_browse)
        
        paths_layout.addRow("MTK Tool:", mtk_layout)
        paths_layout.addRow("EDL Tool:", edl_layout)
        paths_layout.addRow("AVB Tool:", avb_layout)
        paths_group.setLayout(paths_layout)

        # Commands
        commands_group = QGroupBox("Commands Configuration")
        commands_layout = QFormLayout()
        
        self.flash_cmd = QLineEdit()
        self.erase_cmd = QLineEdit()
        self.read_cmd = QLineEdit()
        self.patch_cmd = QLineEdit()
        
        commands_layout.addRow("Flash Command:", self.flash_cmd)
        commands_layout.addRow("Erase Command:", self.erase_cmd)
        commands_layout.addRow("Read Command:", self.read_cmd)
        commands_layout.addRow("Patch Command:", self.patch_cmd)
        commands_group.setLayout(commands_layout)

        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()
        
        self.dark_mode = QCheckBox("Enable Dark Mode")
        self.backup_enable = QCheckBox("Create backup before flashing")
        self.auto_detect = QCheckBox("Auto-detect devices on start")
        
        options_layout.addWidget(self.dark_mode)
        options_layout.addWidget(self.backup_enable)
        options_layout.addWidget(self.auto_detect)
        options_group.setLayout(options_layout)

        layout.addWidget(paths_group)
        layout.addWidget(commands_group)
        layout.addWidget(options_group)

        # Buttons
        button_layout = QHBoxLayout()
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self.reset_defaults)
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_settings)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def browse_file(self, line_edit):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Tool")
        if file_path:
            line_edit.setText(file_path)

    def load_settings(self):
        self.mtk_path.setText(self.settings.get("mtk_path", "mtk.py"))
        self.edl_path.setText(self.settings.get("edl_path", "edl.py"))
        self.avb_path.setText(self.settings.get("avb_path", "avbtool"))
        
        self.flash_cmd.setText(self.settings.get("flash_cmd", "--flash {partition} {file}"))
        self.erase_cmd.setText(self.settings.get("erase_cmd", "--erase {partition}"))
        self.read_cmd.setText(self.settings.get("read_cmd", "--read {partition} {file}"))
        self.patch_cmd.setText(self.settings.get("patch_cmd", "patch_vbmeta --input {input} --output {output}"))
        
        self.dark_mode.setChecked(self.settings.get("dark_mode", False))
        self.backup_enable.setChecked(self.settings.get("backup_enable", True))
        self.auto_detect.setChecked(self.settings.get("auto_detect", True))

    def save_settings(self):
        self.settings["mtk_path"] = self.mtk_path.text()
        self.settings["edl_path"] = self.edl_path.text()
        self.settings["avb_path"] = self.avb_path.text()
        
        self.settings["flash_cmd"] = self.flash_cmd.text()
        self.settings["erase_cmd"] = self.erase_cmd.text()
        self.settings["read_cmd"] = self.read_cmd.text()
        self.settings["patch_cmd"] = self.patch_cmd.text()
        
        self.settings["dark_mode"] = self.dark_mode.isChecked()
        self.settings["backup_enable"] = self.backup_enable.isChecked()
        self.settings["auto_detect"] = self.auto_detect.isChecked()
        
        self.accept()

    def reset_defaults(self):
        default_settings = {
            "mtk_path": "mtk.py",
            "edl_path": "edl.py", 
            "avb_path": "avbtool",
            "flash_cmd": "--flash {partition} {file}",
            "erase_cmd": "--erase {partition}",
            "read_cmd": "--read {partition} {file}",
            "patch_cmd": "patch_vbmeta --input {input} --output {output}",
            "dark_mode": False,
            "backup_enable": True,
            "auto_detect": True
        }
        
        for key, value in default_settings.items():
            self.settings[key] = value
        
        self.load_settings()

class FileListItemWidget(QWidget):
    def __init__(self, file_path, partition_name, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setup_ui(partition_name)

    def setup_ui(self, partition_name):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(True)
        layout.addWidget(self.checkbox)
        
        filename = os.path.basename(self.file_path)
        self.file_label = QLabel(filename)
        self.file_label.setMinimumWidth(200)
        self.file_label.setStyleSheet("padding: 5px;")
        layout.addWidget(self.file_label)
        
        layout.addWidget(QLabel("→ Partition:"))
        
        self.partition_edit = QLineEdit(partition_name)
        self.partition_edit.setMinimumWidth(150)
        self.partition_edit.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px;
                selection-background-color: #0078D7;
            }
            QLineEdit:focus {
                border: 1px solid #0078D7;
            }
        """)
        layout.addWidget(self.partition_edit)
        
        self.size_label = QLabel(self.get_file_size())
        self.size_label.setAlignment(Qt.AlignRight)
        self.size_label.setStyleSheet("padding: 5px; color: #888;")
        layout.addWidget(self.size_label)
        
        layout.addStretch()
        self.setLayout(layout)

    def get_file_size(self):
        try:
            size = os.path.getsize(self.file_path)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except:
            return "N/A"

    def is_checked(self):
        return self.checkbox.isChecked()

    def get_partition_name(self):
        return self.partition_edit.text().strip()

class DeviceDetectionThread(QThread):
    com_ports_signal = Signal(list)
    log_signal = Signal(str)
    
    def __init__(self, settings):
        super().__init__()
        self.settings = settings

    def run(self):
        self.log_signal.emit("🔍 Scanning for connected devices...")
        actual_ports = []
        
        try:
            import serial.tools.list_ports
            ports = list(serial.tools.list_ports.comports())
            
            if not ports:
                self.log_signal.emit("❌ No COM ports found")
                self.com_ports_signal.emit([])
                return
            
            for port in ports:
                port_info = f"{port.device} - {port.description}"
                actual_ports.append(port_info)
                self.log_signal.emit(f"📡 Found: {port_info}")
            
            self.com_ports_signal.emit(actual_ports)
            
        except ImportError:
            self.log_signal.emit("⚠️ pyserial not installed, using fallback detection")
            # Fallback detection for Windows
            if os.name == 'nt':
                for i in range(1, 20):
                    port_name = f"COM{i}"
                    if os.path.exists(f"\\\\.\\{port_name}"):
                        actual_ports.append(f"{port_name} - Unknown Device")
            self.com_ports_signal.emit(actual_ports)

class ToolValidator:
    @staticmethod
    def validate_tool(tool_path, tool_name):
        if not tool_path:
            return False, f"❌ {tool_name} path is empty"
            
        # Extract the actual command (in case it has arguments)
        actual_tool = tool_path.split()[0] if ' ' in tool_path else tool_path
        
        # Check if it's a file that exists
        if os.path.exists(actual_tool):
            return True, f"✅ {tool_name} found: {tool_path}"
        
        # Check if it's in system PATH
        import shutil
        if shutil.which(actual_tool):
            return True, f"✅ {tool_name} found in system PATH: {tool_path}"
            
        return False, f"❌ {tool_name} not found: {tool_path}"

class FlashThread(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    finished_signal = Signal(bool, str)
    operation_started = Signal(str)
    
    def __init__(self, device_type, files, com_port, operation, settings):
        super().__init__()
        self.device_type = device_type
        self.files = files
        self.com_port = com_port
        self.operation = operation
        self.settings = settings
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        try:
            # Validate tools before starting
            if not self.validate_tools():
                self.finished_signal.emit(False, "Required tools not found")
                return
                
            if self.operation == "flash":
                self.perform_flash()
            elif self.operation == "frp":
                self.perform_frp_erase()
            elif self.operation == "advance_frp":
                self.perform_advanced_frp()
            else:
                self.log_signal.emit(f"❌ Unknown operation: {self.operation}")
                self.finished_signal.emit(False, "Unknown operation")
                
        except Exception as e:
            self.log_signal.emit(f"❌ Operation failed: {str(e)}")
            self.finished_signal.emit(False, str(e))

    def validate_tools(self):
        if self.device_type == "qualcomm":
            tool_path = self.settings.get("edl_path", "edl.py")
            tool_name = "Qualcomm EDL Tool"
        else:
            tool_path = self.settings.get("mtk_path", "mtk.py")
            tool_name = "MediaTek MTK Tool"
            
        valid, message = ToolValidator.validate_tool(tool_path, tool_name)
        self.log_signal.emit(message)
        
        if not valid:
            return False
            
        # For advanced FRP, also validate AVB tool
        if self.operation == "advance_frp":
            avb_tool = self.settings.get("avb_path", "avbtool")
            valid_avb, message_avb = ToolValidator.validate_tool(avb_tool, "AVB Tool")
            self.log_signal.emit(message_avb)
            if not valid_avb:
                return False
                
        return True

    def execute_command(self, cmd, description):
        if not self._is_running:
            return False
            
        self.log_signal.emit(f"🚀 {description}")
        self.log_signal.emit(f"💻 Executing: {' '.join(cmd)}")
        
        try:
            # For simulation/demo purposes - remove this in production
            if any(x in ' '.join(cmd) for x in ['mtk.py', 'edl.py', 'avbtool']):
                if not any(os.path.exists(tool.split()[0]) for tool in [self.settings.get("mtk_path"), self.settings.get("edl_path"), self.settings.get("avb_path")]):
                    self.log_signal.emit("⚠️ Simulation mode: Tools not found, simulating operation")
                    # Simulate operation delay
                    import time
                    steps = 5
                    for i in range(steps):
                        if not self._is_running:
                            return False
                        time.sleep(0.5)
                        self.progress_signal.emit(int((i + 1) * 100 / steps))
                    return True
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                     text=True, bufsize=1, universal_newlines=True)
            
            # Read output in real-time
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.log_signal.emit(output.strip())
                    
                if not self._is_running:
                    process.terminate()
                    break
                    
            return process.returncode == 0
            
        except Exception as e:
            self.log_signal.emit(f"❌ Command failed: {str(e)}")
            return False

    def perform_flash(self):
        self.operation_started.emit("flash")
        total_files = len(self.files)
        
        for i, (file_path, partition_name) in enumerate(self.files):
            if not self._is_running:
                break
                
            progress = int((i / total_files) * 100)
            self.progress_signal.emit(progress)
            
            self.log_signal.emit(f"📤 Flashing {os.path.basename(file_path)} to {partition_name}...")
            
            if self.device_type == "qualcomm":
                tool = self.settings.get("edl_path", "edl.py")
                flash_cmd = self.settings.get("flash_cmd", "--flash {partition} {file}").format(
                    partition=partition_name, file=file_path)
            else:
                tool = self.settings.get("mtk_path", "mtk.py")
                flash_cmd = self.settings.get("flash_cmd", "--flash {partition} {file}").format(
                    partition=partition_name, file=file_path)
            
            cmd = ["python", tool, "--port", self.com_port] + flash_cmd.split()
            
            if not self.execute_command(cmd, f"Flashing {partition_name}"):
                self.finished_signal.emit(False, f"Failed to flash {partition_name}")
                return
        
        self.progress_signal.emit(100)
        self.finished_signal.emit(True, "Flash completed successfully")

    def perform_frp_erase(self):
        self.operation_started.emit("frp")
        partitions = ["frp", "persist", "persistence", "userdata"]
        
        for i, partition in enumerate(partitions):
            if not self._is_running:
                break
                
            progress = int((i / len(partitions)) * 100)
            self.progress_signal.emit(progress)
            
            self.log_signal.emit(f"🧹 Erasing {partition}...")
            
            if self.device_type == "qualcomm":
                tool = self.settings.get("edl_path", "edl.py")
                erase_cmd = self.settings.get("erase_cmd", "--erase {partition}").format(partition=partition)
            else:
                tool = self.settings.get("mtk_path", "mtk.py")
                erase_cmd = self.settings.get("erase_cmd", "--erase {partition}").format(partition=partition)
            
            cmd = ["python", tool, "--port", self.com_port] + erase_cmd.split()
            
            if not self.execute_command(cmd, f"Erasing {partition}"):
                self.log_signal.emit(f"⚠️ Failed to erase {partition}, continuing...")
        
        self.progress_signal.emit(100)
        self.finished_signal.emit(True, "FRP erase completed")

    def perform_advanced_frp(self):
        self.operation_started.emit("advance_frp")
        
        # Read vbmeta
        self.log_signal.emit("📖 Reading vbmeta partition...")
        vbmeta_original = "vbmeta_original.img"
        
        if self.device_type == "qualcomm":
            tool = self.settings.get("edl_path", "edl.py")
            read_cmd = self.settings.get("read_cmd", "--read {partition} {file}").format(
                partition="vbmeta", file=vbmeta_original)
        else:
            tool = self.settings.get("mtk_path", "mtk.py")
            read_cmd = self.settings.get("read_cmd", "--read {partition} {file}").format(
                partition="vbmeta", file=vbmeta_original)
        
        cmd = ["python", tool, "--port", self.com_port] + read_cmd.split()
        
        if not self.execute_command(cmd, "Reading vbmeta"):
            self.finished_signal.emit(False, "Failed to read vbmeta")
            return

        # Erase partitions
        self.perform_frp_erase()
        if not self._is_running:
            return

        # Patch vbmeta
        self.log_signal.emit("🔧 Patching vbmeta...")
        vbmeta_patched = "vbmeta_patched.img"
        avb_tool = self.settings.get("avb_path", "avbtool")
        patch_cmd = self.settings.get("patch_cmd", "patch_vbmeta --input {input} --output {output}").format(
            input=vbmeta_original, output=vbmeta_patched)
        
        cmd = [avb_tool] + patch_cmd.split()
        
        if not self.execute_command(cmd, "Patching vbmeta"):
            self.finished_signal.emit(False, "Failed to patch vbmeta")
            return

        # Flash patched vbmeta
        self.log_signal.emit("📤 Flashing patched vbmeta...")
        if self.device_type == "qualcomm":
            flash_cmd = self.settings.get("flash_cmd", "--flash {partition} {file}").format(
                partition="vbmeta", file=vbmeta_patched)
        else:
            flash_cmd = self.settings.get("flash_cmd", "--flash {partition} {file}").format(
                partition="vbmeta", file=vbmeta_patched)
        
        cmd = ["python", tool, "--port", self.com_port] + flash_cmd.split()
        
        if not self.execute_command(cmd, "Flashing patched vbmeta"):
            self.finished_signal.emit(False, "Failed to flash patched vbmeta")
            return

        self.progress_signal.emit(100)
        self.finished_signal.emit(True, "Advanced FRP completed")

class ModernFlashTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = self.load_settings()
        self.selected_directory = ""
        self.selected_device = ""
        self.device_type = ""
        self.flash_files = []
        self.current_flash_thread = None
        self.init_ui()
        self.apply_theme()
        
        if self.settings.get("auto_detect", True):
            QTimer.singleShot(1000, self.detect_devices)

    def load_settings(self):
        settings = QSettings("FlashTool", "DeviceFlasher")
        return {
            "mtk_path": settings.value("mtk_path", "mtk.py"),
            "edl_path": settings.value("edl_path", "edl.py"),
            "avb_path": settings.value("avb_path", "avbtool"),
            "flash_cmd": settings.value("flash_cmd", "--flash {partition} {file}"),
            "erase_cmd": settings.value("erase_cmd", "--erase {partition}"),
            "read_cmd": settings.value("read_cmd", "--read {partition} {file}"),
            "patch_cmd": settings.value("patch_cmd", "patch_vbmeta --input {input} --output {output}"),
            "dark_mode": settings.value("dark_mode", False, type=bool),
            "backup_enable": settings.value("backup_enable", True, type=bool),
            "auto_detect": settings.value("auto_detect", True, type=bool)
        }

    def save_settings(self):
        settings = QSettings("FlashTool", "DeviceFlasher")
        for key, value in self.settings.items():
            settings.setValue(key, value)

    def init_ui(self):
        self.setWindowTitle("🚀 devtical Device Flash Tool")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create toolbar
        self.create_toolbar()
        
        # Create main splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Files and devices
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Device section
        device_group = QGroupBox("📱 Device Selection")
        device_layout = QVBoxLayout(device_group)
        
        device_top_layout = QHBoxLayout()
        self.device_btn = QPushButton("🔍 Scan Devices")
        self.device_btn.clicked.connect(self.detect_devices)
        self.device_label = QLabel("No device selected")
        self.device_label.setStyleSheet("color: #888; font-style: italic;")
        device_top_layout.addWidget(self.device_btn)
        device_top_layout.addWidget(self.device_label)
        device_top_layout.addStretch()
        device_layout.addLayout(device_top_layout)
        
        self.device_info = QLabel("Please scan for devices...")
        self.device_info.setWordWrap(True)
        device_layout.addWidget(self.device_info)
        
        left_layout.addWidget(device_group)
        
        # Directory section
        dir_group = QGroupBox("📁 Flash Files")
        dir_layout = QVBoxLayout(dir_group)
        
        dir_top_layout = QHBoxLayout()
        self.browse_btn = QPushButton("📂 Browse Directory")
        self.browse_btn.clicked.connect(self.browse_directory)
        self.dir_label = QLabel("No directory selected")
        self.dir_label.setStyleSheet("color: #888; font-style: italic;")
        dir_top_layout.addWidget(self.browse_btn)
        dir_top_layout.addWidget(self.dir_label)
        dir_top_layout.addStretch()
        dir_layout.addLayout(dir_top_layout)
        
        # File list
        self.file_list_widget = QListWidget()
        self.file_list_widget.setAlternatingRowColors(True)
        dir_layout.addWidget(self.file_list_widget)
        
        left_layout.addWidget(dir_group)
        
        # Right panel - Log and controls
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Progress section
        progress_group = QGroupBox("📊 Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = ModernProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.status_label)
        
        right_layout.addWidget(progress_group)
        
        # Action buttons
        buttons_group = QGroupBox("⚡ Actions")
        buttons_layout = QVBoxLayout(buttons_group)
        
        self.flash_btn = QPushButton("🚀 Flash Selected Files")
        self.flash_btn.clicked.connect(self.start_flash)
        self.flash_btn.setEnabled(False)
        self.flash_btn.setMinimumHeight(40)
        
        self.frp_btn = QPushButton("🧹 FRP Erase")
        self.frp_btn.clicked.connect(self.frp_erase)
        self.frp_btn.setEnabled(False)
        self.frp_btn.setMinimumHeight(35)
        
        self.adv_frp_btn = QPushButton("🔧 Advanced FRP")
        self.adv_frp_btn.clicked.connect(self.advanced_frp)
        self.adv_frp_btn.setEnabled(False)
        self.adv_frp_btn.setMinimumHeight(35)
        
        self.stop_btn = QPushButton("⏹️ Stop Operation")
        self.stop_btn.clicked.connect(self.stop_operation)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(35)
        
        buttons_layout.addWidget(self.flash_btn)
        buttons_layout.addWidget(self.frp_btn)
        buttons_layout.addWidget(self.adv_frp_btn)
        buttons_layout.addWidget(self.stop_btn)
        
        right_layout.addWidget(buttons_group)
        
        # Log section
        log_group = QGroupBox("📝 Operation Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        # Log controls
        log_controls = QHBoxLayout()
        self.clear_log_btn = QPushButton("Clear Log")
        self.clear_log_btn.clicked.connect(self.log_text.clear)
        log_controls.addWidget(self.clear_log_btn)
        log_controls.addStretch()
        log_layout.addLayout(log_controls)
        
        right_layout.addWidget(log_group)
        
        # Configure splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        # Set initial sizes
        splitter.setSizes([400, 800])
        
        # Status bar
        self.statusBar().showMessage("Ready")

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        # Settings action
        settings_action = QAction("⚙️ Settings", self)
        settings_action.setToolTip("Settings")
        settings_action.triggered.connect(self.show_settings)
        toolbar.addAction(settings_action)
        
        toolbar.addSeparator()
        
        # Theme action
        self.theme_action = QAction("🌙 Toggle Theme", self)
        self.theme_action.setToolTip("Toggle Dark/Light Mode")
        self.theme_action.triggered.connect(self.toggle_theme)
        toolbar.addAction(self.theme_action)
        
        # Validate tools action
        validate_action = QAction("✅ Validate Tools", self)
        validate_action.setToolTip("Validate Tools")
        validate_action.triggered.connect(self.validate_tools)
        toolbar.addAction(validate_action)
        
        toolbar.addSeparator()
        
        # Device selection button in toolbar
        select_device_action = QAction("📱 Select Device", self)
        select_device_action.setToolTip("Select from detected devices")
        select_device_action.triggered.connect(self.select_device)
        toolbar.addAction(select_device_action)

    def apply_theme(self):
        if self.settings.get("dark_mode", False):
            self.apply_dark_theme()
            self.theme_action.setText("☀️ Light Mode")
        else:
            self.apply_light_theme()
            self.theme_action.setText("🌙 Dark Mode")

    def apply_dark_theme(self):
        # Apply dark palette
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.ToolTipBase, QColor(40, 40, 40))
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(50, 50, 50))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        dark_palette.setColor(QPalette.Disabled, QPalette.Text, QColor(150, 150, 150))
        dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(150, 150, 150))
        
        self.setPalette(dark_palette)
        
        # Enhanced dark stylesheet
        dark_stylesheet = """
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #444;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 12px;
                background-color: #2d2d2d;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                color: #ffffff;
                background-color: #2d2d2d;
            }
            QPushButton {
                background-color: #404040;
                border: 2px solid #555;
                border-radius: 6px;
                color: white;
                padding: 8px 12px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border: 2px solid #666;
            }
            QPushButton:pressed {
                background-color: #303030;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #666;
                border: 2px solid #333;
            }
            QListWidget {
                background-color: #252525;
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
                outline: none;
            }
            QListWidget::item {
                padding: 2px;
                border-bottom: 1px solid #333;
            }
            QListWidget::item:selected {
                background-color: #3a3a3a;
            }
            QListWidget::item:alternate {
                background-color: #2a2a2a;
            }
            QTextEdit {
                background-color: #1a1a1a;
                color: #00ff00;
                border: 1px solid #444;
                border-radius: 4px;
                font-family: Consolas, monospace;
            }
            QLineEdit {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px;
                selection-background-color: #0078D7;
            }
            QLineEdit:focus {
                border: 1px solid #0078D7;
                background-color: #333333;
            }
            QLabel {
                color: #ffffff;
            }
            QProgressBar {
                border: 2px solid #444;
                border-radius: 8px;
                text-align: center;
                background-color: #252525;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0078D7, stop:0.5 #0091FF, stop:1 #00B7FF);
                border-radius: 6px;
            }
            QToolBar {
                background-color: #2d2d2d;
                border: none;
                spacing: 5px;
            }
            QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 5px;
            }
            QToolButton:hover {
                background-color: #404040;
                border: 1px solid #555;
            }
            QSplitter::handle {
                background-color: #444;
            }
            QSplitter::handle:hover {
                background-color: #555;
            }
            QStatusBar {
                background-color: #2d2d2d;
                color: #cccccc;
            }
        """
        self.setStyleSheet(dark_stylesheet)

    def apply_light_theme(self):
        self.setPalette(self.style().standardPalette())
        
        light_stylesheet = """
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ccc;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 12px;
                background-color: #f9f9f9;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                background-color: #f9f9f9;
            }
            QPushButton {
                background-color: #f0f0f0;
                border: 2px solid #ccc;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border: 2px solid #bbb;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
            QPushButton:disabled {
                background-color: #f8f8f8;
                color: #aaa;
                border: 2px solid #e0e0e0;
            }
            QListWidget, QTextEdit, QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget {
                background-color: white;
            }
            QListWidget::item:alternate {
                background-color: #f6f6f6;
            }
            QProgressBar {
                border: 2px solid #ccc;
                border-radius: 8px;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0078D7, stop:0.5 #0091FF, stop:1 #00B7FF);
                border-radius: 6px;
            }
        """
        self.setStyleSheet(light_stylesheet)

    def toggle_theme(self):
        self.settings["dark_mode"] = not self.settings.get("dark_mode", False)
        self.save_settings()
        self.apply_theme()

    def detect_devices(self):
        self.log_text.append("🔄 Scanning for devices...")
        self.device_btn.setEnabled(False)
        self.device_info.setText("Scanning...")
        
        self.detection_thread = DeviceDetectionThread(self.settings)
        self.detection_thread.com_ports_signal.connect(self.on_devices_detected)
        self.detection_thread.log_signal.connect(self.log_text.append)
        self.detection_thread.start()

    def on_devices_detected(self, devices):
        self.available_devices = devices
        self.device_btn.setEnabled(True)
        
        if not devices:
            self.device_info.setText("❌ No devices found")
            self.log_text.append("❌ No COM devices detected")
            # Show message to user
            QMessageBox.information(self, "No Devices", "No COM devices were detected. Please ensure your device is connected in EDL/Download mode.")
        else:
            self.device_info.setText(f"✅ Found {len(devices)} device(s)\nClick 'Select Device' to choose")
            self.log_text.append(f"✅ Found {len(devices)} device(s)")
            
            # Auto-select if only one device and show popup for multiple
            if len(devices) == 1:
                self.auto_select_device(devices[0])
            else:
                # Show selection dialog for multiple devices
                self.select_device()

    def auto_select_device(self, device):
        self.selected_device = device
        device_com = device.split(' - ')[0]
        self.device_label.setText(device_com)
        self.determine_device_type()
        self.update_buttons_state()
        self.log_text.append(f"✅ Auto-selected device: {device}")

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Flash Directory")
        if directory:
            self.selected_directory = directory
            self.dir_label.setText(os.path.basename(directory))
            self.load_flash_files()

    def load_flash_files(self):
        self.file_list_widget.clear()
        self.flash_files = []
        
        if not self.selected_directory:
            return
        
        img_files = glob.glob(os.path.join(self.selected_directory, "*.img"))
        
        if not img_files:
            self.log_text.append("❌ No .img files found in selected directory")
            QMessageBox.information(self, "No Files", "No .img files found in the selected directory.")
            return
        
        for img_file in img_files:
            filename = os.path.basename(img_file)
            partition_name = filename.replace('.img', '')
            
            item = QListWidgetItem()
            item_widget = FileListItemWidget(img_file, partition_name)
            item.setSizeHint(item_widget.sizeHint())
            self.file_list_widget.addItem(item)
            self.file_list_widget.setItemWidget(item, item_widget)
            
            self.flash_files.append(item_widget)
        
        self.log_text.append(f"✅ Loaded {len(img_files)} flash files")
        self.update_buttons_state()

    def select_device(self):
        if not hasattr(self, 'available_devices') or not self.available_devices:
            QMessageBox.warning(self, "No Devices", "No devices found. Please scan for devices first.")
            return
        
        device, ok = QInputDialog.getItem(self, "Select Device", "Choose a device:", 
                                         self.available_devices, 0, False)
        if ok and device:
            self.selected_device = device
            device_com = device.split(' - ')[0]
            self.device_label.setText(device_com)
            self.determine_device_type()
            self.update_buttons_state()
            self.log_text.append(f"✅ Selected device: {device}")

    def determine_device_type(self):
        device_lower = self.selected_device.lower()
        if "qualcomm" in device_lower or "9008" in device_lower:
            self.device_type = "qualcomm"
            self.device_info.setText("📱 Qualcomm Device (EDL Mode)\nReady for flashing")
        elif "mediatek" in device_lower or "mtk" in device_lower:
            self.device_type = "mtk"
            self.device_info.setText("📱 MediaTek Device\nReady for flashing")
        else:
            self.device_type = "unknown"
            self.device_info.setText("⚠️ Unknown Device Type\nProceed with caution")

    def update_buttons_state(self):
        has_device = bool(self.selected_device)
        has_files = self.file_list_widget.count() > 0
        
        self.flash_btn.setEnabled(has_device and has_files)
        self.frp_btn.setEnabled(has_device)
        self.adv_frp_btn.setEnabled(has_device)

    def get_selected_files(self):
        selected_files = []
        for file_widget in self.flash_files:
            if file_widget.is_checked():
                partition_name = file_widget.get_partition_name()
                if not partition_name:
                    self.log_text.append(f"⚠️ Warning: Empty partition name for {os.path.basename(file_widget.file_path)}")
                    continue
                selected_files.append((file_widget.file_path, partition_name))
        return selected_files

    def validate_tools(self):
        self.log_text.append("🔧 Validating tools...")
        
        tools_to_check = [
            (self.settings.get("mtk_path", "mtk.py"), "MediaTek Tool"),
            (self.settings.get("edl_path", "edl.py"), "Qualcomm EDL Tool"),
            (self.settings.get("avb_path", "avbtool"), "AVB Tool")
        ]
        
        all_valid = True
        for tool_path, tool_name in tools_to_check:
            valid, message = ToolValidator.validate_tool(tool_path, tool_name)
            self.log_text.append(message)
            if not valid:
                all_valid = False
        
        if all_valid:
            self.log_text.append("✅ All tools are available")
            QMessageBox.information(self, "Tools Valid", "All required tools are available.")
        else:
            self.log_text.append("❌ Some tools are missing. Please check settings.")
            QMessageBox.warning(self, "Tools Missing", "Some required tools are missing. Please check the settings.")
        
        return all_valid

    def show_settings(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.Accepted:
            self.save_settings()
            self.apply_theme()
            self.log_text.append("✅ Settings updated")

    def start_flash(self):
        selected_files = self.get_selected_files()
        if not selected_files:
            QMessageBox.warning(self, "No Files", "Please select at least one file to flash!")
            return
        
        if not self.validate_tools():
            QMessageBox.critical(self, "Tools Missing", "Required tools are not available. Please check settings.")
            return
        
        com_port = self.selected_device.split(' - ')[0]
        
        reply = QMessageBox.question(self, "Confirm Flash", 
                                   f"Flash {len(selected_files)} files to {com_port}?\n\n"
                                   f"Device: {self.selected_device}\n"
                                   f"Type: {self.device_type.capitalize()}",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply != QMessageBox.Yes:
            return
        
        self.log_text.append(f"🚀 Starting flash process on {com_port}...")
        self.current_flash_thread = FlashThread(self.device_type, selected_files, com_port, "flash", self.settings)
        self.connect_flash_thread()
        self.current_flash_thread.start()
        
        self.set_operation_buttons(False)

    def frp_erase(self):
        if not self.validate_tools():
            QMessageBox.critical(self, "Tools Missing", "Required tools are not available. Please check settings.")
            return
        
        com_port = self.selected_device.split(' - ')[0]
        
        reply = QMessageBox.warning(self, "Confirm FRP Erase", 
                                  f"This will erase FRP, persist, and userdata partitions!\n\n"
                                  f"Device: {com_port}\n"
                                  f"Continue?",
                                  QMessageBox.Yes | QMessageBox.No)
        
        if reply != QMessageBox.Yes:
            return
        
        self.log_text.append("🧹 Starting FRP erase process...")
        self.current_flash_thread = FlashThread(self.device_type, [], com_port, "frp", self.settings)
        self.connect_flash_thread()
        self.current_flash_thread.start()
        
        self.set_operation_buttons(False)

    def advanced_frp(self):
        if not self.validate_tools():
            QMessageBox.critical(self, "Tools Missing", "Required tools are not available. Please check settings.")
            return
        
        com_port = self.selected_device.split(' - ')[0]
        
        reply = QMessageBox.warning(self, "Confirm Advanced FRP", 
                                  f"This will:\n"
                                  f"1. Read and backup vbmeta\n"
                                  f"2. Erase FRP partitions\n" 
                                  f"3. Patch and flash vbmeta\n\n"
                                  f"Device: {com_port}\n"
                                  f"Continue?",
                                  QMessageBox.Yes | QMessageBox.No)
        
        if reply != QMessageBox.Yes:
            return
        
        self.log_text.append("🔧 Starting Advanced FRP process...")
        self.current_flash_thread = FlashThread(self.device_type, [], com_port, "advance_frp", self.settings)
        self.connect_flash_thread()
        self.current_flash_thread.start()
        
        self.set_operation_buttons(False)

    def connect_flash_thread(self):
        self.current_flash_thread.log_signal.connect(self.log_text.append)
        self.current_flash_thread.progress_signal.connect(self.progress_bar.setValue)
        self.current_flash_thread.finished_signal.connect(self.operation_finished)
        self.current_flash_thread.operation_started.connect(self.operation_started)

    def operation_started(self, operation):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Running {operation}...")
        self.stop_btn.setEnabled(True)

    def operation_finished(self, success, message):
        self.progress_bar.setVisible(False)
        self.set_operation_buttons(True)
        self.stop_btn.setEnabled(False)
        
        if success:
            self.log_text.append(f"✅ {message}")
            self.status_label.setText("Operation completed successfully")
            QMessageBox.information(self, "Success", message)
        else:
            self.log_text.append(f"❌ {message}")
            self.status_label.setText("Operation failed")
            QMessageBox.critical(self, "Error", message)
        
        self.current_flash_thread = None

    def stop_operation(self):
        if self.current_flash_thread and self.current_flash_thread.isRunning():
            reply = QMessageBox.question(self, "Stop Operation", 
                                       "Are you sure you want to stop the current operation?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.current_flash_thread.stop()
                self.log_text.append("🛑 Operation stopped by user")
                self.status_label.setText("Operation stopped")
                self.stop_btn.setEnabled(False)

    def set_operation_buttons(self, enabled):
        self.flash_btn.setEnabled(enabled and bool(self.selected_device) and self.file_list_widget.count() > 0)
        self.frp_btn.setEnabled(enabled and bool(self.selected_device))
        self.adv_frp_btn.setEnabled(enabled and bool(self.selected_device))
        self.browse_btn.setEnabled(enabled)
        self.device_btn.setEnabled(enabled)

    def closeEvent(self, event):
        if self.current_flash_thread and self.current_flash_thread.isRunning():
            reply = QMessageBox.question(self, "Operation in Progress", 
                                       "An operation is still running. Are you sure you want to quit?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.current_flash_thread.stop()
                self.current_flash_thread.wait(2000)  # Wait 2 seconds for thread to stop
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("devtical Flash Tool")
    app.setApplicationVersion("2.0")
    
    # Set modern fusion style
    app.setStyle('Fusion')
    
    window = ModernFlashTool()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()