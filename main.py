import PySimpleGUI as sg
import util
import ui_tools as ui
import robots
import db_tools as db

config = util.get_config()
con = util.get_connection()
driver = util.get_chrome_driver()
driver.implicitly_wait(10)

# Do the UI stuff
sg.theme(config["gui"]["theme"])   # Add a touch of color

# add the robot buttons
layout = []
rows = db.query(con, 'SELECT button, robot, method, method_args FROM robots;')
for button, robot, method, method_args in rows:
    layout.append(
        [sg.Button(button, key=f"{robot}.{method}.{method_args}")]
    )

# Create the Window
window = sg.Window('Testing grading scripts', layout)

# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read()
    if event in (None, 'Cancel'):   # if user closes window or clicks cancel
        break

    # FIXME: actually add support for method args. Do we need this?
    robot, method, method_args = event.split(".")

    try:
        robot = getattr(robots, robot)(driver, con)
        getattr(robot, method)()
    except Exception as e:
        ui.error_window(e)

con.close()
window.close()
