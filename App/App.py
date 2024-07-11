"""
@auhtor : Aymen Brahim Djelloul
version : 1.0
date : 28.06.2024
license : MIT

"""

# IMPORTS
from PyQt5.Qt import (QApplication, QWidget, QSize, QThread, pyqtSignal, QLabel, QPushButton, Qt, QFrame, QPoint,
                      QTimer, QIcon, QPixmap)

from PyQt5.QtGui import QFont, QFontDatabase
from ProcessorPy import Processor, Sensors
from time import sleep
from webbrowser import open as open_url
import subprocess
import requests
import sys
import os

# DEFINE GLOBAL VARIABLES
AUTHOR: str = "Aymen Brahim Djelloul"
VERSION: str = "1.0.1"
DATE: str = "28.06.2024"


class App(QWidget):
    """

    """

    STYLE = """
    
    QPushButton#cpu_name {
        color: #54656C;
        weight: 500;
        border: 0px;
        padding: 3px;

    }

    QPushButton#cpu_name::hover {
        color: #364950;
    }
    
    QLabel#default_label {
        color: #54656C;
        weight: 500;
    }
    """
    BUTTON1_STYLE = """
    
    QPushButton {
        width: 50px;
        height: 50px;
        border: 0;
        background-color: transparent;
        color: #000000;
        weight: 500;
        padding: 5px;
    
    }
    
    QPushButton::hover {
        color: #707CC0
        border: 1px;
        border-radius: 3px;
        border-color: #707CC0;
        margin-bottom: 3px;
        
    }
    """

    FLAG_BUTTON_STYLE = """
    QPushButton {
        width: 25px;
        height: 25px;
        padding: 1px;
        color: #000000;
        border: 0;
    }

    QPushButton::hover {
        color: #CE3938;
    }

    """

    APP_FONT: str = ""

    def __init__(self):
        super(App, self).__init__(parent=None)

        # Add Ubuntu font
        font_id = QFontDatabase.addApplicationFont("Assets\\Ubuntu-Regular.ttf")

        # With error handling in cases cant import the font file
        if font_id == -1:
            self.APP_FONT: str = "Helvetica"

        else:
            self.APP_FONT: str = "Ubuntu"

        # Create About and updater objects
        self.about = About()
        self.updater = Updater()

        # Create Processor object
        cpu = Processor()
        self.sensors = Sensors()

        # Create a worker to get cpu information
        my_worker = Worker(cpu)
        my_worker.result_ready.connect(self.get_cpu_info)
        my_worker.start()

        # Setup APP window
        self.setWindowTitle(f"ProcessorPy")
        self.setFixedSize(QSize(400, 520))
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowIcon(QIcon("Assets/icon.ico"))

        # Create flags button
        # Create the exit button
        exit_button = QPushButton("X", self)
        exit_button.move(370, 5)
        exit_button.setCursor(Qt.PointingHandCursor)
        exit_button.setFont(QFont(self.APP_FONT, 12))
        exit_button.setStyleSheet(self.FLAG_BUTTON_STYLE)
        exit_button.clicked.connect(sys.exit)

        # Create minimize button
        minimize_button = QPushButton("-", self)
        minimize_button.move(350, 5)
        minimize_button.setCursor(Qt.PointingHandCursor)
        minimize_button.setFont(QFont(self.APP_FONT, 12))
        minimize_button.setStyleSheet(self.FLAG_BUTTON_STYLE)
        minimize_button.clicked.connect(self.showMinimized)

        # Set the App icon
        app_icon = QLabel(self)
        app_icon.move(5, 5)

        pixmap = QPixmap("Assets/icon.ico").scaled(22, 22)
        app_icon.setPixmap(pixmap)
        app_icon.setStyleSheet("""
        border: 0;
        height: 10px;
        weight: 10px;
        """)

        # Create label for cpu name
        cpu_name = QPushButton(cpu.name, self)
        cpu_name.move(10, 35)
        cpu_name.setFont(QFont(self.APP_FONT, 12))
        cpu_name.setObjectName("cpu_name")
        cpu_name.setStyleSheet(self.STYLE)
        cpu_name.setCursor(Qt.PointingHandCursor)
        cpu_name.clicked.connect(self.cpu_name_clicked)

        # Create a horizontal line separator
        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #000000;")

        # Set the size and position of the line
        line.setGeometry(30, 65, 330, 1)  # x, y, width, height

        # Create the please wait label
        self.wait_label = QLabel("Please Wait..", self)
        self.wait_label.setObjectName("default_label")
        self.wait_label.setStyleSheet(self.STYLE)
        self.wait_label.setFont(QFont(self.APP_FONT, 13))

        # Move the label to the center
        self.wait_label.move(151, 239)

        # Create About button
        about_button = QPushButton("About", self)
        about_button.move(15, 460)
        about_button.setFont(QFont("Ubuntu", 11))
        about_button.setStyleSheet(self.BUTTON1_STYLE)
        about_button.setCursor(Qt.PointingHandCursor)

        about_button.clicked.connect(self.about.show)

        # Create Save button
        self.save_button = QPushButton("Save", self)
        self.save_button.move(90, 460)
        self.save_button.setFont(QFont("Ubuntu", 11))
        self.save_button.setStyleSheet(self.BUTTON1_STYLE)
        self.save_button.clicked.connect(self.save)
        self.save_button.setCursor(Qt.PointingHandCursor)

        self.save_button.setDisabled(True)

        # NOTE : THIS FEATURE WILL ENABLED IN FUTURE UPDATES !

        # # Create more button
        # self.more_button = QPushButton("More", self)
        # self.more_button.move(320, 460)
        # self.more_button.setFont(QFont("Ubuntu", 11))
        # self.more_button.setStyleSheet(self.BUTTON1_STYLE)
        # self.more_button.setCursor(Qt.PointingHandCursor)
        # # self.more_button.clicked.connect()
        # self.more_button.setDisabled(True)

    def mousePressEvent(self, event):
        self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        try:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()
        except TypeError:
            pass

    def get_cpu_info(self, cpu_info: dict):
        """ This method will be connected to the worker to fill all information when it's ready"""

        style: str = """
        QLabel {
            color: #000000;
            background-color: #d7dadd;
            weight: 500;
            border: 1px;
            border-radius: 3px;
            border-color: #d7dadd;
            padding: 2px;
            }
        """

        self.cpu_info: dict = cpu_info

        # Hide the please wait label
        self.wait_label.hide()

        # Define x and y
        x: int = 10
        y: int = 80

        # Iterate through dictionary to put cpu info
        for k, v in cpu_info.items():

            # Get the formatted string
            formatted_string = f"{k} : {v}"

            # Create the info label
            info_label = QLabel(formatted_string, self)
            info_label.move(x, y)
            info_label.setFont(QFont(self.APP_FONT, 11))
            info_label.resize(QSize(260, 25))
            # info_label.setObjectName("info_label")
            info_label.setStyleSheet(style)
            info_label.show()

            y += 30

        # Create the sensors readings
        # Create the voltage sensor
        voltage_label = QLabel(f"voltage : {self.sensors.get_cpu_voltage()}", self)
        voltage_label.move(280, 80)
        voltage_label.setFont(QFont(self.APP_FONT, 11))
        voltage_label.resize(QSize(110, 25))
        voltage_label.setStyleSheet(style)
        voltage_label.show()

        # Create the max clock speed sensor
        self.clock_speed = QLabel(f"Speed : {self.sensors.get_cpu_clock_speed()}", self)
        self.clock_speed.move(280, 110)
        self.clock_speed.setFont(QFont(self.APP_FONT, 10))
        self.clock_speed.resize(QSize(110, 25))
        self.clock_speed.setStyleSheet(style)
        self.clock_speed.show()

        # Set a QTimer to update the clock speed label
        # Set up the timer
        # self.clock_speed_timer = QTimer(self)
        # self.clock_speed_timer.timeout.connect(self.update_clock_speed)
        # self.clock_speed_timer.start(1000)  # Update every 1000 milliseconds (1 second)

        # Define empty list for labels to update
        # labels: list = []

        # # Iter through cores count
        # y = 100
        # for i in range(self.cpu_info["Cores"]):
        #
        #     # Create cores load sensor readings
        #     core_load_label = QLabel(f"Core {i}: {self.sensors.get_cpu_usage(per_core=True)[i]}%", self)
        #     core_load_label.move(280, y)
        #     core_load_label.setFont(QFont("Ubuntu", 11))
        #     core_load_label.resize(QSize(90, 25))
        #     core_load_label.setStyleSheet(style)
        #     core_load_label.show()
        #
        #     # Update the label
        #     labels.append(core_load_label)
        #
        #     # Increase y
        #     y += 30

        # Create total load sensor readings
        self.total_load_label = QLabel(f"Total : {self.sensors.get_cpu_usage(per_core=False)}%", self)
        self.total_load_label.move(280, 140)
        self.total_load_label.setFont(QFont(self.APP_FONT, 10))
        self.total_load_label.resize(QSize(90, 25))
        self.total_load_label.setStyleSheet(style)
        self.total_load_label.show()

        # Set up the timer
        self.cpu_load_timer = QTimer(self)
        self.cpu_load_timer.timeout.connect(self.update_cpu_load)
        self.cpu_load_timer.start(2000)  # Update every 1000 milliseconds (1 second)

        # enable the save button
        self.save_button.setDisabled(False)

        # Clear memory
        del x, y, style, k, v, formatted_string, info_label

    def cpu_name_clicked(self):
        """ This method will copy the cpu name to the clipboard"""

    def save(self):
        """ This method will save the cpu information in text file"""

    def update_clock_speed(self):
        """ This method will update the current clock speed label"""
        self.clock_speed.setText(f"Clock : {self.sensors.get_cpu_clock_speed()}")

    def update_cpu_load(self):
        """ This method will update the cpu label per core and total"""
        self.total_load_label.setText(f"Total : {self.sensors.get_cpu_usage(per_core=False)}%")


