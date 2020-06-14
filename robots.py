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
from abc import ABC, abstractmethod, abstractproperty
from selenium.webdriver.common.by import By
from collections import OrderedDict

class LoginSelector:

    def __init__(self, driver, con):

        self.driver = driver
        self.con = con

        # add the code necessary to find login elements on page, get config
        if 'post.blackboard' in self.driver.current_url:
            self.config = util.get_config()['post']
            self.user_elem = driver.find_element_by_id("user_id")
            self.pass_elem = driver.find_element_by_id("password")
            self.submit_btn = driver.find_element_by_id("entry-login")

        elif 'gcu.edu' in self.driver.current_url:
            self.config = util.get_config()['gcu']
            self.user_elem = self.driver.find_element_by_id('usrName')
            self.pass_elem = self.driver.find_element_by_id('passwrd')
            self.submit_btn = self.driver.find_element_by_id('myFormLogin')

    def login(self):
        self.user_elem.clear()
        self.pass_elem.clear()
        self.user_elem.send_keys(self.config["username"])
        self.pass_elem.send_keys(self.config["password"])
        br.safely_click(self.driver, self.submit_btn)

class GraderSelector:

    def __init__(self, driver, con):

        self.driver = driver
        self.con = con

        if "blackboard" in self.driver.current_url:
            self.robot = BlackboardGrader(self.driver, self.con)

        # add the rest of the conditionals once we code this up for the four platforms
        elif "lms-grad.gcu" in self.driver.current_url:
            is_discussion_post = br.element_exists(self.driver, By.CLASS_NAME, 'lcs_rubricsSubcategorySectionTitle')
            if is_discussion_post:
                self.robot = LoudCloudV1(self.driver, self.con)
            else:
                self.robot = LoudCloudAssignmentGrader(self.driver, self.con)
        else:
            raise Exception("No robots were found for grading this page (is your browser currently on the right URL?)")

    def grade(self):
        self.robot.grade()

class RubricElemGrader(ABC):

    def __init__(self, driver, con):

        self.driver = driver
        self.con = con

    '''
    Should return data structure like this: 
    
    rubric_elems = [
        {
            "title": "Grammar",
            "feedback": WebdriverElement to send response to, 
            "radios": {
                "Exemplary-1": {
                    "btn": WebdriverElement to click,
                    "label": "Exemplary"
                }
                ...
            }
        
        }
        ...
    ]
    '''
    @abstractmethod
    def get_rubric_elems(self):
        raise NotImplementedError("You must create a function to get rubric elems from page")

    '''
    Should return a data structure like this: 
    {
        (title, rank): response
    }
    So that responses can be easily looked up by (title, rank)
    '''
    @abstractmethod
    def get_rubric_responses(self):
        raise NotImplementedError("You must create a function to get rubric elems from page")

    @abstractmethod
    def get_max_scoring_keyword(self):
        raise NotImplementedError("You must create a function to get max scoring keyword")

    @abstractmethod
    def button_already_clicked(self, button):
        raise NotImplementedError("You must create a function to check if button clicked")

    @abstractmethod
    def get_rank_of_selected_label(self, label):
        raise NotImplementedError("You must create a function to retrieve rank of selected identifier")

    '''
    Returns tuple of (elem, response)
    '''
    @abstractmethod
    def get_summative_feedback(self):
        raise NotImplementedError("You must create a function to retrieve the summative feedback as tuple (elem, response)")

    @abstractmethod
    def get_final_submit_btn(self):
        raise NotImplementedError("You must create a function to retrieve the final submit button")

    @abstractmethod
    def send_feedback(self, elem, response):
        elem.clear()
        elem.send_keys(br.replace_newlines(response))

    def build_radio_selector_layout(self, rubric_elems, max_scoring_keyword):
        layout = []
        for i, elem in enumerate(rubric_elems):
            layout.append([sg.Text(elem["title"], key=f"title-{i}")])
            max_points_radio = []
            for identifier, radio in elem["radios"].items():
                label = radio["label"]
                if util.same_string(label, max_scoring_keyword):
                    max_points_radio = [sg.Radio(label, f"RADIO{i}", default=True, key=identifier)]
                    break
            layout.append(max_points_radio + [sg.Radio(radio["label"], f"RADIO{i}", key=identifier) for identifier, radio in elem["radios"].items() if radio["label"] != max_scoring_keyword])
        layout.append([sg.Submit()])
        return layout

    def grade(self):

        # all this stuff implemented in derived classes
        rubric_elems = self.get_rubric_elems()
        rubric_responses = self.get_rubric_responses()
        max_scoring_keyword = self.get_max_scoring_keyword()
        summative_elem, summative_response = self.get_summative_feedback()
        final_submit_btn = self.get_final_submit_btn()
        layout = self.build_radio_selector_layout(rubric_elems, max_scoring_keyword)

        # all this is the same
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
                        # does weird stuff if you try to click already selected radio so make sure not selected
                        btn = elem["radios"][selected_identifier]["btn"]
                        if not self.button_already_clicked(btn):
                            br.safely_click(self.driver, btn)

                        # get rank to retrieve response
                        label = elem["radios"][selected_identifier]["label"]
                        rank = self.get_rank_of_selected_label(label)

                        # pass in the tuple (title, is_max_scoring) to get the response
                        response = rubric_responses[(elem["title"], rank)]

                        # send that response to the textbox
                        self.send_feedback(elem["feedback"], response)

                    # submit summative feedback
                    summative_elem.send_keys(br.replace_newlines(summative_response))

                    # submit button!
                    # FIXME: Remove uncomment for actual production
                    # br.safely_click(self.driver, final_submit_btn)

            except Exception as e:
                ui.error_window(e)

