#!/usr/bin/env python3

"""
This code or file is part of 'ProcessorPy' project
copyright (c) 2023-2025, Aymen Brahim Djelloul, All rights reserved.
use of this source code is governed by MIT License that can be found on the project folder.

@author : Aymen Brahim Djelloul
version : 1.1
date : 27.05.2025
license : MIT

"""

# IMPORTS
import os
import sys
from datetime import datetime
from typing import Optional, Dict
from dataclasses import dataclass
from processorpy import Processor, Sensors
from webbrowser import open as open_url
from ._core import Updater, ProcessorPyResult

from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.Qt import (QApplication, QWidget, QSize, QThread, pyqtSignal, QLabel, QMessageBox,
                      QPushButton, Qt, QFrame, QPoint, QTimer, QIcon, QPixmap, QCursor, QFileDialog,
                      QGraphicsDropShadowEffect, QColor, QShortcut, QKeySequence, QVBoxLayout, QHBoxLayout
                      )


# Enable DPI scaling to prevent resolution change
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


@dataclass
class _Const:
    """ Const class contain global ProcessorPy Desktop application constants"""

    # Define global constants
    author: str = "Aymen Brahim Djelloul"
    version: str = "1.1"
    DATE: str = "27.05.2025"
    THIRD_PARTY: tuple = ("pyqt5", "requests")
    website_url: str = "https://aymenbrahimdjelloul.github.io/ProcessorPy"
    github_repo_url: str = "https://github.com/aymenbrahimdjelloul/ProcessorPy"

    # Define Updater constants
    updater_latest_version: str = "https://api.github.com/repos/aymenbrahimdjelloul/ProcessorPy/releases/latest"
    timeout: int = 5


class StyleManager:
    """Centralized style management for consistent theming"""

    # Color palette
    PRIMARY_COLOR: str = "#54656C"
    PRIMARY_HOVER: str = "#364950"
    ACCENT_COLOR: str = "#707CC0"
    DANGER_COLOR: str = "#CE3938"
    BACKGROUND_COLOR: str = "#d7dadd"
    TEXT_COLOR: str = "#000000"

    @classmethod
    def get_cpu_name_style(cls) -> str:
        """ This method will get cpu name style """
        return f"""
        QPushButton#cpu_name {{
            color: {cls.PRIMARY_COLOR};
            font-weight: 500;
            border: 0px;
            padding: 3px;
            background: transparent;
        }}
        QPushButton#cpu_name:hover {{
            color: {cls.PRIMARY_HOVER};
        }}
        """

    @classmethod
    def get_default_label_style(cls) -> str:
        """ This method will get default label style """
        return f"""
        QLabel#default_label {{
            color: {cls.PRIMARY_COLOR};
            font-weight: 500;
        }}
        """

    @classmethod
    def get_action_button_style(cls) -> str:
        """ This method will get action button style """
        return f"""
        QPushButton {{
            min-width: 60px;
            min-height: 30px;
            border: 1px solid transparent;
            background-color: transparent;
            color: {cls.TEXT_COLOR};
            font-weight: 500;
            padding: 8px 12px;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            color: {cls.ACCENT_COLOR};
            border: 1px solid {cls.ACCENT_COLOR};
            background-color: rgba(112, 124, 192, 0.1);
        }}
        QPushButton:disabled {{
            color: #888888;
            border: 1px solid #cccccc;
        }}
        """

    @classmethod
    def get_control_button_style(cls) -> str:
        """ This method will get control label style """
        return f"""
        QPushButton {{
            width: 25px;
            height: 25px;
            padding: 1px;
            color: {cls.TEXT_COLOR};
            border: 0;
            background: transparent;
            border-radius: 3px;
        }}
        QPushButton:hover {{
            color: {cls.DANGER_COLOR};
            background-color: rgba(206, 57, 56, 0.1);
        }}
        """

    @classmethod
    def get_info_label_style(cls) -> str:
        """ This method will get info label style """
        return f"""
        QLabel {{
            color: {cls.TEXT_COLOR};
            background-color: {cls.BACKGROUND_COLOR};
            font-weight: 500;
            border: 1px solid {cls.BACKGROUND_COLOR};
            border-radius: 4px;
            padding: 4px 8px;
            margin: 1px;
        }}
        """

    @classmethod
    def get_priority_sensor_style(cls) -> str:
        """ This method will get priorities sensor style """
        return f"""
        QLabel {{
            color: {cls.TEXT_COLOR};
            background-color: {cls.ACCENT_COLOR};
            font-weight: 600;
            border: 1px solid {cls.ACCENT_COLOR};
            border-radius: 4px;
            padding: 6px 10px;
            margin: 2px;
        }}
        """


