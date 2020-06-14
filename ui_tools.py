'''
Put ui specific tools here
'''



import PySimpleGUI as sg
import traceback
import util

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


'''
Takes the data structure below and builds layout for uI

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
def build_radio_selector_layout(rubric_elems, max_scoring_keyword):
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
