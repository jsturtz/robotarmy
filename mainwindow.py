# -*- coding: utf-8 -*-
from PyQt5.QtCore import QRect, QSize, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import *

import db_tools as db
from robots import LoginSelector, GraderSelector
from ui_core import ClickQLabel


class Ui_MainWindow(object):

    def __init__(self, con, driver):
        self.con = con
        self.driver = driver

    # --------------------------------------------------------
    # Slots

    # Hides/shows grid beneath each checkbox
    def checked(self):
        checkbox = self.centralwidget.sender()
        set_visible = checkbox.isChecked()
        checkbox_name = checkbox.objectName().split("_")[0]
        grid = self.centralwidget.findChild(QWidget, f"{checkbox_name}_gridwidget")
        grid.setVisible(set_visible)

    # handles links in quicklinks
    def link_clicked(self):
        link = self.centralwidget.sender()
        self.driver.get(link.url)

    # grades class based on location of driver webpage
    def grade(self):
        grader = GraderSelector(self.driver, self.con)
        grader.grade()

    # logs in based on location of driver webpage
    def login(self):
        loginner = LoginSelector(self.driver, self.con)
        loginner.login()

    # --------------------------------------------------------
    # Setup
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(728, 858)

        # menu shit
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 728, 34))
        MainWindow.setMenuBar(self.menubar)

        # status bar shit
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")

        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        MainWindow.setStatusBar(self.statusbar)
        MainWindow.setCentralWidget(self.centralwidget)
        MainWindow.setWindowTitle("Robot Army!")

        # fonts
        self.normal_font = QFont()
        self.normal_font.setPointSize(12)
        self.link_font = QFont()
        self.link_font.setPointSize(12)
        self.link_font.setUnderline(True)
        MainWindow.setFont(self.normal_font)

        # add robot layout
        self.gridLayoutWidget = QWidget(self.centralwidget)
        self.gridLayoutWidget.setObjectName(u"gridLayoutWidget")
        self.gridLayoutWidget.setGeometry(QRect(40, 30, 631, 81))

        self.robots_layout = QGridLayout(self.gridLayoutWidget)
        self.robots_layout.setObjectName(u"robots_layout")
        self.robots_layout.setContentsMargins(0, 0, 0, 0)

        self.robot_label = QLabel(self.gridLayoutWidget)
        self.robot_label.setObjectName(u"robot_label")
        self.robot_label.setText("Robots")

        self.grade_btn = QPushButton(self.gridLayoutWidget)
        self.grade_btn.setObjectName(u"grade_btn")
        self.grade_btn.setText("GRADE")
        self.grade_btn.clicked.connect(self.grade)

        self.login_btn = QPushButton(self.gridLayoutWidget)
        self.login_btn.setObjectName(u"login_btn")
        self.login_btn.setText("LOGIN")
        self.login_btn.clicked.connect(self.login)

        self.robot_line_1 = QFrame(self.gridLayoutWidget)
        self.robot_line_1.setObjectName(u"robot_line_1")
        self.robot_line_1.setFrameShape(QFrame.HLine)
        self.robot_line_1.setFrameShadow(QFrame.Sunken)
        self.robot_line_2 = QFrame(self.gridLayoutWidget)
        self.robot_line_2.setObjectName(u"robot_line_2")
        self.robot_line_2.setFrameShape(QFrame.HLine)
        self.robot_line_2.setFrameShadow(QFrame.Sunken)

        self.robots_layout.addWidget(self.robot_label, 1, 0, 1, 1)
        self.robots_layout.addWidget(self.grade_btn, 4, 1, 1, 1)
        self.robots_layout.addWidget(self.login_btn, 4, 0, 1, 1)
        self.robots_layout.addWidget(self.robot_line_1, 2, 0, 1, 1)
        self.robots_layout.addWidget(self.robot_line_2, 2, 1, 1, 1)

        # add scrollArea so quicklinks don't run out of room
        self.scrollArea = QScrollArea(self.centralwidget)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setGeometry(QRect(30, 122, 661, 701))
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 640, 748))

        self.quicklinks_layout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.quicklinks_layout.setObjectName(u"quicklinks_layout")
        self.quicklinks_layout.setContentsMargins(0, 0, 0, 0)
        self.quicklinks_layout.setSizeConstraint(QLayout.SetNoConstraint)

        self.quicklinks_label = QLabel(self.scrollAreaWidgetContents)
        self.quicklinks_label.setObjectName(u"quicklinks_label")
        self.quicklinks_label.setMaximumSize(QSize(16777215, 24))
        self.quicklinks_label.setText("Quicklinks")

        self.quicklinks_line = QFrame(self.scrollAreaWidgetContents)
        self.quicklinks_line.setObjectName(u"quicklinks_line")
        self.quicklinks_line.setFrameShape(QFrame.HLine)
        self.quicklinks_line.setFrameShadow(QFrame.Sunken)

        self.quicklinks_layout.addWidget(self.quicklinks_label)
        self.quicklinks_layout.addWidget(self.quicklinks_line)

        # start building up quicklinks widget
        links_dict = db.get_links_dict(self.con)

        for uni, values in links_dict.items():

            # add checkbox
            uni_checkbox = QCheckBox(self.scrollAreaWidgetContents)
            uni_checkbox.setText(uni)
            uni_checkbox.setObjectName(f"{uni}_checkbox")
            uni_checkbox.setFont(self.normal_font)
            uni_checkbox.setChecked(False)
            uni_checkbox.toggled.connect(self.checked)
            self.quicklinks_layout.addWidget(uni_checkbox)

            # add grid for links and courses
            uni_grid_widget = QWidget(self.scrollAreaWidgetContents)
            uni_grid_widget.setObjectName(f"{uni}_gridwidget")
            uni_grid_widget.hide()
            uni_grid = QGridLayout(uni_grid_widget)
            uni_grid.setObjectName(f"{uni}_grid")
            uni_grid.setSizeConstraint(QLayout.SetNoConstraint)
            uni_grid_index = 0

            # add all uni links
            for url_name, url in values["links"].items():
                link = ClickQLabel(uni_grid_widget)
                link.setObjectName(f"{uni}{url_name}_link")
                link.setFont(self.link_font)
                link.setText(url_name)
                link.setStyleSheet('color: blue')
                link.url = url
                link.clicked.connect(self.link_clicked)
                uni_grid.addWidget(link, uni_grid_index, 1, 1, 1)
                uni_grid_index += 1
            '''
            # Comment this back in when you want to test scroll bar working
            if uni == 'POST':
                for link_name in ("TEST1", "TEST2", "TEST3", "TEST4", "TEST5", "TEST6", "TEST7"):
                    link = QLabel(uni_grid_widget)
                    link.setObjectName(f"{uni}_home_link")
                    link.setFont(self.link_font)
                    link.setText(link_name)
                    link.setStyleSheet('color: blue')
                    uni_grid.addWidget(link, uni_grid_index, 1, 1, 1)
                    uni_grid_index += 1
            '''
            # add courses
            uni_spacer = QSpacerItem(40, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
            uni_grid.addItem(uni_spacer, uni_grid_index, 0, 1, 1)

            for course, values in values["courses"].items():

                # add course checkbox
                course_checkbox = QCheckBox(uni_grid_widget)
                course_checkbox.setText(course)
                course_checkbox.setObjectName(f"{uni}{course}_checkbox")
                course_checkbox.setFont(self.normal_font)
                course_checkbox.setChecked(False)
                course_checkbox.toggled.connect(self.checked)
                uni_grid.addWidget(course_checkbox, uni_grid_index, 1, 1, 1)
                uni_grid_index += 1

                # create widget and grid for course
                course_grid_widget = QWidget(uni_grid_widget)
                course_grid_widget.setObjectName(f"{uni}{course}_gridwidget")
                course_grid_widget.hide()

                course_grid = QGridLayout(course_grid_widget)
                course_grid.setObjectName(f"{uni}{course}_grid")
                course_grid.setSizeConstraint(QLayout.SetNoConstraint)
                course_grid_index = 0

                # add course spacer
                course_spacer = QSpacerItem(40, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
                course_grid.addItem(course_spacer, 0, 0, 1, 1)

                # add links for course
                for url_name, url in values["links"].items():

                    link = ClickQLabel(course_grid_widget)
                    link.setText(url_name)
                    link.setObjectName(f"{uni}{course}{url_name}_link")
                    link.setFont(self.link_font)
                    link.setStyleSheet('color: blue')
                    link.url = url
                    link.clicked.connect(self.link_clicked)
                    course_grid.addWidget(link, course_grid_index, 1, 1, 1)
                    course_grid_index += 1

                # add course grid to uni grid
                uni_grid.addWidget(course_grid_widget, uni_grid_index, 1, 1, 1)
                uni_grid_index += 1

            self.quicklinks_layout.addWidget(uni_grid_widget)

        # final spacer (FIXME: Terrible solution probably)
        # Want to make the entire screen responsive horizontally and vertically to some minimum before
        # scroll bars show up to handle getting smaller
        self.quicklinks_verticalspacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.quicklinks_layout.addItem(self.quicklinks_verticalspacer)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        # dafuq is this?
        # QMetaObject.connectSlotsByName(MainWindow)
