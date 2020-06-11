/*
HOWTO:

Most tables will have a "code" field. This is the field you should be using internally to this file to match
records. For example, suppose you insert a record into universities with a code of "post". You will not necessarily
know the universitiesid of this new record unless you return it directly after the insertion. To make this easier
to code and extend, the "code" field can be used effectively as unique "lookup" for many tables. If you need to
insert the universitiesid later in the file, you can just write
"(SELECT universitiesid FROM universities WHERE code = 'post')".

Only the universities table so far as a UNIQUE constraint on the code field. Others have a UNIQUE contraint on
the code field together with its foreign key reference. So, for example, the courses table requires that each
(universitiesid, code) pair must be unique. So you will want to probably look up the coursesid by
searching by universitiesid and code.

*/


-- drop all the tables first and then recreate them
DROP TABLE IF EXISTS assignments_rubric_elements;
DROP TABLE IF EXISTS universities_rubric_elements;
DROP TABLE IF EXISTS rubric_elements;
DROP TABLE IF EXISTS generic_rubric_elements;
DROP TABLE IF EXISTS assignments_generic_rubric_elements;
DROP TABLE IF EXISTS assignments_quicklinks;;
DROP TABLE IF EXISTS courses_quicklinks;
DROP TABLE IF EXISTS universities_quicklinks;
DROP TABLE IF EXISTS assignments;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS universities;

CREATE TABLE universities (
    universitiesid TEXT,
	pretty_name TEXT,
    summative_feedback TEXT,
    PRIMARY KEY (universitiesid)
);

-- the ui_identifier field should match the string used to identify the course in the browser
-- for blackboard courses, that's the string that looks like this: MKT200_37_Principles of Marketing_2019_20_TERM6
CREATE TABLE courses (
    coursesid TEXT,
    pretty_name TEXT,
    ui_identifier TEXT,
    universitiesid TEXT,
    PRIMARY KEY (coursesid, universitiesid),
    FOREIGN KEY (universitiesid) REFERENCES universities(universitiesid)
);

CREATE TABLE assignments (
    assignmentsid TEXT,
    pretty_name TEXT,
    ui_identifier TEXT UNIQUE,
    summative_feedback TEXT,
    coursesid TEXT NOT NULL,
    universitiesid TEXT NOT NULL,
    max_scoring_keyword TEXT NOT NULL,
    PRIMARY KEY (assignmentsid, coursesid),
    FOREIGN KEY (coursesid, universitiesid) REFERENCES courses(coursesid, universitiesid)
);

-- holds specific rubric elements for assignments
CREATE TABLE rubric_elements (
    rubric_elementsid SERIAL,
    title TEXT,
    response TEXT,
    is_max_scoring BOOLEAN,
    max_scoring_keyword TEXT,
    PRIMARY KEY (rubric_elementsid)
);

/*
generic_rubric_elements works differently than rubric_elements.
Here, the (title, is_max_scoring) will be the primary key, so don't try to insert multiple instances
of the same title. The idea is that if you need to use these with variable contents, then you should wrap any
variables in curly braces. Then, crucially, for any assignment that uses these generic rubric elements,
you must insert a new record into assignment_generic_rubric_variables to hold the variables for each assignment.
So for instance, since "Resources" requires a {number} of pages, then you must insert a record into
assignment_generic_rubric_variables with json that says '{number=2}'. If a particular generic rubric element
does not have variable interpolation, then you must still insert a new record but with the variable field
set to an empty json object.
*/
CREATE TABLE generic_rubric_elements (
    title TEXT,
    response TEXT,
    is_max_scoring BOOLEAN,
    max_scoring_keyword TEXT,
    PRIMARY KEY (title, is_max_scoring)
);

CREATE TABLE assignments_generic_rubric_elements (
    assignment_generic_rubric_elementsid SERIAL,
    title TEXT NOT NULL,
    is_max_scoring BOOLEAN NOT NULL,
    variables JSONB NOT NULL,
    assignmentsid TEXT NOT NULL,
    coursesid TEXT NOT NULL,
    PRIMARY KEY (assignment_generic_rubric_elementsid),
    FOREIGN KEY (assignmentsid, coursesid) REFERENCES assignments(assignmentsid, coursesid)
);

