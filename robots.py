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

class BlackBoardGrader:

    def __init__(self, driver, con):

        self.driver = driver
        self.con = con

        # Determine university from url
        m = re.search('([a-z]*)\.blackboard', self.driver.current_url)
        if not m:
            raise Exception("Could not determine university name")
        self.university_code = m.group(1)

        # determine course from "crumb_1" element
        self.course_code = driver.find_element_by_id('crumb_1').text.strip()
        if not self.course_code:
            raise Exception("Could not determine course name")

        # determine assignment from element with id called "pageTitleText"
        self.assignment_code = driver.find_element_by_id('pageTitleText').text.strip()
        if not self.assignment_code:
            raise Exception("Could not determine assignment name")

        # get max scoring keyword from assignment
        # FIXME: Surely there's a better way to wrap all this connection shit?
        cur = self.con.cursor()
        cur.execute(f"SELECT max_scoring_keyword FROM assignments WHERE code = '{self.assignment_code}'")
        self.max_scoring_keyword = cur.fetchone()[0]
        cur.close()
        if not self.max_scoring_keyword:
            raise Exception('Could not determine max scoring keyword (e.g. "Exemplary")')

        self.rubric_responses = db.get_rubric_responses(self.con, self.university_code, self.course_code, self.assignment_code)

    def grade(self):
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
                    for elem in rubric_elems:

                        # Get the identifiers of all the radios in elem
                        identifiers = elem["radios"].keys()

                        # find which identifier has been selected from ui
                        selected_identifier = [key for key, val in values.items() if key in identifiers and val][0]

                        # click that identifier
                        br.move_and_click(self.driver, elem["radios"][selected_identifier]["btn"])

                        # is max scoring iff selected radio's label matches max scoring keyword
                        is_max_scoring = elem["radios"][selected_identifier]["label"] == self.max_scoring_keyword

                        # pass in the tuple (title, is_max_scoring) to get the response
                        response = self.rubric_responses[(elem["title"], is_max_scoring)]

                        # send that response to the textbox
                        elem["feedback"].send_keys(response)

                    # submit feedback
                    submit_btn = self.driver.find_element_by_xpath("//a[@class='button-3' and text()='Save Rubric']")
                    # FIXME: Uncomment out this line to get the final submission
                    # br.move_and_click(self.driver, submit_btn)

            except Exception as e:
                ui.error_window(e)

    def open_rubric_pane(self):

        # click that little flappy thing if not already clicked
        elem = self.driver.find_element_by_id('currentAttempt_gradeDataPanelLink')
        if elem.get_attribute("aria-expanded") == "false":
            br.move_and_click(self.driver, elem)

        # click the rubric link thing
        elem = self.driver.find_element_by_id("collabRubricList").find_element_by_class_name("itemHead")
        br.move_and_click(self.driver, elem)

        # make sure feedback is open
        if not self.driver.find_element_by_class_name("feedback").is_displayed():
            br.move_and_click(self.driver, self.driver.find_element_by_id("rubricToggleFeedback"))

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
