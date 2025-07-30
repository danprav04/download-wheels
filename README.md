# Offline Python Packager: Wheelhouse Downloader & Local Mirror

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)![License](https://img.shields.io/badge/license-MIT-green.svg)

A set of powerful Python scripts to download all necessary packages and dependencies from a `requirements.txt` file and serve them as a local, offline-accessible `pip` mirror. Ideal for air-gapped environments, CI/CD caching, or managing a controlled set of packages.

## Key Features

-   **Complete Dependency Resolution**: Downloads every sub-dependency for each library in your `requirements.txt`.
-   **High-Speed Parallel Downloads**: Uses multithreading to download up to 10 packages simultaneously, dramatically speeding up the process.
-   **Smart & Resumable**: Automatically skips packages that have already been downloaded, allowing you to easily resume after interruptions or additions.
-   **Build-From-Source Ready**: Pre-installs necessary build tools (`setuptools`, `wheel`, `pybind11`) to handle packages that don't have pre-compiled wheels for your system.
-   **Offline Mirror Creation**: Includes a script to organize the downloaded wheels into a PEP 503-compliant "simple" repository.
-   **Easy to Serve**: Host your local mirror with a single command using Python's built-in web server.

## Prerequisites

-   Python 3.10 or newer.
-   `pip` (usually included with Python).

## Quickstart Guide

Follow these steps to create a complete, offline repository of your project's dependencies.

### Step 1: Clone or Download the Scripts

Make sure you have the following files in your project directory:
-   `download_wheels.py`
-   `create_mirror.py`

### Step 2: Prepare Your `requirements.txt`

Create or update the `requirements.txt` file in the same directory. List all your direct Python dependencies with their versions.

**Example `requirements.txt`:**
```
bcrypt==3.2.0
boto3==1.34.10
fastapi==0.104.1
matplotlib==3.8.4
numpy==1.26.4
requests
# ...and so on
```

### Step 3: Download All Packages

Run the main download script. It will read your `requirements.txt`, create a `wheelhouse` directory, and download every package and dependency into it.

```bash
python download_wheels.py
```

The script will show progress and use multiple threads for speed. If it encounters an error with a specific package, it will stop and provide helpful suggestions (see Troubleshooting section).

### Step 4: Create the Mirror Structure

Once the `wheelhouse` is fully populated, run the `create_mirror.py` script. This organizes the flat list of wheels into the directory structure `pip` expects.

```bash
python create_mirror.py
```
This will create a new directory named `mirror/` containing the organized packages.

### Step 5: Run the Local Mirror

Serve the newly created `mirror` directory using Python's built-in web server.

1.  Navigate into the `mirror` directory:
    ```bash
    cd mirror
    ```

2.  Start the server:
    ```bash
    python -m http.server 8000
    ```
Your local `pip` mirror is now running and accessible at `http://localhost:8000/simple/`. Keep this terminal window open.

## Using Your Local Mirror

You can now instruct `pip` to install packages from your local mirror instead of the public PyPI. Open a **new terminal** for this.

#### Option A: Install Exclusively from Your Mirror (Offline Mode)

This command forces `pip` to only use your local repository. It will fail if a package is not found in your mirror.

```bash
pip install numpy --index-url http://localhost:8000/simple/
```

#### Option B: Use Your Mirror as the Primary Source (Recommended)

This command tells `pip` to look in your local mirror first. If a package isn't found, it will fall back to the public PyPI.

```bash
pip install some-new-package --extra-index-url http://localhost:8000/simple/
```

## Troubleshooting

The most common issue is a package version being incompatible with your Python version (e.g., trying to install a package for Python 3.8 on Python 3.12).

**Example Error:**
```
!!! ERROR downloading numpy==1.24.4 !!!
...
ModuleNotFoundError: No module named 'distutils.msvccompiler'
```

**Solution:**
1.  Read the error message from the script. It will suggest compatible versions.
2.  Open your `requirements.txt` file.
3.  Update the version number of the failing package (e.g., change `numpy==1.24.4` to `numpy==1.26.4`).
4.  Save the file and re-run `python download_wheels.py`. The script will skip the packages it already has and just download the corrected one.

## File Descriptions

-   **`download_wheels.py`**: The main workhorse. A multithreaded downloader that fetches all packages and dependencies listed in `requirements.txt` into the `wheelhouse/` directory.
-   **`create_mirror.py`**: The organizer. Takes the flat `wheelhouse/` directory and structures it into a PEP 503-compliant simple repository inside the `mirror/` directory.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