CREATE TABLE assignments_rubric_elements (
    assignments_rubric_elementsid SERIAL PRIMARY KEY,
    rubric_elementsid INTEGER NOT NULL,
    assignmentsid TEXT NOT NULL,
    coursesid TEXT NOT NULL,
    FOREIGN KEY (rubric_elementsid) REFERENCES rubric_elements(rubric_elementsid),
    FOREIGN KEY (assignmentsid, coursesid) REFERENCES assignments(assignmentsid, coursesid)
);

-- the only use case for this relation is the discussion posts which for Post are university-wide
CREATE TABLE universities_rubric_elements (
    universities_rubric_elementsid SERIAL PRIMARY KEY,
    universitiesid TEXT NOT NULL,
    rubric_elementsid INTEGER NOT NULL,
    FOREIGN KEY (universitiesid) REFERENCES universities(universitiesid),
    FOREIGN KEY (rubric_elementsid) REFERENCES rubric_elements(rubric_elementsid)
);

-- used to associate urls with respective entities
CREATE TABLE universities_quicklinks (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    pretty_name TEXT NOT NULL,
    universitiesid TEXT REFERENCES universities(universitiesid)
);

CREATE TABLE courses_quicklinks (
    quicklinks_coursesid SERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    pretty_name TEXT NOT NULL,
    coursesid TEXT NOT NULL,
    universitiesid TEXT NOT NULL,
    FOREIGN KEY (coursesid, universitiesid) REFERENCES courses(coursesid, universitiesid)
);

CREATE TABLE assignments_quicklinks (
    quicklinks_assignmentsid SERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    pretty_name TEXT NOT NULL,
    assignmentsid TEXT NOT NULL,
    coursesid TEXT NOT NULL,
    FOREIGN KEY (assignmentsid, coursesid) REFERENCES assignments(assignmentsid, coursesid)
);

-- Make the id uppper case. Right now I'm looking up the universitiesid by looking at the URL
INSERT INTO universities (universitiesid, pretty_name, summative_feedback)
VALUES
('POST', 'Post University', '{name}\n\nThank you for your work with this learning activity. Please review my remarks in the rubric for more information about your grade.  Remember, I am invested in you and in your success.  Please be sure to reach out to me if you need help.  :)\n\nDr. Sturtz');

INSERT INTO universities_quicklinks (universitiesid, pretty_name, url)
VALUES
('POST', 'Home', 'https://post.blackboard.com/webapps/portal/execute/tabs/tabAction?tab_tab_group_id=_646_1');

INSERT INTO courses (coursesid, universitiesid, pretty_name, ui_identifier)
VALUES
('MKT200', 'POST', 'Principles of Marketing', 'MKT200_37_Principles of Marketing_2019_20_TERM6'),
('BUS311', 'POST', 'Managerial Communications', 'BUS311_31_Managerial Communications_2019_20_TERM6');

INSERT INTO courses_quicklinks (pretty_name, coursesid, universitiesid, url)
VALUES
('Announcements', 'MKT200', 'POST', 'https://post.blackboard.com/webapps/blackboard/execute/announcement?method=search&context=course&course_id=_94915_1&handle=cp_announcements&mode=cpview'),
('Grading Center', 'MKT200', 'POST', 'https://post.blackboard.com/webapps/gradebook/do/instructor/enterGradeCenter?course_id=_94915_1&cvid=fullGC'),
('Announcements', 'BUS311', 'POST', 'https://post.blackboard.com/webapps/blackboard/execute/announcement?method=search&context=course&course_id=_94961_1&handle=cp_announcements&mode=cpview'),
('Grading Center', 'BUS311', 'POST', 'https://post.blackboard.com/webapps/gradebook/do/instructor/enterGradeCenter?course_id=_94961_1&cvid=fullGC');

