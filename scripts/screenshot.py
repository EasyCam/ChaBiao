#!/usr/bin/env python3
"""Screenshot a running ChaBiao GUI window."""
import sys
import os

from chabiao.gui import ChaBiaoWindow

window = ChaBiaoWindow()

test_file = "/tmp/chabiao_test_large.xlsx"
try:
    info = window.model.load(test_file)
    from pathlib import Path
    if hasattr(window, 'path_label'):
        window.path_label.setText(f"\U0001f4c2 {Path(test_file).name}")
    if hasattr(window, 'info_label'):
        window.info_label.setText(f"{info['rows']} rows x {info['columns']} cols")
    window._current_page = 0
    window._refresh_table()
    print(f"Loaded: {info['rows']} rows, {info['columns']} cols")
except Exception as e:
    print(f"Could not load test file: {e}")
    import traceback
    traceback.print_exc()

window.window.show()
window.window.resize(1280, 800)

screen = window.app.primaryScreen()
if screen:
    geo = screen.availableGeometry()
    x = (geo.width() - 1280) // 2
    y = (geo.height() - 800) // 2
    window.window.move(x, y)

version_tag = sys.argv[1] if len(sys.argv) > 1 else "unknown"
out_path = sys.argv[2] if len(sys.argv) > 2 else f"/tmp/screenshot_{version_tag}.png"

from PySide6.QtCore import QTimer

def take_screenshot():
    win_id = int(window.window.winId())
    scr = window.app.primaryScreen()
    pixmap = scr.grabWindow(win_id)
    pixmap.save(out_path, "png")
    print(f"Screenshot saved: {out_path} ({pixmap.width()}x{pixmap.height()})")
    window.app.quit()

QTimer.singleShot(800, take_screenshot)

window.app.exec()