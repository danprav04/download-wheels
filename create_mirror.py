import os
import shutil
import re
from collections import defaultdict

# --- Configuration ---
SOURCE_DIR = "wheelhouse"
MIRROR_ROOT = "mirror"
# --- End Configuration ---

def create_simple_repository():
    """
    Organizes a flat directory of wheels into a PEP 503 compliant
    simple repository structure.
    """
    if not os.path.isdir(SOURCE_DIR):
        print(f"Error: Source directory '{SOURCE_DIR}' not found.")
        return

    # The root of the simple repository structure
    simple_dir = os.path.join(MIRROR_ROOT, "simple")
    os.makedirs(simple_dir, exist_ok=True)
    print(f"Creating mirror structure in: {simple_dir}")

    # Group files by their normalized package name
    packages = defaultdict(list)
    for filename in os.listdir(SOURCE_DIR):
        if filename.endswith(('.whl', '.tar.gz')):
            # Normalize the package name (PEP 427)
            # e.g., "requests_aws4auth-1.2.3..." -> "requests-aws4auth"
            package_name = re.split(r'-(?=\d)', filename, 1)[0].lower().replace('_', '-')
            packages[package_name].append(filename)

    # Create the directory structure and index.html files
    for package_name, files in packages.items():
        package_dir = os.path.join(simple_dir, package_name)
        os.makedirs(package_dir, exist_ok=True)

        # Generate the index.html for the package
        with open(os.path.join(package_dir, "index.html"), "w") as f:
            f.write("<!DOCTYPE html>\n")
            f.write("<html>\n<head><title>Links for {}</title></head>\n".format(package_name))
            f.write("<body>\n<h1>Links for {}</h1>\n".format(package_name))
            for filename in sorted(files):
                # Copy the wheel file into the package directory
                shutil.copy(os.path.join(SOURCE_DIR, filename), package_dir)
                # Add a link to the index
                f.write('  <a href="{}">{}</a><br />\n'.format(filename, filename))
            f.write("</body>\n</html>\n")
        
        print(f"- Created index for {package_name} with {len(files)} file(s).")

    print("\nMirror structure created successfully.")
    print(f"You can now serve the '{MIRROR_ROOT}' directory with a web server.")

if __name__ == "__main__":
    create_simple_repository()