INSERT INTO assignments (assignmentsid, coursesid, universitiesid, max_scoring_keyword, ui_identifier, summative_feedback)
VALUES
-- MKT200
('A1', 'MKT200', 'POST', 'Exemplary', 'Grade Assignment: Unit 1 Assignment: Social Media', '{name}\n\nThank you for your work with this learning activity. Please review my remarks in the rubric for more information about your grade.  Here, we are looking at the efficacy of social media within the context of one specific company. As we entered away the course, it is important to begin to think like a marketer. Within this context, social media is less about keeping up with friends and family or the news or even sharing funny things from your day-to-day, but more about how companies engage customers. Putting a marketing mindset on will help you throughout the course. :-) Here is a great article on the subject: https://hbr.org/2019/08/to-win-support-for-your-idea-think-like-a-marketer\n\nAs we go, please know that I am invested in you and in your success. This is an something that I say and then throw away. Rather, it is something that I sincerely mean. Be sure to reach out to me if there is anything that I can do to help you succeed throughout the course.\n\nDr. Sturtz'),
('A3', 'MKT200', 'POST', 'Exemplary', 'Grade Assignment: Unit 3 Assignment: Service Organizations', '{name}\n\nThank you for your work with this learning activity. I purchased the first iPhone in 2007 the day after they were released. I paid $600 for this and, a few weeks later, Apple dropped the price by $200. Did Apple take advantage of me? Not really. I was, and still am, an early adopter. In some cases, early adopters pay a price premium for being an early adopter. This is part of the product/service life cycle management that we addressed as part of this week’s assignment. Please review my remarks in the rubric for more information about your grade.  Remember, I am invested in you and in your success.  Please be sure to reach out to me if you need help.  :)\n\nDr. Sturtz'),
('A4', 'MKT200', 'POST', 'Exemplary', 'Grade Assignment: Unit 4 Assignment: Pricing', '{name}\n\nThank you for your work with this learning activity. If you are like most people in this course, you been part of the consumer class for a long time. In this space, you want the most product for the least money. For instance, if you found a top-of-the-line smart phone for one dollar you’d be delighted. You might even tell all your friends and family about this great deal and let them know to rush over to also purchase the top-of-the-line smart phone for one dollar. If you are entrepreneurial, you may even purchase some extra smart phones to resell.\n\nBut! Hang on! If companies actually sell smart phones for one dollar, they will be bankrupt quickly. Then they’ll be no smart phones at any price. This project helped us look into this as marketers.Please review my remarks in the rubric for more information about your grade.  Remember, I am invested in you and in your success.  Please be sure to reach out to me if you need help.  :)\n\nDr. Sturtz'),
('A6', 'MKT200', 'POST', 'Exemplary', 'Grade Assignment: Unit 6 Assignment: Integrated Marketing Presentation', '{name}\n\nThank you for your work with this project. Here, things are a bit different in that the deliverable is a PowerPoint presentation and not a word document. One of the keys with PowerPoint presentations is that we have to communicate our marketing plans in clear and convincing ways. It’s not enough to simply build a strong plan, but we have to tell others what we intend to do so that we can marshal organizational resources in the direction of our plan. I’ve never been in any of your presentations, but I always want to be useful to you. Here is an article that I think will help anybody: https://www.inc.com/jeff-haden/16-ways-to-dramatically-improve-your-presentation-skills-from-16-powerful-ted-ta.html'),
('A7', 'MKT200', 'POST', 'Exemplary', 'Grade Assignment: Unit 7 Assignment: Internet Security and Privacy', '{name}\n\nThank you for your work with this project. One of the really cool things about this project is that we have some hands-on work with the kind of project that relatively common in marketing. Here, we are promoting an internal event. One of the keys with building flyers is that we should do these in a way that captures the attention of passersby. Without this, attendance at the event would be much lower. Also, we can design the flyer in a way that allows this to go out electronically as well. Here is a tool that my team uses all the time: https://spark.adobe.com/templates/flyers/'),
-- BUS311
('A1', 'BUS311', 'POST', 'Exemplary', 'Grade Assignment: Unit 1 Assignment: Email Scenario Response', '{name}\n\nThank you for your work with this learning activity. Professionalism in emails is such a big deal. For instance, even though most students send proper emails to instructors, I''ve had emails that come in something like this:\n\n"where can i find the sylabis u sent link but i couldt find no document"\n\nWhile this is an extreme example, I promise you that I have seen emails this bad. Given the level of frequent email communication in professional contexts, sending professional emails as kind of a ""default"" mode is always a good idea.\n\nTo learn more about professional emails, check out this link: https://www.indeed.com/career-advice/career-development/how-to-write-a-professional-emailPlease review my remarks in the rubric for more information about your grade.  Remember, I am invested in you and in your success.  Please be sure to reach out to me if you need help.  :)\n\nDr. Sturtz'),
('A2', 'BUS311', 'POST', 'Exemplary', 'Grade Assignment: Unit 2 Assignment: Creating an Effective Presentation', '{name}\n\n"Thank you for your work with this project. Communication using a variety of techniques is an absolutely critical skill. For instance, many people in professional positions communicate quite frequently using PowerPoint. Where I work, I often use PowerPoint to gain organizational buy-in to drive change within the company.  Here is a helpful resource on effective PowerPoint presentations: https://www.businessinsider.com/8-tips-for-great-powerpoint-presentations-2015-1\n\nPlease check out the rubric to learn more about your grade. Remember, I am invested in you and in your success. Please be sure to reach out to me if you need any help at all. :-)\n\nDr. Sturtz'),
('A3', 'BUS311', 'POST', 'Exemplary', 'Grade Assignment: Unit 3 Assignment: Top 5 Business Writing Tips', '{name}\n\nThank you for your work with this learning activity! Blogs are  about creating useful and meaningful content in a couple of different subject areas. Given the explosion of communication channels, understanding how to create blog content is important because we can feed parts of this content in various communication channels.  Here is one reason why this really matters: Walmart is engaged with 53 social media profiles! Check out the link to learn more: https://unmetric.com/brands/walmartes\n\nPlease check out the rubric to learn more about your grade. Remember, I am invested in you and in your success. Please be sure to reach out to me if you need any help at all. :-)\n\nDr. Sturtz'),
('A4', 'BUS311', 'POST', 'Exemplary', 'Grade Assignment: Unit 4 Assignment: Writing Routine and Positive Messages', '{name}\n\nThank you for your work with this learning activity. Professionalism in emails is such a big deal. For instance, even though most students send proper emails to instructors, I''ve had emails that come in something like this:\n\n"where can i find the sylabis u sent link but i couldt find no document"\n\nWhile this is an extreme example, I promise you that I have seen emails this bad. Given the level of frequent email communication in professional contexts, sending professional emails as kind of a ""default"" mode is always a good idea.\n\nTo learn more about professional emails, check out this link: https://www.indeed.com/career-advice/career-development/how-to-write-a-professional-emailPlease review my remarks in the rubric for more information about your grade.  Remember, I am invested in you and in your success.  Please be sure to reach out to me if you need help.  :)\n\nDr. Sturtz'),
('A5', 'BUS311', 'POST', 'Exemplary', 'Grade Assignment: Unit 5 Assignment: Persuasive and Negative Messages', '{name}\n\n"Thank you for your work with this assignment. Here, we are practicing writing a memo. These are structured ways to communicate specific and concrete information. Memos can be so much better than something like email narrative or a verbal exchange. This is especially true because a memo can help us go back to understand the information we shared if there’s ever a question about it. Here is a helpful memo writing resource: https://owl.purdue.edu/owl/subject_specific_writing/professional_technical_writing/memos/sample_memo.html\n\nTo learn more about professional emails, check out this link: https://www.indeed.com/career-advice/career-development/how-to-write-a-professional-emailPlease review my remarks in the rubric for more information about your grade.  Remember, I am invested in you and in your success.  Please be sure to reach out to me if you need help.  :)\n\nDr. Sturtz'),
('A6', 'BUS311', 'POST', 'Exemplary', 'Grade Assignment: Unit 6 Assignment: Listening and Non-Verbal Skills Presentation', '{name}\n\n"Thank you for your work with this project. Communication using a variety of techniques is an absolutely critical skill. For instance, many people in professional positions communicate quite frequently using PowerPoint. Where I work, I often use PowerPoint to gain organizational buy-in to drive change within the company.  Here is a helpful resource on effective PowerPoint presentations: https://www.businessinsider.com/8-tips-for-great-powerpoint-presentations-2015-1\n\nPlease check out the rubric to learn more about your grade. Remember, I am invested in you and in your success. Please be sure to reach out to me if you need any help at all. :-)\n\nDr. Sturtz'),
('A7', 'BUS311', 'POST', 'Exemplary', 'Grade Assignment: Unit 7 Assignment: Doing Business In...', '{name}\n\n"Thank you for your work with this assignment. Here, we are practicing writing a memo. These are structured ways to communicate specific and concrete information. Memos can be so much better than something like email narrative or a verbal exchange. This is especially true because a memo can help us go back to understand the information we shared if there’s ever a question about it. Here is a helpful memo writing resource: https://owl.purdue.edu/owl/subject_specific_writing/professional_technical_writing/memos/sample_memo.html\n\nTo learn more about professional emails, check out this link: https://www.indeed.com/career-advice/career-development/how-to-write-a-professional-emailPlease review my remarks in the rubric for more information about your grade.  Remember, I am invested in you and in your success.  Please be sure to reach out to me if you need help.  :)\n\nDr. Sturtz');

