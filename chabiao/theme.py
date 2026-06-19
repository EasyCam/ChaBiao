"""Theme module for ChaBiao — light and dark QSS themes."""

from __future__ import annotations

LIGHT_QSS = """
QMainWindow { background: #f8f9fa; }
QLabel { color: #333; }
QPushButton {
    background: #1976D2; color: white; border: none;
    padding: 5px 14px; border-radius: 4px; font-size: 13px;
}
QPushButton:hover { background: #1565C0; }
QPushButton:pressed { background: #0D47A1; }
QPushButton#clearBtn { background: #78909C; color: white; }
QPushButton#clearBtn:hover { background: #607D8B; }
QPushButton#pageBtn { background: #e0e0e0; color: #333; padding: 3px 10px; }
QPushButton#pageBtn:hover { background: #bdbdbd; }
QComboBox {
    padding: 4px 8px; border: 1px solid #ccc; border-radius: 4px;
    background: white; min-width: 100px; color: #333;
}
QComboBox QAbstractItemView { background: white; color: #333; selection-background-color: #BBDEFB; }
QLineEdit {
    padding: 4px 8px; border: 1px solid #ccc; border-radius: 4px;
    background: white; color: #333;
}
QTableWidget {
    gridline-color: #e0e0e0; border: 1px solid #ddd;
    selection-background-color: #BBDEFB; color: #333; background: white;
}
QHeaderView::section {
    background: #1976D2; color: white; padding: 6px 10px;
    border: none; font-weight: 500;
}
QStatusBar { background: #f5f5f5; color: #666; }
QMenuBar { background: #f8f9fa; color: #333; }
QMenuBar::item:selected { background: #e3f2fd; }
QMenu { background: white; color: #333; border: 1px solid #ddd; }
QMenu::item:selected { background: #e3f2fd; }
QTabBar::tab {
    background: #e0e0e0; color: #333; padding: 6px 16px;
    border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px;
}
QTabBar::tab:selected { background: white; font-weight: bold; }
QScrollBar:vertical {
    background: #f0f0f0; width: 10px; border: none;
}
QScrollBar::handle:vertical { background: #bbb; border-radius: 5px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #f0f0f0; height: 10px; border: none;
}
QScrollBar::handle:horizontal { background: #bbb; border-radius: 5px; min-width: 30px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
"""

DARK_QSS = """
QMainWindow { background: #1e1e2e; }
QLabel { color: #cdd6f4; }
QPushButton {
    background: #89b4fa; color: #1e1e2e; border: none;
    padding: 5px 14px; border-radius: 4px; font-size: 13px; font-weight: 500;
}
QPushButton:hover { background: #b4befe; }
QPushButton:pressed { background: #74c7ec; }
QPushButton#clearBtn { background: #585b70; color: #cdd6f4; }
QPushButton#clearBtn:hover { background: #6c7086; }
QPushButton#pageBtn { background: #45475a; color: #cdd6f4; padding: 3px 10px; }
QPushButton#pageBtn:hover { background: #585b70; }
QComboBox {
    padding: 4px 8px; border: 1px solid #45475a; border-radius: 4px;
    background: #313244; min-width: 100px; color: #cdd6f4;
}
QComboBox QAbstractItemView {  # noqa: E501
    background: #313244; color: #cdd6f4; selection-background-color: #45475a;
}
QComboBox::drop-down { border: none; }
QLineEdit {
    padding: 4px 8px; border: 1px solid #45475a; border-radius: 4px;
    background: #313244; color: #cdd6f4;
}
QTableWidget {
    gridline-color: #45475a; border: 1px solid #45475a;
    selection-background-color: #45475a; color: #cdd6f4; background: #1e1e2e;
    alternate-background-color: #181825;
}
QHeaderView::section {
    background: #89b4fa; color: #1e1e2e; padding: 6px 10px;
    border: none; font-weight: 600;
}
QStatusBar { background: #181825; color: #a6adc8; }
QMenuBar { background: #1e1e2e; color: #cdd6f4; }
QMenuBar::item:selected { background: #45475a; }
QMenu { background: #313244; color: #cdd6f4; border: 1px solid #45475a; }
QMenu::item:selected { background: #45475a; }
QTabBar::tab {
    background: #313244; color: #cdd6f4; padding: 6px 16px;
    border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px;
}
QTabBar::tab:selected { background: #45475a; font-weight: bold; }
QScrollBar:vertical {
    background: #1e1e2e; width: 10px; border: none;
}
QScrollBar::handle:vertical { background: #45475a; border-radius: 5px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #1e1e2e; height: 10px; border: none;
}
QScrollBar::handle:horizontal { background: #45475a; border-radius: 5px; min-width: 30px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
"""

THEMES = {
    "light": LIGHT_QSS,
    "dark": DARK_QSS,
}

SPOTLIGHT_COLORS = {
    "light": {
        "row_col": (255, 255, 224),
        "focus": (255, 235, 59),
    },
    "dark": {
        "row_col": (49, 50, 68),
        "focus": (137, 180, 250),
    },
}
