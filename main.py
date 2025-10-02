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
from PySide6.QtCore import Qt, QThread, Signal, QSettings, QTimer, QSize, QProcess
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
        self.setMinimumSize(800, 700)
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Create tab widget for better organization
        tab_widget = QTabWidget()
        
        # Basic Tools Tab
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        
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
        basic_layout.addWidget(paths_group)

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
        basic_layout.addWidget(commands_group)

        # FRP Configuration
        frp_group = QGroupBox("FRP Configuration")
        frp_layout = QFormLayout()
        
        self.basic_frp_partitions = QLineEdit()
        self.advanced_frp_partitions = QLineEdit()
        
        frp_layout.addRow("Basic FRP Partitions:", self.basic_frp_partitions)
        frp_layout.addRow("Advanced FRP Partitions:", self.advanced_frp_partitions)
        
        frp_info = QLabel("Enter comma-separated partition names (e.g., frp,metadata,userdata)")
        frp_info.setStyleSheet("color: #888; font-size: 10px;")
        frp_layout.addRow("", frp_info)
        
        frp_group.setLayout(frp_layout)
        basic_layout.addWidget(frp_group)

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
        basic_layout.addWidget(options_group)
        
        basic_layout.addStretch()
        tab_widget.addTab(basic_tab, "Basic Tools")

        # SPD Client Tab
        spd_tab = QWidget()
        spd_layout = QVBoxLayout(spd_tab)
        
        spd_group = QGroupBox("SPD Client (Spreadtrum/Unisoc)")
        spd_form = QFormLayout()
        
        self.spd_path = QLineEdit()
        self.spd_browse = QPushButton("Browse")
        self.spd_browse.clicked.connect(lambda: self.browse_file(self.spd_path))
        spd_path_layout = QHBoxLayout()
        spd_path_layout.addWidget(self.spd_path)
        spd_path_layout.addWidget(self.spd_browse)
        
        self.spd_flash_cmd = QLineEdit()
        self.spd_erase_cmd = QLineEdit()
        self.spd_read_cmd = QLineEdit()
        self.spd_extract_cmd = QLineEdit()
        self.spd_adv_frp_cmd = QLineEdit()
        
        spd_form.addRow("SPD Tool Path:", spd_path_layout)
        spd_form.addRow("Flash Command:", self.spd_flash_cmd)
        spd_form.addRow("Erase Command:", self.spd_erase_cmd)
        spd_form.addRow("Read Command:", self.spd_read_cmd)
        spd_form.addRow("Extract PAC Command:", self.spd_extract_cmd)
        spd_form.addRow("Advanced FRP Command:", self.spd_adv_frp_cmd)
        
        spd_group.setLayout(spd_form)
        spd_layout.addWidget(spd_group)
        
        spd_info = QLabel(
            "SPD Advanced FRP can use:\n"
            "• Engineering FDL files\n"
            "• Pre-patched loaders\n"
            "• Factory reset partitions\n"
            "Use {fdl1}, {fdl2}, {partitions} placeholders"
        )
        spd_info.setWordWrap(True)
        spd_info.setStyleSheet("background-color: #2a2a2a; padding: 10px; border-radius: 5px;")
        spd_layout.addWidget(spd_info)
        spd_layout.addStretch()
        tab_widget.addTab(spd_tab, "SPD Client")

        # XYN Client Tab
        xyn_tab = QWidget()
        xyn_layout = QVBoxLayout(xyn_tab)
        
        xyn_group = QGroupBox("XYN Client (Exynos)")
        xyn_form = QFormLayout()
        
        self.xyn_path = QLineEdit()
        self.xyn_browse = QPushButton("Browse")
        self.xyn_browse.clicked.connect(lambda: self.browse_file(self.xyn_path))
        xyn_path_layout = QHBoxLayout()
        xyn_path_layout.addWidget(self.xyn_path)
        xyn_path_layout.addWidget(self.xyn_browse)
        
        self.xyn_flash_cmd = QLineEdit()
        self.xyn_erase_cmd = QLineEdit()
        self.xyn_read_cmd = QLineEdit()
        self.xyn_detect_cmd = QLineEdit()
        self.xyn_partitions_cmd = QLineEdit()
        self.xyn_adv_frp_cmd = QLineEdit()
        
        xyn_form.addRow("XYN Tool Path:", xyn_path_layout)
        xyn_form.addRow("Flash Command:", self.xyn_flash_cmd)
        xyn_form.addRow("Erase Command:", self.xyn_erase_cmd)
        xyn_form.addRow("Read Command:", self.xyn_read_cmd)
        xyn_form.addRow("Detect Command:", self.xyn_detect_cmd)
        xyn_form.addRow("Partitions Command:", self.xyn_partitions_cmd)
        xyn_form.addRow("Advanced FRP Command:", self.xyn_adv_frp_cmd)
        
        xyn_group.setLayout(xyn_form)
        xyn_layout.addWidget(xyn_group)
        
        xyn_info = QLabel(
            "XYN Advanced FRP can use:\n"
            "• Combination firmware\n"
            "• Engineering bootloaders\n"
            "• Custom PIT files\n"
            "Use {partitions} placeholder"
        )
        xyn_info.setWordWrap(True)
        xyn_info.setStyleSheet("background-color: #2a2a2a; padding: 10px; border-radius: 5px;")
        xyn_layout.addWidget(xyn_info)
        xyn_layout.addStretch()
        tab_widget.addTab(xyn_tab, "XYN Client")

        layout.addWidget(tab_widget)

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
        # Basic tools
        self.mtk_path.setText(self.settings.get("mtk_path", "mtk.py"))
        self.edl_path.setText(self.settings.get("edl_path", "edl.py"))
        self.avb_path.setText(self.settings.get("avb_path", "avbtool"))
        
        self.flash_cmd.setText(self.settings.get("flash_cmd", "--flash {partition} {file}"))
        self.erase_cmd.setText(self.settings.get("erase_cmd", "--erase {partition}"))
        self.read_cmd.setText(self.settings.get("read_cmd", "--read {partition} {file}"))
        self.patch_cmd.setText(self.settings.get("patch_cmd", "patch_vbmeta --input {input} --output {output}"))
        
        # FRP Configuration
        self.basic_frp_partitions.setText(self.settings.get("basic_frp_partitions", "frp,metadata,userdata"))
        self.advanced_frp_partitions.setText(self.settings.get("advanced_frp_partitions", "frp,metadata,userdata,persist"))
        
        self.dark_mode.setChecked(self.settings.get("dark_mode", False))
        self.backup_enable.setChecked(self.settings.get("backup_enable", True))
        self.auto_detect.setChecked(self.settings.get("auto_detect", True))
        
        # SPD Client
        self.spd_path.setText(self.settings.get("spd_path", "spd.py"))
        self.spd_flash_cmd.setText(self.settings.get("spd_flash_cmd", "writepart {partition} {file} --fdl1 {fdl1} --fdl2 {fdl2}"))
        self.spd_erase_cmd.setText(self.settings.get("spd_erase_cmd", "erasepart {partition} --fdl1 {fdl1} --fdl2 {fdl2}"))
        self.spd_read_cmd.setText(self.settings.get("spd_read_cmd", "readpart {partition} {file} --fdl1 {fdl1} --fdl2 {fdl2}"))
        self.spd_extract_cmd.setText(self.settings.get("spd_extract_cmd", "extractpac {pac_file}"))
        self.spd_adv_frp_cmd.setText(self.settings.get("spd_adv_frp_cmd", "writepart {partition} zero.bin --fdl1 {fdl1} --fdl2 {fdl2}"))
        
        # XYN Client
        self.xyn_path.setText(self.settings.get("xyn_path", "xyn_cli.py"))
        self.xyn_flash_cmd.setText(self.settings.get("xyn_flash_cmd", "write {partition} {file}"))
        self.xyn_erase_cmd.setText(self.settings.get("xyn_erase_cmd", "erase {partition} --force"))
        self.xyn_read_cmd.setText(self.settings.get("xyn_read_cmd", "read {partition} {file}"))
        self.xyn_detect_cmd.setText(self.settings.get("xyn_detect_cmd", "detect"))
        self.xyn_partitions_cmd.setText(self.settings.get("xyn_partitions_cmd", "partitions"))
        self.xyn_adv_frp_cmd.setText(self.settings.get("xyn_adv_frp_cmd", "erase {partition} --force"))

    def save_settings(self):
        # Basic tools
        self.settings["mtk_path"] = self.mtk_path.text()
        self.settings["edl_path"] = self.edl_path.text()
        self.settings["avb_path"] = self.avb_path.text()
        
        self.settings["flash_cmd"] = self.flash_cmd.text()
        self.settings["erase_cmd"] = self.erase_cmd.text()
        self.settings["read_cmd"] = self.read_cmd.text()
        self.settings["patch_cmd"] = self.patch_cmd.text()
        
        # FRP Configuration
        self.settings["basic_frp_partitions"] = self.basic_frp_partitions.text()
        self.settings["advanced_frp_partitions"] = self.advanced_frp_partitions.text()
        
        self.settings["dark_mode"] = self.dark_mode.isChecked()
        self.settings["backup_enable"] = self.backup_enable.isChecked()
        self.settings["auto_detect"] = self.auto_detect.isChecked()
        
        # SPD Client
        self.settings["spd_path"] = self.spd_path.text()
        self.settings["spd_flash_cmd"] = self.spd_flash_cmd.text()
        self.settings["spd_erase_cmd"] = self.spd_erase_cmd.text()
        self.settings["spd_read_cmd"] = self.spd_read_cmd.text()
        self.settings["spd_extract_cmd"] = self.spd_extract_cmd.text()
        self.settings["spd_adv_frp_cmd"] = self.spd_adv_frp_cmd.text()
        
        # XYN Client
        self.settings["xyn_path"] = self.xyn_path.text()
        self.settings["xyn_flash_cmd"] = self.xyn_flash_cmd.text()
        self.settings["xyn_erase_cmd"] = self.xyn_erase_cmd.text()
        self.settings["xyn_read_cmd"] = self.xyn_read_cmd.text()
        self.settings["xyn_detect_cmd"] = self.xyn_detect_cmd.text()
        self.settings["xyn_partitions_cmd"] = self.xyn_partitions_cmd.text()
        self.settings["xyn_adv_frp_cmd"] = self.xyn_adv_frp_cmd.text()
        
        self.accept()

    def reset_defaults(self):
        default_settings = {
            # Basic tools
            "mtk_path": "mtk.py",
            "edl_path": "edl.py", 
            "avb_path": "avbtool",
            "flash_cmd": "--flash {partition} {file}",
            "erase_cmd": "--erase {partition}",
            "read_cmd": "--read {partition} {file}",
            "patch_cmd": "patch_vbmeta --input {input} --output {output}",
            
            # FRP Configuration
            "basic_frp_partitions": "frp,metadata,userdata",
            "advanced_frp_partitions": "frp,metadata,userdata,persist",
            
            "dark_mode": False,
            "backup_enable": True,
            "auto_detect": True,
            
            # SPD Client
            "spd_path": "spd.py",
            "spd_flash_cmd": "writepart {partition} {file} --fdl1 {fdl1} --fdl2 {fdl2}",
            "spd_erase_cmd": "erasepart {partition} --fdl1 {fdl1} --fdl2 {fdl2}",
            "spd_read_cmd": "readpart {partition} {file} --fdl1 {fdl1} --fdl2 {fdl2}",
            "spd_extract_cmd": "extractpac {pac_file}",
            "spd_adv_frp_cmd": "writepart {partition} zero.bin --fdl1 {fdl1} --fdl2 {fdl2}",
            
            # XYN Client
            "xyn_path": "xyn_cli.py",
            "xyn_flash_cmd": "write {partition} {file}",
            "xyn_erase_cmd": "erase {partition} --force",
            "xyn_read_cmd": "read {partition} {file}",
            "xyn_detect_cmd": "detect",
            "xyn_partitions_cmd": "partitions",
            "xyn_adv_frp_cmd": "erase {partition} --force"
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

class TerminalWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = None
        self.setup_ui()
        self.start_shell()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Terminal header
        header_layout = QHBoxLayout()
        self.shell_label = QLabel("Terminal")
        self.shell_label.setStyleSheet("font-weight: bold; color: #00ff00;")
        header_layout.addWidget(self.shell_label)
        
        self.current_dir_label = QLabel("")
        self.current_dir_label.setStyleSheet("color: #888; font-size: 10px;")
        header_layout.addWidget(self.current_dir_label)
        
        header_layout.addStretch()
        
        # Terminal controls
        self.restart_btn = QPushButton("🔄 Restart")
        self.restart_btn.clicked.connect(self.restart_shell)
        self.restart_btn.setMaximumWidth(100)
        header_layout.addWidget(self.restart_btn)
        
        self.clear_btn = QPushButton("🧹 Clear")
        self.clear_btn.clicked.connect(self.clear_terminal)
        self.clear_btn.setMaximumWidth(100)
        header_layout.addWidget(self.clear_btn)
        
        layout.addLayout(header_layout)
        
        # Terminal output
        self.terminal_output = QTextEdit()
        self.terminal_output.setFont(QFont("Consolas", 10))
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #00ff00;
                border: 1px solid #444;
                border-radius: 4px;
                font-family: Consolas, monospace;
            }
        """)
        layout.addWidget(self.terminal_output)
        
        # Input area
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("$"))
        
        self.terminal_input = QLineEdit()
        self.terminal_input.setPlaceholderText("Enter command...")
        self.terminal_input.returnPressed.connect(self.execute_command)
        self.terminal_input.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b2b;
                color: #00ff00;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px;
                font-family: Consolas, monospace;
            }
            QLineEdit:focus {
                border: 1px solid #0078D7;
            }
        """)
        input_layout.addWidget(self.terminal_input)
        
        self.execute_btn = QPushButton("Run")
        self.execute_btn.clicked.connect(self.execute_command)
        self.execute_btn.setMaximumWidth(80)
        input_layout.addWidget(self.execute_btn)
        
        layout.addLayout(input_layout)
        
        self.setLayout(layout)

    def start_shell(self):
        """Start the appropriate shell for the current OS"""
        self.terminal_output.append("🚀 Starting terminal session...\n")
        
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.readyReadStandardError.connect(self.read_error)
        self.process.finished.connect(self.process_finished)
        
        # Set working directory to current directory
        current_dir = os.getcwd()
        self.process.setWorkingDirectory(current_dir)
        self.current_dir_label.setText(f"Directory: {current_dir}")
        
        if os.name == 'nt':  # Windows
            shell = "cmd.exe"
            self.shell_label.setText("Windows Command Prompt")
            self.terminal_output.append("💻 Windows Command Prompt (cmd.exe)\n")
        else:  # Linux/Mac
            shell = "/bin/bash"
            self.shell_label.setText("Bash Terminal")
            self.terminal_output.append("🐧 Bash Terminal (/bin/bash)\n")
        
        self.terminal_output.append(f"📁 Working directory: {current_dir}\n")
        self.terminal_output.append("─" * 50 + "\n")
        
        try:
            self.process.start(shell)
            if not self.process.waitForStarted(3000):
                self.terminal_output.append("❌ Failed to start shell process\n")
        except Exception as e:
            self.terminal_output.append(f"❌ Error starting shell: {str(e)}\n")

    def execute_command(self):
        command = self.terminal_input.text().strip()
        if not command:
            return
            
        # Show the command in terminal
        self.terminal_output.append(f"$ {command}\n")
        self.terminal_input.clear()
        
        if self.process and self.process.state() == QProcess.Running:
            # Add newline to execute the command
            self.process.write((command + "\n").encode())
        else:
            self.terminal_output.append("❌ Shell process not running. Restart the terminal.\n")

    def read_output(self):
        if self.process:
            data = self.process.readAllStandardOutput().data().decode()
            self.terminal_output.append(data)
            # Auto-scroll to bottom
            self.terminal_output.verticalScrollBar().setValue(
                self.terminal_output.verticalScrollBar().maximum()
            )

    def read_error(self):
        if self.process:
            data = self.process.readAllStandardError().data().decode()
            self.terminal_output.append(f"<span style='color: #ff6b6b;'>{data}</span>")
            # Auto-scroll to bottom
            self.terminal_output.verticalScrollBar().setValue(
                self.terminal_output.verticalScrollBar().maximum()
            )

    def process_finished(self, exit_code, exit_status):
        self.terminal_output.append(f"\n💥 Shell process finished with exit code: {exit_code}\n")

    def restart_shell(self):
        self.terminal_output.append("\n🔄 Restarting shell...\n")
        if self.process:
            self.process.kill()
            self.process.waitForFinished(1000)
        self.start_shell()

    def clear_terminal(self):
        self.terminal_output.clear()

    def closeEvent(self, event):
        if self.process and self.process.state() == QProcess.Running:
            self.process.kill()
            self.process.waitForFinished(1000)
        event.accept()
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
        self.fdl1_path = None
        self.fdl2_path = None
        self.pac_file_path = None

    def set_fdl_files(self, fdl1_path, fdl2_path):
        self.fdl1_path = fdl1_path
        self.fdl2_path = fdl2_path

    def set_pac_file(self, pac_file_path):
        self.pac_file_path = pac_file_path

    def stop(self):
        self._is_running = False

    def run(self):
        try:
            # Validate tools before starting
            if not self.validate_tools():
                self.finished_signal.emit(False, "Required tools not found")
                return
                
            # For SPD devices, check if we have FDL files or PAC file
            if self.device_type == "spreadtrum":
                if not self.setup_spd_environment():
                    self.finished_signal.emit(False, "SPD operation setup failed")
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

    def setup_spd_environment(self):
        """Setup FDL files for SPD operations"""
        # If we have a PAC file, extract FDL files first
        if self.pac_file_path and os.path.exists(self.pac_file_path):
            self.log_signal.emit("📦 Extracting FDL files from PAC file...")
            spd_tool = self.settings.get("spd_path", "spd.py")
            extract_cmd = self.settings.get("spd_extract_cmd", "extractpac {pac_file}").format(
                pac_file=self.pac_file_path)
            
            cmd = ["python", spd_tool] + extract_cmd.split()
            
            if not self.execute_command(cmd, "Extracting FDL from PAC"):
                self.log_signal.emit("❌ Failed to extract FDL files from PAC")
                return False
            
            # After extraction, FDL files should be in the same directory as PAC
            pac_dir = os.path.dirname(self.pac_file_path)
            self.fdl1_path = os.path.join(pac_dir, "FDL1.bin")
            self.fdl2_path = os.path.join(pac_dir, "FDL2.bin")
        
        # Check if we have valid FDL files
        if not self.fdl1_path or not os.path.exists(self.fdl1_path):
            self.log_signal.emit("❌ FDL1.bin file not found or not provided")
            return False
            
        if not self.fdl2_path or not os.path.exists(self.fdl2_path):
            self.log_signal.emit("❌ FDL2.bin file not found or not provided")
            return False
            
        self.log_signal.emit(f"✅ Using FDL1: {os.path.basename(self.fdl1_path)}")
        self.log_signal.emit(f"✅ Using FDL2: {os.path.basename(self.fdl2_path)}")
        return True

    def validate_tools(self):
        if self.device_type == "qualcomm":
            tool_path = self.settings.get("edl_path", "edl.py")
            tool_name = "Qualcomm EDL Tool"
        elif self.device_type == "mtk":
            tool_path = self.settings.get("mtk_path", "mtk.py")
            tool_name = "MediaTek MTK Tool"
        elif self.device_type == "spreadtrum":
            tool_path = self.settings.get("spd_path", "spd.py")
            tool_name = "SPD Client"
        elif self.device_type == "xynos":
            tool_path = self.settings.get("xyn_path", "xyn_cli.py")
            tool_name = "XYN Client"
        else:
            self.log_signal.emit("❌ Unknown device type")
            return False
            
        valid, message = ToolValidator.validate_tool(tool_path, tool_name)
        self.log_signal.emit(message)
        
        if not valid:
            return False
            
        # For advanced FRP, also validate AVB tool for Qualcomm/MTK
        if self.operation == "advance_frp" and self.device_type in ["qualcomm", "mtk"]:
            avb_tool = self.settings.get("avb_path", "avbtool")
            valid_avb, message_avb = ToolValidator.validate_tool(avb_tool, "AVB Tool")
            self.log_signal.emit(message_avb)
            if not valid_avb:
                return False
                
        return True

    def get_frp_partitions(self, frp_type="basic"):
        """Get FRP partitions from settings"""
        if frp_type == "advanced":
            partitions_str = self.settings.get("advanced_frp_partitions", "frp,metadata,userdata,persist")
        else:
            partitions_str = self.settings.get("basic_frp_partitions", "frp,metadata,userdata")
        
        partitions = [p.strip() for p in partitions_str.split(',') if p.strip()]
        return partitions

    def execute_command(self, cmd, description):
        if not self._is_running:
            return False
            
        self.log_signal.emit(f"🚀 {description}")
        self.log_signal.emit(f"💻 Executing: {' '.join(cmd)}")
        
        try:
            # For simulation/demo purposes - remove this in production
            tool_exists = False
            if any(x in ' '.join(cmd).lower() for x in ['mtk.py', 'edl.py', 'avbtool', 'spd.py', 'xyn_cli.py']):
                if 'spd.py' in ' '.join(cmd).lower():
                    tool_exists = os.path.exists(self.settings.get("spd_path", "spd.py").split()[0])
                elif 'xyn_cli.py' in ' '.join(cmd).lower():
                    tool_exists = os.path.exists(self.settings.get("xyn_path", "xyn_cli.py").split()[0])
                else:
                    tool_exists = any(os.path.exists(tool.split()[0]) for tool in [
                        self.settings.get("mtk_path"), 
                        self.settings.get("edl_path"), 
                        self.settings.get("avb_path")
                    ])
                
                if not tool_exists:
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
                cmd = ["python", tool, "--port", self.com_port] + flash_cmd.split()
                
            elif self.device_type == "mtk":
                tool = self.settings.get("mtk_path", "mtk.py")
                flash_cmd = self.settings.get("flash_cmd", "--flash {partition} {file}").format(
                    partition=partition_name, file=file_path)
                cmd = ["python", tool, "--port", self.com_port] + flash_cmd.split()
                
            elif self.device_type == "spreadtrum":
                tool = self.settings.get("spd_path", "spd.py")
                flash_cmd = self.settings.get("spd_flash_cmd", "writepart {partition} {file} --fdl1 {fdl1} --fdl2 {fdl2}").format(
                    partition=partition_name, file=file_path, fdl1=self.fdl1_path, fdl2=self.fdl2_path)
                cmd = ["python", tool, self.com_port] + flash_cmd.split()
                
            elif self.device_type == "xynos":
                tool = self.settings.get("xyn_path", "xyn_cli.py")
                flash_cmd = self.settings.get("xyn_flash_cmd", "write {partition} {file}").format(
                    partition=partition_name, file=file_path)
                cmd = ["python", tool] + flash_cmd.split()
            
            if not self.execute_command(cmd, f"Flashing {partition_name}"):
                self.finished_signal.emit(False, f"Failed to flash {partition_name}")
                return
        
        self.progress_signal.emit(100)
        self.finished_signal.emit(True, "Flash completed successfully")

    def perform_frp_erase(self):
        """Basic FRP erase for all device types"""
        self.operation_started.emit("frp")
        partitions = self.get_frp_partitions("basic")
        
        if not partitions:
            self.log_signal.emit("❌ No FRP partitions configured")
            self.finished_signal.emit(False, "No FRP partitions configured")
            return
            
        self.log_signal.emit(f"🧹 Erasing partitions: {', '.join(partitions)}")
        
        for i, partition in enumerate(partitions):
            if not self._is_running:
                break
                
            progress = int((i / len(partitions)) * 100)
            self.progress_signal.emit(progress)
            
            self.log_signal.emit(f"🧹 Erasing {partition}...")
            
            if self.device_type == "qualcomm":
                tool = self.settings.get("edl_path", "edl.py")
                erase_cmd = self.settings.get("erase_cmd", "--erase {partition}").format(partition=partition)
                cmd = ["python", tool, "--port", self.com_port] + erase_cmd.split()
                
            elif self.device_type == "mtk":
                tool = self.settings.get("mtk_path", "mtk.py")
                erase_cmd = self.settings.get("erase_cmd", "--erase {partition}").format(partition=partition)
                cmd = ["python", tool, "--port", self.com_port] + erase_cmd.split()
                
            elif self.device_type == "spreadtrum":
                tool = self.settings.get("spd_path", "spd.py")
                erase_cmd = self.settings.get("spd_erase_cmd", "erasepart {partition} --fdl1 {fdl1} --fdl2 {fdl2}").format(
                    partition=partition, fdl1=self.fdl1_path, fdl2=self.fdl2_path)
                cmd = ["python", tool, self.com_port] + erase_cmd.split()
                
            elif self.device_type == "xynos":
                tool = self.settings.get("xyn_path", "xyn_cli.py")
                erase_cmd = self.settings.get("xyn_erase_cmd", "erase {partition} --force").format(partition=partition)
                cmd = ["python", tool] + erase_cmd.split()
            
            if not self.execute_command(cmd, f"Erasing {partition}"):
                self.log_signal.emit(f"⚠️ Failed to erase {partition}, continuing...")
        
        self.progress_signal.emit(100)
        self.finished_signal.emit(True, "Basic FRP erase completed")

    def perform_advanced_frp(self):
        """Advanced FRP for ALL device types with appropriate methods"""
        self.operation_started.emit("advance_frp")
        
        if self.device_type in ["qualcomm", "mtk"]:
            self.perform_standard_advanced_frp()
        elif self.device_type == "spreadtrum":
            self.perform_spd_advanced_frp()
        elif self.device_type == "xynos":
            self.perform_xyn_advanced_frp()
        else:
            self.finished_signal.emit(False, "Advanced FRP not supported for this device type")

    def perform_standard_advanced_frp(self):
        """Advanced FRP for Qualcomm/MTK with vbmeta patching"""
        self.log_signal.emit("🔧 Starting Advanced FRP (Qualcomm/MTK)...")
        
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

        # Erase advanced FRP partitions
        partitions = self.get_frp_partitions("advanced")
        self.log_signal.emit(f"🧹 Erasing advanced partitions: {', '.join(partitions)}")
        
        for partition in partitions:
            if not self._is_running:
                break
                
            self.log_signal.emit(f"🧹 Erasing {partition}...")
            
            if self.device_type == "qualcomm":
                erase_cmd = self.settings.get("erase_cmd", "--erase {partition}").format(partition=partition)
            else:
                erase_cmd = self.settings.get("erase_cmd", "--erase {partition}").format(partition=partition)
            
            cmd = ["python", tool, "--port", self.com_port] + erase_cmd.split()
            
            if not self.execute_command(cmd, f"Erasing {partition}"):
                self.log_signal.emit(f"⚠️ Failed to erase {partition}, continuing...")

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

    def perform_spd_advanced_frp(self):
        """Advanced FRP for Spreadtrum/Unisoc devices"""
        self.log_signal.emit("🔧 Starting Advanced FRP (Spreadtrum/Unisoc)...")
        
        partitions = self.get_frp_partitions("advanced")
        self.log_signal.emit(f"🧹 Erasing advanced partitions: {', '.join(partitions)}")
        
        tool = self.settings.get("spd_path", "spd.py")
        
        for i, partition in enumerate(partitions):
            if not self._is_running:
                break
                
            progress = int((i / len(partitions)) * 100)
            self.progress_signal.emit(progress)
            
            self.log_signal.emit(f"🧹 Advanced erase {partition}...")
            
            # Use advanced FRP command for SPD
            adv_frp_cmd = self.settings.get("spd_adv_frp_cmd", "writepart {partition} zero.bin --fdl1 {fdl1} --fdl2 {fdl2}").format(
                partition=partition, fdl1=self.fdl1_path, fdl2=self.fdl2_path)
            
            cmd = ["python", tool, self.com_port] + adv_frp_cmd.split()
            
            if not self.execute_command(cmd, f"Advanced FRP on {partition}"):
                self.log_signal.emit(f"⚠️ Failed advanced FRP on {partition}, continuing...")
        
        self.progress_signal.emit(100)
        self.finished_signal.emit(True, "Advanced FRP completed for Spreadtrum")

    def perform_xyn_advanced_frp(self):
        """Advanced FRP for Exynos devices"""
        self.log_signal.emit("🔧 Starting Advanced FRP (Exynos)...")
        
        partitions = self.get_frp_partitions("advanced")
        self.log_signal.emit(f"🧹 Erasing advanced partitions: {', '.join(partitions)}")
        
        tool = self.settings.get("xyn_path", "xyn_cli.py")
        
        for i, partition in enumerate(partitions):
            if not self._is_running:
                break
                
            progress = int((i / len(partitions)) * 100)
            self.progress_signal.emit(progress)
            
            self.log_signal.emit(f"🧹 Advanced erase {partition}...")
            
            # Use advanced FRP command for XYN
            adv_frp_cmd = self.settings.get("xyn_adv_frp_cmd", "erase {partition} --force").format(partition=partition)
            
            cmd = ["python", tool] + adv_frp_cmd.split()
            
            if not self.execute_command(cmd, f"Advanced FRP on {partition}"):
                self.log_signal.emit(f"⚠️ Failed advanced FRP on {partition}, continuing...")
        
        self.progress_signal.emit(100)
        self.finished_signal.emit(True, "Advanced FRP completed for Exynos")

class ModernFlashTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = self.load_settings()
        self.selected_directory = ""
        self.selected_device = ""
        self.device_type = ""
        self.flash_files = []
        self.current_flash_thread = None
        self.fdl1_path = None
        self.fdl2_path = None
        self.pac_file_path = None
        
        # Setup system tray
        self.setup_tray_icon()
        
        self.init_ui()
        self.apply_theme()
        
        if self.settings.get("auto_detect", True):
            QTimer.singleShot(1000, self.detect_devices)

    def load_settings(self):
        settings = QSettings("FlashTool", "DeviceFlasher")
        default_settings = {
            "mtk_path": "mtk.py",
            "edl_path": "edl.py",
            "avb_path": "avbtool",
            "flash_cmd": "--flash {partition} {file}",
            "erase_cmd": "--erase {partition}",
            "read_cmd": "--read {partition} {file}",
            "patch_cmd": "patch_vbmeta --input {input} --output {output}",
            "basic_frp_partitions": "frp,metadata,userdata",
            "advanced_frp_partitions": "frp,metadata,userdata,persist",
            "dark_mode": False,
            "backup_enable": True,
            "auto_detect": True,
            # SPD Client
            "spd_path": "spd.py",
            "spd_flash_cmd": "writepart {partition} {file} --fdl1 {fdl1} --fdl2 {fdl2}",
            "spd_erase_cmd": "erasepart {partition} --fdl1 {fdl1} --fdl2 {fdl2}",
            "spd_read_cmd": "readpart {partition} {file} --fdl1 {fdl1} --fdl2 {fdl2}",
            "spd_extract_cmd": "extractpac {pac_file}",
            "spd_adv_frp_cmd": "writepart {partition} zero.bin --fdl1 {fdl1} --fdl2 {fdl2}",
            # XYN Client
            "xyn_path": "xyn_cli.py",
            "xyn_flash_cmd": "write {partition} {file}",
            "xyn_erase_cmd": "erase {partition} --force",
            "xyn_read_cmd": "read {partition} {file}",
            "xyn_detect_cmd": "detect",
            "xyn_partitions_cmd": "partitions",
            "xyn_adv_frp_cmd": "erase {partition} --force"
        }
        
        loaded_settings = {}
        for key, default_value in default_settings.items():
            if isinstance(default_value, bool):
                loaded_settings[key] = settings.value(key, default_value, type=bool)
            else:
                loaded_settings[key] = settings.value(key, default_value)
                
        return loaded_settings

    def save_settings(self):
        settings = QSettings("FlashTool", "DeviceFlasher")
        for key, value in self.settings.items():
            settings.setValue(key, value)

    def setup_tray_icon(self):
        """Setup system tray icon"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
            
        self.tray_icon = QSystemTrayIcon(self)
        
        # Create tray icon menu
        tray_menu = QMenu()
        
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self.show_window)
        
        quit_action = tray_menu.addAction("Exit")
        quit_action.triggered.connect(self.quit_application)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # Set icon (you can replace this with your own icon path)
        app_icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
        self.tray_icon.setIcon(app_icon)
        self.tray_icon.setToolTip("devtical Flash Tool")
        self.tray_icon.show()

    def show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def quit_application(self):
        self.close()

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()

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
        
        # Create tab widget for Log and Terminal
        self.log_terminal_tabs = QTabWidget()
        
        # Log tab
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        
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
        
        self.log_terminal_tabs.addTab(log_tab, "📝 Operation Log")
        
        # Terminal tab
        self.terminal_widget = TerminalWidget()
        self.log_terminal_tabs.addTab(self.terminal_widget, "💻 Shell")
        
        right_layout.addWidget(self.log_terminal_tabs)
        
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
        
        toolbar.addSeparator()
        
        # Terminal actions
        terminal_action = QAction("💻 Terminal", self)
        terminal_action.setToolTip("Switch to Terminal tab")
        terminal_action.triggered.connect(self.switch_to_terminal)
        toolbar.addAction(terminal_action)
        
        log_action = QAction("📝 Log", self)
        log_action.setToolTip("Switch to Log tab")
        log_action.triggered.connect(self.switch_to_log)
        toolbar.addAction(log_action)

    def switch_to_terminal(self):
        self.log_terminal_tabs.setCurrentIndex(1)  # Switch to terminal tab

    def switch_to_log(self):
        self.log_terminal_tabs.setCurrentIndex(0)  # Switch to log tab

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
            QTabWidget::pane {
                border: 1px solid #444;
                background-color: #2d2d2d;
            }
            QTabBar::tab {
                background-color: #404040;
                color: white;
                padding: 8px 16px;
                border: 1px solid #555;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #0078D7;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #4a4a4a;
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
            QTabWidget::pane {
                border: 1px solid #ccc;
                background-color: #f9f9f9;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                color: #333;
                padding: 8px 16px;
                border: 1px solid #ccc;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #0078D7;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #d0d0d0;
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
        elif "spreadtrum" in device_lower or "unisoc" in device_lower or "sprd" in device_lower:
            self.device_type = "spreadtrum"
            self.device_info.setText("📱 Spreadtrum/Unisoc Device\nFDL files required for flashing")
        elif "xynos" in device_lower or "exynos" in device_lower or "samsung" in device_lower:
            self.device_type = "xynos"
            self.device_info.setText("📱 Exynos Device\nReady for flashing")
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
            (self.settings.get("avb_path", "avbtool"), "AVB Tool"),
            (self.settings.get("spd_path", "spd.py"), "SPD Client"),
            (self.settings.get("xyn_path", "xyn_cli.py"), "XYN Client")
        ]
        
        all_valid = True
        for tool_path, tool_name in tools_to_check:
            valid, message = ToolValidator.validate_tool(tool_path, tool_name)
            self.log_text.append(message)
            if not valid:
                all_valid = False
        
        if all_valid:
            self.log_text.append("✅ All tools are available")
        else:
            self.log_text.append("❌ Some tools are missing. Please check settings.")
        
        return all_valid

    def show_settings(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.Accepted:
            self.save_settings()
            self.apply_theme()
            self.log_text.append("✅ Settings updated")

    def setup_spd_operation(self):
        """Setup FDL files for SPD operations"""
        # Check if we already have FDL files set
        if self.fdl1_path and self.fdl2_path and os.path.exists(self.fdl1_path) and os.path.exists(self.fdl2_path):
            return True
            
        # Check for FDL files in the selected directory
        selected_dir = self.selected_directory
        if selected_dir:
            fdl1_candidates = glob.glob(os.path.join(selected_dir, "*fdl1*.bin")) + glob.glob(os.path.join(selected_dir, "FDL1.bin"))
            fdl2_candidates = glob.glob(os.path.join(selected_dir, "*fdl2*.bin")) + glob.glob(os.path.join(selected_dir, "FDL2.bin"))
            pac_candidates = glob.glob(os.path.join(selected_dir, "*.pac"))
            
            if fdl1_candidates and fdl2_candidates:
                self.fdl1_path = fdl1_candidates[0]
                self.fdl2_path = fdl2_candidates[0]
                self.log_text.append(f"✅ Auto-detected FDL1: {os.path.basename(self.fdl1_path)}")
                self.log_text.append(f"✅ Auto-detected FDL2: {os.path.basename(self.fdl2_path)}")
                return True
            elif pac_candidates:
                reply = QMessageBox.question(self, "PAC File Found", 
                                           f"Found PAC file: {os.path.basename(pac_candidates[0])}\n\n"
                                           "Do you want to extract FDL files from this PAC file?",
                                           QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.pac_file_path = pac_candidates[0]
                    return True
        
        # If no auto-detection, ask user to select files
        return self.prompt_for_spd_files()

    def prompt_for_spd_files(self):
        """Prompt user to select FDL files or PAC file"""
        msg = QMessageBox(self)
        msg.setWindowTitle("SPD Client - File Selection")
        msg.setText("SPD Client requires FDL1 and FDL2 files for operation.\n\nHow would you like to proceed?")
        
        btn_fdl = msg.addButton("Select FDL Files", QMessageBox.ActionRole)
        btn_pac = msg.addButton("Select PAC File", QMessageBox.ActionRole)
        btn_cancel = msg.addButton("Cancel", QMessageBox.RejectRole)
        
        msg.exec()
        
        if msg.clickedButton() == btn_fdl:
            return self.select_fdl_files()
        elif msg.clickedButton() == btn_pac:
            return self.select_pac_file()
        else:
            return False

    def select_fdl_files(self):
        """Let user select FDL1 and FDL2 files"""
        fdl1_path, _ = QFileDialog.getOpenFileName(self, "Select FDL1 File", "", "Binary Files (*.bin);;All Files (*)")
        if not fdl1_path:
            return False
            
        fdl2_path, _ = QFileDialog.getOpenFileName(self, "Select FDL2 File", "", "Binary Files (*.bin);;All Files (*)")
        if not fdl2_path:
            return False
            
        self.fdl1_path = fdl1_path
        self.fdl2_path = fdl2_path
        self.log_text.append(f"✅ Selected FDL1: {os.path.basename(self.fdl1_path)}")
        self.log_text.append(f"✅ Selected FDL2: {os.path.basename(self.fdl2_path)}")
        return True

    def select_pac_file(self):
        """Let user select a PAC file"""
        pac_path, _ = QFileDialog.getOpenFileName(self, "Select PAC File", "", "PAC Files (*.pac);;All Files (*)")
        if not pac_path:
            return False
            
        self.pac_file_path = pac_path
        self.log_text.append(f"✅ Selected PAC file: {os.path.basename(self.pac_file_path)}")
        return True

    def start_flash(self):
        selected_files = self.get_selected_files()
        if not selected_files:
            QMessageBox.warning(self, "No Files", "Please select at least one file to flash!")
            return
        
        if not self.validate_tools():
            QMessageBox.critical(self, "Tools Missing", "Required tools are not available. Please check settings.")
            return
        
        # For SPD devices, check if we have FDL files or PAC file
        if self.device_type == "spreadtrum":
            if not self.setup_spd_operation():
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
        
        # Set FDL files for SPD operations
        if self.device_type == "spreadtrum":
            self.current_flash_thread.set_fdl_files(self.fdl1_path, self.fdl2_path)
            if self.pac_file_path:
                self.current_flash_thread.set_pac_file(self.pac_file_path)
                
        self.connect_flash_thread()
        self.current_flash_thread.start()
        
        self.set_operation_buttons(False)

    def frp_erase(self):
        if not self.validate_tools():
            QMessageBox.critical(self, "Tools Missing", "Required tools are not available. Please check settings.")
            return
        
        # For SPD devices, check if we have FDL files
        if self.device_type == "spreadtrum":
            if not self.setup_spd_operation():
                return
        
        com_port = self.selected_device.split(' - ')[0]
        
        # Get basic FRP partitions for confirmation
        basic_partitions = self.settings.get("basic_frp_partitions", "frp,metadata,userdata")
        
        reply = QMessageBox.warning(self, "Confirm FRP Erase", 
                                  f"This will erase partitions: {basic_partitions}\n\n"
                                  f"Device: {com_port}\n"
                                  f"Continue?",
                                  QMessageBox.Yes | QMessageBox.No)
        
        if reply != QMessageBox.Yes:
            return
        
        self.log_text.append("🧹 Starting Basic FRP erase process...")
        self.current_flash_thread = FlashThread(self.device_type, [], com_port, "frp", self.settings)
        
        # Set FDL files for SPD operations
        if self.device_type == "spreadtrum":
            self.current_flash_thread.set_fdl_files(self.fdl1_path, self.fdl2_path)
            
        self.connect_flash_thread()
        self.current_flash_thread.start()
        
        self.set_operation_buttons(False)

    def advanced_frp(self):
        if not self.validate_tools():
            QMessageBox.critical(self, "Tools Missing", "Required tools are not available. Please check settings.")
            return
        
        # For SPD devices, check if we have FDL files
        if self.device_type == "spreadtrum":
            if not self.setup_spd_operation():
                return
        
        com_port = self.selected_device.split(' - ')[0]
        
        # Get advanced FRP partitions for confirmation
        advanced_partitions = self.settings.get("advanced_frp_partitions", "frp,metadata,userdata,persist")
        
        reply = QMessageBox.warning(self, "Confirm Advanced FRP", 
                                  f"This will perform Advanced FRP on:\n{advanced_partitions}\n\n"
                                  f"Device: {com_port}\n"
                                  f"Type: {self.device_type.capitalize()}\n"
                                  f"Continue?",
                                  QMessageBox.Yes | QMessageBox.No)
        
        if reply != QMessageBox.Yes:
            return
        
        self.log_text.append("🔧 Starting Advanced FRP process...")
        self.current_flash_thread = FlashThread(self.device_type, [], com_port, "advance_frp", self.settings)
        
        # Set FDL files for SPD operations
        if self.device_type == "spreadtrum":
            self.current_flash_thread.set_fdl_files(self.fdl1_path, self.fdl2_path)
            
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
        # Close terminal process
        if hasattr(self, 'terminal_widget'):
            self.terminal_widget.closeEvent(event)
        
        # Close flash thread if running
        if self.current_flash_thread and self.current_flash_thread.isRunning():
            reply = QMessageBox.question(self, "Operation in Progress", 
                                       "An operation is still running. Are you sure you want to quit?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.current_flash_thread.stop()
                self.current_flash_thread.wait(2000)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("devtical Flash Tool")
    app.setApplicationVersion("3.1")
    
    # Set application icon (you can replace this path with your icon)
    if os.path.exists("icon.ico"):
        app.setWindowIcon(QIcon("icon.ico"))
    
    # Set modern fusion style
    app.setStyle('Fusion')
    
    window = ModernFlashTool()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
