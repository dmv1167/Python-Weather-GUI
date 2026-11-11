"""
Author: Dominic Vinciulla
1024x600 weather information application built on customtkinter
"""

from datetime import datetime, timedelta
from io import BytesIO
import threading
import time
from urllib.request import urlopen

import customtkinter as ctk
from dotenv import dotenv_values
from PIL import Image
from WeatherData import WeatherDataObj

values = dotenv_values(".env")
DAYCOUNT = 7
DAYBG = '#a2c1fa'
DAYTEXT = '#0c1d3d'
NIGHTBG = '#0d1026'

# Dynamic Light/Dark color tuples (Light_Mode, Dark_Mode)
BG_COLOR = (DAYBG, NIGHTBG)
TEXT_COLOR = (DAYTEXT, DAYBG)

city = ''
state = ''

if 'CITY' in values:
    city = values.pop('CITY')
if 'STATE' in values:
    state = values.pop('STATE')

weatherObj = WeatherDataObj(values, city, state)


def suffix(day: int) -> str:
    if 11 <= day % 100 <= 13:
        return f"{day}th"
    return f"{day}{['th', 'st', 'nd', 'rd', 'th', 'th', 'th', 'th', 'th', 'th'][day % 10]}"


def ms_until_next_minute():
    now = datetime.now()
    next_minute = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
    delta = next_minute - now
    return int(delta.total_seconds() * 1000)


