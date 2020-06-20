import PySimpleGUI as sg
import util
import ui_tools as ui
import robots
import db_tools as db
from collections import OrderedDict
import sys
from PyQt5 import QtWidgets, QtCore

config = util.get_config()
con = util.get_connection()
driver = util.get_chrome_driver()
driver.implicitly_wait(10)

app = QtWidgets.QApplication(sys.argv)
window = QtWidgets.QWidget()
layout = QtWidgets.QVBoxLayout(window)

rows = db.query_dict(con, """
    select  u.universitiesid, ul.pretty_name as uni_pretty_name, ul.url as uni_url, 
            c.coursesid, cl.pretty_name as course_pretty_name, cl.url as course_url
    from universities u 
    left join courses c on u.universitiesid = c.universitiesid 
    left join universities_links ul on ul.universitiesid = u.universitiesid 
    left join courses_links cl on cl.coursesid = c.coursesid and cl.universitiesid = u.universitiesid 
    order by u.universitiesid, c.coursesid;
""")

structure = OrderedDict()
for row in rows:
    structure.setdefault(row["universitiesid"], OrderedDict())
    if row["uni_url"] and row["uni_pretty_name"]:
        structure[row["universitiesid"]].setdefault("links", OrderedDict())
        structure[row["universitiesid"]]["links"].setdefault(row["uni_pretty_name"], row["uni_url"])

    structure[row["universitiesid"]].setdefault("courses", OrderedDict())
    if row["course_pretty_name"] and row["course_url"]:
        structure[row["universitiesid"]]["courses"].setdefault(row["coursesid"], OrderedDict())
        structure[row["universitiesid"]]["courses"][row["coursesid"]].setdefault("links", OrderedDict())
        structure[row["universitiesid"]]["courses"][row["coursesid"]]["links"][row["course_pretty_name"]] = row["course_url"]

tw = QtWidgets.QTreeWidget()
tw.setHeaderLabels(['Quicklinks'])
tw.setAlternatingRowColors(True)
top_widget = QtWidgets.QTreeWidgetItem(tw, ['Universities'])

for uni_name, values in structure.items():
    uni_widget = QtWidgets.QTreeWidgetItem(top_widget, [uni_name])
    courses_widget = QtWidgets.QTreeWidgetItem(uni_widget, ['Courses'])
    for course_name, values in values["courses"].items():
        course_widget = QtWidgets.QTreeWidgetItem(courses_widget, [course_name])
        for url_name, url in values["links"].items():
            link_widget = QtWidgets.QTreeWidgetItem(course_widget, [url_name])
            tw.setItemWidget(link_widget, 0, QtWidgets.QLabel(url_name))

    for url_name, url in values["links"].items():
        link_widget = QtWidgets.QTreeWidgetItem(uni_widget, [url_name])
        tw.setItemWidget(link_widget, 0, QtWidgets.QLabel(url_name))

layout.addWidget(tw)
window.show()
sys.exit(app.exec_())

con.close()
