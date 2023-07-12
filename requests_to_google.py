import requests
from bs4 import BeautifulSoup

CITY = "Kazan"

URL = "https://www.google.com/search?q="+"weather"+CITY


def get_weather_information():
    try:
        response = requests.get(URL)
    except:
        print('Пожалуйста, проверте подключение к интернету')
        return None, None
    if response.status_code != 200:
        print('Сервис не отвечает')
        return None, None
    html = response.content
    soup = BeautifulSoup(html, 'html.parser')
    temperature = soup.find('div', attrs={'class': 'BNeawe iBp4i AP7Wnd'}).text[:-2]
    weather_data = soup.find('div', attrs={'class': 'BNeawe tAd8D AP7Wnd'}).text.split('\n')
    sky = weather_data[1]

    return temperature, sky
