from urllib.request import urlopen, urlretrieve
from datetime import datetime
from json import loads

def getPage(url: str):
    """
    Parses api call into json dictionaries
    :param url: url to be accessed
    :return: resulting dictionary from json parsing
    """
    try:
        weatherPage = urlopen(url)
    except Exception as e:
        with open('log.txt', 'a+') as file:
            now = datetime.now().strftime('[%m/%d/%Y %I:%M %p]')
            file.write(f'\n{now}\n{str(e)}\n')
        return None
    else:
        return loads(weatherPage.read())

class ForecastData:
    def __init__(self, data, unit):
        self.data = data
        self.unit = unit

    def temp(self) -> float:
        return self.data['temp']['day']

    def feelsLike(self) -> float:
        return self.data['feels_like']['day']

    def humidity(self) -> int:
        return self.data['humidity']

    def windSpeed(self) -> float:
        return self.data['wind_speed']

    def icon(self):
        return r'https://openweathermap.org/payload/api/media/file/' + self.data['weather'][0]['icon'] + '@2x.png'

    def description(self) -> str:
        return self.data['weather'][0]['description']

    def getUnit(self) -> str:
        return self.unit

class WeatherDataObj:
    def __init__(self, headers: dict):
        self.headers = headers
        self.headers["UNITS"] = "imperial"
        self.url = ""
        self.buildUrl()
        self.latest = getPage(self.url)
        self.speedUnit = 'mph'
        self.city = ""
        self.state = ""
        print(self.latest)

    def buildUrl(self):
        self.url = f'https://api.openweathermap.org/data/3.0/onecall?'
        for header in self.headers:
            self.url += f'&{header.lower()}={self.headers[header]}'

    def refresh(self):
        self.latest = getPage(self.url)

    def setUnit(self, unit: str):
        self.headers["UNITS"] = unit
        if unit == "imperial":
            self.speedUnit = "mph"
        else:
            self.speedUnit = "kmh"

    def getUnit(self) -> str:
        return self.speedUnit

    def currentTemp(self) -> float:
        return self.latest['current']['temp']

    def feelsLike(self) -> float:
        return self.latest['current']['feels_like']

    def humidity(self) -> int:
        return self.latest['current']['humidity']

    def windSpeed(self) -> float:
        return self.latest['current']['wind_speed']

    def icon(self) -> str:
        return r'https://openweathermap.org/payload/api/media/file/' + self.latest['current']['weather'][0]['icon'] + '@2x.png'

    def description(self) -> str:
        return self.latest['current']['weather'][0]['description']

    def sunset(self) -> int:
        return self.latest['current']['sunset']

    def sunrise(self) -> int:
        return self.latest['current']['sunrise']

    def forecast(self, index: int):
        return ForecastData(self.latest['daily'][index], self.speedUnit)

    def generateCity(self):
        page = getPage(f'http://api.openweathermap.org/geo/1.0/reverse?lat={self.headers["LAT"]}&lon={self.headers["LON"]}&limit=1&appid={self.headers["APPID"]}')
        self.city = page[0]["name"]
        self.state = page[0]["state"]

    def getCity(self):
        return self.city

    def getState(self):
        return self.state
