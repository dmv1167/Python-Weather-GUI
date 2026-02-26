# Python Weather GUI

This application utilizes the OpenWeather API using the OneApi 3.0 system.
The first 1000 daily api calls are free, and this application is intended to use
less than that in 24 hours.

The application displays current temperature in both Fahrenheit and Celsius along with a description of the weather, 
accompanied by the appropriate icon to represent current conditions. Alongside this information is the date and time, as well as wind speed and humidity percentage.
High and low temps are available, as well as a drop-down menu allowing the user to review the weather up to a week into the future. The GUI automatically darkens after sunset, a time determined from API data as well.

# Installation

Simply execute WeatherApp.py after having installed the necessary packages from the included requirements.txt. This program was written with the intent to be displayed by a Raspberry Pi Zero 
with a 1024x600 LCD. Instructions for setting up drivers for your screen will be available from the manufacturer.
