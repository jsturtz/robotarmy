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
import functools

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

        elif 'snhu' in self.driver.current_url:
            self.config = util.get_config()['snhu']
            self.user_elem = self.driver.find_element_by_id('input_1')
            self.pass_elem = self.driver.find_element_by_id('input_2')
            self.submit_btn = self.driver.find_element_by_id('SubmitCreds')
            
        elif 'coloradotech' in self.driver.current_url:
            self.config = util.get_config()['ctu']
            self.user_elem = self.driver.find_element_by_xpath('//input[@type="text"]')
            self.pass_elem = self.driver.find_element_by_xpath('//input[@type="password"]')
            self.submit_btn = self.driver.find_element_by_xpath('//button[contains(text(), "Log In")]')

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
                
        elif "coloradotech" in self.driver.current_url:
            self.robot = ColoradoTechGrader(self.driver, self.con)
        else:
            raise Exception("No robots were found for grading this page (is your browser currently on the right URL?)")

    def grade(self):
        self.robot.grade()
'''
Base class that represents a browser screen with multiple rubric elements, multiple individual feedback boxes, 
and a summative feedback box. 
'''
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
        br.send_keys(self.driver, elem, br.replace_newlines(response))

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
                    br.send_keys(self.driver, summative_elem, br.replace_newlines(summative_response))

                    # submit button!
                    # FIXME: Remove uncomment for actual production
                    # br.safely_click(self.driver, final_submit_btn)

            except Exception as e:
                ui.error_window(e)

'''
Concrete class that implements RubricElemGrader
Will only work on blackboard sites. Grades both discussion posts and assignments
'''
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

'''
FIXME: Broken ass shit
Implements RubricElemGrader. Works on Loud Cloud assignments with rubric elements
'''
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
            br.send_keys(self.driver, elem, response)
        else:
            super().send_feedback(elem, response)


'''
Base class that will grade assignments that have a single box for feedback and a single score to  submit
'''
class SingleBoxGrader(ABC):

    def __init__(self, driver, con):

        self.driver = driver
        self.con = con

    @abstractmethod
    def send_feedback(self):
        raise NotImplementedError("You must create a function to send feedback to the page")

    @abstractmethod
    def send_score(self):
        raise NotImplementedError("You must create a function to send score to the page")

    @abstractmethod
    def get_layout(self):
        raise NotImplementedError("You must create a function to create the layout for the ui")

    @abstractmethod
    def get_response_and_score(self, value):
        raise NotImplementedError("You must create a function to return (response, score) from the values")

    def grade(self):

        layout = self.get_layout()
        window = sg.Window("Select grades", layout)
        while True:
            try:
                event, values = window.read()
                if event in (None, 'Cancel'):   # if user closes window or clicks cancel
                    break

                if event == 'Submit':
                    response, score = self.get_response_and_score(values)
                    self.send_feedback(response)
                    self.send_score(score)
            except Exception as e:
                ui.error_window(e)

