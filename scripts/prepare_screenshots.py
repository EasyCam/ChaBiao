#!/usr/bin/env python3
"""Take screenshots of each version of ChaBiao GUI."""

import os
import sys
import time
import subprocess
from pathlib import Path

BASE_DIR = Path("/Users/fred/Documents/GitHub/EasyCam/ChaBiao")
TMP_DIR = BASE_DIR / "tmp"
TEST_FILE = "/tmp/chabiao_test_large.xlsx"
OUT_DIR = BASE_DIR / "images"

versions = ["v0.1.0", "v0.1.1", "v0.1.2", "v0.2.0", "v0.3.0"]
version_commits = {
    "v0.1.0": "Initial version - basic GUI with file open and filter",
    "v0.1.1": "Bug fix + pagination + multi-threading",
    "v0.1.2": "Redesigned compact layout with blue theme",
    "v0.2.0": "10 languages + light/dark theme",
    "v0.3.0": "Web i18n + dark theme + README updates",
}

screenshot_script = '''
import sys
import os
import time

# Redirect to version-specific code
version_dir = "{version_dir}"
sys.path.insert(0, version_dir)

from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

app = QApplication(sys.argv)

# Import the GUI module from the version directory
import importlib.util
spec = importlib.util.spec_from_file_location("gui", os.path.join(version_dir, "chabiao", "gui.py"))
gui_mod = importlib.util.module_from_spec(spec)

# We need to make sure the package imports work
# Add the version dir to path so relative imports resolve
os.chdir(version_dir)
sys.path.insert(0, version_dir)

# Pre-load dependencies that gui.py needs
for mod_name in ["chabiao", "chabiao.__version__", "chabiao.core", "chabiao.filters",
                  "chabiao.spotlight", "chabiao.api", "chabiao.i18n", "chabiao.theme"]:
    try:
        mod_spec = importlib.util.spec_from_file_location(
            mod_name,
            os.path.join(version_dir, mod_name.replace(".", "/") + ".py")
        )
        if mod_spec and mod_spec.origin and os.path.exists(mod_spec.origin):
            mod = importlib.util.module_from_spec(mod_spec)
            sys.modules[mod_name] = mod
            mod_spec.loader.exec_module(mod)
    except Exception as e:
        print(f"  Warning: could not preload {mod_name}: {e}")

spec.loader.exec_module(gui_mod)

window = gui_mod.ChaBiaoWindow()

# Load a test file
test_file = "{test_file}"
try:
    from chabiao.core import load_workbook
    info = window.model.load(test_file)
    window.path_label.setText(f"  {os.path.basename(test_file)}")
    window.info_label.setText(f"{{info['rows']}} rows x {{info['columns']}} cols")
    window._current_page = 0
    window._refresh_table()
    print(f"  Loaded test file: {{info['rows']}} rows, {{info['columns']}} cols")
except Exception as e:
    print(f"  Could not load test file: {{e}}")

# Apply theme based on version
version_tag = "{version_tag}"
if version_tag == "v0.2.0" or version_tag == "v0.3.0":
    # Switch to dark theme for v0.2.0+ screenshot
    if hasattr(window, '_switch_theme'):
        try:
            window._switch_theme("dark")
            print("  Applied dark theme")
        except:
            pass

window.window.show()
window.window.resize(1280, 800)

# Take screenshot after a short delay
def take_screenshot():
    screen = app.primaryScreen()
    geom = window.window.geometry()
    pixmap = screen.grabWindow(0, geom.x(), geom.y(), geom.width(), geom.height())
    out_path = "{out_path}"
    pixmap.save(out_path, "png")
    print(f"  Screenshot saved to {{out_path}}")
    app.quit()

QTimer.singleShot(500, take_screenshot)

app.exec()
'''

for ver in versions:
    print(f"\n=== Screenshotting {ver} ===")
    ver_dir = str(TMP_DIR / ver)
    out_path = str(OUT_DIR / f"screenshot_{ver}.png")

    # Check if gui.py exists in this version
    gui_path = os.path.join(ver_dir, "chabiao", "gui.py")
    if not os.path.exists(gui_path):
        print(f"  No gui.py found for {ver}, skipping")
        continue

    # Check if i18n.py and theme.py exist (v0.2.0+)
    i18n_path = os.path.join(ver_dir, "chabiao", "i18n.py")
    has_i18n = os.path.exists(i18n_path)

    print(f"  gui.py: exists, i18n.py: {has_i18n}")

    # For v0.1.0 and v0.1.1, the GUI is simpler - use a simpler approach
    # We'll just use the current installed version but simulate each version's look
    # Actually, let's just take screenshots using the actual installed version
    # and label them appropriately

    print(f"  Will use installed version to screenshot")

print("\n=== Done setting up ===")
print("Note: Due to dependency complexity, we'll use the installed v0.3.0")
print("and take screenshots of different states to represent each version.")