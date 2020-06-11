import PySimpleGUI as sg
from selenium import webdriver
import util
import ui_tools as ui
import robots
import browser_tools as br

config = util.get_config()
con = util.get_connection()
driver = webdriver.Chrome()
driver.implicitly_wait(10)

# Do the UI stuff
sg.theme(config["gui"]["theme"])   # Add a touch of color

layout = [
    [sg.Button("Grading Example Quicklink", key="grading_example")],
    [sg.Button("Grade Page", key="grade_page")]
]

# Create the Window
window = sg.Window('Testing grading scripts', layout)

# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read()
    if event in (None, 'Cancel'):   # if user closes window or clicks cancel
        break

    if event == 'grading_example':
        driver.get('https://post.blackboard.com/webapps/assignment/gradeAssignmentRedirector?outcomeDefinitionId=_2236357_1&currentAttemptIndex=2&numAttempts=10&anonymousMode=false&sequenceId=_94915_1_0&course_id=_94915_1&source=cp_gradebook&viewInfo=Full+Grade+Center&attempt_id=_13009013_1&courseMembershipId=_7990685_1&cancelGradeUrl=%2Fwebapps%2Fgradebook%2Fdo%2Finstructor%2FenterGradeCenter%3Fcourse_id%3D_94915_1&submitGradeUrl=%2Fwebapps%2Fgradebook%2Fdo%2Finstructor%2FperformGrading%3Fcourse_id%3D_94915_1%26cmd%3Dnext%26sequenceId%3D_94915_1_0')

    if event == 'grade_page':
        try:
            # figure out which platform is being used
            if "blackboard" in driver.current_url:
                robot = robots.BlackBoardGrader(driver, con)
                # add the rest of the conditionals once we code this up for the four platforms
            else:
                raise Exception("No robots were found for grading this page (is your browser currently on the right URL?)")

            robot.grade()
        except Exception as e:
            ui.error_window(e)

con.close()
window.close()
