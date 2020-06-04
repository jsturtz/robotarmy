-- drop all the tables first and then recreate them
DROP TABLE IF EXISTS assignments_rubric_elements;
DROP TABLE IF EXISTS rubric_elements;
DROP TABLE IF EXISTS assignments;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS universities;

-- FIXME: should inspect all these columns to decide which should have constraints
-- FIXME: should decide on the data values of all these "TEXT" types. Do they all need that freedom?
CREATE TABLE universities (
	universitiesid SERIAL PRIMARY KEY,
	pretty_name TEXT,
    code TEXT NOT NULL UNIQUE
);

-- FIXME: Using unique codes to identify courses is going to be problematic.
-- FIXME: Should we add a semester column to uniquely identify multiple of the same code?
CREATE TABLE courses (
    coursesid SERIAL PRIMARY KEY,
    pretty_name TEXT,
    code TEXT NOT NULL UNIQUE,
    universitiesid INTEGER REFERENCES universities(universitiesid) NOT NULL
);

-- FIXME: Using unique codes to identify assignments is going to be problematic.
-- FIXME: Should be a unique combination at least of code and coursesid
CREATE TABLE assignments (
    assignmentsid SERIAL PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    pretty_name TEXT,
    coursesid INTEGER REFERENCES courses(coursesid) NOT NULL
);

CREATE TABLE rubric_elements (
    rubric_elementsid SERIAL PRIMARY KEY,
    name TEXT,
    response TEXT,
    is_exemplary BOOLEAN
);

CREATE TABLE assignments_rubric_elements (
    assignments_rubric_elementsid  SERIAL PRIMARY KEY,
    assignmentsid INTEGER REFERENCES assignments(assignmentsid) NOT NULL,
    rubric_elementsid INTEGER REFERENCES rubric_elements(rubric_elementsid) NOT NULL
);

-- data for post university
INSERT INTO universities (pretty_name, code)
VALUES
('Post University', 'PU'),
('This is a test', 'Hi');

INSERT INTO courses (pretty_name, code, universitiesid)
values
('Principles of Marketing', 'MKT200', (SELECT universitiesid FROM universities WHERE code = 'PU'));

INSERT INTO assignments (pretty_name, code, coursesid)
values
('UNIT 4 ASSIGNMENT: PRICING', 'U4', (SELECT coursesid FROM courses WHERE code ='MKT200'));

-- RUBRIC ELEMENTS --------------------------------------------------------------------------------

-- course MKT200, assignment U4
DO $$
    DECLARE
        _assignmentsid BIGINT;
    BEGIN
        _assignmentsid := (SELECT assignmentsid FROM assignments WHERE code = 'U4');

	    WITH ids as (
	    	INSERT INTO rubric_elements (name, is_exemplary, response)
        	VALUES
        	('Complete addressing', TRUE, 'This rubric element evaluates how completely you addressed the questions in the project document. Thank you for putting in the necessary work to fully address the topic.  This kind of effort demonstrates your commitment to your education.  In the end, the work you put in is your investment in you!  Well done.'),
        	('Complete addressing', FALSE, 'This rubric element evaluates how completely you addressed the questions in the project document. This include both specific questions as outlined in the prompt and also addressing these topics with a certain word count range.  To learn more about the project, please refer to the project assignment document in the courseroom.  This document includes the rubric that lays out various performance levels and the score for each.\nYou might benefit from this resource: https://owl.purdue.edu/owl/general_writing/academic_writing/index.html'),
        	('References to course materials', TRUE, 'This rubric element looks at your use of course materials or other sources to support your work. Excellent!  You brought in strong references to outside course materials.  By including these references, we’re moving beyond your opinion and you are showing how your ideas have basis in what you are learning. Awesome!'),
        	('References to course materials', FALSE, 'This rubric element looks at your use of course materials or other sources to support your work. To have maximized your grade it was necessary to include references to outside sources in the text and in the reference list. Reference lists without a corresponding in text reference are incomplete. By including these references, we’re moving beyond your opinion and you are showing how your ideas have basis in what you are learning. For more information about this part of the rubric, please check out the project document in the courseroom.  In particular, I recommend that you review the rubric for “references to weekly course materials.'),
        	('Reflective thinking', TRUE, 'This rubric element considers critical thinking, which involves the correct application of course content and other learning to the question at hand.  Essentially, this rubric element measures how well you demonstrate learning through your written work.\nI am happy to say that you did an awesome job in this area.  You have shown that you are digging into the course material to the extent that you are able to apply your new learning to our course topics.  Fine work!'),
        	('Reflective thinking', FALSE, 'This rubric element considers critical thinking, which involves the correct application of course content and other learning to the question at hand.  Essentially, this rubric element measures how well you demonstrate learning through your written work.\nThis is an area that could use some work.  It is important to spend time with the course material.  When there is reading, I recommend that you read all of it.  When there are videos, it is a good idea to watch them.  Essentially, it is a good idea to do everything you can to learn as much as you can in the course.\nThen, of course, it is also important to show the application of the new learning in your written work. This resources might also be helpful to you: https://owl.purdue.edu/owl/subject_specific_writing/writing_in_the_social_sciences/index.html'),
        	('Grammar', TRUE, 'You did a fantastic job in this rubric element.  There are no grammar errors that I saw. Super!'),
        	('Grammar', FALSE, 'This rubric element considers the professional nature of your communications by looking at grammar errors.  There are a lot of resources that can help you in the area of writing. First, the school has an excellent writing center that is designed to support students in their writing. People who struggle with this rubric element often benefit from working with the writing center and using some of the resources there. Second, there are grammar and spell checking tools directly within word. It’s always a good idea to use these before submitting assignments.\nThere are also a number of great commercial programs, such as Grammarly, that help people develop in this important part of our rubric criteria.  Here is a resource that the school has for you as well: https://post.edu/student-services/university-learning-center/writing-center'),
        	('Late', TRUE, ''),
        	('Late', FALSE, 'Please note there is a late penalty. There is not a policy in place school and so this means that late assignments are not accepted. Instructors may make exception to the policy.  I sometimes accept late assignments with a late penalty and I am accepting this one:)  The best way to proceed with assignment is to proactively communicate with your instructor if you think you might be late.  By doing this, you maximize both your learning and your grade.')
        	RETURNING rubric_elementsid
	    )
	    INSERT INTO assignments_rubric_elements (rubric_elementsid, assignmentsid)
	    SELECT rubric_elementsid, _assignmentsid AS assignmentsid
	    FROM ids;
    END
$$;
