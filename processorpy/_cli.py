"""
This code or file is part of 'ProcessorPy' project
copyright (c) 2023-2025, Aymen Brahim Djelloul, All rights reserved.
use of this source code is governed by MIT License that can be found on the project folder.

@author : Aymen Brahim Djelloul
version : 0.1
date : 29.05.2025
license : MIT License

"""

# !/usr/bin/env python3
"""
CPU Monitor CLI Application
A comprehensive command-line tool for monitoring CPU information and sensors.
"""

import sys
import os
import time
import argparse
import threading
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from processorpy import Processor, Sensors
except ImportError:
    print("Error: processorpy module not found. Please install it first.")
    print("pip install processorpy")
    sys.exit(1)

try:
    import colorama
    from colorama import Fore, Back, Style

    colorama.init(autoreset=True)


    class Colors:
        RED = Fore.RED
        GREEN = Fore.GREEN
        YELLOW = Fore.YELLOW
        BLUE = Fore.BLUE
        MAGENTA = Fore.MAGENTA
        CYAN = Fore.CYAN
        WHITE = Fore.WHITE
        BRIGHT = Style.BRIGHT
        DIM = Style.DIM
        RESET = Style.RESET_ALL

except ImportError:
    print("Warning: colorama not installed. Running without colors.")
    print("Install with: pip install colorama")


    class Colors:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = ""
        BRIGHT = DIM = RESET = ""

try:
    import ctypes
    import ctypes.wintypes

    HAS_CTYPES = True
except ImportError:
    HAS_CTYPES = False


def _run_as_admin() -> bool:
    """Run the application as administrator on Windows"""
    if os.name != 'nt' or not HAS_CTYPES:
        return False

    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            # Re-run the program with admin rights
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            return True
    except Exception as e:
        print(f"Failed to run as administrator: {e}")
        return False
    return False


class Const:
    """Application constants"""
    APP_NAME = "CPU Monitor"
    APP_VERSION = "2.0.0"
    APP_AUTHOR = "Enhanced CLI Tool"
    UPDATE_INTERVAL = 1.0  # seconds
    CONSOLE_WIDTH = 80

    # Menu options
    MENU_CPU_INFO = "1"
    MENU_CPU_SENSORS = "2"
    MENU_LIVE_MONITOR = "3"
    MENU_HELP = "4"
    MENU_ABOUT = "5"
    MENU_EXIT = "q"


