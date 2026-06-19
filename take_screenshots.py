"""Take screenshots for ChaBiao v0.4.0 — GUI and CLI."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

IMG_DIR = Path("/Users/fred/Documents/GitHub/EasyCam/ChaBiao/images")
DEMO_FILE = "/tmp/chabiao_demo.xlsx"
IMG_DIR.mkdir(exist_ok=True)


def take_gui_screenshots():
    """Generate a standalone screenshot script and run it."""
    script = '''
import sys
import time
from pathlib import Path

IMG_DIR = Path("''' + str(IMG_DIR) + '''")
DEMO_FILE = "''' + DEMO_FILE + '''"

from PySide6 import QtCore, QtWidgets
from chabiao.gui import ChaBiaoWindow

app = QtWidgets.QApplication(sys.argv)
win = ChaBiaoWindow()

def _grab(name):
    pixmap = win.window.grab()
    path = str(IMG_DIR / name)
    pixmap.save(path, "PNG")
    print(f"  Saved: {path}", flush=True)

steps = []

def _load():
    win.model.load(DEMO_FILE)
    win.path_label.setText("📂 chabiao_demo.xlsx")
    win.info_label.setText("2000 rows × 6 cols")
    win._load_data_to_table(win.model.current_df)
    win._update_page_info()

def _filter():
    win.filter_column.setCurrentText("Department")
    win.filter_keyword.setText("Engineering")
    win.filter_mode.setCurrentText("contains")
    win._do_filter()

def _clear():
    win._clear_filter()

def _spotlight():
    win._toggle_spotlight()
    win.table.setCurrentCell(2, 1)
    win._apply_spotlight(2, 1)

def _spotlight_off():
    win._toggle_spotlight()

def _dark():
    win._switch_theme("dark")

def _zh():
    win._switch_language("zh")

def _ja():
    win._switch_language("ja")

def _light_en():
    win._switch_theme("light")
    win._switch_language("en")

def _products_sheet():
    win.sheet_tab.setCurrentIndex(1)
    win._on_sheet_changed(1)

steps = [
    ("gui_light_empty.png", lambda: None),
    ("gui_light_data.png", _load),
    ("gui_light_filter.png", _filter),
    ("gui_light_spotlight.png", lambda: (_clear(), _spotlight())),
    ("gui_dark_data.png", lambda: (_spotlight_off(), _dark())),
    ("gui_dark_zh.png", _zh),
    ("gui_dark_ja.png", _ja),
    ("gui_light_multisheet.png", _light_en),
    ("gui_light_products_sheet.png", _products_sheet),
]

current = [0]

def next_step():
    idx = current[0]
    if idx >= len(steps):
        app.quit()
        return
    name, action = steps[idx]
    action()
    QtCore.QCoreApplication.processEvents()
    time.sleep(0.3)
    _grab(name)
    current[0] += 1
    QtCore.QTimer.singleShot(50, next_step)

win.window.show()
win.window.raise_()
QtCore.QCoreApplication.processEvents()
time.sleep(0.3)
QtCore.QTimer.singleShot(200, next_step)
app.exec()
print("GUI screenshots done!", flush=True)
'''
    script_path = Path("/tmp/chabiao_screenshot_gui.py")
    script_path.write_text(script)
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(Path(__file__).parent if '__file__' in dir() else "."),
        timeout=60,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"  GUI screenshot error: {result.stderr[:500]}")


def take_cli_screenshots():
    """Capture CLI output to text files."""
    cmds = [
        ("cli_open.txt", ["chabiao", "open", DEMO_FILE]),
        ("cli_filter.txt", ["chabiao", "filter", DEMO_FILE, "--column", "Department", "--contains", "Engineering"]),
        ("cli_search.txt", ["chabiao", "search", DEMO_FILE, "--keyword", "Engineering"]),
        ("cli_spotlight.txt", ["chabiao", "spotlight", DEMO_FILE, "--row", "5", "--column", "Salary"]),
    ]
    for name, cmd in cmds:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            output = result.stdout if result.stdout else result.stderr
            (IMG_DIR / name).write_text(output[:5000])
            print(f"  CLI {name}: {len(output)} chars")
        except Exception as e:
            print(f"  CLI {name} error: {e}")


def take_web_screenshots_note():
    """Print note about web screenshots."""
    print("\n  Web screenshots need manual browser capture at http://localhost:8900")
    print("  Suggested URLs:")
    print("    http://localhost:8900/?lang=en&theme=light  → web_light.png")
    print("    http://localhost:8900/?lang=zh&theme=dark   → web_dark_zh.png")


if __name__ == "__main__":
    print("=== Taking GUI screenshots ===")
    take_gui_screenshots()
    print("\n=== Taking CLI screenshots ===")
    take_cli_screenshots()
    print("\n=== Web screenshots ===")
    take_web_screenshots_note()
    print("\nDone!")