---------------------------------------------------------------------------------------------------
-- RUBRIC ELEMENTS
-- GENERIC DISCUSSION POSTS
INSERT INTO generic_rubric_elements (title, is_max_scoring, max_scoring_keyword, response)
VALUES
('Resources', TRUE, 'Exemplary', 'You had at least {number} references in your work.  Good.'),
('Resources', FALSE, 'Exemplary', 'You did not have more than {number} references in the text and in your reference list.'),
('Paper Length', TRUE, 'Exemplary', 'Your work was  more than {number} properly APA formatted pages.'),
('Paper Length', FALSE, 'Exemplary', 'Your work was not more than {number} properly APA formatted pages.  Also, only that which you actually write counts toward page count.  This means that both front matter and back matter (title, abstract, reference pages and so on) do not count toward page count. '),
('Clear and Professional Writing and APA Format', TRUE, 'Exemplary', 'You have excellent work in this rubric element.'),
('Clear and Professional Writing and APA Format', FALSE, 'Exemplary', 'To have earned the most points in this rubric element your work should have been  clear, professional, and consistent with APA.\n\nIt is okay to need work in this area, but it will be necessary to develop yourself in this area. Here is a resource: https://post.blackboard.com/webapps/portal/execute/tabs/tabAction?tab_tab_group_id=_649_');

