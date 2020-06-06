'''
Put any common database tools here
'''

def get_rubric_responses(con, uni, course, assign):

    # get data from database
    cur = con.cursor()
    cur.execute(f"""
        SELECT re."name", re.is_max_scoring, re.response
        FROM rubric_elements re 
        JOIN assignments_rubric_elements are1 ON are1.rubric_elementsid = re.rubric_elementsid 
        JOIN assignments a ON a.assignmentsid = are1.assignmentsid 
        JOIN courses c ON a.coursesid = c.coursesid 
        JOIN universities u on u.universitiesid = c.universitiesid 
        WHERE u.code = '{uni}'
        AND c.code = '{course}'
        AND a.code = '{assign}';
    """)
    # use the tuple (name, is_exemplary) to uniquely identify a row
    return {(row[0], row[1]): row[2] for row in cur.fetchall()}