# Define the Worker class
class Worker(QThread):
    """


    """

    result_ready = pyqtSignal(dict)

    def __init__(self, cpu_obj):
        super(Worker, self).__init__()
        self.cpu_obj = cpu_obj

    def run(self):
        """ This method will get the cpu information using threading to prevent program lag"""

        cpu_info: dict = {
            "Manufacturer": self.cpu_obj.manufacturer,
            "Architecture": self.cpu_obj.architecture,
            "Family": self.cpu_obj.family,
            "Stepping": self.cpu_obj.stepping(),
            "Socket": self.cpu_obj.socket,
            "L1 Cache": self.cpu_obj.l1_cache_size(),
            "L2 Cache": self.cpu_obj.l2_cache_size(),
            "L3 Cache": self.cpu_obj.l3_cache_size(),
            "Max clock speed": self.cpu_obj.max_clock_speed(),
            "Cores": self.cpu_obj.core_count(),
            "Threads": self.cpu_obj.core_count(logical=True),
        }
        # Get if the cpu support virtualization
        if self.cpu_obj.is_support_virtualization():
            cpu_info.update({"Virtualization": "YES"})
        else:
            cpu_info.update({"Virtualization": "NO"})

        self.result_ready.emit(cpu_info)


class About(QLabel):

    style = """
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
    QPushButton#contactBtn {
        border-color: #dbdbdb;
        background-color: #8B9EA7;
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

    """

    def __init__(self):
        super(About, self).__init__(parent=None)
        # hide it
        self.hide()

        # set about widget
        self.setStyleSheet(self.style)
        self.setFixedSize(QSize(350, 380))
        self.setWindowFlags(Qt.FramelessWindowHint)

        # Create flags button
        # Create the exit button
        exit_button = QPushButton("X", self)
        exit_button.move(315, 10)
        exit_button.setCursor(Qt.PointingHandCursor)
        exit_button.setFont(QFont("Ubuntu", 12))
        exit_button.setStyleSheet(App.FLAG_BUTTON_STYLE)
        exit_button.clicked.connect(self.hide)

        # create logo label
        self.logo = QLabel('ProcessorPy', self)
        self.logo.setObjectName('logo')
        self.logo.move(15, 20)
        self.logo.setFont(QFont('Ubuntu', 14))
        self.logo.setStyleSheet(self.style)
        self.logo.adjustSize()

        # Developed by
        self.developed_by = QLabel(self)
        self.developed_by.setObjectName('others')
        self.developed_by.setText(f"Developed by {AUTHOR}")
        self.developed_by.move(20, 80)
        self.developed_by.setFont(QFont('Ubuntu', 10))
        self.developed_by.setStyleSheet(self.style)

        # build label
        self.license = QLabel(self)
        self.license.setObjectName('others')
        self.license.setText(f"built on {DATE}")
        self.license.move(20, 115)
        self.license.setFont(QFont('Ubuntu', 10))

        self.license.setStyleSheet(self.style)

        # runtime version
        self.version = QLabel(self)
        self.version.setObjectName('others')
        self.version.setText(f"Runtime version : {VERSION}")
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
        self.contact_me_btn = QPushButton('Contact Me', self)
        self.contact_me_btn.setObjectName('contactBtn')
        self.contact_me_btn.move(100, 320)
        self.contact_me_btn.setStyleSheet(self.style)
        self.contact_me_btn.setFont(QFont('Ubuntu', 10))
        self.contact_me_btn.setCursor(Qt.PointingHandCursor)
        self.contact_me_btn.clicked.connect(
            lambda: open_url('https://github.com/aymenbrahimdjelloul'))

        # GitHub repo button
        self.github_repo_btn = QPushButton('GitHub', self)
        self.github_repo_btn.setObjectName('githubBtn')
        self.github_repo_btn.move(15, 320)
        self.github_repo_btn.setStyleSheet(self.style)
        self.github_repo_btn.setFont(QFont('Ubuntu', 11))
        self.github_repo_btn.setCursor(Qt.PointingHandCursor)
        self.github_repo_btn.clicked.connect(
            lambda: open_url('https://github.com/aymenbrahimdjelloul/ProcessorPy'))


    def mousePressEvent(self, event):
        self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        try:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()
        except TypeError:
            pass


