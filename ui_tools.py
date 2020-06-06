'''
Put ui specific tools here
'''



import PySimpleGUI as sg
import traceback

'''
Generic error window that will display error message and traceback
'''
def error_window(e):
    layout = [
        [sg.Text("Error message")],
        [sg.Text(e)],
        [sg.Text(traceback.format_exc())],
        [sg.Button("Ok")],
    ]
    window = sg.Window("Error!", layout)
    while True:
        event, values = window.read()
        if event in (None, 'Ok'):   # if user closes window or clicks cancel
            break
    window.close()
