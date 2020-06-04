import PySimpleGUI as sg
import util

"""
    Allows you to "browse" through the Theme settings.  Click on one and you'll see a
    Popup window using the color scheme you chose.  Will write chosen theme to settings.conf
"""
config = util.get_config()
selected_theme = config["gui"]["theme"]
sg.theme(selected_theme)

layout = [[sg.Text('Theme Browser')],
          [sg.Text('Click a Theme color to see demo window')],
          [sg.Listbox(values=sg.theme_list(), size=(20, 12), key='-LIST-', enable_events=True)],
          [sg.Text('Selected theme: %s' % selected_theme, key='selected_theme', auto_size_text=True)],
          [sg.Button('Exit')]]

window = sg.Window('Theme Browser', layout)

while True:  # Event Loop
    event, values = window.read()
    if event in (None, 'Exit'):
        # write new theme to settings.conf
        config["gui"]["theme"] = selected_theme
        util.set_config(config)
        break
    selected_theme = values['-LIST-'][0]
    sg.theme(selected_theme)
    sg.popup_get_text(f'This is {selected_theme}')
    window["selected_theme"].update(f"Selected theme: {selected_theme}")

window.close()