class FontManager:
    """Manages font loading and fallback"""

    def __init__(self) -> None:
        self.app_font: str = self._load_font()

    @staticmethod
    def _load_font() -> str:
        """Load custom font with fallback"""
        font_paths = [
            "../Assets/Ubuntu-Regular.ttf",
            "./Assets/Ubuntu-Regular.ttf",
            "Ubuntu-Regular.ttf"
        ]

        for font_path in font_paths:
            try:
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id != -1:
                    return "Ubuntu"
            except Exception:
                continue

        return "Helvetica"  # Fallback font

    def get_font(self, size: int = 11, weight: Optional[int] = None) -> QFont:
        """Get font with specified size and weight"""
        font = QFont(self.app_font, size)
        if weight:
            font.setWeight(weight)
        return font


class InfoDisplayWidget(QWidget):
    """Optimized widget for displaying CPU/sensor information with absolute positioning"""

    # Class constants for consistent sizing
    LABEL_WIDTH = 380
    LABEL_HEIGHT = 30
    DEFAULT_MARGIN = 10
    INFO_X = 10
    SENSOR_X = 220

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        # Use ordered dicts to maintain insertion order
        self.info_labels: dict = {}
        self.sensor_labels: dict = {}

        # Track positions
        self.current_info_y: int = self.DEFAULT_MARGIN
        self.current_sensor_y: int = self.DEFAULT_MARGIN

        # Pre-create fonts
        self.default_font = QFont("Segoe UI", 9)
        self.priority_font = QFont("Segoe UI", 9, QFont.Weight.Bold)

        # Pre-load styles
        self.info_style = StyleManager.get_info_label_style()
        self.priority_style = StyleManager.get_priority_sensor_style()

    def add_info_item(self, key: str, value: str, x: int = None, y: int = None, font: QFont = None) -> QLabel:
        """Add an information item with optimized layout"""
        if x is None:
            x = self.INFO_X

        label = self._create_label(
            key=key,
            value=value,
            x=x,
            y=y,
            font=font or self.default_font,
            style=self.info_style,
            y_counter=self.current_info_y,
            storage=self.info_labels
        )
        return label

    def add_sensor_item(self, key: str, value: str, x: int = None, y: int = None,
                        font: QFont = None, priority: bool = False) -> QLabel:
        """Add a sensor item with optimized layout"""
        if x is None:
            x = self.SENSOR_X

        label = self._create_label(
            key=key,
            value=value,
            x=x,
            y=y,
            font=font or (self.priority_font if priority else self.default_font),
            style=self.priority_style if priority else self.info_style,
            y_counter=self.current_sensor_y,
            storage=self.sensor_labels
        )
        return label

    def _create_label(self, key: str, value: str, x: int, y: int, font: QFont,
                      style: str, y_counter: int, storage: dict) -> QLabel:
        """Internal method to create and position labels efficiently"""
        formatted_text = f"{key}: {value}" if ":" not in key else f"{key} {value}"
        label = QLabel(formatted_text, self)

        # Apply styles and settings
        label.setStyleSheet(style)
        label.setFont(font)
        label.setFixedSize(self.LABEL_WIDTH, self.LABEL_HEIGHT)

        # Calculate position
        if y is None:
            y = y_counter
            setattr(self, f"current_{'info' if storage is self.info_labels else 'sensor'}_y",
                    y + self.LABEL_HEIGHT + self.DEFAULT_MARGIN)

        label.move(x, y)
        storage[key] = label
        return label

    def update_sensor_value(self, key: str, value: str) -> None:
        """Optimized sensor value update with minimal operations"""
        if label := self.sensor_labels.get(key):
            if ":" in key:
                label.setText(f"{key.split(':')[0]}: {value}")
            else:
                label.setText(f"{key}: {value}")

    def clear(self) -> None:
        """Efficiently clear all widgets"""
        for label in (*self.info_labels.values(), *self.sensor_labels.values()):
            label.deleteLater()
        self.info_labels.clear()
        self.sensor_labels.clear()
        self.current_info_y = self.DEFAULT_MARGIN
        self.current_sensor_y = self.DEFAULT_MARGIN


