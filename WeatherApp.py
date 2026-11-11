"""
Author: Dominic Vinciulla
1024x600 weather information application built on tkinter
"""

import tkinter as tk
import customtkinter as ctk
import time
import threading
from io import BytesIO
from datetime import datetime, timedelta
from urllib.request import urlopen
from PIL import Image
from dotenv import dotenv_values
from WeatherData import WeatherDataObj

values = dotenv_values(".env")
DAYCOUNT = 7
DAYBG = '#a2c1fa'
DAYTEXT = '#0c1d3d'
NIGHTBG = '#0d1026'
city = ''
state = ''

if 'CITY' in values:
    city = values.pop('CITY')
if 'STATE' in values:
    state = values.pop('STATE')

weatherObj = WeatherDataObj(values, city, state)

def suffix(day: int) -> str:
    """
    Returns correct suffix given day of the month
    :param day: day of the month
    :return: suffix in ['th', 'st', 'nd', 'rd']
    """
    if 11 <= day % 100 <= 13:
        return f"{day}th"
    return f"{day}{['th', 'st', 'nd', 'rd', 'th', 'th', 'th', 'th', 'th', 'th'][day % 10]}"

def ms_until_next_minute():
    """
    Calculates how many milliseconds there are until the next minute starts,
    allowing for accurate time updates
    :return: ms until next minute
    """
    now = datetime.now()
    next_minute = (now.replace(second=0, microsecond=0) + timedelta(minutes=1))
    delta = next_minute - now
    return int(delta.total_seconds() * 1000)