'''
Base class that implements SingleBoxGrader
Use this whenever you have behind-the-scenes rubrics that map to visible rubric elements and when
you want to send its particular formatted content in the feedback box.
'''
class SingleBoxV1(SingleBoxGrader):

    def __init__(self, driver, con):

        self.driver = driver
        self.con = con
        self.student_name = self.get_student_name()
        self.total_points = self.get_total_points()
        self.universitiesid = self.get_universitiesid()
        self.rubric_elems = self.get_rubric_elems()

        # this base class depends on having the right data in universities_rubric_elements

        super().__init__(self.driver, self.con)

    def get_rubric_elems(self):
        return db.query_grouped_by_dict(
            self.con,
            table="universities_rubric_elements",
            grouped_by="title",
            columns=["rank", "rank_name", "rank_modifier", "percent_total", "response", "title_order", "title", "is_radio"],
            where=f"WHERE universitiesid = '{self.universitiesid}'",
            order_by="ORDER BY title_order, rank")

    def get_student_name(self):
        raise NotImplementedError("You must provide a function to get student name")
    
    def get_total_points(self):
        raise NotImplementedError("You must provide a function to get total points for assignment")
    
    def get_universitiesid(self):
        raise NotImplementedError("You must provide a function to get universitiesid")
    
    # layout fully dependent on self.rubric_elems. Builds a basic radio UI layout
    def get_layout(self):
        layout = []
        for title, rows in self.rubric_elems.items():
            layout.append([sg.Text(title)])
            if rows[0]["is_radio"]:
                top, *others = rows
                radios = [sg.Radio(top["rank_name"], group_id=f"{title}", key=f"{top['rank']}-{title}", default=True)]
                radios += [sg.Radio(cols["rank_name"], group_id=f"{title}", key=f"{cols['rank']}-{title}") for cols in others]
                layout.append(radios)
            else:
                for row in rows:
                    # ignore rank modifier 0 because that indicates full points
                    if row["rank_modifier"] > 0:
                        layout.append([sg.Checkbox(row["rank_name"], default=False, key=f"{row['rank']}-{title}")])
        layout.append([sg.Submit()])
        return layout

    # the "values" is the output from the UI
    def get_response_and_score(self, values):

        # builds up total possible score, actual score, and responses to be used below when building up responses and final score
        rubric_results = OrderedDict()

        # loop over each rubric element to calculate score and response for each category
        for title, rows in self.rubric_elems.items():
            
            # check if radio or checkbox
            if rows[0]["is_radio"]:
                
                # get chosen radio for this title from values
                selected_rank = [key for key, val in values.items() if title in key and val][0].split('-')[0]

                # use selected rank and title to lookup record
                record = [row for row in rows if row['rank'] == int(selected_rank)][0]

                # add scores and response to rubric_results dictionary
                rubric_results[title] = {}
                total_possible_score = record["percent_total"] * self.total_points
                rubric_results[title]["total_possible_score"] = total_possible_score
                rubric_results[title]["actual_score"] = total_possible_score * record["rank_modifier"]
                rubric_results[title]["responses"] = [record["response"]]   # keep as list for consistency below
                
            else: 
                # calculate total score first and set actual to total possible if key not already in rubric results
                total_possible_score = rows[0]["percent_total"] * self.total_points
                rubric_results.setdefault(title, {"total_possible_score": total_possible_score, "actual_score": total_possible_score, "responses": []})

                # get all checked boxes (checked boxes represent points to be subtracted from total)
                selected_ranks = [key.split('-')[0] for key, val in values.items() if title in key and val]

                # in no checkboxes selected, only add a response indicating full points
                if not selected_ranks:
                    # get full points response
                    full_points_response = [row["response"] for row in rows if int(row["rank_modifier"]) == 0][0]
                    rubric_results[title]["responses"].append(full_points_response)

                # iterate over ranks
                for rank in selected_ranks:

                    # use selected rank to lookup record
                    record = [row for row in rows if row['rank'] == int(rank)][0]

                    # then compute the score given the reduction and re-assign actual score
                    lost_points = total_possible_score * record["rank_modifier"]
                    response = record["response"]

                    # subtract lost points from actual score and add response for this checkbox item
                    rubric_results[title]["actual_score"] -= lost_points
                    rubric_results[title]["responses"].append(response)

        # calculate total score
        scores = [val["actual_score"] for key, val in rubric_results.items()]
        total_score = str(int(functools.reduce(lambda a,b : a+b, scores)))

        # build up responses list
        responses = []
        responses.append(f"{self.student_name},")
        responses.append("Thank you for your work with this learning activity. Below, I will outline your earned points for this learning activity. \
            I will also provide feedback specific to each rubric element. Please check it out! Remember, I am invested in you and your success. \
            Please reach out if you need anything")
        responses.append(f"The total points you earned for this learning activity: {total_score}")

        # add responses and scores from visible categories
        for category, values in rubric_results.items():
            
            actual_score = str(values["actual_score"]).strip('0').strip('.')
            total_possible_score = str(values["total_possible_score"]).strip('0').strip('.')

            # then append a response for the whole category
            responses.append(f'Points earned under the category "{category}": {actual_score} out of a total {total_possible_score}')
            responses.append(f'Here is the feedback for {category}:')

            # then append responses for each subcategory
            for resp in values["responses"]:
                responses.append(resp)

        # add closing remarks
        responses.append("I am invested in you and your success. Let me know if you have any questions.")
        responses.append("Dr. Sturtz")
        total_response = "\n\n".join(responses)
        
        return total_response, total_score

'''
Concrete class that implements SingleBoxV1
Works to grade any Loud Cloud course (i.e. courses at GCU)
'''
class ColoradoTechGrader(SingleBoxV1):

    def __init__(self, driver, con):
        self.driver = driver
        self.con = con

        # use this to switch to window FIXME: Make this into a function?
        found_window = False
        for handle in driver.window_handles[-1:]:
            driver.switch_to_window(handle)
            if "coloradotech.edu" in driver.current_url and "gradebook" in driver.current_url:
                found_window = True
                break
        if not found_window:
            raise Exception("Cannot find window to grade")

        # decide whether screen is for discussion post or assignment
        self.is_db = "Discussion Board" in self.driver.find_element_by_xpath('//label[contains(text(), "Type:")]/..').get_attribute("innerHTML")

        # pass to base SingleBoxV1 class
        super().__init__(self.driver, self.con)

    # these are specific to Colorado Tech
    def get_rubric_elems(self):
        return db.query_grouped_by_dict(
            self.con,
            table="universities_rubric_elements",
            grouped_by="title",
            columns=["rank", "rank_name", "rank_modifier", "percent_total", "response", "title_order", "title", "is_radio"],
            where=f"WHERE universitiesid = '{self.universitiesid}' AND is_db = {self.is_db}",
            order_by="ORDER BY title_order, rank")

    def get_universitiesid(self):
        return 'CTU'
    
    def get_student_name(self):
        return self.driver.find_element_by_xpath('//h3[contains(text(), "Comment for")]').text.split(", ")[1]

    def get_total_points(self):
        # doing insane shit here, so decided on a hacky regex workaround to get the text
        elem = self.driver.find_element_by_xpath('//label[contains(text(), "Points Possible")]/..')
        m = re.search('</label>([0-9]*)', elem.get_attribute('innerHTML'))
        return int(m.group(1))

    def send_feedback(self, feedback):
        # iframes are nasty, so switch to iframe, then send, then switch back to main window
        # Because the sent values are wrapped in html we cannot change, you must manually delete existing content
        current_handle = self.driver.current_window_handle
        iframe = self.driver.find_element_by_xpath('//iframe[contains(@id, "ui-tinymce")]')
        self.driver.switch_to.frame(iframe)
        feedback_elem = self.driver.find_element_by_id("tinymce")
        br.send_keys(self.driver, feedback_elem, feedback)
        self.driver.switch_to_window(current_handle)

    def send_score(self, score):
        score_elem = self.driver.find_element_by_xpath('//form[@name="editGradeCommentForm"]//input[@name="grade"]')
        score_elem.clear()
        br.send_keys(self.driver, score_elem, score)

'''
Class that will generate UI to display links in universities_links, courses_links, and assignment_links
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
'''
