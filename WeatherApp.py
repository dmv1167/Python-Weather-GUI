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
        self.day = True
        self.date = datetime.today()
        self.iconUrl = ""

        # StringVars for automatic UI binding
        self.city_var = ctk.StringVar(value="City")
        self.temp_var = ctk.StringVar(value="00°")
        self.feels_var = ctk.StringVar(value="Feels Like: --")
        self.desc_var = ctk.StringVar(value="")
        self.high_var = ctk.StringVar(value="00")
        self.low_var = ctk.StringVar(value="00")
        self.wind_var = ctk.StringVar(value="00")
        self.hum_var = ctk.StringVar(value="00%")
        self.date_var = ctk.StringVar(value="Date")
        self.units = ctk.BooleanVar(value=False)

        # Structured fonts
        self.fonts = {
            "title": ctk.CTkFont("Courier", size=50, weight="bold"),
            "temp": ctk.CTkFont("Courier", size=155, weight="bold"),
            "mid_val": ctk.CTkFont("Courier", size=40, weight="bold"),
            "mid_lbl": ctk.CTkFont("Courier", size=20),
            "footer": ctk.CTkFont("Courier", size=20),
        }

        self.build_layout()
        self.light_mode()
        self.schedule_update()
        self.update_time()

    def on_close(self):
        self.root.destroy()
        import sys
        sys.exit(0)

    def build_layout(self):
        self.root.configure(fg_color=BG_COLOR)

        main = ctk.CTkFrame(self.root, fg_color=BG_COLOR)
        main.pack(fill="both", expand=True, padx=15, pady=15)

        # Top Bar
        top = ctk.CTkFrame(main, fg_color=BG_COLOR)
        top.pack(fill='x')

        ctk.CTkLabel(top, textvariable=self.city_var, font=self.fonts["title"], fg_color=BG_COLOR, text_color=TEXT_COLOR).pack(side="left")

        self.day_selector = ctk.CTkSegmentedButton(
            top, values=["Today"], command=lambda choice: self.update_window()
        )
        self.day_selector.pack(side="right")

        # Weather Summary
        desc_box = ctk.CTkFrame(main, fg_color=BG_COLOR)
        desc_box.pack(fill='x', pady=5)

        self.img_label = ctk.CTkLabel(desc_box, fg_color=BG_COLOR, text="")
        self.img_label.pack(side="left", padx=5)

        ctk.CTkLabel(desc_box, textvariable=self.desc_var, font=self.fonts["mid_lbl"], fg_color=BG_COLOR, text_color=TEXT_COLOR).pack(side="left")

        # Mid Content Frame
        mid = ctk.CTkFrame(main, fg_color=BG_COLOR)
        mid.pack(fill="both", expand=True)

        # Temp Block
        temp_col = ctk.CTkFrame(mid, fg_color=BG_COLOR)
        temp_col.pack(side="left", expand=True)

        self.temp_label = ctk.CTkLabel(temp_col, textvariable=self.temp_var, font=self.fonts["temp"], fg_color=BG_COLOR, text_color=TEXT_COLOR)
        self.temp_label.pack()
        ctk.CTkLabel(temp_col, textvariable=self.feels_var, font=self.fonts["footer"], fg_color=BG_COLOR, text_color=TEXT_COLOR).pack()

        # High/Low Block
        hl_col = ctk.CTkFrame(mid, fg_color=BG_COLOR)
        hl_col.pack(side="left", expand=True)

        ctk.CTkLabel(hl_col, textvariable=self.high_var, font=self.fonts["mid_val"], fg_color=BG_COLOR, text_color=TEXT_COLOR).pack()
        ctk.CTkLabel(hl_col, text="High", font=self.fonts["mid_lbl"], fg_color=BG_COLOR, text_color=TEXT_COLOR).pack()
        ctk.CTkLabel(hl_col, textvariable=self.low_var, font=self.fonts["mid_val"], fg_color=BG_COLOR, text_color=TEXT_COLOR).pack()
        ctk.CTkLabel(hl_col, text="Low", font=self.fonts["mid_lbl"], fg_color=BG_COLOR, text_color=TEXT_COLOR).pack()

        # Separator Line
        ctk.CTkFrame(mid, fg_color=TEXT_COLOR, width=2).pack(side="left", fill="y", padx=15)

        # Wind/Humidity Block
        wh_col = ctk.CTkFrame(mid, fg_color=BG_COLOR)
        wh_col.pack(side="left", expand=True)

        ctk.CTkLabel(wh_col, text="Wind", font=self.fonts["mid_lbl"], fg_color=BG_COLOR, text_color=TEXT_COLOR).pack()
        ctk.CTkLabel(wh_col, textvariable=self.wind_var, font=self.fonts["mid_val"], fg_color=BG_COLOR, text_color=TEXT_COLOR).pack()
        ctk.CTkLabel(wh_col, text="Humidity", font=self.fonts["mid_lbl"], fg_color=BG_COLOR, text_color=TEXT_COLOR).pack()
        ctk.CTkLabel(wh_col, textvariable=self.hum_var, font=self.fonts["mid_val"], fg_color=BG_COLOR, text_color=TEXT_COLOR).pack()

        # Bottom Bar
        bottom = ctk.CTkFrame(main, fg_color=BG_COLOR)
        bottom.pack(fill="x")

        ctk.CTkLabel(bottom, textvariable=self.date_var, font=self.fonts["footer"], fg_color=BG_COLOR, text_color=TEXT_COLOR).pack(side="left")

        # CTkSwitch replaces CTkCheckBox
        ctk.CTkSwitch(
            bottom, text="°C", font=self.fonts["footer"], variable=self.units,
            fg_color=BG_COLOR, text_color=TEXT_COLOR, command=self.on_unit_changed
        ).pack(side="right", padx=10)

        ctk.CTkButton(
            bottom, text="Quit", font=self.fonts["footer"], fg_color=BG_COLOR,
            text_color=TEXT_COLOR, command=self.on_close, width=60
        ).pack(side="right")

    def update_window(self, event=None):
        index = self.update_days(False)

        currObj = weatherObj if index == 0 else weatherObj.forecast(index)

        temp = int(currObj.currentTemp())
        desc = currObj.description().title()

        # Update StringVars
        self.city_var.set(f"{weatherObj.getCity()},{weatherObj.getState()}")
        self.temp_var.set(f"{temp}°")
        self.high_var.set(f"{round(currObj.highTemp())}")
        self.low_var.set(f"{round(currObj.lowTemp())}")
        self.feels_var.set(f"Feels like: {round(currObj.feelsLike())}°")
        self.wind_var.set(f"{round(currObj.windSpeed())} {currObj.getUnit()}")
        self.hum_var.set(f"{currObj.humidity()}%")
        self.desc_var.set(desc)

        self.load_image_async(currObj.icon())

        # Mode switching
        sunset = weatherObj.sunset()
        sunrise = weatherObj.sunrise()
        current_time = time.time()
        if sunset > current_time >= sunrise and not self.day:
            self.day = True
            self.light_mode()
        elif (current_time < sunrise or current_time >= sunset) and self.day:
            self.day = False
            self.dark_mode()

        # Dynamic temperature color coding
        temperature = round(temp if not self.units.get() else (temp * 9 / 5) + 32)
        color = TEXT_COLOR
        if temperature >= 80:
            color = "red"
        elif temperature >= 70:
            color = "orange"
        elif temperature <= 45:
            color = "#03b6fc"
        elif temperature <= 30:
            color = "#0013bf"

        self.temp_label.configure(text_color=color)

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
        self.img_label.configure(image=self.icon)

    def on_unit_changed(self):
        weatherObj.setUnit("metric" if self.units.get() else "imperial")
        weatherObj.refresh()
        self.update_window()

    def update_time(self):
        now = datetime.now()
        self.date_var.set(
            f'{now.strftime("%A, %B")} {suffix(now.day)} | {now.strftime("%I:%M %p")}'
        )
        self.root.after(ms_until_next_minute(), self.update_time)

    def update_days(self, force: bool):
        if force or self.date != datetime.today():
            now = datetime.now()
            days = [now + timedelta(days=i) for i in range(DAYCOUNT)]
            dates = [d.strftime('%A, %m/%d') for d in days]
            dates[0] = "Today"
            self.day_selector.configure(values=dates)
            self.date = datetime.today()

        values = self.day_selector.cget("values")
        selected = self.day_selector.get()
        return values.index(selected) if selected in values else 0

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