class Interface:
    """Main interface class for the CPU monitoring application"""

    def __init__(self) -> None:
        """Initialize the interface with processor and sensor objects"""
        try:
            self.processor = Processor()
            self.sensors = Sensors()
            self.cpu_info: Dict[str, Any] = self.processor.get_all_info()
            self.running = False
            self.monitor_thread: Optional[threading.Thread] = None

        except Exception as e:
            print(f"{Colors.RED}Error initializing processor/sensors: {e}{Colors.RESET}")
            sys.exit(1)

    def _center_text(self, text: str, width: int = Const.CONSOLE_WIDTH) -> str:
        """Center text within specified width"""
        if len(text) >= width:
            return text
        padding = (width - len(text)) // 2
        return " " * padding + text

    def _handle_parameters(self) -> None:
        """Handle command line parameters"""
        parser = argparse.ArgumentParser(
            description="CPU Monitor - Monitor your CPU information and sensors"
        )
        parser.add_argument(
            "--info", "-i",
            action="store_true",
            help="Show CPU information and exit"
        )
        parser.add_argument(
            "--sensors", "-s",
            action="store_true",
            help="Show CPU sensors and exit"
        )
        parser.add_argument(
            "--monitor", "-m",
            action="store_true",
            help="Start live monitoring mode"
        )
        parser.add_argument(
            "--admin", "-a",
            action="store_true",
            help="Run as administrator (Windows only)"
        )
        parser.add_argument(
            "--version", "-v",
            action="version",
            version=f"{Const.APP_NAME} {Const.APP_VERSION}"
        )

        args = parser.parse_args()

        if args.admin and os.name == 'nt':
            if _run_as_admin():
                sys.exit(0)

        if args.info:
            self._clear_console()
            self._print_header()
            self._print_cpu_info()
            sys.exit(0)
        elif args.sensors:
            self._clear_console()
            self._print_header()
            self._print_cpu_sensors()
            sys.exit(0)
        elif args.monitor:
            self._clear_console()
            self._print_header()
            self._start_live_monitor()
            sys.exit(0)

    def _print_help(self) -> None:
        """Print help section"""
        self._clear_console()
        self._print_header()

        help_text = f"""
{Colors.BRIGHT}{Colors.CYAN}HELP - CPU Monitor Commands{Colors.RESET}
{Colors.YELLOW}{'=' * 50}{Colors.RESET}

{Colors.BRIGHT}Interactive Menu Options:{Colors.RESET}
  {Colors.GREEN}1{Colors.RESET} - Show detailed CPU information
  {Colors.GREEN}2{Colors.RESET} - Show current CPU sensor readings
  {Colors.GREEN}3{Colors.RESET} - Start live monitoring mode
  {Colors.GREEN}4{Colors.RESET} - Show this help screen
  {Colors.GREEN}5{Colors.RESET} - Show about information
  {Colors.GREEN}q{Colors.RESET} - Quit application

{Colors.BRIGHT}Command Line Options:{Colors.RESET}
  {Colors.GREEN}--info, -i{Colors.RESET}     Show CPU info and exit
  {Colors.GREEN}--sensors, -s{Colors.RESET}  Show sensors and exit
  {Colors.GREEN}--monitor, -m{Colors.RESET}  Start live monitoring
  {Colors.GREEN}--admin, -a{Colors.RESET}    Run as administrator (Windows)
  {Colors.GREEN}--help, -h{Colors.RESET}     Show command line help
  {Colors.GREEN}--version, -v{Colors.RESET}  Show version information

{Colors.BRIGHT}Live Monitor Controls:{Colors.RESET}
  {Colors.GREEN}Press 'q' or Ctrl+C{Colors.RESET} to exit live monitoring

{Colors.BRIGHT}Examples:{Colors.RESET}
  python cpu_monitor.py --info
  python cpu_monitor.py --monitor
  python cpu_monitor.py --admin --sensors
        """

        print(help_text)
        self._get_user_input()

    def _print_about(self) -> None:
        """Print about section"""
        self._clear_console()
        self._print_header()

        about_text = f"""
{Colors.BRIGHT}{Colors.MAGENTA}ABOUT - {Const.APP_NAME}{Colors.RESET}
{Colors.YELLOW}{'=' * 50}{Colors.RESET}

{Colors.BRIGHT}Application:{Colors.RESET} {Const.APP_NAME}
{Colors.BRIGHT}Version:{Colors.RESET}     {Const.APP_VERSION}
{Colors.BRIGHT}Author:{Colors.RESET}      {Const.APP_AUTHOR}

{Colors.BRIGHT}Description:{Colors.RESET}
This is a comprehensive CPU monitoring tool that provides detailed
information about your processor and real-time sensor readings.

{Colors.BRIGHT}Features:{Colors.RESET}
• Detailed CPU specifications and capabilities
• Real-time temperature and usage monitoring
• Live monitoring mode with continuous updates
• Cross-platform support (Windows, Linux, macOS)
• Command-line interface with multiple options
• Colorized output for better readability

{Colors.BRIGHT}Requirements:{Colors.RESET}
• Python 3.6+
• processorpy library
• colorama library (optional, for colors)

{Colors.BRIGHT}Platform:{Colors.RESET} {sys.platform}
{Colors.BRIGHT}Python:{Colors.RESET}   {sys.version.split()[0]}
        """

        print(about_text)
        self._get_user_input()

    def _print_cpu_sensors(self) -> None:
        """Print CPU sensor readings with real-time updates"""
        try:
            sensor_data = self.sensors.get_cpu_temperature()
            usage_data = self.sensors.get_cpu_usage()

            print(f"\n{Colors.BRIGHT}{Colors.CYAN}CPU SENSOR READINGS{Colors.RESET}")
            print(f"{Colors.YELLOW}{'=' * 50}{Colors.RESET}")
            print(f"{Colors.DIM}Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")

            # Temperature readings
            if sensor_data:
                print(f"\n{Colors.BRIGHT}Temperature Sensors:{Colors.RESET}")
                for sensor, temp in sensor_data.items():
                    color = Colors.GREEN
                    if temp > 70:
                        color = Colors.YELLOW
                    elif temp > 85:
                        color = Colors.RED
                    print(f"  {sensor}: {color}{temp:.1f}°C{Colors.RESET}")
            else:
                print(f"\n{Colors.YELLOW}Temperature sensors not available{Colors.RESET}")

            # CPU Usage
            if usage_data:
                print(f"\n{Colors.BRIGHT}CPU Usage:{Colors.RESET}")
                if isinstance(usage_data, (int, float)):
                    color = Colors.GREEN if usage_data < 70 else Colors.YELLOW if usage_data < 90 else Colors.RED
                    print(f"  Overall: {color}{usage_data:.1f}%{Colors.RESET}")
                elif isinstance(usage_data, list):
                    for i, usage in enumerate(usage_data):
                        color = Colors.GREEN if usage < 70 else Colors.YELLOW if usage < 90 else Colors.RED
                        print(f"  Core {i}: {color}{usage:.1f}%{Colors.RESET}")
            else:
                print(f"\n{Colors.YELLOW}CPU usage data not available{Colors.RESET}")

        except Exception as e:
            print(f"{Colors.RED}Error reading sensors: {e}{Colors.RESET}")

    def _print_cpu_info(self) -> None:
        """Print detailed CPU information"""
        print(f"\n{Colors.BRIGHT}{Colors.CYAN}CPU INFORMATION{Colors.RESET}")
        print(f"{Colors.YELLOW}{'=' * 50}{Colors.RESET}")

        try:
            info_map = {
                'brand': 'Processor Brand',
                'model': 'Model',
                'architecture': 'Architecture',
                'cores': 'Physical Cores',
                'threads': 'Logical Processors',
                'frequency': 'Base Frequency',
                'max_frequency': 'Max Frequency',
                'cache_l1': 'L1 Cache',
                'cache_l2': 'L2 Cache',
                'cache_l3': 'L3 Cache',
                'stepping': 'Stepping',
                'family': 'Family',
                'vendor': 'Vendor'
            }

            for key, label in info_map.items():
                if key in self.cpu_info and self.cpu_info[key]:
                    value = self.cpu_info[key]
                    if key in ['frequency', 'max_frequency'] and isinstance(value, (int, float)):
                        value = f"{value / 1000:.2f} GHz" if value > 1000 else f"{value} MHz"
                    elif key in ['cache_l1', 'cache_l2', 'cache_l3'] and isinstance(value, (int, float)):
                        value = f"{value} KB" if value < 1024 else f"{value / 1024:.1f} MB"

                    print(f"{Colors.BRIGHT}{label}:{Colors.RESET} {Colors.GREEN}{value}{Colors.RESET}")

            # Additional system information
            print(f"\n{Colors.BRIGHT}System Information:{Colors.RESET}")
            print(f"{Colors.BRIGHT}Platform:{Colors.RESET} {Colors.GREEN}{sys.platform}{Colors.RESET}")
            print(f"{Colors.BRIGHT}Python Version:{Colors.RESET} {Colors.GREEN}{sys.version.split()[0]}{Colors.RESET}")

        except Exception as e:
            print(f"{Colors.RED}Error displaying CPU info: {e}{Colors.RESET}")

    def _print_header(self) -> None:
        """Print application header"""
        header = f"""
{Colors.BRIGHT}{Colors.BLUE}╔{'═' * (Const.CONSOLE_WIDTH - 2)}╗{Colors.RESET}
{Colors.BRIGHT}{Colors.BLUE}║{self._center_text(f"{Const.APP_NAME} v{Const.APP_VERSION}", Const.CONSOLE_WIDTH - 2)}║{Colors.RESET}
{Colors.BRIGHT}{Colors.BLUE}║{self._center_text(Const.APP_AUTHOR, Const.CONSOLE_WIDTH - 2)}║{Colors.RESET}
{Colors.BRIGHT}{Colors.BLUE}╚{'═' * (Const.CONSOLE_WIDTH - 2)}╝{Colors.RESET}
        """
        print(header)

    def _print_menu(self) -> None:
        """Print the main menu"""
        menu = f"""
{Colors.BRIGHT}{Colors.CYAN}MAIN MENU{Colors.RESET}
{Colors.YELLOW}{'=' * 20}{Colors.RESET}

{Colors.GREEN}1{Colors.RESET} - Show CPU Information
{Colors.GREEN}2{Colors.RESET} - Show CPU Sensors
{Colors.GREEN}3{Colors.RESET} - Live Monitor Mode
{Colors.GREEN}4{Colors.RESET} - Help
{Colors.GREEN}5{Colors.RESET} - About
{Colors.GREEN}q{Colors.RESET} - Quit

{Colors.BRIGHT}Select an option:{Colors.RESET} """

        print(menu, end="")

    def _get_user_input(self) -> str:
        """Get user input and handle KeyboardInterrupt"""
        try:
            return input(f"\n{Colors.BRIGHT}Press Enter to continue...{Colors.RESET}").strip().lower()
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Interrupted by user{Colors.RESET}")
            return "q"

    def _clear_console(self) -> None:
        """Clear the console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def _set_title(self) -> None:
        """Set console title for both Linux and Windows"""
        title = f"{Const.APP_NAME} v{Const.APP_VERSION}"
        if os.name == 'nt':
            os.system(f'title {title}')
        else:
            sys.stdout.write(f'\033]0;{title}\007')
            sys.stdout.flush()

    def _start_live_monitor(self) -> None:
        """Start live monitoring mode"""
        print(f"\n{Colors.BRIGHT}{Colors.GREEN}LIVE MONITORING MODE{Colors.RESET}")
        print(f"{Colors.YELLOW}Press 'q' + Enter or Ctrl+C to exit{Colors.RESET}\n")

        self.running = True

        def monitor_loop():
            while self.running:
                try:
                    # Clear and show current readings
                    if os.name == 'nt':
                        os.system('cls')
                    else:
                        print('\033[H\033[J', end='')

                    self._print_header()
                    self._print_cpu_sensors()
                    print(
                        f"\n{Colors.DIM}Updating every {Const.UPDATE_INTERVAL}s... Press 'q' + Enter to exit{Colors.RESET}")

                    time.sleep(Const.UPDATE_INTERVAL)
                except Exception as e:
                    print(f"{Colors.RED}Monitor error: {e}{Colors.RESET}")
                    break

        # Start monitoring in a separate thread
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()

        # Wait for user input to stop
        try:
            while self.running:
                user_input = input().strip().lower()
                if user_input == 'q':
                    break
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=2)

    def run(self) -> None:
        """Main application entry point"""
        self._set_title()
        self._handle_parameters()

        while True:
            try:
                self._clear_console()
                self._print_header()
                self._print_menu()

                choice = input().strip().lower()

                if choice == Const.MENU_CPU_INFO:
                    self._clear_console()
                    self._print_header()
                    self._print_cpu_info()
                    self._get_user_input()

                elif choice == Const.MENU_CPU_SENSORS:
                    self._clear_console()
                    self._print_header()
                    self._print_cpu_sensors()
                    self._get_user_input()

                elif choice == Const.MENU_LIVE_MONITOR:
                    self._clear_console()
                    self._print_header()
                    self._start_live_monitor()

                elif choice == Const.MENU_HELP:
                    self._print_help()

                elif choice == Const.MENU_ABOUT:
                    self._print_about()

                elif choice == Const.MENU_EXIT:
                    print(f"\n{Colors.BRIGHT}{Colors.GREEN}Thank you for using {Const.APP_NAME}!{Colors.RESET}")
                    break

                else:
                    print(f"\n{Colors.RED}Invalid option. Please try again.{Colors.RESET}")
                    time.sleep(1)

            except KeyboardInterrupt:
                print(f"\n\n{Colors.YELLOW}Exiting...{Colors.RESET}")
                break
            except Exception as e:
                print(f"\n{Colors.RED}Unexpected error: {e}{Colors.RESET}")
                print("Please report this issue.")
                time.sleep(2)


def main() -> None:
    """Main function executed when script is run from command line"""
    try:
        app = Interface()
        app.run()

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Application interrupted by user{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"{Colors.RED}Fatal error: {e}{Colors.RESET}")
        sys.exit(1)


if __name__ == '__main__':
    main()