class BlackboardGrader(RubricElemGrader):

    def __init__(self, driver, con):

        self.driver = driver
        self.con = con

        # Determine university from url
        m = re.search('([a-z]*)\.blackboard', self.driver.current_url)
        if not m:
            raise Exception("Could not determine university name")
        self.universitiesid = m.group(1).upper()

        # determine assignment from element with id called "pageTitleText"
        self.assignment_ui_id = self.driver.find_element_by_id('pageTitleText').text.strip()

        # determine course from "crumb_1" element
        course_ui_id = self.driver.find_element_by_id('crumb_1').text.strip()
        self.coursesid = db.queryOneVal(self.con, f"""
                SELECT coursesid FROM courses 
                WHERE ui_identifier = '{course_ui_id}';""")
        if not course_ui_id or not self.coursesid:
            raise Exception("Could not determine course name")

        self.is_discussion_post = "Discussion Forum" in self.assignment_ui_id
        if self.is_discussion_post:
            self.assignmentsid = None
            self.student_name = self.assignment_ui_id.split(": ")[1].split(" ")[0]
        else:
            self.assignmentsid = db.queryOneVal(self.con, f"""
                    SELECT assignmentsid FROM assignments 
                    WHERE ui_identifier = '{self.assignment_ui_id}'
                    AND coursesid = '{self.coursesid}';""")
            if not self.assignmentsid:
                raise Exception(f"Could not determine assignmentsid from coursesid {self.coursesid} and assignment ui identifier {self.assignment_ui_id}")

            elem = self.driver.find_element_by_xpath('//div[@class="students-pager"]//span[contains(text(), "Attempt")]')
            self.student_name = elem.text.split(" ")[0]
        if not self.student_name:
            raise Exception("Student name could not be determined from page")

        # always call base class constructor
        super().__init__(self.driver, self.con)

    # implement all these for the base class
    def get_rubric_elems(self):

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

    def get_rubric_responses(self):
        # if discussion post, just use rubric elements on university
        if self.is_discussion_post:
            rows = db.get_discussion_board_rubric_elements(self.con, self.universitiesid)
        else:
            rows = db.get_all_rubric_elements(self.con, self.universitiesid, self.coursesid, self.assignmentsid)
        return {(row[0], row[1]): row[2] for row in rows if rows}

    def get_max_scoring_keyword(self):
        return 'Excellent' if self.is_discussion_post else 'Exemplary'

    def button_already_clicked(self, btn):
        btn_parent = btn.find_element_by_xpath("./..")
        return "selectedCell" in btn_parent.get_attribute("class")

    def get_rank_of_selected_label(self, label):
        return 1 if label == self.get_max_scoring_keyword() else 2

    def get_summative_feedback(self):
        response = db.get_university_summative_feedback(self.con, self.universitiesid, self.student_name)
        elem = self.driver.find_element_by_xpath('//div[@class="rubricGradingComments"]//textarea')
        return (elem, response)

    def get_final_submit_btn(self):
        return self.driver.find_element_by_xpath("//a[@class='button-3' and text()='Save Rubric']")

    # use default implemented in base class
    def send_feedback(self, elem, response):
        super().send_feedback(elem, response)

