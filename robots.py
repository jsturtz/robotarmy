'''
For now, put all "robot" classes here.
All "Grader" classes should have a "grade" method that the caller can execute.
'''

import re
import ui_tools as ui
import browser_tools as br
import db_tools as db
import PySimpleGUI as sg
import util

class QuickLinks:

    def __init__(self, driver, con):
        self.driver = driver
        self.con = con

    def display_links(self):
        columns = ['pretty_name', 'url']
        uni_links = db.query_grouped_by_dict(self.con, 'universities_links', 'universitiesid', columns)
        course_links = db.query_grouped_by_dict(self.con, 'courses_links', 'coursesid', columns)
        assign_links = db.query_grouped_by_dict(self.con, 'assignments_links', 'assignmentsid', columns)

        layout = []
        if uni_links:
            layout.append([sg.Text('Universities')])
            for uni, links in uni_links.items():
                layout.append([sg.Text(uni)] + [sg.Button(link[0], key=link[1]) for link in links])
        if course_links:
            layout.append([sg.Text('Courses')])
            for course, links in course_links.items():
                layout.append([sg.Text(course)] + [sg.Button(link[0], key=link[1]) for link in links])
        if assign_links:
            layout.append([sg.Text('Universities')])
            for assignment, links in uni_links.items():
                layout.append([sg.Text(assignment)] + [sg.Button(link[0], key=link[1]) for link in links])
        if not layout:
            layout.append([sg.Text("You have not created any links. Insert some records into universities_links, courses_links, or assignments_links")])
        layout.append([sg.Cancel()])

        window = sg.Window('Quicklinks', layout)
        while True:
            event, values = window.read()
            if event in (None, 'Cancel'):   # if user closes window or clicks cancel
                break

            # the event in this case always holds the url
            self.driver.get(event)
        window.close()

class Grader:

    def __init__(self, driver, con):

        self.driver = driver
        self.con = con

        if "blackboard" in self.driver.current_url:
            self.robot = BlackBoardGrader(self.driver, self.con)
            # add the rest of the conditionals once we code this up for the four platforms
        elif "lms-grad.gcu" in self.driver.current_url:
            self.robot = LoudCloudGrader(self.driver, self.con)
        else:
            raise Exception("No robots were found for grading this page (is your browser currently on the right URL?)")

    def grade(self):
        self.robot.grade()

