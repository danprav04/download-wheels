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
BUILD_DEPENDENCIES = ["wheel", "setuptools", "pip"]

# --- Target Platform Configuration ---
# Define the Python version and platforms you want to download packages for.
# manylinux2014 is used for broad compatibility across most Linux distributions.
TARGET_PYTHON_VERSION = "3.12"
TARGET_PYTHON_ABI_TAG = f"cp{TARGET_PYTHON_VERSION.replace('.', '')}" # e.g., "cp312"

TARGET_PLATFORMS = [
    {
        "name": "Windows (64-bit)",
        "platform_tag": "win_amd64",
    },
    {
        "name": "Windows (32-bit)",
        "platform_tag": "win32",
    },
    {
        "name": "Linux (64-bit, x86_64)",
        "platform_tag": "manylinux2014_x86_64",
    },
    {
        "name": "Linux (32-bit, i686)",
        "platform_tag": "manylinux2014_i686",
    },
    {
        "name": "Linux (ARM 64-bit, aarch64)",
        "platform_tag": "manylinux2014_aarch64",
    },
]
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
    Processes a single requirement, downloading it and its dependencies for all
    target platforms. This function is designed to be called by a worker thread.
    """
    index, total, req = req_tuple

    # This function is called for each *line* in requirements.txt
    # We loop through platforms inside this function.
    for platform_info in TARGET_PLATFORMS:
        platform_name = platform_info["name"]
        platform_tag = platform_info["platform_tag"]
        
        # We check for existing files before every download attempt to avoid
        # re-downloading dependencies that another package already pulled in.
        downloaded_files = os.listdir(output_directory)

        with print_lock:
            print(f"[{index}/{total}] Processing: {req} for {platform_name}")

        # Check if a wheel for the *main package* already exists for this platform.
        # This is a simple check; pip will handle dependencies internally.
        package_name = re.split(r'[=<>~!]', req)[0].lower().replace('_', '-')
        is_downloaded = any(
            f.lower().startswith(package_name) and platform_tag in f.lower()
            for f in downloaded_files
        )

        if is_downloaded:
            with print_lock:
                print(f"  └── Skipping: A matching file for {req} ({platform_name}) already exists.")
            continue # Move to the next platform

        # --- If not downloaded, proceed to download ---
        try:
            # Note: The `--no-deps` flag is REMOVED to ensure all dependencies are downloaded.
            command = [
                sys.executable, "-m", "pip", "download",
                "--only-binary=:all:",
                "--platform", platform_tag,
                "--python-version", TARGET_PYTHON_VERSION,
                "--implementation", "cp",
                "--abi", TARGET_PYTHON_ABI_TAG,
                "-d", output_directory,
                req,
            ]
            subprocess.run(command, check=True, capture_output=True, text=True)
            with print_lock:
                print(f"  └── Success: Downloaded {req} and its dependencies for {platform_name}")

        except subprocess.CalledProcessError as e:
            error_output = e.stderr.strip()
            # If a binary wheel doesn't exist, pip gives a specific error.
            if f"Could not find a version that satisfies the requirement" in error_output:
                 with print_lock:
                    print(f"  └── WARNING: Could not find a pre-built binary for {req} (or one of its dependencies) on {platform_name}.")
                    print(f"     Pip Error: {error_output.splitlines()[-1]}")
            else:
                # For other errors, stop the script
                return False, (req, platform_name, error_output)

    return True, None # Success for this requirement across all platforms

def download_packages_multithreaded():
    """
    Reads the requirements file and uses a thread pool to download packages
    and their dependencies in parallel for all specified platforms.
    """
    print(f"--- Step 2: Downloading packages and all dependencies from {requirements_file} ---")
    platform_names = ', '.join([p['name'] for p in TARGET_PLATFORMS])
    print(f"Targeting Python {TARGET_PYTHON_VERSION} for platforms: {platform_names}\n")

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    try:
        with open(requirements_file, "r") as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        with print_lock:
            print(f"Error: '{requirements_file}' not found in this directory.")
        return

    # Create a list of tasks for the thread pool
    tasks = [(i + 1, len(requirements), req) for i, req in enumerate(requirements)]

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = executor.map(process_single_requirement, tasks)

        for success, error_info in results:
            if not success:
                failed_req, platform_name, error_output = error_info
                with print_lock:
                    print(f"\n  └── !!! FATAL ERROR downloading {failed_req} for {platform_name} !!!")
                    print("----------------- PIP ERROR OUTPUT -----------------")
                    print(error_output)
                    print("----------------------------------------------------")
                    print("\n--- ACTION REQUIRED ---")
                    print(f"The package '{failed_req}' (or one of its dependencies) failed to download for {platform_name}.")
                    print("This usually means a pre-built wheel is not available on PyPI for that specific platform.")

                print("\nScript stopped due to a fatal error. Please check the package's availability and restart.")
                executor.shutdown(wait=False, cancel_futures=True)
                return

    print(f"\nAll packages and their dependencies successfully processed for all target platforms!")
    print(f"Files are located in the '{output_directory}' directory.")


if __name__ == "__main__":
    if install_build_dependencies():
        download_packages_multithreaded()