class WeatherApp:
    """
    Represents the main tkinter application responsible for displaying info
    """
    def __init__(self, root):
        self.root = root
        self.root.geometry("1024x600")
        self.root.overrideredirect(True)
        self.widgets = {}
        self.day = True
        self.units = tk.BooleanVar()
        self.units.set(False)
        self.iconUrl = ''
        self.icon = self.generate_image(weatherObj.icon())
        self.date = datetime.today()

        self.build_layout()
        self.light_mode()

        # Bind dropdown selection to update immediately
        self.widgets["-SELECTOR-"].bind("<<ComboboxSelected>>", self.update_window)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Start the periodic 2-minute update loop
        self.schedule_update()
        self.update_time()

    def on_close(self):
        self.root.destroy()
        import sys
        sys.exit(0)

    def build_layout(self):
        bg = self.root["bg"]

        main = ctk.CTkFrame(self.root, fg_color=bg)
        main.pack(fill="both", expand=True)

        # Top row: City + Icon + Day selector
        top = ctk.CTkFrame(main, fg_color=bg)
        top.pack(fill='x')

        self.widgets["-CITY-"] = ctk.CTkLabel(top, text="City", font=("Courier", 50, "bold"), fg_color=bg, text_color="white")
        self.widgets["-CITY-"].pack(side="left", padx=10)

        date_values = [datetime.now().strftime('%A, %m/%d')]

        self.widgets["-SELECTOR-"] = ctk.CTkComboBox(top, values=date_values, state="readonly")
        self.widgets["-SELECTOR-"].pack(side="right", padx=15)
        self.widgets["-SELECTOR-"].set(date_values[0])

        self.update_days(True)

        desc_box = ctk.CTkFrame(main, fg_color=bg)
        desc_box.pack(fill='x', )

        self.widgets["-IMAGE-"] = ctk.CTkLabel(desc_box, fg_color=bg, image=self.icon)
        self.widgets["-IMAGE-"].pack(side="left", padx=10)

        self.widgets["-DESC-"] = ctk.CTkLabel(desc_box, text="Desc", font=("Courier", 20, 'bold'), fg_color=bg, text_color="white")
        self.widgets["-DESC-"].pack(side="left")

        # Middle row: Temp, High/Low, Wind/Humidity
        mid = ctk.CTkFrame(main, fg_color=bg)
        mid.pack(fill="x", expand=True, pady=10)

        # TEMP COLUMN
        temp_col = ctk.CTkFrame(mid, fg_color=bg)
        temp_col.pack(side="left", expand=True)

        self.widgets["-TEMP-"] = ctk.CTkLabel(temp_col, text="00°", font=("Courier", 155, "bold"), fg_color=bg, text_color="white")
        self.widgets["-TEMP-"].pack()

        self.widgets["-FEELS-"] = ctk.CTkLabel(temp_col, text="Feels Like:", font=("Courier", 30), fg_color=bg, text_color="white")
        self.widgets["-FEELS-"].pack()

        # HIGH/LOW COLUMN
        hl_col = ctk.CTkFrame(mid, fg_color=bg)
        hl_col.pack(side="left", expand=True)

        self.widgets["-HIGH-"] = ctk.CTkLabel(hl_col, text="00", font=("Courier", 40, "bold"), fg_color=bg, text_color="white")
        self.widgets["-HIGH-"].pack()
        ctk.CTkLabel(hl_col, text="High", font=("Courier", 20), fg_color=bg, text_color="white").pack()

        self.widgets["-LOW-"] = ctk.CTkLabel(hl_col, text="00", font=("Courier", 40, "bold"), fg_color=bg, text_color="white")
        self.widgets["-LOW-"].pack()
        ctk.CTkLabel(hl_col, text="Low", font=("Courier", 20), fg_color=bg, text_color="white").pack()

        # VERTICAL SEPARATOR
        sep = ctk.CTkFrame(mid, fg_color="white", width=2)
        sep.static_color = False
        sep.pack(side="left", fill="y", padx=10)

        # WIND/HUMIDITY COLUMN
        wh_col = ctk.CTkFrame(mid, fg_color=bg)
        wh_col.pack(side="left", expand=True)

        ctk.CTkLabel(wh_col, text="Wind", font=("Courier", 40), fg_color=bg, text_color="white").pack()
        self.widgets["-WIND-"] = ctk.CTkLabel(wh_col, text="00", font=("Courier", 40, "bold"), fg_color=bg, text_color="white")
        self.widgets["-WIND-"].pack()

        ctk.CTkLabel(wh_col, text="Humidity", font=("Courier", 40), fg_color=bg, text_color="white").pack()
        self.widgets["-HUM-"] = ctk.CTkLabel(wh_col, text="00", font=("Courier", 40, "bold"), fg_color=bg, text_color="white")
        self.widgets["-HUM-"].pack()

        # Bottom row: Date + Units checkbox
        bottom = ctk.CTkFrame(main, fg_color=bg)
        bottom.pack(fill="x")

        self.widgets["-DATE-"] = ctk.CTkLabel(bottom, text="Date", font=("Courier", 25), fg_color=bg, text_color="white")
        self.widgets["-DATE-"].pack(side="left", padx=10)

        self.widgets["-UNITS-"] = ctk.CTkCheckBox(bottom, text="C°", font=("Courier", 20), variable=self.units, highlightcolor=bg, selectcolor=bg, fg_color=bg, text_color="white", command=self.on_unit_changed)
        self.widgets["-UNITS-"].pack(side="right", padx=15, pady=5)

        self.widgets["-QUIT-"] = ctk.CTkButton(bottom, text="Quit", font=("Courier", 15), fg_color=bg, text_color="white", command=self.on_close)
        self.widgets["-QUIT-"].pack(side="right")

    def generate_image(self, url):
        if self.iconUrl == url:
            return self.icon

        self.iconUrl = url
        with urlopen(self.iconUrl) as u:
            data = u.read()

        image = Image.open(BytesIO(data))
        photo = ctk.CTkImage(image)
        self.icon = photo
        return photo

    def update_window(self, event=None):
        # Update dropdown values
        index = self.update_days(False)

        currObj = weatherObj if index == 0 else weatherObj.forecast(index)

        temp = int(currObj.currentTemp())
        desc = currObj.description().title()

        self.widgets["-CITY-"].config(text=f'{weatherObj.getCity()},{weatherObj.getState()}')
        self.widgets["-TEMP-"].config(text=f"{temp}°")
        self.widgets["-HIGH-"].config(text=f"{round(currObj.highTemp())}")
        self.widgets["-LOW-"].config(text=f"{round(currObj.lowTemp())}")
        self.widgets["-FEELS-"].config(text=f"Feels like: {round(currObj.feelsLike())}°")
        self.widgets["-WIND-"].config(text=f"{round(currObj.windSpeed())} {currObj.getUnit()}")
        self.widgets["-HUM-"].config(text=f"{currObj.humidity()}%")
        self.widgets["-DESC-"].config(text=desc)
        self.load_image_async(currObj.icon())

        sunset = weatherObj.sunset()
        sunrise = weatherObj.sunrise()
        current_time = time.time()
        if sunset > current_time >= sunrise and not self.day:
            self.day = True
            self.light_mode()
        elif (current_time < sunrise or current_time >= sunset) and self.day:
            self.day = False
            self.dark_mode()

        # Temperature color logic
        temperature = round(temp if not self.units.get() else (temp * 9/5) + 32)
        color = self.widgets["-HUM-"].cget("fg")
        if temperature >= 80: color = "red"
        elif temperature >= 70: color = "orange"
        elif temperature <= 45: color = "#03b6fc"
        elif temperature <= 30: color = "#0013bf"
        self.widgets["-TEMP-"].config(text_color=color)

    def load_image_async(self, url):
        if self.iconUrl == url:
            return

        self.iconUrl = url

        thread = threading.Thread(
            target=self._download_image,
            args=(url,),
            daemon=True
        )
        thread.start()

    def _download_image(self, url):
        try:
            with urlopen(url) as u:
                data = u.read()

            image = Image.open(BytesIO(data))
            photo = ctk.CTkImage(image)

            self.root.after(0, self._update_image_label, photo, url)

        except Exception as e:
            print(f"Image download failed: {e}")

    def _update_image_label(self, photo, url):
        if url != self.iconUrl:
            return

        self.icon = photo
        self.widgets["-IMAGE-"].config(image=self.icon)

    def on_unit_changed(self):
        weatherObj.setUnit("metric" if self.units.get() else "imperial")
        weatherObj.refresh()
        self.update_window()

    def update_time(self):
        now = datetime.now()
        self.widgets["-DATE-"].config(
            text=f'{now.strftime("%A, %B")} {suffix(now.day)} | {now.strftime("%I:%M %p")}'
        )
        self.root.after(ms_until_next_minute(), self.update_time)

    def update_days(self, force: bool):
        selector = self.widgets["-SELECTOR-"]
        if force or self.date != datetime.today():
            now = datetime.now()
            days = [now + timedelta(days=i) for i in range(DAYCOUNT)]
            dates = [d.strftime('%A, %m/%d') for d in days]
            dates[0] = "Today"
            selector["values"] = dates
            self.date = datetime.today()

        values = selector.cget("values")
        index = values.index(selector.get()) if selector.get() in values else 0
        return index

    def schedule_update(self):
        weatherObj.refresh()
        self.update_window()
        self.root.after(180000, self.schedule_update)

    def dark_mode(self):
        self.set_theme(self.root, NIGHTBG, DAYBG)

    def light_mode(self):
        self.set_theme(self.root, DAYBG, DAYTEXT)

    def set_theme(self, component, bg, fg):
        if 'bg' in component.keys() and getattr(component, "static_color", True):
            component.configure(fg_color=bg)

        if 'fg' in component.keys() and getattr(component, "static_color", True):
            component.configure(text_color=fg)

        for w in component.winfo_children():
            self.set_theme(w, bg, fg)

# tkRoot = tk.Tk()
ctkRoot = ctk.CTk()
app = WeatherApp(ctkRoot)
ctkRoot.mainloop()