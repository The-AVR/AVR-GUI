import os
import sys

if getattr(sys, "frozen", False):
    DATA_DIR = sys._MEIPASS  # type: ignore
    ROOT_DIR = os.path.dirname(sys.executable)
else:
    DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
    ROOT_DIR = DATA_DIR

# Root dir is the directory of the main entrypoint
# When bundled as an executable, this is the directory of the executable
ROOT_DIR = os.path.abspath(ROOT_DIR)
# Data dir is the root directory within the application itself
# When bundled as an executable, this is the temp extraction directory
DATA_DIR = os.path.abspath(DATA_DIR)
# Directory that contains images
IMG_DIR = os.path.join(DATA_DIR, "assets", "img")