class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1024x600")
        self.root.overrideredirect(True)
        self.widgets = {}
        self.day = True
        self.units = ctk.BooleanVar(value=False)
        self.iconUrl = ''
        self.icon = self.generate_image(weatherObj.icon())
        self.date = datetime.today()

        # Reusable font definitions
        self.font_city = ctk.CTkFont(family="Courier", size=50, weight="bold")
        self.font_desc = ctk.CTkFont(family="Courier", size=20, weight="bold")
        self.font_temp = ctk.CTkFont(family="Courier", size=155, weight="bold")
        self.font_feels = ctk.CTkFont(family="Courier", size=30)
        self.font_hl_val = ctk.CTkFont(family="Courier", size=40, weight="bold")
        self.font_hl_lbl = ctk.CTkFont(family="Courier", size=20)
        self.font_wh_lbl = ctk.CTkFont(family="Courier", size=40)
        self.font_wh_val = ctk.CTkFont(family="Courier", size=40, weight="bold")
        self.font_date = ctk.CTkFont(family="Courier", size=25)
        self.font_units = ctk.CTkFont(family="Courier", size=20)
        self.font_quit = ctk.CTkFont(family="Courier", size=15)

        self.build_layout()
        self.light_mode()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Start periodic updates
        self.schedule_update()
        self.update_time()

    def on_close(self):
        self.root.destroy()
        import sys
        sys.exit(0)

    def build_layout(self):
        self.root.configure(fg_color=BG_COLOR)

        main = ctk.CTkFrame(self.root, fg_color=BG_COLOR)
        main.pack(fill="both", expand=True)

        # Top row: City + Icon + Day selector
        top = ctk.CTkFrame(main, fg_color=BG_COLOR)
        top.pack(fill='x')

        self.widgets["-CITY-"] = ctk.CTkLabel(
            top, text="City", font=self.font_city, fg_color=BG_COLOR, text_color=TEXT_COLOR
        )
        self.widgets["-CITY-"].pack(side="left", padx=10)

        date_values = [datetime.now().strftime('%A, %m/%d')]

        self.widgets["-SELECTOR-"] = ctk.CTkComboBox(
            top,
            values=date_values,
            state="readonly",
            command=lambda choice: self.update_window()
        )
        self.widgets["-SELECTOR-"].pack(side="right", padx=15)
        self.widgets["-SELECTOR-"].set(date_values[0])

        self.update_days(True)

        desc_box = ctk.CTkFrame(main, fg_color=BG_COLOR)
        desc_box.pack(fill='x')

        self.widgets["-IMAGE-"] = ctk.CTkLabel(desc_box, fg_color=BG_COLOR, text="", image=self.icon)
        self.widgets["-IMAGE-"].pack(side="left", padx=10)

        self.widgets["-DESC-"] = ctk.CTkLabel(
            desc_box, text="Desc", font=self.font_desc, fg_color=BG_COLOR, text_color=TEXT_COLOR
        )
        self.widgets["-DESC-"].pack(side="left")

        # Middle row: Temp, High/Low, Wind/Humidity
        mid = ctk.CTkFrame(main, fg_color=BG_COLOR)
        mid.pack(fill="x", expand=True, pady=10)

        # TEMP COLUMN
        temp_col = ctk.CTkFrame(mid, fg_color=BG_COLOR)
        temp_col.pack(side="left", expand=True)

        self.widgets["-TEMP-"] = ctk.CTkLabel(
            temp_col, text="00°", font=self.font_temp, fg_color=BG_COLOR, text_color=TEXT_COLOR
        )
        self.widgets["-TEMP-"].pack()

        self.widgets["-FEELS-"] = ctk.CTkLabel(
            temp_col, text="Feels Like:", font=self.font_feels, fg_color=BG_COLOR, text_color=TEXT_COLOR
        )
        self.widgets["-FEELS-"].pack()

        # HIGH/LOW COLUMN
        hl_col = ctk.CTkFrame(mid, fg_color=BG_COLOR)
        hl_col.pack(side="left", expand=True)

        self.widgets["-HIGH-"] = ctk.CTkLabel(
            hl_col, text="00", font=self.font_hl_val, fg_color=BG_COLOR, text_color=TEXT_COLOR
        )
        self.widgets["-HIGH-"].pack()
        ctk.CTkLabel(hl_col, text="High", font=self.font_hl_lbl, fg_color=BG_COLOR, text_color=TEXT_COLOR).pack()

        self.widgets["-LOW-"] = ctk.CTkLabel(
            hl_col, text="00", font=self.font_hl_val, fg_color=BG_COLOR, text_color=TEXT_COLOR
        )
        self.widgets["-LOW-"].pack()
        ctk.CTkLabel(hl_col, text="Low", font=self.font_hl_lbl, fg_color=BG_COLOR, text_color=TEXT_COLOR).pack()

        # VERTICAL SEPARATOR
        sep = ctk.CTkFrame(mid, fg_color=TEXT_COLOR, width=2)
        sep.pack(side="left", fill="y", padx=10)

        # WIND/HUMIDITY COLUMN
        wh_col = ctk.CTkFrame(mid, fg_color=BG_COLOR)
        wh_col.pack(side="left", expand=True)

        ctk.CTkLabel(wh_col, text="Wind", font=self.font_wh_lbl, fg_color=BG_COLOR, text_color=TEXT_COLOR).pack()
        self.widgets["-WIND-"] = ctk.CTkLabel(
            wh_col, text="00", font=self.font_wh_val, fg_color=BG_COLOR, text_color=TEXT_COLOR
        )
        self.widgets["-WIND-"].pack()

        ctk.CTkLabel(wh_col, text="Humidity", font=self.font_wh_lbl, fg_color=BG_COLOR, text_color=TEXT_COLOR).pack()
        self.widgets["-HUM-"] = ctk.CTkLabel(
            wh_col, text="00", font=self.font_wh_val, fg_color=BG_COLOR, text_color=TEXT_COLOR
        )
        self.widgets["-HUM-"].pack()

        # Bottom row: Date + Units checkbox
        bottom = ctk.CTkFrame(main, fg_color=BG_COLOR)
        bottom.pack(fill="x")

        self.widgets["-DATE-"] = ctk.CTkLabel(
            bottom, text="Date", font=self.font_date, fg_color=BG_COLOR, text_color=TEXT_COLOR
        )
        self.widgets["-DATE-"].pack(side="left", padx=10)

        self.widgets["-UNITS-"] = ctk.CTkCheckBox(
            bottom,
            text="C°",
            font=self.font_units,
            variable=self.units,
            fg_color=BG_COLOR,
            text_color=TEXT_COLOR,
            command=self.on_unit_changed
        )
        self.widgets["-UNITS-"].pack(side="right", padx=15, pady=5)

        self.widgets["-QUIT-"] = ctk.CTkButton(
            bottom, text="Quit", font=self.font_quit, fg_color=BG_COLOR, text_color=TEXT_COLOR, command=self.on_close
        )
        self.widgets["-QUIT-"].pack(side="right")

    def generate_image(self, url):
        if self.iconUrl == url:
            return self.icon

        self.iconUrl = url
        with urlopen(self.iconUrl) as u:
            data = u.read()

        image = Image.open(BytesIO(data))
        photo = ctk.CTkImage(light_image=image, dark_image=image, size=(50, 50))
        self.icon = photo
        return photo

    def update_window(self, event=None):
        index = self.update_days(False)

        currObj = weatherObj if index == 0 else weatherObj.forecast(index)

        temp = int(currObj.currentTemp())
        desc = currObj.description().title()

        self.widgets["-CITY-"].configure(text=f'{weatherObj.getCity()},{weatherObj.getState()}')
        self.widgets["-TEMP-"].configure(text=f"{temp}°")
        self.widgets["-HIGH-"].configure(text=f"{round(currObj.highTemp())}")
        self.widgets["-LOW-"].configure(text=f"{round(currObj.lowTemp())}")
        self.widgets["-FEELS-"].configure(text=f"Feels like: {round(currObj.feelsLike())}°")
        self.widgets["-WIND-"].configure(text=f"{round(currObj.windSpeed())} {currObj.getUnit()}")
        self.widgets["-HUM-"].configure(text=f"{currObj.humidity()}%")
        self.widgets["-DESC-"].configure(text=desc)
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

        temperature = round(temp if not self.units.get() else (temp * 9/5) + 32)
        # Default back to dynamic tuple color unless temperature threshold is met
        color = TEXT_COLOR
        if temperature >= 80:
            color = "red"
        elif temperature >= 70:
            color = "orange"
        elif temperature <= 45:
            color = "#03b6fc"
        elif temperature <= 30:
            color = "#0013bf"
        self.widgets["-TEMP-"].configure(text_color=color)

    def load_image_async(self, url):
        if self.iconUrl == url:
            return

        self.iconUrl = url
        thread = threading.Thread(target=self._download_image, args=(url,), daemon=True)
        thread.start()

    def _download_image(self, url):
        try:
            with urlopen(url) as u:
                data = u.read()

            image = Image.open(BytesIO(data))
            photo = ctk.CTkImage(light_image=image, dark_image=image, size=(50, 50))
            self.root.after(0, self._update_image_label, photo, url)
        except Exception as e:
            print(f"Image download failed: {e}")

    def _update_image_label(self, photo, url):
        if url != self.iconUrl:
            return
        self.icon = photo
        self.widgets["-IMAGE-"].configure(image=self.icon)

    def on_unit_changed(self):
        weatherObj.setUnit("metric" if self.units.get() else "imperial")
        weatherObj.refresh()
        self.update_window()

    def update_time(self):
        now = datetime.now()
        self.widgets["-DATE-"].configure(
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
            selector.configure(values=dates)
            self.date = datetime.today()

        values = selector.cget("values")
        index = values.index(selector.get()) if selector.get() in values else 0
        return index

    def schedule_update(self):
        weatherObj.refresh()
        self.update_window()
        self.root.after(180000, self.schedule_update)

    def dark_mode(self):
        ctk.set_appearance_mode("Dark")

    def light_mode(self):
        ctk.set_appearance_mode("Light")


ctkRoot = ctk.CTk()
app = WeatherApp(ctkRoot)
ctkRoot.mainloop()