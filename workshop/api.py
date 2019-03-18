import os
import configparser
import requests

# response = requests.get('https://httpbin.org/ip')

# print('Your IP is {0}'.format(response.json()['origin']))

config = configparser.ConfigParser()

config.read("config.ini")

key = config["api-fxpractice.oanda.com"]["authtoken"]

headers = {"Content-Type": "application/json",
           "Authorization": "Bearer {0}".format(key)}

payload = {"count": "6", "price": "M", "granularity": "S5"}

url = "https://api-fxpractice.oanda.com/v3/instruments/EUR_USD/candles?"

r = requests.get(url, headers=headers, params=payload)

r.json()
