"""
Author: Dominic Vinciulla
open_weather.py uses openweathermap.org api to display real-time weather information
from a given area to a 480 by 320 screen
"""

import time
import PySimpleGUI as gui
from WeatherData import WeatherDataObj
from datetime import datetime, timedelta
from dotenv import dotenv_values


values = dotenv_values(".env")

DAYCOUNT = 7
weatherObj = WeatherDataObj(values)

def suffix(myDate: int) -> str:
    """
    Returns the day of the month with the correct suffix
    :param myDate: input day of the month (1-31)
    :return: date along with suffix
    """
    date_suffix = ['th', 'st', 'nd', 'rd']

    if myDate % 10 in [1, 2, 3] and myDate not in [11, 12, 13]:
        return str(myDate) + date_suffix[myDate % 10]
    else:
        return str(myDate) + date_suffix[0]

# def callApi() -> tuple:
#     """
#     Gathers info from api and returns tuple of json info,
#     including the wind speed suffix for simplicity
#     :return: Tuple of data from api
#     """
#     # check if metric option is selected
#     # change units if necessary
#     if window['-UNITS-'].get():
#         unit = '&units=metric'
#         speed = ' kmh'
#     else:
#         unit = '&units=imperial'
#         speed = ' mph'
#
#     return getPage(CURRENT + unit), speed

def layoutGenerator() -> list:
    """
    Generates the layout of the window as a new object each time,
    avoiding the reuse of the same layout object
    :return: PySimpleGui layout, a list
    """
    return [
            [gui.Column([
                        [gui.Column([
                                    [gui.Text('City', key='-CITY-', font='Courier 30 bold', pad=((5,0),0)),
                                     gui.Image(key='-IMAGE-', pad=((10,10),0)),
                                     gui.Combo([datetime.now().strftime('%A, %m/%d')], default_value=datetime.now().strftime('%A, %m/%d'), size=(16,1), auto_size_text=True, pad=0, readonly=True, key='-SELECTOR-')],
                                    [gui.Text('Desc', font='Courier 10', key='-DESC-')]],
                                    expand_x=True, pad=0)],
                        [gui.Column([
                                    [gui.Text('00', key='-TEMP-', font='Courier 55 bold', pad=((10,10),0))],
                                    [gui.Text('Feels Like: ', font='Courier 10', key='-FEELS-')]],
                                    element_justification='center'),
                        gui.Column([
                                    [gui.Text('00', font='Courier 20 bold', pad=((0,0),(0,30)), key='-HIGH-'), gui.Text('High', font='Courier 10', pad=(0,0))],
                                    [gui.Text('00', font='Courier 20 bold', pad=((0,0),(30,0)), key='-LOW-'), gui.Text('Low', font='Courier 10', pad=(0,(60,0)))]],
                                    element_justification='center'),
                        gui.VerticalSeparator(color='white', pad=((20,20),(0,0))),
                        gui.Column([
                                    [gui.Text('Wind', font='Courier 20', pad=((0,0),(0,5)))],
                                    [gui.Text('00', font='Courier 20 bold', pad=((0,0),(0,30)), key='-WIND-')],
                                    [gui.Text('Humidity', font='Courier 20', pad=((0,0),(0,5)))],
                                    [gui.Text('00', font='Courier 20 bold', pad=((0,0),(0,30)), key='-HUM-')]],
                                    element_justification='center')]
                        ],
                        expand_x=True, element_justification='center', pad=((0,10),0), expand_y=True)
                    ],
                [gui.Text('Date', font='Courier 10', pad=0, key='-DATE-'), gui.Checkbox('C' + u'\xb0', pad=((130,0),0), key='-UNITS-')]
            ]

