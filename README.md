# Offline Python Package Downloader

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)

A powerful and efficient Python script that downloads all packages and their dependencies from a `requirements.txt` file into a local directory. This creates a portable "wheelhouse" that can be used to install packages on a machine with no internet access.

## Key Features

-   **Offline Installation Ready**: Creates a complete bundle of wheel (`.whl`) files for fully offline setups.
-   **Full Dependency Resolution**: Automatically downloads all dependencies and sub-dependencies for every library listed.
-   **Blazing Fast & Efficient**: Uses multithreading to download up to 10 packages in parallel, drastically reducing wait times.
-   **Intelligent Error Handling**: If a package fails to download due to version incompatibility, the script stops and provides smart suggestions for compatible versions.
-   **Skips Duplicates**: Automatically detects already downloaded packages and skips them, making it fast to resume after fixing an error.
-   **Automatic Build Tool Management**: Installs and manages necessary build dependencies like `setuptools` and `pybind11` to handle packages that need to be compiled from source.

## Requirements

-   **Python 3.8+** (Tested on Python 3.12)
-   A `requirements.txt` file listing the packages to download.

## How to Use

#### Step 1: Create your `requirements.txt`

Create a file named `requirements.txt` in the same directory as the script. List one package per line. You can specify exact versions or let pip choose the latest.

**Example `requirements.txt`:**

```txt
# You can specify exact versions
pandas==2.2.2
numpy==1.26.4
matplotlib==3.8.4

# Or let pip find the latest version
requests
fastapi
```

#### Step 2: Save the Script

Save the provided Python code as `download_wheels.py` in the same directory.

#### Step 3: Run from your Terminal

Open a terminal or command prompt, navigate to the directory, and run the script:

```bash
python download_wheels.py
```

The script will create a `wheelhouse` directory and begin downloading all necessary files.

## Troubleshooting

The most common error is when a specific package version is not compatible with your Python version (e.g., trying to download a package for Python 3.10 when you are running Python 3.12).

**Example Error Output:**

```
  └── !!! ERROR downloading numpy==1.24.4 !!!
----------------- PIP ERROR OUTPUT -----------------
ModuleNotFoundError: No module named 'distutils.msvccompiler'
----------------------------------------------------

--- ACTION REQUIRED ---
The package 'numpy==1.24.4' failed to download. It is likely not compatible with your system (Python 3.12).
Please MANUALLY UPDATE your requirements.txt file with a different version and run the script again.
  - Suggestion: numpy==1.26.4 (Latest in 1.26.x series with Py3.12 support)
  - Suggestion: numpy (To get the absolute latest version)
```

**How to Fix:**

1.  Read the suggestion provided by the script.
2.  Open your `requirements.txt` file.
3.  Update the version number of the failing package (e.g., change `numpy==1.24.4` to `numpy==1.26.4`).
4.  Save the file and run the script again. It will skip the already-downloaded packages and just try the one you fixed.

## Using the `wheelhouse` for Offline Installation

After the script finishes, you will have a `wheelhouse` directory full of `.whl` files. To use these for an offline installation:

1.  Copy the entire `wheelhouse` directory to the target machine (the one without internet access).
2.  Copy your `requirements.txt` file to the same machine.
3.  Open a terminal on the offline machine, navigate to the location of the files, and run the following command:

```bash
pip install --no-index --find-links=./wheelhouse -r requirements.txt
```

-   `--no-index`: Tells pip to not look for packages on the Python Package Index (PyPI).
-   `--find-links=./wheelhouse`: Tells pip to look for the required files in your local `wheelhouse` directory instead.

## Customization

You can easily configure the script by changing the constants at the top of the file:

```python
# --- Configuration ---
# The name of the requirements file
requirements_file = "requirements.txt"
# The directory to download the wheel files to
output_directory = "wheelhouse"
# Number of parallel downloads
MAX_WORKERS = 10
# --- End Configuration ---
```

---