class TitleBarWidget(QWidget):
    """Custom title bar with window controls"""

    close_requested = pyqtSignal()
    minimize_requested = pyqtSignal()

    def __init__(self, title: str = "", icon_path: str = "", font_manager: FontManager = None, parent=None) -> None:
        super().__init__(parent)
        self.font_manager = font_manager or FontManager()
        self.init_ui(title, icon_path)

    def init_ui(self, title: str, icon_path: str) -> None:
        """Initialize the title bar UI"""

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # App icon
        if icon_path:
            icon_label = QLabel()
            try:
                pixmap = QPixmap(icon_path).scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_label.setPixmap(pixmap)
            except Exception:
                icon_label.setText("📊")  # Fallback icon

            layout.addWidget(icon_label)

        # Title
        if title:
            title_label = QLabel(title)
            title_label.setFont(self.font_manager.get_font(10))
            title_label.setStyleSheet("color: #54656C; font-weight: 500;")
            layout.addWidget(title_label)

        # Spacer
        layout.addStretch()

        # Window controls
        minimize_btn = QPushButton("−")
        minimize_btn.setFont(self.font_manager.get_font(12))
        minimize_btn.setStyleSheet(StyleManager.get_control_button_style())
        minimize_btn.setCursor(QCursor(Qt.PointingHandCursor))
        minimize_btn.clicked.connect(self.minimize_requested.emit)

        close_btn = QPushButton("✕")
        close_btn.setFont(self.font_manager.get_font(10))
        close_btn.setStyleSheet(StyleManager.get_control_button_style())
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.clicked.connect(self.close_requested.emit)

        layout.addWidget(minimize_btn)
        layout.addWidget(close_btn)


