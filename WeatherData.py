from urllib.request import urlopen
from json import loads
import logging


logging.basicConfig(filename='log.txt',
                    filemode='a',
                    format='[%(asctime)s] %(levelname)s: %(message)s',
                    level=logging.INFO
)

def check_field_not_none(field_name):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if getattr(self, field_name, None) is None:
                logging.error(f"Attribute '{field_name}' cannot be None before running {func.__name__}")
                return None
            return func(self, *args, **kwargs)
        return wrapper
    return decorator

def getPage(url: str):
    """
    Parses api call into JSON dictionaries
    :param url: url to be accessed
    :return: resulting dictionary from JSON parsing
    """
    try:
        weatherPage = urlopen(url)
    except Exception as e:
        logging.error(f"Error: {e}")
        return None
    else:
        return loads(weatherPage.read())

class ForecastData:
    def __init__(self, data, unit):
        self.data = data
        self.speedUnit = unit

    @check_field_not_none('data')
    def currentTemp(self) -> float:
        return self.data['temp']['day']

    @check_field_not_none('data')
    def highTemp(self) -> float:
        return self.data['temp']['max']

    @check_field_not_none('data')
    def lowTemp(self) -> float:
        return self.data['temp']['min']

    @check_field_not_none('data')
    def feelsLike(self) -> float:
        return self.data['feels_like']['day']

    @check_field_not_none('data')
    def humidity(self) -> int:
        return self.data['humidity']

    @check_field_not_none('data')
    def windSpeed(self) -> float:
        return self.data['wind_speed'] * (1 if self.speedUnit == 'mph' else 3.6)

    @check_field_not_none('data')
    def iconCode(self) -> str:
        return self.data['weather'][0]['icon']

    def icon(self):
        return f'https://openweathermap.org/payload/api/media/file/{self.iconCode()}.png'

    @check_field_not_none('data')
    def description(self) -> str:
        return self.data['weather'][0]['description']

    @check_field_not_none('speedUnit')
    def getUnit(self) -> str:
        return self.speedUnit

class WeatherDataObj:
    def __init__(self, headers: dict, city: str, state: str):
        self.headers = headers
        self.headers["UNITS"] = "imperial"
        self.url = ""
        self.buildUrl()
        self.data = getPage(self.url)
        self.speedUnit = 'mph'
        self.city = city
        self.state = state
        if not city or not state:
            self.generateCity()

    def buildUrl(self):
        self.url = f'https://api.openweathermap.org/data/3.0/onecall?'
        for header in self.headers:
            self.url += f'&{header.lower()}={self.headers[header]}'

    def refresh(self):
        self.buildUrl()
        data = getPage(self.url)
        if data is None:
            logging.error("Error: Could not refresh data")
            return

        self.data = getPage(self.url)

    def setUnit(self, unit: str):
        self.headers["UNITS"] = unit
        self.speedUnit = "mph" if unit == "imperial" else "kmh"

    @check_field_not_none('speedUnit')
    def getUnit(self) -> str:
        return self.speedUnit

    @check_field_not_none('data')
    def currentTemp(self) -> float:
        return self.data['current']['temp']

    @check_field_not_none('data')
    def highTemp(self) -> float:
        return self.data['daily'][0]['temp']['max']

    @check_field_not_none('data')
    def lowTemp(self) -> float:
        return self.data['daily'][0]['temp']['min']

    @check_field_not_none('data')
    def feelsLike(self) -> float:
        return self.data['current']['feels_like']

    @check_field_not_none('data')
    def humidity(self) -> int:
        return self.data['current']['humidity']

    @check_field_not_none('data')
    def windSpeed(self) -> float:
        return self.data['current']['wind_speed'] * (1 if self.speedUnit == 'mph' else 3.6)

    @check_field_not_none('data')
    def iconCode(self) -> str:
        return self.data['current']['weather'][0]['icon']

    def icon(self) -> str:
        return f'https://openweathermap.org/payload/api/media/file/{self.iconCode()}.png'

    @check_field_not_none('data')
    def description(self) -> str:
        return self.data['current']['weather'][0]['description']

    @check_field_not_none('data')
    def sunset(self) -> int:
        return self.data['current']['sunset']

    @check_field_not_none('data')
    def sunrise(self) -> int:
        return self.data['current']['sunrise']

    @check_field_not_none('data')
    def forecast(self, index: int):
        return ForecastData(self.data['daily'][index], self.speedUnit)

    def generateCity(self):
        page = getPage(f'http://api.openweathermap.org/geo/1.0/reverse?lat={self.headers["LAT"]}&lon={self.headers["LON"]}&limit=3&appid={self.headers["APPID"]}')
        self.city = page[0]["name"]
        self.state = page[0]["state"]

    def getCity(self):
        return self.city

    def getState(self):
        return self.state
