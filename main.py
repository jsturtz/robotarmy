import PySimpleGUI as sg
import util
import ui_tools as ui
import robots
import db_tools as db
from collections import OrderedDict
import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow
from mainwindow import Ui_MainWindow

def main():

    config = util.get_config()
    con = util.get_connection()
    driver = util.get_chrome_driver()
    driver.implicitly_wait(10)

    app = QApplication(sys.argv)
    window = QMainWindow()
    ui = Ui_MainWindow(con, driver)
    ui.setupUi(window)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
