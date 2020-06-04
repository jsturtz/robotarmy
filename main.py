import PySimpleGUI as sg
import psycopg2
import util

# set up connection to database
config = util.get_config()
con = util.get_connection()

# Do the UI stuff
sg.theme(config["gui"]["theme"])   # Add a touch of color

# All the stuff inside your window.
layout = [[sg.Text('Some text on Row 1')],
          [sg.Text('University Name'), sg.InputText()],
          [sg.Text('University Code'), sg.InputText()],
          [sg.Button('Ok'), sg.Button('Cancel')]]

# Create the Window
window = sg.Window('Window Title', layout)

# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read()
    if event in (None, 'Cancel'):   # if user closes window or clicks cancel
        break

    # insert pretty name and code into newly created table
    pretty_name, code = values[0], values[1]
    sql = f"INSERT INTO universities (pretty_name, code) VALUES ('{pretty_name}', '{code}');"
    cur = con.cursor()
    cur.execute(sql)
    cur.close()
    con.commit()
    print(f'You inserted {pretty_name}, {code} into the database')

window.close()
