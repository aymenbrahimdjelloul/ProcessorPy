"""
@author : Aymen Brahim Djelloul
version : 1.0.1
date : 10.07.2024
License : MIT


    // Updater Module for ProcessorPy //

Description:
    This module is designed to handle the downloading and updating of application data for MyApp.
     It facilitates the process of fetching update files from a specified URL and saving them to a local directory.

Functionality:
    - Downloads update files from a given URL.
    - Saves the downloaded files to a specified path on the local file system.
    - Ensures that the directory structure exists before saving the file.

Operational Notes:
    - Verify that the script has sufficient permissions to write to the specified
      file path to avoid any `PermissionError`.
    - The script should handle potential network issues and file I/O errors gracefully.
    - Ensure the URL provided is correct and accessible to prevent download failures.


"""

# IMPORTS
import sys
import os
import requests
import zipfile
import subprocess
from time import sleep

def _is_process_running(process_name: str = "ProcessorPy") -> bool:
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


class Updater:

    def __init__(self):

        # Make a request to get the latest update data
        self.UPDATE_DATA = requests.get(
            "https://api.github.com/repos/aymenbrahimdjelloul/ProcessorPy/releases/latest").json()

        # Define variables
        self.download_link: str = self.UPDATE_DATA['assets'][0]['browser_download_url']

    def run(self):
        """ This method will download and install the update"""

        # Download the update data
        print("Downloading..")  # For Debugging
        # self.download_update(self.download_link, os.getcwd())

        # Kill the previous ProcessorPy App
        self.__kill_processor_py_process()

        # Check if ProcessorPy is running
        if _is_process_running():
            # retry to kill it cause sometimes it will not dead from the first execution
            self.__kill_processor_py_process()

        # Wait a half second to give ProcessorPy process time to end
        sleep(0.5)

        # Extract the downloaded data
        print("unzip..")   # For Debugging
        self.__extract_data("data.zip", os.getcwd())

        # Restart the App
        self.__restart_processor_py()

        print("update finished !")      # For debugging

        # Remove the downloaded data
        os.system("rm data.zip")
        # input()     # For Debugging
        # Exit the updater
        sys.exit([])

    @staticmethod
    def download_update(download_url: str, path: str):
        """ This method will download the update data"""

        #
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(f"{path}\\data.zip", 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        # Clear memory
        del r, f, chunk

    @staticmethod
    def __extract_data(zip_path: str, extract_to: str):
        """
        Extracts the contents of a ZIP file to a specified location.

        Parameters:
        zip_path (str): The path to the ZIP file.
        extract_to (str): The directory where the contents should be extracted.

        Raises:
        FileNotFoundError: If the ZIP file does not exist.
        zipfile.BadZipFile: If the file is not a valid ZIP file.
        PermissionError: If there are permission issues accessing the file or directory.
        """

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Extracted all contents of {zip_path} to {extract_to}")

        # except FileNotFoundError as fnf_error:
        #     print(fnf_error)
        # except zipfile.BadZipFile:
        #     print(f"The file '{zip_path}' is not a valid ZIP file.")
        # except PermissionError as perm_error:
        #     print(f"Permission error: {perm_error}")
        # except Exception as e:
        #     # print(f"An unexpected error occurred: {e}")
        #     pass

    @staticmethod
    def __kill_processor_py_process(process_name: str = "ProcessorPy.exe") -> int:
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

    @staticmethod
    def __restart_processor_py():
        """
        This function will rerun the ProcessorPy Application with the new update
        """

        # Run 'ProcessorPy.exe'
        os.startfile("ProcessorPy.exe")


if __name__ == "__main__":

    # Run the Updater program only if ProcessorPy is running
    if _is_process_running():
        # Create Updater object
        updater = Updater()
        # Run ProcessorPy updating process
        updater.run()