-- RUBRIC ELEMENTS FOR DISCUSSION POST
WITH ids as (
    INSERT INTO rubric_elements (title, is_max_scoring, max_scoring_keyword, response)
    VALUES
    ('Professional Communication', TRUE, 'Excellent', 'This rubric element evaluates your grammar and syntax as well as the way in which you supported your ideas with high quality sources. You crushed this rubric element! In school, we practice professional communications so that you are able to easily exhibit professional communications out there in your professional career. You did an awesome job in this rubric element! Thank you.'),
    ('Professional Communication', FALSE, 'Excellent', 'This rubric element considers two important writing topics. First, there''s the topic of grammar, spelling, and APA format. The second topic is how well you are supporting your work from outside sources. Each of these topics combine into professional communication. In the college context, it''s important to have error-free writing as well as to have writing that supports your examples with evidence from high-quality citations.  The citations need to be in a reference list AND in the text.\n\nTo earn the maximum possible rating in the future, please be sure to have error free writing and then also to have writing that has citations to support your ideas.\n\nThe school has some excellent resources for grammar and other helpful topics: https://post.blackboard.com/webapps/portal/execute/tabs/tabAction?tab_tab_group_id=_649_1\n\nWe even have free 24/7 tutoring!\n\nYou might find this site helpful to learn more about grammar and citations: https://owl.english.purdue.edu/owl/section/1/5/'),
    ('Response to Questions', TRUE, 'Excellent', 'Fantastic! This rubric element evaluates the quality of your response to the initial question. This topic is really about how well you answered the initial question. This might include things like the completeness of your response and the overall quality of the response. Work like this shows that you are serious about your education and you are investing in your future. Keep going!'),
    ('Response to Questions', FALSE, 'Excellent', 'This particular discussion board rubric element measures how thoroughly you responded to the discussion questions.\n\nOne of important things about our discussion questions is to carefully read the discussion question and then answer the entire question and do so at a relatively substantial level. By doing this, you are maximizing your opportunity to earn points and, perhaps more importantly, you are ensuring that you are thoroughly learning the course material. :-)'),
    ('Evidence of Critical Thinking', TRUE, 'Excellent', 'You did a wonderful job in this rubric element. Critical thinking involves your own analysis and understanding. This is closely related to comprehension. Remember, comprehension involves the application of course content. Critical thinking, on the other hand, is when you bring comprehension to the next level by applying your own understanding and analysis of the topic. Super!'),
    ('Evidence of Critical Thinking', FALSE, 'Excellent', 'High-quality academic writing involves, among others, two important elements: comprehension and critical thinking. Comprehension is the application of course concepts. In all courses but capstone courses, this means that people apply the information in the various learning materials for the course directly in the written work.\n\nCritical thinking involves the synthesis of the various concepts in the discipline with your own analysis and understanding of the concepts. Essentially, this is your own thoughts, ideas, and perspectives on what you know about the discipline as related to the various learning activities.\n\nCombined, critical thinking and comprehension show that you are learning the course materials sufficiently to succeed in the rest of the program or, in the case of the capstone, to the extent that you are ready to go forward with a new degree.\n\nAs a general formula, we can consider comprehension is the application of program or course outcome learning objectives and then critical thinking is the synthesis of this with other information to bring forward examples of your application.\n\nAlso, it is necessary to have participation posts in additional to your initial post to demonstrate this rubric element to the extent that your work earns the highest possible rating on this rubric element.\n\nHere''s a great resource for critical thinking: criticalthinking.org/files/Concepts_Tools.pdf'),
    ('Course Connections', TRUE, 'Excellent', 'Thank you for the awesome work with your course connection.  I can clearly see your application of concepts in the course.'),
    ('Course Connections', FALSE, 'Excellent', 'To maximize your grade in this area, please be sure to be thoughtful and careful application of course content in both your initial reply and in your participation posts.\n\nBy incorporating the course content into your academic writing, you have the opportunity to show what you are learning and how you are learning it. You incorporate the course content into your work by bringing in examples that support your arguments.\n\nAlso, it is necessary to have participation posts in additional to your initial post to demonstrate this rubric element to the extent that your work earns the highest possible rating on this rubric element.\n\nHere is a resource that will be helpful for you:owl.english.purdue.edu/owl/section/1/2/'),
    ('Active Participation', TRUE, 'Excellent', 'Thank you for the awesome work with your active participation! By actively participating in the ongoing discussion boards, you maximize your learning. This better prepares you for the rest of your program. Well done.'),
    ('Active Participation', FALSE, 'Excellent', 'Please review the engagement requirements. Remember, you earn points by posting an initial reply to the discussion question and then you also earn points by engaging with your peers through participation posts.\n\nTo maximize your grade, it''s important to both meet minimum number of expected participation posts and then it''s also important that your participation posts are of a sufficient quality to add substantively to our ongoing discussion.'),
    ('Timely Participation', TRUE, 'Excellent', 'Thank you for your excellence in the area of timely participation and engagement. By taking this approach, you maximize your learning and then you also earn the highest possible points in this rubric element. :-)'),
    ('Timely Participation', FALSE, 'Excellent', 'This rubric element looks at the timing of your participation.   At a minimum, your participation posts should be in by Saturday each unit to maximize your point in this rubric element.\n\nBy fully engaging in the work through participation and then posting on time in the courseroom,  you are creating the best opportunity for your own learning.')
    RETURNING rubric_elementsid
)
INSERT INTO universities_rubric_elements (rubric_elementsid, universitiesid)
SELECT rubric_elementsid, 'POST'
FROM ids;