class App(QWidget):
    """Main application window with improved structure and performance"""

    def __init__(self) -> None:
        super().__init__()

        # Initialize managers
        self.icon_paths = None
        self.font_manager = FontManager()
        self.cpu_info: Optional[Dict] = None
        # Create Sensor object
        self.sensors = Sensors()

        # Initialize about widget
        self.about_widget = About()
        # Initialize updater widget
        # self.updater = UpdateWidget()
        self.thread = None
        self.worker = None

        # Timers
        self.sensors_timer = QTimer()
        self.sensors_timer.timeout.connect(self._update_sensors)

        # UI Components
        self.wait_label: Optional[QLabel] = None
        self.cpu_name_button: Optional[QPushButton] = None
        self.info_display: Optional[InfoDisplayWidget] = None
        self.save_button: Optional[QPushButton] = None

        # Window setup
        self.init_window()
        self.init_ui()

        # Load CPU info asynchronously
        self.load_cpu_info()

    def init_window(self) -> None:
        """Initialize window properties"""

        self.setWindowTitle("ProcessorPy")
        self.setFixedSize(QSize(470, 590))
        self.setWindowFlags(Qt.FramelessWindowHint)

        # Try to set window icon
        self.icon_paths: tuple | str = ("../Assets/icon.ico", "./Assets/icon.ico", "icon.ico")
        for icon_path in self.icon_paths:

            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                self.icon_paths = icon_path

                break

    def init_ui(self) -> None:
        """Initialize the user interface"""

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Title bar
        title_bar = TitleBarWidget("ProcessorPy", self.icon_paths, self.font_manager)
        title_bar.close_requested.connect(self.close)
        title_bar.minimize_requested.connect(self.showMinimized)
        main_layout.addWidget(title_bar)

        # Content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 10, 15, 15)

        # CPU name button (initially empty)
        self.cpu_name_button = QPushButton("Loading...")
        self.cpu_name_button.setObjectName("cpu_name")
        self.cpu_name_button.setFont(self.font_manager.get_font(12))
        self.cpu_name_button.setStyleSheet(StyleManager.get_cpu_name_style())
        self.cpu_name_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.cpu_name_button.clicked.connect(self.copy_cpu_name)
        content_layout.addWidget(self.cpu_name_button)

        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #cccccc; margin: 5px 0;")
        content_layout.addWidget(line)

        # Loading message
        self.wait_label = QLabel("Please wait...")
        self.wait_label.setAlignment(Qt.AlignCenter)
        self.wait_label.setFont(self.font_manager.get_font(13))
        self.wait_label.setStyleSheet(StyleManager.get_default_label_style())
        content_layout.addWidget(self.wait_label)

        # Info display (initially hidden)
        self.info_display = InfoDisplayWidget()
        self.info_display.setFixedSize(420, 400)  # Set fixed size for absolute positioning
        self.info_display.hide()
        content_layout.addWidget(self.info_display)

        # Spacer
        content_layout.addStretch()

        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(5, 10, 5, 5)

        about_btn = QPushButton("About")
        about_btn.setFont(self.font_manager.get_font())
        about_btn.setStyleSheet(StyleManager.get_action_button_style())
        about_btn.setCursor(QCursor(Qt.PointingHandCursor))
        about_btn.clicked.connect(self.show_about)

        self.save_button = QPushButton("Save")
        self.save_button.setFont(self.font_manager.get_font())
        self.save_button.setStyleSheet(StyleManager.get_action_button_style())
        self.save_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.save_button.clicked.connect(self.save_info)
        self.save_button.setEnabled(False)

        button_layout.addWidget(about_btn)
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()

        content_layout.addLayout(button_layout)
        main_layout.addWidget(content_widget)

    def load_cpu_info(self) -> None:
        """This method will load CPU info using a worker thread."""

        self.thread = QThread()
        self.worker = Worker(Processor())  # Assume Worker takes a Processor object

        self.worker.moveToThread(self.thread)

        # Connect signals
        self.thread.started.connect(self.worker.run)
        self.worker.result_ready.connect(self.display_cpu_info)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def display_cpu_info(self, cpu_info: Dict) -> None:
        """Display CPU information in the UI using absolute positioning"""
        self.cpu_info = cpu_info

        # Update CPU name button
        name: str = cpu_info.get("name", "Unknown CPU").value
        self.cpu_name_button.setText(name)
        # Remove name from cpu name dict
        self.cpu_info.pop("name")

        # Hide loading message
        self.wait_label.hide()

        # First add the priority sensor readings (Voltage and Usage at the top right)
        priority_sensors: dict = {
            "Voltage": "1.25V",
            "Total Load": "45%",  # Usage
        }

        # Reset sensor Y position for priority items
        self.info_display.current_sensor_y = 10

        for key, value in priority_sensors.items():
            self.info_display.add_sensor_item(
                key, value, 50, None,  # x=220 for right column, y=None for auto-positioning
                self.font_manager.get_font(10),
                priority=True  # Use priority styling
            )

        # Add CPU info (left column) - reset Y position
        self.info_display.current_info_y = 10

        for key, value in cpu_info.items():
            if key != "name":  # Skip name as it's in the button
                self.info_display.add_info_item(
                    key, value.value, 10, None,  # x=10 for left column, y=None for auto-positioning
                    self.font_manager.get_font(10)
                )

        # Add remaining sensor readings (right column, continuing after priority sensors)
        remaining_sensors: dict = {
            "Speed": "4.2 GHz",
            "Temperature": "65°C"
        }

        for key, value in remaining_sensors.items():
            self.info_display.add_sensor_item(
                key, value, 220, None,  # x=220 for right column, y=None for auto-positioning
                self.font_manager.get_font(10)
            )

        self.info_display.show()
        self.save_button.setEnabled(True)

        # Start CPU monitoring
        self.start_monitoring()

    def start_monitoring(self) -> None:
        """Start monitoring CPU metrics"""
        self.sensors_timer.start(2000)  # Update every 2 seconds

    def _update_sensors(self) -> None:
        """Update CPU load and other dynamic metrics"""

        # Mock dynamic data - replace with actual sensor readings
        # dynamic_values: dict = {
        #     "Voltage": f"{self.sensors.get_cpu_voltage():.2f}V",
        #     "Total Load": f"{self.sensors.get_cpu_usage()}%",
        #     "Speed": f"{self.sensors.get_clock_speed():.1f} GHz",
        #     "Temperature": f"{self.sensors.get_cpu_temperature()}°C"
        # }
        #
        # for key, value in dynamic_values.items():
        #     self.info_display.update_sensor_value(key, value)

    def copy_cpu_name(self) -> None:
        """Copy CPU name to clipboard"""

        if self.cpu_info and "name" in self.cpu_info:
            try:
                # Note: pyperclip import was missing in original code
                # You would need to install and import pyperclip for this to work
                # import pyperclip
                # pyperclip.copy(self.cpu_info["Name"])

                # Visual feedback
                self.cpu_name_button.setText("Copied!")
                QTimer.singleShot(1000, lambda: self.cpu_name_button.setText(self.cpu_info["name"]))
            except Exception as e:
                print(e)

    def save_info(self) -> None:
        """Save detailed CPU information as a formatted TXT report."""
        if not self.cpu_info:
            QMessageBox.warning(self, "No Data", "No CPU information available to save.")
            return

        try:
            now: float = datetime.now()
            timestamp: str = now.strftime("%Y%m%d_%H%M%S")
            default_filename: str = f"cpu_report_{timestamp}.txt"

            # Ask user for save location
            filepath, _ = QFileDialog.getSaveFileName(
                self,
                "Save CPU Report",
                default_filename,
                "Text Files (*.txt);;All Files (*)"
            )

            if not filepath:
                return  # User cancelled

            # Ensure .txt extension
            if not filepath.lower().endswith('.txt') and '.' not in os.path.basename(filepath):
                filepath += '.txt'

            # Build report content
            report_lines: list = [
                "=" * 60,
                f"{'ProcessorPy - CPU Report':^60}",
                f"{now.strftime('%A, %B %d, %Y %H:%M:%S'):^60}",
                "=" * 60,
                "",
                "CPU Information:",
                "-" * 60,
            ]

            # Format key-value CPU info
            max_key_len = max(len(str(k)) for k in self.cpu_info)
            for key, value in self.cpu_info.items():
                if isinstance(value, str) and '\n' in value:
                    lines = value.split('\n')
                    report_lines.append(f"{key.ljust(max_key_len)} : {lines[0]}")
                    for line in lines[1:]:
                        report_lines.append(f"{' ' * (max_key_len + 3)}{line}")
                else:
                    report_lines.append(f"{key.ljust(max_key_len)} : {value}")

            # Software metadata
            report_lines += [
                "",
                "-" * 60,
                "About:",
                f"Application : ProcessorPy",
                f"Version     : {getattr(self, 'version', '1.0')}",
                f"Author      : {getattr(self, 'author', 'Your Name')}",
                f"Total Entries: {len(self.cpu_info)}",
                "=" * 60,
            ]

            report_text: str = "\n".join(report_lines)

            # Save to file
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(report_text)
            except PermissionError:
                QMessageBox.critical(self, "Permission Error",
                                     "Cannot write to the selected location.\nPlease choose a different location or run as administrator.")
                return
            except OSError as e:
                QMessageBox.critical(self, "File Error",
                                     f"Cannot create file at the selected location:\n{str(e)}")
                return

            # Feedback (if save_button exists)
            if hasattr(self, 'save_button'):
                original_text = self.save_button.text()
                self.save_button.setText("✓ Saved!")
                QTimer.singleShot(2000, lambda: self.save_button.setText(original_text))

            # Show confirmation
            QMessageBox.information(self, "Success",
                                    f"CPU report saved successfully!\n\nLocation: {filepath}")

        except Exception as e:
            QMessageBox.critical(self, "Error",
                                 f"An unexpected error occurred while saving the report:\n{str(e)}")

    def show_about(self) -> None:
        """Show about dialog"""
        self.about_widget.show()

    def mousePressEvent(self, event) -> None:
        """Handle mouse press for window dragging"""

        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.globalPos()

    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move for window dragging"""

        if (event.buttons() == Qt.LeftButton and
                hasattr(self, 'drag_start_position')):
            delta = event.globalPos() - self.drag_start_position
            self.move(self.pos() + delta)
            self.drag_start_position = event.globalPos()

    def closeEvent(self, event) -> None:
        """Clean up when closing"""
        # Stop sensor timer
        self.sensors_timer.stop()
        # exit the application
        sys.exit(0)


class Worker(QThread):
    """ This is the Worker class contain QThread to get cpu information values"""

    result_ready: pyqtSignal = pyqtSignal(dict)

    def __init__(self, cpu_obj) -> None:
        super(Worker, self).__init__(parent=None)
        self.cpu_obj: _Processor = cpu_obj

    def run(self) -> None:
        """ This method will get the cpu information using threading to prevent program lag"""

        # Get all cpu information
        cpu_info: dict = self.cpu_obj.get_all_info()
        # emit result
        self.result_ready.emit(cpu_info)


class MoreWidget(QLabel):

    style: str = """
    QLabel {
        border: 1px solid;
        border-radius: 7px;
        background-color: #ebe8ed;
        border-color: #ebe8ed;
    }
    
    """
    
    def __init__(self) -> None:
        super(MoreWidget, self).__init__(parent=None)

        self.old_pos = None

        # Setup widget
        self.setStyleSheet(self.style)
        self.setFixedSize(QSize(800, 500))
        self.setWindowFlags(Qt.FramelessWindowHint)

    def mousePressEvent(self, event) -> None:
        """ This method will capture the mouse press event"""
        self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event) -> None:
        """ This method will capture the mouse move event"""
        try:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()
        except TypeError:
            pass


class About(QLabel):
    """ About class contain the about widget for ProcessorPy software """

    style: str = """
    QLabel {
        border: 1px solid;
        border-radius: 7px;
        background-color: #ebe8ed;
        border-color: #ebe8ed;
    }
    QLabel#logo {
        border: none;
        color: #8B9EA7;
        font-weight: 500;
    }
    QLabel#others {
        color: #404040;
        font-weight: 500;
        border: none;
    }
    QPushButton {
        width: 60px;
        height: 18px;
        padding: 5px;
        border: 1px solid;
        border-radius: 7px;
        color: white;
    }
    QPushButton#visitus {
        border-color: #dbdbdb;
        background-color: #8B9EA7;
        width: 70px;
    }
    QPushButton#githubBtn {
        border-color: #4754c9;
        background-color: #37429e;
    }
    QPushButton#hyperlink {
        color: #1046a3;
        border: none;
        background: none;
        padding: 0;
        font-weight: 400;
        text-decoration: underline;

    }

    QPushButton#exit_button {
        width: 20px;
        height: 18px;
        padding: 0;
        background-color: transparent;
        border: 1px solid;
        border-radius: 7px;
        border-color: transparent;
        color: black;
    }

    """

    def __init__(self) -> None:
        super(About, self).__init__(parent=None)

        # set about widget
        self.setStyleSheet(self.style)
        self.setFixedSize(QSize(500, 550))
        self.setWindowFlags(Qt.FramelessWindowHint)

        # Create the exit button
        exit_button = QPushButton("X", self)
        exit_button.move(self.width() - 30, 10)
        exit_button.setObjectName("exit_button")
        exit_button.setCursor(Qt.PointingHandCursor)
        exit_button.setFont(QFont("Ubuntu", 12))
        exit_button.setStyleSheet(self.style)
        exit_button.clicked.connect(self.hide)

        # create logo label
        self.logo = QLabel('ProcessorPy', self)
        self.logo.setObjectName('logo')
        self.logo.move(15, 20)
        self.logo.setFont(QFont('Ubuntu', 12))
        self.logo.setStyleSheet(self.style)
        self.logo.adjustSize()

        # Developed by
        self.developed_by = QLabel(self)
        self.developed_by.setObjectName('others')
        self.developed_by.setText(f"Developed by {_Const.author}")
        self.developed_by.move(20, 80)
        self.developed_by.setFont(QFont('Ubuntu', 10))
        self.developed_by.setStyleSheet(self.style)

        # build label
        self.license = QLabel(self)
        self.license.setObjectName('others')
        self.license.setText(f"built on {_Const.DATE}")
        self.license.move(20, 115)
        self.license.setFont(QFont('Ubuntu', 10))

        self.license.setStyleSheet(self.style)

        # runtime version
        self.version = QLabel(self)
        self.version.setObjectName('others')
        self.version.setText(f"Runtime version : {_Const.version}")
        self.version.move(20, 180)
        self.version.setFont(QFont('Ubuntu', 10))
        self.version.setStyleSheet(self.style)

        # copyright all right reserved label
        self.copyright = QLabel(self)
        self.copyright.setObjectName('others')
        self.copyright.setText('All Copyright © are reserved under\n MIT License')
        self.copyright.move(20, 210)
        self.copyright.setFont(QFont('Ubuntu', 10))
        self.copyright.setStyleSheet(self.style)

        # contact me button
        self.contact_me_btn = QPushButton('Visit us', self)
        self.contact_me_btn.setObjectName('visitus')
        self.contact_me_btn.move(100, self.height() - 30)
        self.contact_me_btn.setStyleSheet(self.style)
        self.contact_me_btn.setFont(QFont('Ubuntu', 11))
        self.contact_me_btn.setCursor(Qt.PointingHandCursor)
        self.contact_me_btn.clicked.connect(lambda: open_url(_Const.website_url))

        # GitHub repo button
        self.github_repo_btn = QPushButton('GitHub', self)
        self.github_repo_btn.setObjectName('githubBtn')
        self.github_repo_btn.move(15, self.height() - 30)
        self.github_repo_btn.setStyleSheet(self.style)
        self.github_repo_btn.setFont(QFont('Ubuntu', 11))
        self.github_repo_btn.setCursor(Qt.PointingHandCursor)
        self.github_repo_btn.clicked.connect(lambda: open_url(_Const.github_repo_url))

    def mousePressEvent(self, event) -> None:
        """ This method will capture the mouse press event"""
        self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event) -> None:
        """ This method will capture the mouse move event"""
        try:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()
        except TypeError:
            pass


class UpdateWidget(QWidget):

    """
    This Updater class contain the widget and logic for
    checking and install updates for ProcessorPy software

     """

    style: str = """
    QLabel {
        color: #4E4D4D;
        weight: 500;
    }
    
    QPushButton {
        width: 80px;
        height: 35px;
        color: #4E4D4D;
        
        border: 1px;
        border-radius: 4px;
        border-color: #54656C;
        background-color: transparent;
    }
    
    QPushButton::hover {
        font-size: 16px;
    }
    """

    def __init__(self) -> None:
        super(UpdateWidget, self).__init__(parent=None)

        # Create updater object
        _updater = Updater(_Const.version)
        _update_data = _updater.latest_data

        # First check if new update available
        if not _updater.is_update:
            self.hide()

        # Set up the Updater window
        self.REQUEST_DATA: None | dict = None
        self.setFixedSize(QSize(500, 120))
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: #DCDDDD;")
        self.old_pos: int | None = None

        self.update_label = QLabel(self)
        self.update_label.setFont(QFont("Ubuntu", 11))
        self.update_label.move(10, 20)
        self.update_label.setStyleSheet(self.style)

        # Create Cancel button
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.move(15, 80)
        self.cancel_button.setStyleSheet(self.style)
        self.cancel_button.setFont(QFont("Ubuntu", 11))
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.clicked.connect(self._cancel)

        # Create Install now button
        self.install_button = QPushButton("Install", self)
        self.install_button.move(110, 80)
        self.install_button.setStyleSheet(self.style)
        self.install_button.setFont(QFont("Ubuntu", 10))
        self.install_button.setCursor(Qt.PointingHandCursor)
        self.install_button.clicked.connect(self._install)



    def mousePressEvent(self, event) -> None:
        """ This method will be called when a mouse button is pressed."""
        self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event) -> None:
        """ This method will be called when a mouse button is moved."""

        try:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()
        except TypeError:
            pass

    def _set_update(self) -> None:
        """ This method will set up the update widget"""

        # Set the new version update description
        text: str = f"New update available! Please download the latest version. {self.REQUEST_DATA['tag_name']}\n\n"\
                    f" Download size : {self.bytes_to_megabytes(self.REQUEST_DATA['assets'][0]['size'])} Mb"

    def _install(self) -> None:
        """ This method will direct use to download the latest version from website"""

    def _cancel(self) -> None:
        """ This method will cancel the whole update process"""

        # Hide updater widget
        self.hide()
        # Kill it
        self.deleteLater()


    @staticmethod
    def bytes_to_megabytes(num: int) -> int:
        """ This method will convert the given bytes to megabytes """
        return num // 1048576


def __main__() -> None:
    """ This method will start the app """

    app = QApplication(sys.argv)

    _window = App()
    _window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    __main__()
