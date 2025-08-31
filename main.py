from windows import mainWindow
from core.AppController import AppController
import sys
from PySide6.QtWidgets import QApplication


def main():
    app = QApplication(sys.argv)
    win = mainWindow.MainWindow()
    contro = AppController(win)
    contro.start()
    win.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()