-- course:      MKT200_37_Principles of Marketing_2019_20_TERM6
-- assignment:  Unit 1 Assignment: Social Media

-- insert new specific rubric elements for assignment
WITH ids as (
    INSERT INTO rubric_elements (title, is_max_scoring, max_scoring_keyword, response)
    VALUES
    ('Introduction of Company, Including Needs, Value, Target Customer, Social Media Platform(s)', TRUE, 'Exemplary', 'Super. I can see your excellence in your work in this area.'),
    ('Introduction of Company, Including Needs, Value, Target Customer, Social Media Platform(s)', FALSE, 'Exemplary', '"To have maximized your grade in this rubric element, it was necessary to have an introduction that is fully and thoughtfully addressed these details: target customer and the social media platforms they are utilizing. If they are using multiple platforms, list them here and then choose 1 to evaluate in the next section.  To maximize your grade and learning, it is necessary to address each element of each rubric section.\n\nYou might benefit from this resource: https://owl.purdue.edu/owl/general_writing/academic_writing/index.html'),
    ('Effectiveness of the Social Media Platform', TRUE, 'Exemplary', 'Nicely done!  Your work is strong in this rubric element.  Very good!'),
    ('Effectiveness of the Social Media Platform', FALSE, 'Exemplary', 'To have earned the maximum possible points in this rubric element it was necessary to have work that  includes writing about effectiveness of the social media platform and your work should include information that is fully and thoughtfully addressed these details: Evaluate the effectiveness of the social media platform you chose in building and maintaining customer relationships while providing information about the brand.\n\nYour work did not include this information.  Here is a resource for you: https://www.marketingprofs.com/topic/all/social-media'),
    ('Effectiveness of Customer Engagement and Branding Alignment', TRUE, 'Exemplary', 'I can see your good work in this part of the rubric.  Awesome!'),
    ('Effectiveness of Customer Engagement and Branding Alignment', FALSE, 'Exemplary', 'To have earned all the points in this part of the rubric, the work needed to discuss effectiveness of customer engagement and branding alignment and this should have been fully and thoughtfully addresse these details:Evaluate the effectiveness of the company in creating customer engagement. How does their branding message align with the company’s marketing mix? Your work did not meet this requirement.   Here is a resource for you: https://blog.hubspot.com/service/customer-engagement-guide'),
    ('Observation and Discussion on Social Media’s ROI for the Company', TRUE, 'Exemplary', 'Very good.  I can see commitment to you studies in this rubric'),
    ('Observation and Discussion on Social Media’s ROI for the Company', FALSE, 'Exemplary', 'To have earned the most points in this part of the work the writing should have include an observation and discussion of social media ROI  that  fully and thoughtfully addressed this question: based on your observation, do you think social media is a positive return on investment for the company? Why or why not?  Your work was short in this area. Check out this resource.  It might be helpful: https://www.forbes.com/sites/forbesagencycouncil/2018/01/30/social-media-measuring-the-roi/#79769cb16d9f')
    RETURNING rubric_elementsid
)
INSERT INTO assignments_rubric_elements (rubric_elementsid, assignmentsid, coursesid)
SELECT rubric_elementsid, 'A1', 'MKT200'
FROM ids;