class BlackBoardGrader:

    def __init__(self, driver, con):

        self.driver = driver
        self.con = con


    def grade(self):
        self.initialize_data_from_page()
        self.open_rubric_pane()
        rubric_elems = self.get_rubric_elems_from_page()
        layout = self.build_radio_selector_layout(rubric_elems)

        window = sg.Window("Select grades", layout)
        while True:
            try:
                event, values = window.read()
                if event in (None, 'Cancel'):   # if user closes window or clicks cancel
                    break

                if event == 'Submit':

                    # iterate over the rubric_elems
                    for index, elem in enumerate(rubric_elems):
                        # Get the identifiers of all the radios in elem
                        identifiers = elem["radios"].keys()

                        # find which identifier has been selected from ui
                        selected_identifier = [key for key, val in values.items() if key in identifiers and val][0]

                        # click that identifier
                        btn = elem["radios"][selected_identifier]["btn"]
                        btn_parent = btn.find_element_by_xpath("./..")
                        # does weird stuff if you try to click already selected radio so make sure not selected
                        if "selectedCell" not in btn_parent.get_attribute("class"):
                            br.safely_click(self.driver, btn)

                        # is max scoring iff selected radio's label matches max scoring keyword
                        is_max_scoring = elem["radios"][selected_identifier]["label"] == self.max_scoring_keyword

                        # pass in the tuple (title, is_max_scoring) to get the response
                        response = self.rubric_responses[(elem["title"], is_max_scoring)]

                        # send that response to the textbox
                        elem["feedback"].clear()
                        elem["feedback"].send_keys(br.replace_newlines(response))

                    # submit summative feedback
                    elem = self.driver.find_element_by_xpath('//div[@class="rubricGradingComments"]//textarea')
                    elem.send_keys(br.replace_newlines(self.summative_feedback))

                    # submit button!
                    submit_btn = self.driver.find_element_by_xpath("//a[@class='button-3' and text()='Save Rubric']")
                    # FIXME: Uncomment out this line to get the final submission
                    # br.safely_click(self.driver, submit_btn)

            except Exception as e:
                ui.error_window(e)

    def initialize_data_from_page(self):

        # Determine university from url
        m = re.search('([a-z]*)\.blackboard', self.driver.current_url)
        if not m:
            raise Exception("Could not determine university name")
        universitiesid = m.group(1).upper()

        # determine assignment from element with id called "pageTitleText"
        assignment_ui_id = self.driver.find_element_by_id('pageTitleText').text.strip()

        # if discussion post, just use rubric elements on university
        if "Discussion Forum" in assignment_ui_id:
            rows = db.get_discussion_board_rubric_elements(self.con, universitiesid)
            self.rubric_responses = {(row[0], row[1]): row[2] for row in rows if rows}
            self.student_name = assignment_ui_id.split(": ")[1].split(" ")[0]
            self.max_scoring_keyword = 'Excellent'  #FIXME: Hardcoded value here is bad booooo

        # else, must get rubric elems on assignment, course, uni
        else:
            # get student first name from page
            elem = self.driver.find_element_by_xpath('//div[@class="students-pager"]//span[contains(text(), "Attempt")]')
            self.student_name = elem.text.split(" ")[0] if elem else None

            # determine course from "crumb_1" element
            course_ui_id = self.driver.find_element_by_id('crumb_1').text.strip()
            coursesid = db.queryOneVal(self.con, f"""
                SELECT coursesid FROM courses 
                WHERE ui_identifier = '{course_ui_id}';""")
            if not course_ui_id or not coursesid:
                raise Exception("Could not determine course name")

            assignmentsid = db.queryOneVal(self.con, f"""
                SELECT assignmentsid FROM assignments 
                WHERE ui_identifier = '{assignment_ui_id}'
                AND coursesid = '{coursesid}';""")
            if not assignmentsid:
                raise Exception("Could not determine assignmentsid")

            # get max scoring keyword from assignment
            self.max_scoring_keyword = db.queryOneVal(self.con, f"""
                SELECT max_scoring_keyword FROM assignments
                WHERE assignmentsid = '{assignmentsid}' AND coursesid = '{coursesid}';""")
            if not self.max_scoring_keyword:
                raise Exception('Could not determine max scoring keyword (e.g. "Exemplary")')

            # get rubric element responses
            rows = db.get_all_rubric_elements(self.con, universitiesid, coursesid, assignmentsid)
            self.rubric_responses = {(row[0], row[1]): row[2] for row in rows if rows}

        # assign summative feedback for rubric elements
        self.summative_feedback = db.get_university_summative_feedback(self.con, universitiesid, self.student_name)

        if not self.student_name:
            raise Exception("No student name found on the page")
        if not self.rubric_responses:
            raise Exception("No rubric responses found for this assignment.")

    def open_rubric_pane(self):

        # click that little flappy thing if not already clicked
        elem = self.driver.find_element_by_id('currentAttempt_gradeDataPanelLink')
        if elem.get_attribute("aria-expanded") == "false":
            br.safely_click(self.driver, elem)

        # click the rubric link thing
        elem = self.driver.find_element_by_id("collabRubricList").find_element_by_class_name("itemHead")
        br.safely_click(self.driver, elem)

        # make sure feedback is open
        if not self.driver.find_element_by_class_name("feedback").is_displayed():
            br.safely_click(self.driver, self.driver.find_element_by_id("rubricToggleFeedback"))

    '''
    This creates a data structure like this: 

    rubric_elems = [
        "title": "Grammar", 
        "feedback": WebdriverElement to send response to
        "radios": {
            "Exemplary-1": {
                "btn": WebdriverElement to click,
                "label": "Exemplary"
            }
        }
    ]
    '''

    def get_rubric_elems_from_page(self):
        rubric_elems = []
        grading_element = self.driver.find_elements_by_class_name("rubricGradingRow")
        for index, elem in enumerate(grading_element):
            rubric_elem = {}
            rubric_elem["title"] = br.get_text_excluding_children(self.driver, elem.find_element_by_tag_name("h4")).strip()
            rubric_elem["feedback"] = elem.find_element_by_class_name("rowFeedbackField")
            rubric_elem["radios"] = {}
            grading_cells = elem.find_elements_by_class_name("rubricGradingCell")
            for cell in grading_cells:
                btn = cell.find_element_by_class_name("rubricCellRadio")
                label = br.get_text_excluding_children(self.driver, cell.find_element_by_class_name("radioLabel")).strip()
                identifier = f"{label}-{index}"
                rubric_elem["radios"][identifier] = {"btn": btn, "label": label}
            rubric_elems.append(rubric_elem)
        return rubric_elems

    def build_radio_selector_layout(self, rubric_elems):
        layout = []
        for i, elem in enumerate(rubric_elems):
            layout.append([sg.Text(elem["title"], key=f"title-{i}")])
            max_points_radio = []
            for identifier, radio in elem["radios"].items():
                label = radio["label"]
                if util.same_string(label, self.max_scoring_keyword):
                    max_points_radio = [sg.Radio(label, f"RADIO{i}", default=True, key=identifier)]
                    break
            layout.append(max_points_radio + [sg.Radio(radio["label"], f"RADIO{i}", key=identifier) for identifier, radio in elem["radios"].items() if radio["label"] != self.max_scoring_keyword])
        layout.append([sg.Submit()])
        return layout

class LoudCloudGrader:

    def __init__(self, driver, con):

        self.driver = driver
        self.con = con

    def grade(self):
        print("We're grading loudcloud now!")
