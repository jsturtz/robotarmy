import PySimpleGUI as sg
import util
import ui_tools as ui
import robots
import db_tools as db
from collections import OrderedDict

config = util.get_config()
con = util.get_connection()
driver = util.get_chrome_driver()
driver.implicitly_wait(10)

# Do the UI stuff
sg.theme(config["gui"]["theme"])   # Add a touch of color

# add the quicklinks buttons
def add_links(layout):

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
    '''
    structure = {
        "POST" : {
            "links": {"Home" : "some_url"},
            "courses": {
                "MKT200": {
                    "links": {"Home": "some_url"}
                }
            }
        },
        "GCU"...
    }
    
    '''
    print(structure)
    layout = add_subtitle(layout, "Universities")
    for uni, values in structure.items():
        layout.append([sg.Text(uni)] + [sg.Button(name, key=f"link-{url}") for name, url in values["links"].items()])
        for course, values in values["courses"].items():
            layout.append([sg.Text(f"\t{course}")] + [sg.Button(name, key=f"link-{url}") for name, url in values["links"].items()])
    return layout

def add_robots(layout):
    # add the robot buttons
    rows = db.query(con, 'SELECT button, robot, method, method_args FROM robots;')
    for button, robot, method, method_args in rows:
        layout.append(
            [sg.Button(button, key=f"robot-{robot}.{method}.{method_args}")]
        )
    return layout

def add_horizontal_line(layout):
    layout.append([sg.Text('---------------------------------------------------------------------')])
    return layout

def add_title(layout, title):
    layout.append([sg.Text(title, font=('Times New Roman', 24, 'bold'))])
    return layout

def add_subtitle(layout, subtitle):
    layout.append([sg.Text(subtitle, font=('Times New Roman', 14, 'bold'))])
    return layout


layout = []
layout = add_title(layout, "Quicklinks")
layout = add_links(layout)
layout = add_horizontal_line(layout)
layout = add_title(layout, "Robots")
layout = add_robots(layout)
layout = add_horizontal_line(layout)
layout.append([sg.Cancel()])

# Create the Window
window = sg.Window('Testing grading scripts', layout)

# Event Loop to process "events" and get the "values" of the inputs
while True:

    try:
        event, values = window.read()
        if event in (None, 'Cancel'):   # if user closes window or clicks cancel
            break

        event_type, event = event.split('-', 1)

        if event_type == "link":
            driver.get(event)

        elif event_type == "robot":
            # FIXME: actually add support for method args. Do we need this?
            robot, method, method_args = event.split(".")
            robot = getattr(robots, robot)(driver, con)
            getattr(robot, method)()

        else:
            raise Exception("Badly configured layout. Event type not valid")

    except Exception as e:
        ui.error_window(e)

con.close()
window.close()
