'''
Put any common database tools here
'''

def query(con, query):
    cur = con.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    return rows

def queryOneVal(con, query):
    cur = con.cursor()
    cur.execute(query)
    rows = cur.fetchone()
    cur.close()
    return rows[0]

# FIXME: kinda shit function. User has to access columns they request by index they provide
def query_grouped_by_dict(con, table, grouped_by, columns):
    cur = con.cursor()
    cur.execute(f"SELECT %s, %s FROM %s ORDER BY %s;" % (grouped_by, ", ".join(columns), table, grouped_by) )
    rows = cur.fetchall()
    return_dict = {key: [] for key in set([row[0] for row in rows])}

    for row in rows:
        return_dict[row[0]].append(row[1:])
    cur.close()
    return return_dict


def get_discussion_board_rubric_elements(con, universitiesid):
    cur = con.cursor()
    cur.execute(f"""
        SELECT re.title, re.is_max_scoring, re.response
        FROM rubric_elements re
        JOIN universities_rubric_elements ure ON ure.rubric_elementsid = re.rubric_elementsid 
        WHERE ure.universitiesid = '{universitiesid}';
    """)
    rows = cur.fetchall()
    cur.close()
    return rows

def get_all_rubric_elements(con, universitiesid, coursesid, assignmentsid):
    # get specific rubric elements first
    cur = con.cursor()
    cur.execute(f"""
        SELECT re.title, re.is_max_scoring, re.response
        FROM rubric_elements re 
        JOIN assignments_rubric_elements are1 ON are1.rubric_elementsid = re.rubric_elementsid 
        JOIN assignments a ON a.assignmentsid = are1.assignmentsid 
        JOIN courses c ON a.coursesid = c.coursesid 
        JOIN universities u on u.universitiesid = c.universitiesid 
        WHERE u.universitiesid = '{universitiesid}'
        AND c.coursesid = '{coursesid}'
        AND a.assignmentsid = '{assignmentsid}';
    """)

    specific_rubric_elems = cur.fetchall()

    # then grab the generic rubric elements together with their variable interpolation
    cur.execute(f"""
        SELECT gre.title, gre.is_max_scoring, gre.response, agre.variables
        FROM generic_rubric_elements gre
        JOIN assignments_generic_rubric_elements agre ON agre.title = gre.title
        JOIN assignments a ON a.assignmentsid = agre.assignmentsid AND a.coursesid = agre.coursesid
        WHERE gre.universitiesid = '{universitiesid}';
    """)

    # interpolate variables
    generic_rubric_elems = [list(row) for row in cur.fetchall()]
    for index, elem in enumerate(generic_rubric_elems):
        response, variables = elem[2], elem[3]
        for key, val in variables.items():
            response = response.replace('{%s}' % key, str(val))
            generic_rubric_elems[index][2] = response

    cur.close()
    return specific_rubric_elems + generic_rubric_elems

def get_university_summative_feedback(con, universitiesid, name):

    feedback = queryOneVal(con, f"SELECT summative_feedback FROM universities WHERE universitiesid = '{universitiesid}';")
    if not feedback:
        raise Exception(f'No summative feedback found for {uni}')

    return feedback.format(name=name)


