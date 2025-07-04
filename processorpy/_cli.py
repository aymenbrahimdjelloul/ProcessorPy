#!/usr/bin/env python3
"""
ProcessorPy Interface - Advanced CPU Information and Sensor Monitoring Tool
A sophisticated command-line interface for real-time CPU monitoring and reporting.
"""

import re
import os
import sys
import json
import shutil
import argparse
import datetime
import threading
from time import sleep
from typing import Any, Dict, List, Optional, Tuple

# Handle missing imports
try:
    from processorpy import Processor, Sensors, ProcessorPyException

    # Use colorama for cross-platform coloring
    from colorama import Fore, Style, init

    # Initialize colorama
    init(autoreset=True)


    class Colors:
        """A utility class that defines Interface coloring using 'colorama'"""
        HEADER = Fore.CYAN + Style.BRIGHT
        SUBHEADER = Fore.BLUE + Style.BRIGHT
        SUCCESS = Fore.GREEN + Style.BRIGHT
        WARNING = Fore.YELLOW + Style.BRIGHT
        ERROR = Fore.RED + Style.BRIGHT
        INFO = Fore.CYAN
        HIGHLIGHT = Fore.MAGENTA + Style.BRIGHT
        BOLD = Style.BRIGHT
        DIM = Style.DIM
        UNDERLINE = '\033[4m'
        END = Style.RESET_ALL

except ImportError as e:
    print(f"Error importing required libraries: {e}")
    print("Please install: pip install processorpy colorama")


    # Fallback with traditional ANSI color codes
    class Colors:
        """Fallback ANSI color codes for basic terminal styling"""
        HEADER = "\033[96m\033[1m"
        SUBHEADER = "\033[94m\033[1m"
        SUCCESS = "\033[92m\033[1m"
        WARNING = "\033[93m\033[1m"
        ERROR = "\033[91m\033[1m"
        INFO = "\033[96m"
        HIGHLIGHT = "\033[95m\033[1m"
        BOLD = "\033[1m"
        DIM = "\033[2m"
        UNDERLINE = "\033[4m"
        END = "\033[0m"

except ProcessorPyException:
    import traceback
    traceback.print_exc()

    input("Press enter to exit...")
    sys.exit(1)


class Config:
    """Configuration constants for the ProcessorPy Interface application"""

    APP_NAME: str = "ProcessorPy Interface"
    VERSION: str = "1.1"
    AUTHOR: str = "Aymen Brahim Djelloul"
    WEBSITE: str = "https://github.com/aymenbrahimdjelloul/ProcessorPy"
    DESCRIPTION: str = "Advanced CPU Information and Sensor Monitoring Tool"

    # Display configuration
    MIN_TERMINAL_WIDTH: int = 80
    DEFAULT_TERMINAL_WIDTH: int = 120
    REPORT_WIDTH: int = 80

    # Timing configuration
    DEFAULT_REFRESH_INTERVAL: int = 2
    MIN_REFRESH_INTERVAL: int = 1
    MAX_REFRESH_INTERVAL: int = 60

    # File configuration
    DEFAULT_OUTPUT_DIR: str = "cpu_reports"
    SUPPORTED_FORMATS: tuple[str] = ("text", "json", "csv", "all")