-- then insert the variables needed for any generic rubric elements used
INSERT INTO assignments_generic_rubric_elements (title, is_max_scoring, variables, assignmentsid, coursesid)
VALUES
('Resources', TRUE, '{"number":"two"}', 'A1', 'MKT200'),
('Resources', FALSE, '{"number":"two"}', 'A1', 'MKT200'),
('Paper Length', TRUE, '{"number":"two"}', 'A1', 'MKT200'),
('Paper Length', FALSE, '{"number":"two"}', 'A1', 'MKT200'),
('Clear and Professional Writing and APA Format', TRUE, '{}', 'A1', 'MKT200'),
('Clear and Professional Writing and APA Format', FALSE, '{}', 'A1', 'MKT200');

-- course:      MKT200_37_Principles of Marketing_2019_20_TERM6
-- assignment:  Unit 3 Assignment: Service Organizations

WITH ids as (
    INSERT INTO rubric_elements (title, is_max_scoring, max_scoring_keyword, response)
    VALUES
    ('Introduction: Identify Why you Chose the Company, Services They Provide, Location, How Many, Employees', TRUE, 'Exemplary', ''),
    ('Introduction: Identify Why you Chose the Company, Services They Provide, Location, How Many, Employees', FALSE, 'Exemplary', ''),
    ('Company''s Branding Strategy: Brand Positioning, Brand Recognition, Crowdsourcing, Private Label Branding or Brand Extensions.', TRUE, 'Exemplary', ''),
    ('Company''s Branding Strategy: Brand Positioning, Brand Recognition, Crowdsourcing, Private Label Branding or Brand Extensions.', FALSE, 'Exemplary', ''),
    ('Evaluation: Identify and discuss 4 Key Service Characteristics', TRUE, 'Exemplary', ''),
    ('Evaluation: Identify and discuss 4 Key Service Characteristics', FALSE, 'Exemplary', '')
    RETURNING rubric_elementsid
)
INSERT INTO assignments_rubric_elements (rubric_elementsid, assignmentsid, coursesid)
SELECT rubric_elementsid, 'A3', 'MKT200'
FROM ids;

-- then insert the variables needed for any generic rubric elements used
INSERT INTO assignments_generic_rubric_elements(title, is_max_scoring, variables, assignmentsid, coursesid)
VALUES
('Resources', TRUE, '{"number":2}', 'A1', 'MKT200'),
('Resources', FALSE, '{"number":2}', 'A1', 'MKT200'),
('Paper Length', TRUE, '{"number":2}', 'A1', 'MKT200'),
('Paper Length', FALSE, '{"number":2}', 'A1', 'MKT200'),
('Clear and Professional Writing and APA Format', TRUE, '{}', 'A1', 'MKT200'),
('Clear and Professional Writing and APA Format', FALSE, '{}', 'A1', 'MKT200');

