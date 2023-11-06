import requests
# URL de una API de clima
url = "https://api.openweathermap.org/data/2.5/weather?units=metric&lang=es"
params = {
    "q": "Valencia,ESP",
    "appid": "yourapikey_here"
}
# Realizar una solicitud GET a la API
response = requests.get(url, params=params)
if response.status_code == 200:
    data = response.json()
    temperatura = data["main"]["temp"]
    descripcion = data["weather"][0]["description"]
    print(f"Temperatura: {temperatura}°C, Condición: {descripcion}")
else:
    print("Error al obtener datos del clima")