class Interface:
    """
    Advanced interactive Interface tool for displaying and saving CPU information
    and sensor readings with real-time monitoring capabilities.
    """

    def __init__(self) -> None:
        """Initialize the CPU monitoring interface"""

        try:
            # Create Processor and Sensors objects
            self.processor = Processor()
            self.sensors = Sensors()

            # Get initial CPU info
            self.cpu_info: dict[str, Any] = self.processor.get_all_info(all_info=True)

        except ProcessorPyException:
            import traceback
            traceback.print_exc()

            input("Press enter to exit...")
            sys.exit(1)

        # Parse command line arguments
        self.args = self._parse_arguments()

        # Application state
        self.running = True
        self.auto_refresh = False
        self.refresh_thread = None

        # Terminal configuration
        self.terminal_width = self._get_terminal_width()

        # Statistics tracking
        self.start_time = datetime.datetime.now()
        self.refresh_count = 0
        self.last_update = None

    @staticmethod
    def _get_terminal_width() -> int:
        """Get the current terminal width with fallback"""
        try:
            terminal_size = shutil.get_terminal_size()
            width = terminal_size.columns
            return max(width, Config.MIN_TERMINAL_WIDTH)

        except (AttributeError, OSError):
            return Config.DEFAULT_TERMINAL_WIDTH

    @staticmethod
    def _parse_arguments() -> argparse.Namespace:
        """Parse and validate command line arguments"""

        parser = argparse.ArgumentParser(
            description=f"{Config.APP_NAME} - {Config.DESCRIPTION}",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=f"""
Examples:
  {sys.argv[0]} -i                          # Interactive mode
  {sys.argv[0]} -s -f json                  # Save JSON report
  {sys.argv[0]} -r 5 -i                     # Auto-refresh every 5 seconds
  {sys.argv[0]} --sensors --interactive     # Show sensors in interactive mode
  {sys.argv[0]} --benchmark --save          # Run benchmark and save results

Visit: {Config.WEBSITE}
            """
        )

        # Mode options
        mode_group = parser.add_argument_group('Mode Options')
        mode_group.add_argument(
            "-i", "--interactive",
            action="store_true",
            help="Run in interactive mode with command prompt"
        )

        mode_group.add_argument(
            "--sensors",
            action="store_true",
            help="Display sensor readings (temperature, usage, etc.)"
        )

        mode_group.add_argument(
            "--benchmark",
            action="store_true",
            help="Run CPU benchmark tests"
        )

        # Output options
        output_group = parser.add_argument_group('Output Options')
        output_group.add_argument(
            "-s", "--save",
            action="store_true",
            help="Save CPU information report"
        )

        output_group.add_argument(
            "-f", "--format",
            choices=Config.SUPPORTED_FORMATS,
            default="all",
            help="Format for saving reports"
        )

        output_group.add_argument(
            "-o", "--output-dir",
            type=str,
            default=Config.DEFAULT_OUTPUT_DIR,
            help="Directory for saving reports"
        )

        # Display options
        display_group = parser.add_argument_group('Display Options')

        display_group.add_argument(
            "--compact",
            action="store_true",
            help="Use compact display format"
        )

        display_group.add_argument(
            "--no-color",
            action="store_true",
            help="Disable colored output"
        )

        # Information options
        info_group = parser.add_argument_group('Information Options')
        info_group.add_argument(
            "-v", "--version",
            action="store_true",
            help="Show application version and exit"
        )

        info_group.add_argument(
            "--info",
            action="store_true",
            help="Show detailed system information and exit"
        )

        args = parser.parse_args()

        return args

    def run(self) -> None:
        """Main entry point - run the Interface tool based on provided arguments"""

        # Handle version flag
        if self.args.version:
            self._display_version()
            return

        # Handle info flag
        if self.args.info:
            self._display_system_info()
            return

        # Initial display
        self._refresh_display()

        # Save reports if requested
        if self.args.save:
            self._save_reports()

        # Enter interactive mode if requested or as default
        if self.args.interactive or not any([self.args.save, self.args.info]):
            self.args.interactive = True
            self._run_interactive_mode()

    def _refresh_display(self) -> None:
        """Refresh the main display with current CPU information"""

        try:
            # Clear screen
            self._clear_screen()

            # Update data
            self.cpu_info = self.processor.get_all_info()
            if self.args.sensors:
                self.sensor_data = self._get_sensor_data()

            # Display components
            self._display_header()
            self._display_cpu_info()

            if self.args.sensors:
                self._display_sensor_data()

            # Update statistics
            self.last_update = datetime.datetime.now()
            self.refresh_count += 1

            # Display footer with statistics
            self._display_footer()

            # Display command menu in interactive mode
            if self.args.interactive:
                self._display_command_menu()

        except ProcessorPyException:
            print(f"{Colors.ERROR}Error refreshing display: {e}{Colors.END}")

    def _get_sensor_data(self) -> Dict[str, Any]:
        """Get current sensor readings"""

        try:
            sensor_info = {}

            # Get temperature data
            if hasattr(self.sensors, 'get_temperature'):
                sensor_info['temperature'] = self.sensors.get_temperature()

            # Get CPU usage
            if hasattr(self.sensors, 'get_cpu_usage'):
                sensor_info['cpu_usage'] = self.sensors.get_cpu_usage()

            # Get frequency information
            if hasattr(self.sensors, 'get_frequency'):
                sensor_info['frequency'] = self.sensors.get_frequency()

            return sensor_info

        except Exception:
            import traceback
            traceback.print_exc()

            input("Press enter to exit...")
            sys.exit(1)


    @staticmethod
    def _clear_screen() -> None:
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def _set_terminal_title() -> None:
        """Set the terminal window title"""
        try:
            title = f"{Config.APP_NAME} v{Config.VERSION}"
            if os.name == 'nt':  # Windows
                os.system(f'title {title}')
            else:  # Unix-like systems
                print(f'\033]0;{title}\007', end='')

        except OSError:
            pass  # Ignore if unable to set title

    @staticmethod
    def _strip_ansi(text: str) -> str:
        """Remove ANSI escape codes from a string"""
        return re.sub(r'\x1B[@-_][0-?]*[ -/]*[@-~]', '', text)

    def _center_text(self, text: str) -> str:
        """Center text considering ANSI codes"""
        plain_text = self._strip_ansi(text)
        padding = max(0, (self.terminal_width - len(plain_text)) // 2)
        return f"{' ' * padding}{text}"

    def _display_header(self) -> None:
        """Display the application header"""

        self._clear_screen()

        print()
        print(self._center_text(f"╭{'─' * (self.terminal_width - 4)}╮"))

        # Logo line
        logo = f" ProcessorPy "
        version_str: str = f"V {Config.VERSION} "

        # Calculate the padding values
        padding = self.terminal_width - len(logo) - len(version_str) - 4

        # Print it
        print(f"  {Fore.MAGENTA}{Fore.CYAN}{Style.BRIGHT}{logo}{' ' * padding}{version_str}{Fore.MAGENTA}")

        print(self._center_text(f"╰{'─' * (self.terminal_width - 4)}╯"))

    @staticmethod
    def _display_version() -> None:
        """Display detailed version and system information"""

        print(f"\n{Colors.HEADER}{Config.APP_NAME}{Colors.END}")
        print(f"{Colors.BOLD}Version  : {Colors.END}        {Config.VERSION}")
        print(f"{Colors.BOLD}Author   : {Colors.END}         {Config.AUTHOR}")
        print(f"{Colors.BOLD}Website  : {Colors.END}        {Config.WEBSITE}")
        print(f"{Colors.BOLD}Python   : {Colors.END}         {sys.version.split()[0]}")
        print(f"{Colors.BOLD}Platform : {Colors.END}       {sys.platform}")

        try:
            from processorpy import __version__ as processorpy_version
            print(f"{Colors.BOLD}ProcessorPy:{Colors.END}    v{processorpy_version}")

        except ImportError:
            print(f"{Colors.BOLD}ProcessorPy:{Colors.END}    Version unknown")

    def _display_system_info(self) -> None:
        """Display comprehensive system information"""

        self._clear_screen()
        self._display_header()

        print(f"{Colors.SUBHEADER}SYSTEM INFORMATION{Colors.END}")
        print(f"{Colors.BOLD}{'─' * self.terminal_width}{Colors.END}")

        # Get and display CPU info
        info = self.cpu_info

        # Critical information first
        critical_keys = ['brand', 'architecture', 'cores', 'threads', 'base_frequency', 'max_frequency']

        for key in critical_keys:
            if key in info:
                label = key.replace('_', ' ').title()
                value = info[key]
                print(f"{Colors.BOLD}{label + ':':<20}{Colors.END} {Colors.INFO}{value}{Colors.END}")

        print()

        # Additional information
        print(f"{Colors.SUBHEADER}DETAILED SPECIFICATIONS{Colors.END}")
        print(f"{Colors.BOLD}{'─' * self.terminal_width}{Colors.END}")

        remaining_keys = [k for k in sorted(info.keys()) if k not in critical_keys]

        for key in remaining_keys:
            label = key.replace('_', ' ').title()
            value = info[key]

            # Format boolean values
            if isinstance(value, bool):
                value = "Yes" if value else "No"
                color = Colors.SUCCESS if value == "Yes" else Colors.WARNING
            else:
                color = Colors.INFO

            print(f"{Colors.BOLD}{label + ':':<25}{Colors.END} {color}{value}{Colors.END}")

    def _format_info_line(self, label: str, value: Any, color_code: str = "") -> str:
        """Format an information line with aligned columns"""

        label_width = 25 if not self.args.compact else 20

        # Format boolean values
        if isinstance(value, bool):
            value = "Yes" if value else "No"
            if not color_code:
                color_code = Colors.SUCCESS if value == "Yes" else Colors.WARNING

        # Apply color formatting
        if color_code:
            formatted_value = f"{color_code}{value}{Colors.END}"
        else:
            formatted_value = f"{Colors.INFO}{value}{Colors.END}"

        return f"{Colors.BOLD}{label + ':':<{label_width}}{Colors.END} {formatted_value}"

    def _display_cpu_info(self) -> None:
        """Display ALL CPU information with optimal organization"""
        print(f"{Colors.BOLD}{'─' * self.terminal_width}{Colors.END}")

        info = self.cpu_info

        # Main display groups (now using ALL your keys)
        display_groups = {
            'Identification': [
                ('cpu_name', 'Name'),
                ('vendor', 'Vendor'),
                ('release_date', 'Release Date'),
                ('code_name', 'Code Name'),
                ('architecture', 'Architecture'),
                ('family', 'Family'),
                ('stepping', 'Stepping')
            ],
            'Physical Specifications': [
                ('socket', 'Socket'),
                ('cpu_lithography', 'Lithography'),
                ('cpu_tdp', 'TDP'),
                ('cores', 'Physical Cores'),
                ('threads', 'Threads')
            ],
            'Cache': [
                ('l1_cache', 'L1 Cache'),
                ('l2_cache', 'L2 Cache'),
                ('l3_cache', 'L3 Cache')
            ],
            'Performance': [
                ('max_speed', 'Max Clock Speed'),
                ('turbo_boost_support', 'Turbo Boost'),
                ('virtualization_support', 'Virtualization')
            ],
            'Memory': [
                ('supported_memory_types', 'Memory Types'),
                ('memory_channels', 'Memory Channels'),
                ('max_memory_size', 'Max Memory'),
                ('max_memory_bandwidth', 'Memory Bandwidth'),
                ('ecc_support', 'ECC Support')
            ],
            'Features': [
                ('flags', 'Instruction Flags')
            ]
        }

        # Track which keys we've displayed
        displayed_keys = set()

        # Display grouped information
        for group_name, fields in display_groups.items():
            valid_fields = []

            for key, label in fields:
                if key in info and info[key] is not None:
                    valid_fields.append((key, label))
                    displayed_keys.add(key)

            if valid_fields:
                print(f"\n{Colors.SUBHEADER}{group_name}{Colors.END}")
                for key, label in valid_fields:

                    value = info[key].value
                    formatted_value = self._format_cpu_value(key, value)
                    print(self._format_info_line(label, formatted_value))

        # Display ANY remaining fields that weren't in groups
        all_keys = set(info.keys())
        remaining_keys = sorted(all_keys - displayed_keys)


        if remaining_keys:
            print(f"\n{Colors.SUBHEADER}Additional Information{Colors.END}")
            for key in remaining_keys:
                if info[key] is not None:  # Only show if not None
                    label = key.replace('_', ' ').title()
                    value = info[key]
                    formatted_value = self._format_cpu_value(key, value)
                    print(self._format_info_line(label, formatted_value))

        print(f"{Colors.BOLD}{'─' * self.terminal_width}{Colors.END}")

    def _format_cpu_value(self, key: str, value: Any) -> str:
        """Enhanced formatter with more specific cases"""

        if value is None:
            return "N/A"

        if isinstance(value, bool):
            return "Yes" if value else "No"

        if isinstance(value, (list, tuple, set)):
            if not value:
                return "None"
            return ', '.join(str(v) for v in value)

        # Numeric formatting
        if isinstance(value, (int, float)):
            if key == 'cpu_tdp':
                return f"{value} W"

            if key in ('l1_cache', 'l2_cache', 'l3_cache'):
                return f"{value} KB"  # Assuming your _safe_call already formats cache sizes

            if key == 'max_speed':
                return f"{value / 1000:.2f} GHz" if value >= 1000 else f"{value} MHz"

            if key == 'cpu_lithography':
                return f"{value} nm"

            if key == 'max_memory_size':
                if value >= 1024:
                    return f"{value / 1024:.1f} GB"
                return f"{value} MB"

            if key == 'max_memory_bandwidth':
                return f"{value} GB/s"

        return str(value)

    def _format_cpu_value(self, key: str, value: Any) -> str:
        """Specialized formatter for CPU-specific values"""
        if isinstance(value, bool):
            return "Yes" if value else "No"

        if isinstance(value, (list, tuple, set)):
            return ', '.join(str(v) for v in value) if value else "None"

        if key == 'cpu_tdp':
            return f"{value} W"

        if key in ('l1_cache', 'l2_cache', 'l3_cache'):
            return value if isinstance(value, str) else f"{value} KB"

        if key == 'max_speed':
            if isinstance(value, str):
                return value
            return f"{value / 1000:.2f} GHz" if value >= 1000 else f"{value} MHz"

        if key == 'cpu_lithography':
            return f"{value} nm"

        if key == 'max_memory_size':
            return f"{value / 1024:.1f} GB" if value >= 1024 else f"{value} MB"

        return str(value)

    def _display_sensor_data(self) -> None:
        """Display real-time sensor information"""

        if not self.sensor_data:
            return

        print(f"\n{Colors.SUBHEADER}SENSOR READINGS{Colors.END}")
        print(f"{Colors.BOLD}{'─' * self.terminal_width}{Colors.END}")

        for sensor_type, data in self.sensor_data.items():
            if sensor_type == 'error':
                print(f"{Colors.ERROR}Sensor Error: {data}{Colors.END}")
                continue

            label = sensor_type.replace('_', ' ').title()

            if isinstance(data, dict):
                print(f"{Colors.BOLD}{label}:{Colors.END}")
                for key, value in data.items():
                    sub_label = f"  {key.replace('_', ' ').title()}"

                    # Color coding for temperature
                    if 'temperature' in sensor_type and isinstance(value, (int, float)):
                        if value > 80:
                            color = Colors.ERROR
                        elif value > 60:
                            color = Colors.WARNING
                        else:
                            color = Colors.SUCCESS
                        print(f"{sub_label:<23} {color}{value}°C{Colors.END}")
                    else:
                        print(f"{sub_label:<23} {Colors.INFO}{value}{Colors.END}")
            else:
                print(self._format_info_line(label, data))

    def _display_footer(self) -> None:
        """Display footer with runtime statistics"""

        print(f"\n{Colors.BOLD}{'─' * self.terminal_width}{Colors.END}")

        # Calculate runtime
        runtime = datetime.datetime.now() - self.start_time
        runtime_str = str(runtime).split('.')[0]  # Remove microseconds

        # Last update time
        update_time = self.last_update.strftime('%H:%M:%S') if self.last_update else "Never"

        footer_info: tuple = (
            f"Runtime: {runtime_str}",
            f"Updates: {self.refresh_count}",
            f"Last Update: {update_time}"
        )

        if self.auto_refresh:
            footer_info.append(f"Auto-refresh: {self.args.refresh}s")

        footer_text = " | ".join(footer_info)
        print(f"{Colors.DIM}{footer_text}{Colors.END}")

    @staticmethod
    def _display_command_menu() -> None:
        """Display command menu for interactive mode"""

        commands: tuple = (
            f"{Colors.SUCCESS}[s]{Colors.END} sensors",
            f"{Colors.SUCCESS}[save]{Colors.END} report",
            f"{Colors.SUCCESS}[q]{Colors.END} quit"
        )

        print(f"\n{Colors.BOLD}Commands:{Colors.END} {' | '.join(commands)}")

    @staticmethod
    def _display_command_help() -> None:
        """Display comprehensive command help"""

        commands: list[tuple] = [
            ("sensors (s)", "Toggle sensor display on/off"),
            ("save (save)", "Save detailed CPU report"),
            ("clear (c)", "Clear the screen"),
            ("help (h, ?)", "Show this help message"),
            ("version (v)", "Show version information"),
            ("quit (q, exit, bye)", "Exit the application")
        ]

        print(f"\n{Colors.HEADER}AVAILABLE COMMANDS{Colors.END}")
        print(f"{Colors.BOLD}{'─' * 60}{Colors.END}")

        max_cmd_len = max(len(cmd[0]) for cmd in commands)

        for cmd, desc in commands:
            print(f"{Colors.SUCCESS}{cmd.ljust(max_cmd_len + 2)}{Colors.END}{desc}")

        print(f"\n{Colors.DIM}Tip: Most commands can be abbreviated to their first letter{Colors.END}")

    def _run_interactive_mode(self) -> None:
        """Run the application in interactive mode with enhanced command handling"""

        self.running = True
        self._set_terminal_title()

        print(f"\n{Colors.INFO}Interactive mode active. Type 'help' for commands.{Colors.END}")

        while self.running:
            try:
                user_input = input(f"{Colors.BOLD}>{Colors.END} ").strip().lower()

                if not user_input:
                    continue

                # Parse command and arguments
                parts = user_input.split()
                command = parts[0]

                # Handle commands
                if command in ('q', 'quit', 'exit', 'bye'):
                    self._handle_quit()

                elif command in ('s', 'sensors'):
                    self.args.sensors = not self.args.sensors
                    status = "enabled" if self.args.sensors else "disabled"
                    print(f"{Colors.INFO}Sensor display {status}{Colors.END}")
                    self._refresh_display()

                elif command == 'save':
                    self._save_reports()
                    self._wait_for_input()
                    self._refresh_display()

                elif command in ('c', 'clear'):
                    self._refresh_display()

                elif command in ('v', 'version'):
                    self._display_version()
                    self._wait_for_input()
                    self._refresh_display()

                elif command in ('h', '?', 'help'):
                    self._display_command_help()
                    self._wait_for_input()
                    self._refresh_display()

                else:
                    print(
                        f"{Colors.ERROR}Unknown command: '{command}'. Type 'help' for available commands.{Colors.END}")

            except KeyboardInterrupt:
                self._handle_quit()

            except EOFError:
                self._handle_quit()

            except Exception:
                import traceback
                traceback.print_exc()

                input("Press enter to exit...")
                sys.exit(1)

    def _handle_quit(self) -> None:
        """Handle application quit with cleanup"""

        self.running = False
        self._stop_auto_refresh()

        print(f"\n{Colors.WARNING}Shutting down {Config.APP_NAME}...{Colors.END}")
        sleep(1)

        print(f"{Colors.SUCCESS}Thank you for using {Config.APP_NAME}!{Colors.END}")
        sys.exit(0)

    def _handle_auto_refresh(self, args: List[str]) -> None:
        """Handle auto-refresh toggle and configuration"""

        if self.auto_refresh:
            self._stop_auto_refresh()
            print(f"{Colors.INFO}Auto-refresh disabled{Colors.END}")
        else:
            # Parse interval if provided
            if args:
                try:
                    interval = int(args[0])
                    if Config.MIN_REFRESH_INTERVAL <= interval <= Config.MAX_REFRESH_INTERVAL:
                        self.args.refresh = interval
                    else:
                        print(
                            f"{Colors.WARNING}Invalid interval. Using default: {Config.DEFAULT_REFRESH_INTERVAL}s{Colors.END}")
                        self.args.refresh = Config.DEFAULT_REFRESH_INTERVAL
                except ValueError:
                    print(
                        f"{Colors.WARNING}Invalid interval format. Using default: {Config.DEFAULT_REFRESH_INTERVAL}s{Colors.END}")
                    self.args.refresh = Config.DEFAULT_REFRESH_INTERVAL
            elif self.args.refresh == 0:
                self.args.refresh = Config.DEFAULT_REFRESH_INTERVAL

            self.auto_refresh = True
            self._start_auto_refresh()
            print(f"{Colors.INFO}Auto-refresh enabled ({self.args.refresh}s interval){Colors.END}")

    @staticmethod
    def _wait_for_input() -> None:
        """Wait for user input with styled prompt"""
        input(f"\n{Colors.DIM}Press Enter to continue...{Colors.END}")

    def _format_text_report(self) -> str:
        """Format CPU information as a comprehensive text report"""

        report = []
        width = Config.REPORT_WIDTH

        # Header
        report.append("=" * width)
        report.append(f"{Config.APP_NAME} - CPU Information Report".center(width))
        report.append("=" * width)
        report.append(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Runtime: {datetime.datetime.now() - self.start_time}")
        report.append("=" * width)
        report.append("")

        # CPU Information
        report.append("PROCESSOR INFORMATION".center(width))
        report.append("-" * width)

        info = self.cpu_info
        label_width = 25

        # Format all CPU information
        for key in sorted(info.keys()):
            label = key.replace('_', ' ').title()
            value = info[key]

            if isinstance(value, bool):
                value = "Yes" if value else "No"

            report.append(f"{label + ':':<{label_width}} {value}")

        # Sensor data if available
        if self.sensor_data:
            report.append("")
            report.append("SENSOR READINGS".center(width))
            report.append("-" * width)

            for sensor_type, data in self.sensor_data.items():
                if sensor_type == 'error':
                    report.append(f"Sensor Error: {data}")
                    continue

                label = sensor_type.replace('_', ' ').title()

                if isinstance(data, dict):
                    report.append(f"\n{label}:")
                    for key, value in data.items():
                        sub_label = f"  {key.replace('_', ' ').title()}"
                        report.append(f"{sub_label + ':':<{label_width}} {value}")
                else:
                    report.append(f"{label + ':':<{label_width}} {data}")

        # Footer
        report.append("")
        report.append("=" * width)
        report.append(f"Report generated by {Config.APP_NAME} v{Config.VERSION}".center(width))
        report.append(f"{Config.WEBSITE}".center(width))
        report.append("=" * width)

        return "\n".join(report)

    def _format_csv_report(self) -> str:
        """Format CPU information as CSV for data analysis"""

        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(['Timestamp', 'Category', 'Property', 'Value'])

        timestamp = datetime.datetime.now().isoformat()

        # CPU Information
        for key, value in self.cpu_info.items():
            writer.writerow([timestamp, 'CPU', key, str(value)])

        # Sensor data if available
        if self.sensor_data:
            for sensor_type, data in self.sensor_data.items():
                if isinstance(data, dict):
                    for sub_key, sub_value in data.items():
                        writer.writerow([timestamp, f'Sensor_{sensor_type}', sub_key, str(sub_value)])
                else:
                    writer.writerow([timestamp, 'Sensor', sensor_type, str(data)])

        return output.getvalue()

    def _save_reports(self) -> None:
        """Save CPU information reports in specified formats"""

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create output directory if it doesn't exist
        os.makedirs(self.args.output_dir, exist_ok=True)

        # Determine formats to save
        formats = []
        if self.args.format == "all":
            formats = ["text", "json", "csv"]
        elif self.args.format == "text":
            formats = ["text"]
        elif self.args.format == "json":
            formats = ["json"]
        elif self.args.format == "csv":
            formats = ["csv"]

        saved_files = []

        for fmt in formats:
            try:
                if fmt == "text":
                    filepath = os.path.join(self.args.output_dir, f"cpu_report_{timestamp}.txt")
                    with open(filepath, "w", encoding='utf-8') as f:
                        f.write(self._format_text_report())
                    saved_files.append(("Text report", filepath))

                elif fmt == "json":
                    filepath = os.path.join(self.args.output_dir, f"cpu_report_{timestamp}.json")
                    report_data = {
                        "generated_by": Config.APP_NAME,
                        "version": Config.VERSION,
                        "timestamp": datetime.datetime.now().isoformat(),
                        "runtime_seconds": (datetime.datetime.now() - self.start_time).total_seconds(),
                        "refresh_count": self.refresh_count,
                        "cpu_info": self.cpu_info,
                        "sensor_data": self.sensor_data if self.sensor_data else None,
                        "system_info": {
                            "python_version": sys.version,
                            "platform": sys.platform,
                            "terminal_width": self.terminal_width
                        }
                    }

                    with open(filepath, "w", encoding='utf-8') as f:
                        json.dump(report_data, f, indent=2, default=str)
                    saved_files.append(("JSON report", filepath))

                elif fmt == "csv":
                    filepath = os.path.join(self.args.output_dir, f"cpu_report_{timestamp}.csv")
                    with open(filepath, "w", encoding='utf-8', newline='') as f:
                        f.write(self._format_csv_report())
                    saved_files.append(("CSV report", filepath))

            except Exception:
                import traceback
                traceback.print_exc()

                input("Press enter to exit...")
                sys.exit(1)

        # Display save confirmation
        if saved_files:
            print(f"\n{Colors.SUCCESS}Reports saved successfully:{Colors.END}")
            for report_type, path in saved_files:
                file_size = os.path.getsize(path)
                size_str = f"({file_size:,} bytes)" if file_size < 1024 else f"({file_size / 1024:.1f} KB)"
                print(f"  {Colors.SUCCESS}✓ {report_type}: {Colors.END}{path} {Colors.DIM}{size_str}{Colors.END}")
        else:
            print(f"{Colors.ERROR}No reports were saved{Colors.END}")


def __main__() -> int:
    """Main function to run the CPU monitoring Interface tool"""

    try:
        # Create and run the interface
        cli = Interface()
        cli.run()
        return 0

    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Application interrupted by user{Colors.END}")
        return 1

    except (ProcessorPyException, Exception):
        import traceback
        traceback.print_exc()

        input("Press enter to exit...")
        return 1


if __name__ == "__main__":
    sys.exit(__main__())
