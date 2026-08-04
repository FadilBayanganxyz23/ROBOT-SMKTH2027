"""
Main Launcher for Field Layout Editor & Robot Simulator.
Run this script to launch the GUI application.
"""

import sys
import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from gui.main_window import MainWindow


def main():
    # High-DPI Scaling configuration
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("Field Layout Editor & Robot Simulator")
    app.setOrganizationName("Robotics Lab")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