-- course:      MKT200_37_Principles of Marketing_2019_20_TERM6
-- assignment:  Unit 4 Assignment: Pricing
WITH ids as (
    INSERT INTO rubric_elements (title, is_max_scoring, max_scoring_keyword, response)
    VALUES
    ('Introduction of Product and Why You Chose it', TRUE, 'Exemplary', 'Super. I can see your excellence in your work in this area.'),
    ('Introduction of Product and Why You Chose it', FALSE, 'Exemplary', 'To have maximized your grade in this rubric element, it was necessary to have work that included an  introduction of the product and why you chose it.  This section shoud have  fully and thoughtfully addressed and it should have included all details. This is where you defend the decisions you’ve made so that your stakeholders understand why you made one decision over another.  The project needed more development in this area.'),
    ('The Product Chart Depicting Sales Locations and Prices', TRUE, 'Exemplary', 'Nicely done!  Your work is strong in this rubric element.  Very good!'),
    ('The Product Chart Depicting Sales Locations and Prices', FALSE, 'Exemplary', 'To have earned the maximum possible points in this rubric element it was necessary to have work that  includes a product chart depicting sales locations and prices that is fully and thoughtfully addressed.  This should have included all details.  The project needed more information in this part of the project. In this section, you layout the product chart detailing locations and prices. Without these data, it’s difficult articulate why you made the choices you did.'),
    ('Explanation of Price Differences with External and Internal Factors for the Price Discrepancy', TRUE, 'Exemplary', 'I can see your good work in this part of the rubric.  Awesome!'),
    ('Explanation of Price Differences with External and Internal Factors for the Price Discrepancy', FALSE, 'Exemplary', 'To have earned all the points in this part of the rubric, the work needed to have an explanation of price differences with external and internal factors for the price discrepancy. To earm the maximum points, this section needed to explain why you think there are price differences for the same product at different stores. This section needed to include at least 2 of the external and 2 of the internal factors which might be affecting the companies pricing strategies. '),
    ('Description of Why Consumers Might Shop at a Higher Price Store Than the Lower Price Store', TRUE, 'Exemplary', 'Very good.  I can see commitment to you studies in this rubric'),
    ('Description of Why Consumers Might Shop at a Higher Price Store Than the Lower Price Store', FALSE, 'Exemplary', 'To have earned the most points in this part of the work the writing should have included description of why consumers might shop at a higher price store than the lower price store. The description should have been fully and thoughtfully addressed, including all details.  Your work did not fully address this topic at the maximum points level.'),
    ('Conclusion, Including What You Learned From This', TRUE, 'Exemplary', 'You did a very good job with this rubric element. '),
    ('Conclusion, Including What You Learned From This', FALSE, 'Exemplary', 'To have maxed out the points in this rubric element, your work needed to include a conclusion, including what you learned from this. The conclusion fully and thoughtfully addressed and it needed to  include all details.')
    RETURNING rubric_elementsid
)
INSERT INTO assignments_rubric_elements (rubric_elementsid, assignmentsid, coursesid)
SELECT rubric_elementsid, 'A4', 'MKT200'
FROM ids;

-- then insert the variables needed for any generic rubric elements used
INSERT INTO assignments_generic_rubric_elements (title, is_max_scoring, variables, assignmentsid, coursesid)
VALUES
('Resources', TRUE, '{"number":2}', 'A4', 'MKT200'),
('Resources', FALSE, '{"number":2}', 'A4', 'MKT200'),
('Paper Length', TRUE, '{"number":2}', 'A4', 'MKT200'),
('Paper Length', FALSE, '{"number":2}', 'A4', 'MKT200'),
('Clear and Professional Writing and APA Format', TRUE, '{}', 'A1', 'MKT200'),
('Clear and Professional Writing and APA Format', FALSE, '{}', 'A1', 'MKT200');

-- course:      MKT200_37_Principles of Marketing_2019_20_TERM6
-- assignment:  Unit 6 Assignment: Integrated Marketing Presentation

-- course:      MKT200_37_Principles of Marketing_2019_20_TERM6
-- assignment:  Unit 7 Assignment: Internet Security and Privacy