class LoudCloudAssignmentGrader(RubricElemGrader):

    def __init__(self, driver, con):

        self.driver = driver
        self.con = con

    def get_rubric_elems(self):

        rubric_elems = []
        grading_element = self.driver.find_elements_by_class_name("lcs_rubricsSubcategorySectionTitle")
        for index, elem in enumerate(grading_element):
            rubric_elem = {}
            rubric_elem["title"] = br.get_text_excluding_children(self.driver, elem.find_element_by_tag_name("h3")).split(" (")[0].strip()
            rubric_elem["feedback"] = elem.find_element_by_class_name("lcs_textarea")
            rubric_elem["radios"] = {}
            grading_cells = elem.find_elements_by_tag_name("li")
            for cell in grading_cells:
                btn = cell.find_element_by_xpath('//input[@type="radio"]')
                label = br.get_text_excluding_children(self.driver, cell.find_element_by_class_name("lcs_rubricsSubcategoryLevelTitle")).strip()
                identifier = f"{label}-{index}"
                rubric_elem["radios"][identifier] = {"btn": btn, "label": label}
            rubric_elems.append(rubric_elem)
        return rubric_elems

    '''
    Should return a data structure like this: 
    {
        (title, rank): response
    }
    So that responses can be easily looked up by (title, rank)
    '''
    def get_rubric_responses(self):

        raise NotImplementedError("You must create a function to get rubric elems from page")

    def get_max_scoring_keyword(self):
        raise NotImplementedError("You must create a function to get max scoring keyword")

    def button_already_clicked(self, button):
        raise NotImplementedError("You must create a function to check if button clicked")

    def get_rank_of_selected_label(self, label):
        raise NotImplementedError("You must create a function to retrieve rank of selected identifier")

    '''
    Returns tuple of (elem, response)
    '''
    def get_summative_feedback(self):
        raise NotImplementedError("You must create a function to retrieve the summative feedback as tuple (elem, response)")

    def get_final_submit_btn(self):
        raise NotImplementedError("You must create a function to retrieve the final submit button")

    # if this is a db, send feedback without clearing field (will condate
    # else, just use the default method in the base class
    def send_feedback(self, elem, response):
        if self.is_discussion_post:
            elem.send_keys(response)
        else:
            super().send_feedback(elem, response)


'''
    Grades assignments that have a single box for feedback and a single grade to submit
'''
class SingleBoxGrader(ABC):

    def __init__(self, driver, con):

        self.driver = driver
        self.con = con

    @abstractmethod
    def get_feedback_elem(self):
        raise NotImplementedError("You must create a function to get feedback box from page")

    @abstractmethod
    def get_score_elem(self):
        raise NotImplementedError("You must create a function to get score elem from page")

    @abstractmethod
    def get_submit_btn(self):
        raise NotImplementedError("You must create a function to get the submit button")

    @abstractmethod
    def get_layout(self):
        raise NotImplementedError("You must create a function to create the layout for the ui")

    @abstractmethod
    def get_response_and_score(self, value):
        raise NotImplementedError("You must create a function to return (response, score) from the values")

    def grade(self):

        feedback_elem = self.get_feedback_elem()
        score_elem = self.get_score_elem()
        submit_btn = self.get_submit_btn()
        layout = self.get_layout()

        window = sg.Window("Select grades", layout)
        while True:
            try:
                event, values = window.read()
                if event in (None, 'Cancel'):   # if user closes window or clicks cancel
                    break

                if event == 'Submit':
                    response, score = self.get_response_and_score(values)
                    feedback_elem.clear()
                    feedback_elem.send_keys(br.replace_newlines(response))
                    score_elem.clear()
                    score_elem.send_keys(score)
                    # br.safely_click(submit_btn)
            except Exception as e:
                ui.error_window(e)

