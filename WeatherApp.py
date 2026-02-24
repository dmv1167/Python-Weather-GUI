"""
Author: Dominic Vinciulla
Tkinter port of open_weather.py
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import time
from dotenv import dotenv_values
from WeatherData import WeatherDataObj
# from PIL import Image, ImageTk
# import io

values = dotenv_values(".env")
DAYCOUNT = 7
weatherObj = WeatherDataObj(values)

def suffix(myDate: int) -> str:
    """Returns day of month with correct suffix"""
    date_suffix = ['th', 'st', 'nd', 'rd']
    if myDate % 10 in [1,2,3] and myDate not in [11,12,13]:
        return str(myDate) + date_suffix[myDate % 10]
    return str(myDate) + date_suffix[0]

class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("480x320")
        self.root.overrideredirect(True)
        self.root.configure(bg="#1c2b4a")
        self.widgets = {}
        self.last_index = None
        self.day = True

        self.build_layout()

        # Bind dropdown selection to update immediately
        self.widgets["-SELECTOR-"].bind("<<ComboboxSelected>>", self.on_day_selected)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Start the periodic 2-minute update loop
        self.schedule_update()

    def on_close(self):
        self.root.destroy()
        import sys
        sys.exit(0)

    def build_layout(self):
        bg = self.root["bg"]

        main = tk.Frame(self.root, bg=bg)
        main.pack(fill="both", expand=True)

        # Top row: City + Icon + Day selector
        top = tk.Frame(main, bg=bg)
        top.pack(fill="x", pady=5)

        self.widgets["-CITY-"] = tk.Label(top, text="City", font=("Courier", 30, "bold"), bg=bg, fg="white")
        self.widgets["-CITY-"].pack(side="left")

        self.widgets["-IMAGE-"] = tk.Label(top, bg=bg)
        self.widgets["-IMAGE-"].pack(side="left", padx=10)

        self.widgets["-SELECTOR-"] = ttk.Combobox(top, state="readonly")
        self.widgets["-SELECTOR-"].pack(side="right", padx=5)
        self.widgets["-SELECTOR-"]["values"] = [datetime.now().strftime('%A, %m/%d')]

        self.widgets["-DESC-"] = tk.Label(main, text="Desc", font=("Courier", 10), bg=bg, fg="white")
        self.widgets["-DESC-"].pack()

        # Middle row: Temp, High/Low, Wind/Humidity
        mid = tk.Frame(main, bg=bg)
        mid.pack(fill="x", expand=True, pady=10)

        # TEMP COLUMN
        temp_col = tk.Frame(mid, bg=bg)
        temp_col.pack(side="left", expand=True)

        self.widgets["-TEMP-"] = tk.Label(temp_col, text="00°", font=("Courier", 55, "bold"), bg=bg, fg="white")
        self.widgets["-TEMP-"].pack()

        self.widgets["-FEELS-"] = tk.Label(temp_col, text="Feels Like:", font=("Courier", 10), bg=bg, fg="white")
        self.widgets["-FEELS-"].pack()

        # HIGH/LOW COLUMN
        hl_col = tk.Frame(mid, bg=bg)
        hl_col.pack(side="left", expand=True)

        self.widgets["-HIGH-"] = tk.Label(hl_col, text="00", font=("Courier", 20, "bold"), bg=bg, fg="white")
        self.widgets["-HIGH-"].pack()
        tk.Label(hl_col, text="High", font=("Courier", 10), bg=bg, fg="white").pack()

        self.widgets["-LOW-"] = tk.Label(hl_col, text="00", font=("Courier", 20, "bold"), bg=bg, fg="white")
        self.widgets["-LOW-"].pack()
        tk.Label(hl_col, text="Low", font=("Courier", 10), bg=bg, fg="white").pack()

        # VERTICAL SEPARATOR
        sep = tk.Frame(mid, bg="white", width=2)
        sep.pack(side="left", fill="y", padx=10)

        # WIND/HUMIDITY COLUMN
        wh_col = tk.Frame(mid, bg=bg)
        wh_col.pack(side="left", expand=True)

        tk.Label(wh_col, text="Wind", font=("Courier", 20), bg=bg, fg="white").pack()
        self.widgets["-WIND-"] = tk.Label(wh_col, text="00", font=("Courier", 20, "bold"), bg=bg, fg="white")
        self.widgets["-WIND-"].pack()

        tk.Label(wh_col, text="Humidity", font=("Courier", 20), bg=bg, fg="white").pack()
        self.widgets["-HUM-"] = tk.Label(wh_col, text="00", font=("Courier", 20, "bold"), bg=bg, fg="white")
        self.widgets["-HUM-"].pack()

        # Bottom row: Date + Units checkbox
        bottom = tk.Frame(main, bg=bg)
        bottom.pack(fill="x")

        self.widgets["-DATE-"] = tk.Label(bottom, text="Date", font=("Courier", 10), bg=bg, fg="white")
        self.widgets["-DATE-"].pack(side="left")

        self.units = tk.BooleanVar()
        self.widgets["-UNITS-"] = tk.Checkbutton(bottom, text="C°", variable=self.units, bg=bg, fg="white")
        self.widgets["-UNITS-"].pack(side="right")

    def update_window(self, force=False):
        now = datetime.now()
        days = [now + timedelta(days=i) for i in range(DAYCOUNT)]
        dates = [d.strftime('%A, %m/%d') for d in days]

        # Update dropdown values
        selector = self.widgets["-SELECTOR-"]
        selector["values"] = dates
        index = selector.current() if selector.get() else 0

        # Skip if same day and not forced
        if index == self.last_index and not force:
            return
        self.last_index = index

        forecast = weatherObj.forecast(index)
        temp = int(forecast.temp())
        feels = int(forecast.feelsLike())
        hum = forecast.humidity()
        wind = int(forecast.windSpeed())
        desc = forecast.description()
        icon_bytes = forecast.icon()

        self.widgets["-TEMP-"].config(text=f"{temp}°")
        self.widgets["-FEELS-"].config(text=f"Feels like: {feels}°")
        self.widgets["-WIND-"].config(text=f"{wind} mph")
        self.widgets["-HUM-"].config(text=f"{hum}%")
        self.widgets["-DESC-"].config(text=desc)
        self.widgets["-DATE-"].config(
            text=now.strftime("%A, %B ") + suffix(now.day) + now.strftime(" | %I:%M %p")
        )

        # Temperature color logic
        temperature = temp if not self.units.get() else (temp * 9/5) + 32
        color = "white"
        if temperature >= 80: color = "red"
        elif temperature >= 70: color = "orange"
        elif temperature <= 45: color = "#03b6fc"
        elif temperature <= 30: color = "#0013bf"
        self.widgets["-TEMP-"].config(fg=color)

        # TODO: theme switching based on sunrise/sunset
        # if sunset > time.time() >= sunrise and not self.day:
        #     self.day = True
        #     self.set_theme("#1c2b4a")
        # elif (time.time() < sunrise or time.time() >= sunset) and self.day:
        #     self.day = False
        #     self.set_theme("#0d1026")

    def on_day_selected(self, event=None):
        self.update_window(force=True)

    def schedule_update(self):
        self.update_window()
        self.root.after(120000, self.schedule_update)  # 2 minutes

    def set_theme(self, bg):
        self.root.configure(bg=bg)
        for w in self.widgets.values():
            try:
                w.config(bg=bg)
            except:
                pass

# ---------------- Run App ----------------
root = tk.Tk()
app = WeatherApp(root)
root.mainloop()