class Updater(QWidget):

    # Store the request json data
    IS_UP_TO_DATE: bool

    STYLE: str = """
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

    def __init__(self):
        super(Updater, self).__init__(parent=None)

        # Set up the Updater window
        self.setFixedSize(QSize(500, 120))
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: #DCDDDD;")

        try:
            # Check the latest release version
            if self.is_up_to_date():
                # If the App is Up-to-date kill it
                self.hide()
                self.deleteLater()

                # delete defined variables
                del self.REQUEST_DATA

            else:
                # Otherwise ask the user to download latest version
                self.setup_update()

        # Error Handling
        except requests.RequestException:
            self.hide()
            self.deleteLater()

            # delete defined variables
            del self.REQUEST_DATA

    def mousePressEvent(self, event):
        self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        try:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()
        except TypeError:
            pass

    def is_up_to_date(self) -> bool:
        """ This method will connect and check for new updates"""

        # Get the current version
        current_version: str = f"v{VERSION}"

        # Get the latest release version
        # Get a request
        r = requests.get("https://api.github.com/repos/aymenbrahimdjelloul/ProcessorPy/releases/latest").json()
        latest_release: str = r["tag_name"]

        # Store request data
        self.REQUEST_DATA = r
        latest_release = "1.1"

        return True if current_version == latest_release else False

    def setup_update(self):
        """ This method will set up the update widget"""

        # Create Updater label
        self.update_label = QLabel(f"New update available! Please download the latest version."
                              f" {self.REQUEST_DATA['tag_name']}\n\n"
                              f" Download size : {self.bytes_to_megabytes(self.REQUEST_DATA['assets'][0]['size'])} Mb", self)
        self.update_label.setFont(QFont("Ubuntu", 11))
        self.update_label.move(10, 20)
        self.update_label.setStyleSheet(self.STYLE)

        # Create Cancel button
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.move(15, 80)
        self.cancel_button.setStyleSheet(self.STYLE)
        self.cancel_button.setFont(QFont("Ubuntu", 11))
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.clicked.connect(self.cancel_update)

        # Create Install now button
        self.install_button = QPushButton("Install Now", self)
        self.install_button.move(110, 80)
        self.install_button.setStyleSheet(self.STYLE)
        self.install_button.setFont(QFont("Ubuntu", 10))
        self.install_button.setCursor(Qt.PointingHandCursor)
        self.install_button.clicked.connect(self.update_app)

        # Show Updater widget
        self.show()

    def cancel_update(self):
        """ This method will cancel the whole update process"""

        # First of all hide the update widget
        self.hide()

        # Check if 'updater.exe' is running
        if self.__is_process_running():
            # Kill 'updater.exe' process
            self.__kill_processor_py_process()
            # Delete the downloaded data zip file
            os.system("rm data.zip")

    def update_app(self):
        """ This method will download and install the new version """

        # Hide install now button
        self.install_button.hide()
        # Change the label text
        self.update_label.setText("Please wait..")
        self.update_label.move(30, 20)

        # Run the updater
        os.startfile("updater.exe")

    def update_finished(self):
        """ This method will called when the update is finished"""

        # Set the finish label
        self.update_label.setText(f"The {self.REQUEST_DATA['tag_name']} Update Installed succefully !"
                                  f" Please restart the App.")
        self.update_label.setStyleSheet("color: #308578;")

    @staticmethod
    def bytes_to_megabytes(num: int) -> int:
        """ This method will convert the given bytes to megabytes """
        return num // 1048576

    @staticmethod
    def __is_process_running(process_name: str = "updater") -> bool:
        """
        This function will detect if the 'ProcessorPy' process is running or not

        :param: 'process_name'
        :return: bool
        """

        try:
            # Run the 'tasklist' command to get the list of running processes
            output = subprocess.check_output(['tasklist'], universal_newlines=True)
            # Check if the process name is in the output
            if process_name in output:
                return True
            else:
                return False
        except subprocess.CalledProcessError as e:
            # print(f"An error occurred: {e}")
            return False

    @staticmethod
    def __kill_processor_py_process(process_name: str = "updater.exe") -> int:
        """
           This function will kill the specified process by name and return its PID.

           :param process_name: Name of the process to kill.
           :return: PID of the killed process if successful, -1 otherwise.
           """
        try:
            # Find the PID of the process
            result = subprocess.check_output(['tasklist', '/FI', f'IMAGENAME eq {process_name}'],
                                             universal_newlines=True)

            # Parse the output to get the PID
            for line in result.splitlines():
                if process_name in line:
                    # Extract PID (assuming the PID is the second column in the output)
                    pid = int(line.split()[1])

                    # Kill the process using the PID
                    subprocess.run(['taskkill', '/PID', str(pid), '/F'], check=True)
                    print(f"Process {process_name} with PID {pid} has been killed.")  # For Debugging
                    return pid

            # If process name is not found in the output
            print(f"Process {process_name} not found.")  # For Debugging
            return -1
        except subprocess.CalledProcessError as e:
            print(f"An error occurred: {e}")  # For Debugging


if __name__ == "__main__":
    app = QApplication(sys.argv)

    _window = App()
    _window.show()

    sys.exit(app.exec_())