def updateWindow(lastValues: dict) -> None:
    """
    Calls api function and updates all screen values
    :param apiInfo: A tuple consisting of the two datasets and the wind speed unit
    :param lastValues: A dictionary of values from the current state of the screen
    :return: None
    """

    # get current datetime object and list of datetime objects for concurrent days
    now = datetime.now()
    days = [now + timedelta(days=count) for count in range(DAYCOUNT)]
    dates = [select.strftime('%A, %m/%d') for select in days]

    # store results from apiInfo tuple into their own variables
    # weatherJson, speed = apiInfo
    #
    # currentInfo = weatherJson['current']
    # futureInfo = weatherJson['daily']

    #retain prior selection or reset if it is a new day
    if lastValues['-SELECTOR-'] in dates:
        index = dates.index(lastValues['-SELECTOR-'])
    else:
        index = 0


    # organize necessary info into dict
    if index != 0:
        window['-SELECTOR-'].update(values=dates, set_to_index=index)
        forecast = weatherObj.forecast(index)
        info = {
            '-TEMP-': str(int(forecast.temp())) + u'\xb0',
            '-FEELS-': 'Feels like: ' + str(int(forecast.feelsLike())) + u'\xb0',
            '-HUM-': str(forecast.humidity()) + '%',
            '-WIND-': str(int(forecast.windSpeed())) + forecast.getUnit(),
            '-IMAGE-': gui.net_download_file_binary(forecast.icon()),
            '-DATE-': now.strftime('%A, %B') + ' ' + suffix(now.day) + '  |  ' + now.strftime('%I:%M %p'),
            '-DESC-': ' '.join([word[0].upper() + word[1:] for word in
                                (forecast.description()).split(' ')]).strip()
        }
    else:
        info = {
            '-TEMP-': str(int(weatherObj.currentTemp())) + u'\xb0',
            '-FEELS-': 'Feels like: ' + str(int(weatherObj.feelsLike())) + u'\xb0',
            '-HUM-': str(int(weatherObj.humidity())) + '%',
            '-WIND-': str(int(weatherObj.windSpeed())) + weatherObj.getUnit(),
            '-IMAGE-': weatherObj.icon(),
            '-DESC-': ' '.join([word[0].upper() + word[1:] for word in weatherObj.description().split(' ')]).strip()
        }
    info.update({
        '-DATE-':now.strftime('%A, %B') + ' ' + suffix(now.day) + '  |  ' + now.strftime('%I:%M %p')
    })
    # if weatherJson:
    #     info.update({
    #         '-CITY-':weatherJson['city']['name'],
    #         '-HIGH-':str(int(weatherJson['list'][index]['temp']['max'])) + u'\xb0',
    #         '-LOW-':str(int(weatherJson['list'][index]['temp']['min'])) + u'\xb0',
    #     })

    # iterate dict and update each value
    # change temp value colors to reflect temperature
    # notify if value changed for debug purposes
    for key in info:
        if not (key in ['-IMAGE-', '-DATE-', '-SELECTOR-']) and str(window[key].get()) != info[key]:
            print(now.strftime('[%m/%d/%Y %I:%M %p]'), key, 'changed to', info[key])
        window[key].update(info[key])

        if key in ['-TEMP-', '-HIGH-', '-LOW-']:
            if lastValues['-UNITS-']:
                temperature = (int(window[key].get()[:-1]) * (9/5)) + 32
            else:
                temperature = int(window[key].get()[:-1])

            color = 'white'
            if temperature >= 80:
                color='red'
            elif temperature >= 70:
                color='orange'
            elif temperature <= 45:
                color='#03b6fc'
            elif temperature <= 30:
                color='#0013bf'

            window[key].update(text_color=color)


# initialize window
gui.theme('DarkBlue3')
window = gui.Window('Weather', layoutGenerator(), no_titlebar=True, location=(0, 0), size=(480, 320), keep_on_top=True, finalize=True)

start = time.time()
first = True
day = True
# persistent window loop
while True:
    event, values = window.read(timeout=5000)
    # exit loop on window close
    if event == gui.WIN_CLOSED:
        break
    # on click of update button or every 90 seconds, update
    if (time.time() - start) >= 180 or first:
        first = False
        start = time.time()
        time.sleep(0.01)
        # if not (data[0] and data[1]):
        #     continue
        sunset = weatherObj.sunset()
        sunrise = weatherObj.sunrise()
        if sunset > time.time() >= sunrise and not day:
            day = True
            window.close()
            gui.theme('DarkBlue3')
            window = gui.Window('Weather', layoutGenerator(), no_titlebar=True, location=(0, 0), size=(480, 320),
                                keep_on_top=True, finalize=True)
        elif (time.time() < sunrise or time.time() >= sunset) and day:
            day = False
            window.close()
            gui.theme('DarkBlue14')
            window = gui.Window('Weather', layoutGenerator(), no_titlebar=True, location=(0, 0), size=(480, 320),
                                keep_on_top=True, finalize=True)

        updateWindow(values)

# close window on exit of loop
window.close()