'''
Put any common database tools here
'''
from collections import OrderedDict
import psycopg2.extras

def query(con, query):
    cur = con.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    return rows

def query_dict(con, query):
    cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    return rows

def queryOneVal(con, query):
    cur = con.cursor()
    cur.execute(query)
    rows = cur.fetchone()
    cur.close()
    return rows[0] if rows else None

# returns data structure where user can access each group by key and then each column in the group by key
def query_grouped_by_dict(con, table, grouped_by, columns="*", where="", order_by=""):
    cur = con.cursor()
    cur.execute(f"SELECT %s, %s FROM %s %s %s;" % (grouped_by, ", ".join(columns), table, where, order_by) )
    rows = cur.fetchall()
    # ensure orderedict gets values inserted in right order
    return_dict = OrderedDict()
    for head, *tail in rows:
        return_dict.setdefault(head, [])
        return_dict[head].append({col: tail[i] for i, col in enumerate(columns)})
    cur.close()
    return return_dict

# specific functions meant to get specific data
def get_discussion_board_rubric_elements(con, universitiesid):
    cur = con.cursor()
    cur.execute(f"""
        SELECT title, rank, response
        FROM universities_rubric_elements
        WHERE universitiesid = '{universitiesid}';
    """)
    rows = cur.fetchall()
    cur.close()
    return rows

def get_all_rubric_elements(con, universitiesid, coursesid, assignmentsid):
    # get specific rubric elements first
    cur = con.cursor()
    cur.execute(f"""
        SELECT are1.title, are1.rank, are1.response
        FROM assignments_rubric_elements are1
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
        SELECT gre.title, gre.rank, gre.response, agre.variables
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
        raise Exception(f'No summative feedback found for {universitiesid}')

    return feedback.format(name=name)

def get_links_dict(con):

    rows = query_dict(con, """
        select  u.universitiesid, ul.pretty_name as uni_pretty_name, ul.url as uni_url, 
                c.coursesid, cl.pretty_name as course_pretty_name, cl.url as course_url
        from universities u 
        left join courses c on u.universitiesid = c.universitiesid 
        left join universities_links ul on ul.universitiesid = u.universitiesid 
        left join courses_links cl on cl.coursesid = c.coursesid and cl.universitiesid = u.universitiesid 
        order by u.universitiesid, c.coursesid;
    """)

    structure = OrderedDict()
    for row in rows:
        structure.setdefault(row["universitiesid"], OrderedDict())
        if row["uni_url"] and row["uni_pretty_name"]:
            structure[row["universitiesid"]].setdefault("links", OrderedDict())
            structure[row["universitiesid"]]["links"].setdefault(row["uni_pretty_name"], row["uni_url"])

        structure[row["universitiesid"]].setdefault("courses", OrderedDict())
        if row["course_pretty_name"] and row["course_url"]:
            structure[row["universitiesid"]]["courses"].setdefault(row["coursesid"], OrderedDict())
            structure[row["universitiesid"]]["courses"][row["coursesid"]].setdefault("links", OrderedDict())
            structure[row["universitiesid"]]["courses"][row["coursesid"]]["links"][row["course_pretty_name"]] = row["course_url"]

    return structure






