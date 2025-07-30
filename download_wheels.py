import subprocess
import sys
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor

# --- Configuration ---
# The name of the requirements file
requirements_file = "requirements.txt"
# The directory to download the wheel files to
output_directory = "wheelhouse"
# Number of parallel downloads
MAX_WORKERS = 10
# A list of packages that are required to build other packages from source.
BUILD_DEPENDENCIES = ["wheel", "setuptools", "pybind11"]
# --- End Configuration ---

# Global lock for thread-safe printing
print_lock = threading.Lock()

def install_build_dependencies():
    """Installs packages that are required for building other packages."""
    print("--- Step 1: Installing build dependencies ---")
    try:
        command = [
            sys.executable, "-m", "pip", "install", "--upgrade", *BUILD_DEPENDENCIES
        ]
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Successfully installed/updated: {', '.join(BUILD_DEPENDENCIES)}\n")
        return True
    except subprocess.CalledProcessError as e:
        with print_lock:
            print("!!!CRITICAL ERROR!!!\nFailed to install build dependencies.")
            print(f"Error details:\n{e.stderr}")
        return False
    except FileNotFoundError:
        with print_lock:
            print("Error: python/pip command not found. Is Python installed and in your PATH?")
        return False

def process_single_requirement(req_tuple):
    """
    Processes a single requirement: checks if it exists, otherwise downloads it.
    This function is designed to be called by a worker thread.
    """
    index, total, req, downloaded_files = req_tuple
    
    with print_lock:
        print(f"[{index}/{total}] Processing: {req}")

    # --- Check if already downloaded ---
    package_name = re.split(r'[=<>~!]', req)[0].lower().replace('_', '-')
    file_prefix_to_check = f"{package_name}-"
    if '==' in req:
        version = req.split('==')[1].split(';')[0].strip()
        file_prefix_to_check = f"{package_name}-{version}"
    
    is_downloaded = any(f.lower().startswith(file_prefix_to_check) for f in downloaded_files)

    if is_downloaded:
        with print_lock:
            print(f"  └── Skipping: A matching file for {req} already exists.")
        return True, None # Success

    # --- If not downloaded, proceed to download ---
    try:
        command = [
            sys.executable, "-m", "pip", "download",
            "--no-build-isolation",
            "-d", output_directory,
            req,
        ]
        subprocess.run(command, check=True, capture_output=True, text=True)
        with print_lock:
            print(f"  └── Success: Downloaded {req}")
        return True, None # Success

    except subprocess.CalledProcessError as e:
        # On error, return the error details for the main thread to handle
        error_output = e.stderr.strip()
        return False, (req, error_output)

def download_packages_multithreaded():
    """
    Reads the requirements file and uses a thread pool to download packages
    in parallel.
    """
    print(f"--- Step 2: Downloading packages from {requirements_file} using up to {MAX_WORKERS} threads ---")

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    downloaded_files = os.listdir(output_directory)

    try:
        with open(requirements_file, "r") as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        with print_lock:
            print(f"Error: '{requirements_file}' not found in this directory.")
        return

    # Create a list of tasks for the thread pool
    tasks = [(i+1, len(requirements), req, downloaded_files) for i, req in enumerate(requirements)]

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # map() runs tasks in parallel and returns results in order
        results = executor.map(process_single_requirement, tasks)

        for success, error_info in results:
            if not success:
                failed_req, error_output = error_info
                with print_lock:
                    print(f"\n  └── !!! ERROR downloading {failed_req} !!!")
                    print("----------------- PIP ERROR OUTPUT -----------------")
                    print(error_output)
                    print("----------------------------------------------------")
                    
                    package_name = re.split(r'[=<>~!]', failed_req)[0]
                    
                    print("\n--- ACTION REQUIRED ---")
                    print(f"The package '{failed_req}' failed to download. It is likely not compatible with your system (Python 3.12).")
                    print("Please MANUALLY UPDATE your requirements.txt file with a different version and run the script again.")
                    
                    # Provide specific advice for common packages
                    if 'numpy' in package_name.lower():
                        print("  - Suggestion: numpy==1.26.4 (Latest in 1.26.x series with Py3.12 support)")
                        print("  - Suggestion: numpy (To get the absolute latest version)")
                    elif 'matplotlib' in package_name.lower():
                         print("  - Suggestion: matplotlib==3.8.4 (Latest in 3.8.x series with Py3.12 support)")

                print("\nScript stopped due to the error. Please update the requirements file and restart.")
                # This will gracefully shut down the thread pool
                executor.shutdown(wait=False, cancel_futures=True)
                return

    print("\nAll packages and their dependencies downloaded successfully!")


if __name__ == "__main__":
    if install_build_dependencies():
        download_packages_multithreaded()