class SingleBoxV1(SingleBoxGrader):

    def __init__(self, driver, con, universitiesid):

        self.driver = driver
        self.con = con
        self.universitiesid = universitiesid

        # get rubric elems from database
        self.rubric_elems = db.query_grouped_by_dict(
            self.con,
            table="universities_rubric_elements",
            grouped_by="title",
            columns=["rank", "rank_name", "rank_modifier", "percent_total", "response", "visible_category", "visible_order"],
            where=f"WHERE universitiesid = '{self.universitiesid}'",
            order_by="ORDER BY visible_order, title, rank")

        # FIXME: get student name from page
        self.student_name = self.driver.find_element_by_xpath('//div[contains(@class, "selectedstudentSelectGroup")]//span').text.split(" ")[0]

        # FIXME: get total possible points for this assignments
        self.total_points = int(self.driver.find_element_by_xpath('//span[contains(@class, "lcs_totalScorelabel")]').text.split(" ")[1])

        super().__init__(self.driver, self.con)

    def get_layout(self):
        layout = []
        for title, rows in self.rubric_elems.items():
            layout.append([sg.Text(title)])
            top, *others = rows
            radios = [sg.Radio(top["rank_name"], group_id=f"{title}", key=f"{top['rank']}-{title}", default=True)]
            radios += [sg.Radio(cols["rank_name"], group_id=f"{title}", key=f"{cols['rank']}-{title}") for cols in others]
            layout.append(radios)
        layout.append([sg.Submit()])
        return layout

    def get_response_and_score(self, values):

        responses = []
        total_score = 0
        visible_categories = OrderedDict()

        # loop over each rubric element to calculate score and response for each visible category
        for title, rows in self.rubric_elems.items():

            # get chosen key for this title from values
            selected_rank = [key for key, val in values.items() if title in key and val][0].split('-')[0]

            # use selected rank and title to lookup record
            record = [row for row in rows if row['rank'] == int(selected_rank)][0]

            # calculate scores
            total_possible_score = record["percent_total"] * self.total_points
            actual_score = total_possible_score * record["rank_modifier"]
            visible_category = record["visible_category"]
            response = record["response"]

            # set key in visible_categories and append response and score data
            visible_categories.setdefault(visible_category, {"total_possible_score": 0, "actual_score": 0, "responses": []})

            # add scores and response to visible_categories dictionary
            visible_categories[visible_category]["total_possible_score"] += total_possible_score
            visible_categories[visible_category]["actual_score"] += actual_score
            visible_categories[visible_category]["responses"].append(response)

        # build up responses list
        responses.append(f"Hi {self.student_name},")
        responses.append(f"Your response is graded on the following metrics: " + ", ".join(visible_categories.keys()))

        # add responses and scores from visible categories
        for category, values in visible_categories.items():
            actual_score = values["actual_score"]
            total_possible_score = values["total_possible_score"]

            # first add subscore to total
            total_score += actual_score

            # then append a response for the whole category
            responses.append(f"For rubric element {category} you earned {str(int(actual_score))} out of a total possible {str(int(total_possible_score))}")

            # then append responses for each subcategory
            for resp in values["responses"]:
                responses.append(resp)

        # add closing remarks
        responses.append("I am invested in you and your success. Let me know if you have any questions.")
        responses.append("Dr. Sturtz")

        response_string = "\n\n".join(responses)
        score_string = str(int(total_score))
        return response_string, score_string

class LoudCloudV1(SingleBoxV1):

    def __init__(self, driver, con):
        self.driver = driver
        self.con = con

        # Determine university from url
        m = re.search('([a-z]*)\.edu', self.driver.current_url)
        if not m:
            raise Exception("Could not determine university name")
        self.universitiesid =  m.group(1).upper()

        # pass to base SingleBoxV1 class
        super().__init__(self.driver, self.con, self.universitiesid)

    # these are specific to Loud Cloud
    def get_feedback_elem(self):
        return self.driver.find_element_by_class_name("lcs_textarea")

    def get_score_elem(self):
        return self.driver.find_element_by_xpath("//input[contains(@class, 'lcs_scoreInput')]")

    def get_submit_btn(self):
        return self.driver.find_element_by_xpath("//button[contains(@class, 'pub')]")

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
                layout.append([sg.Text(uni)] + [sg.Button(link['pretty_name'], key=link['url']) for link in links])
        if course_links:
            layout.append([sg.Text('Courses')])
            for course, links in course_links.items():
                layout.append([sg.Text(course)] + [sg.Button(link['pretty_name'], key=link['url']) for link in links])
        if assign_links:
            layout.append([sg.Text('Universities')])
            for assignment, links in uni_links.items():
                layout.append([sg.Text(assignment)] + [sg.Button(link['pretty_name'], key=link['url']) for link in links])
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
