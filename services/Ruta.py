import requests
import time
import geopandas as gpd
import csv
from pathlib import Path
import openrouteservice
import folium
import json
import os
#Token de locationiq
locationiq = "pk.d81a2970f82d6294a9d04107082be838"
#Token de POIs
POIs = "5b3ce3597851110001cf6248c78a74e4d1fd423588a0378499a42c6d"

def minutos_a_tiempo(Minutos):
    """Convierte minutos a HHh MMm SSs"""
    segundos = int(round(Minutos * 60))
    dias = segundos // 86400
    tiempo = time.strftime('%Hh %Mm %Ss', time.gmtime(segundos % 86400))
    return f"{dias}d {tiempo}" if dias > 0 else tiempo


def obtener_coordenadas(ciudad):
    ciudad = ciudad.replace("#", "%23")
    url = f"https://us1.locationiq.com/v1/search?key={locationiq}&q={ciudad}&format=json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()[0]
        return float(data['lon']), float(data['lat'])
    else:
        return("Error al obtener las coordenadas", response.text)
        

def reverse_geocode(lat, lon):
    url = f"https://us1.locationiq.com/v1/reverse?key={locationiq}&lat={lat}&lon={lon}&format=json"
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.json().get('display_name')
    return "Error al obtener dirección"

def sugerencias(lon, lat, categoria = 596):
    url = "https://api.openrouteservice.org/pois"

    headers = {
        "Authorization": POIs,
        "Content-Type": "application/json"
    }
    body = {
        "request": "pois",
        "geometry": {
            "geojson": {
                "type": "Point",
                "coordinates": [lon, lat]
            },
            "buffer": 1000
        },
        "filters": {
            "category_ids": [ categoria ]
        }
    }

    response = requests.post(url, headers=headers, json=body)
    
    if response.status_code == 200:
        info = []
        data = response.json()
        features = data.get("features", [])
        encontrados = len(features)
        #open("devuelve.json", "w", encoding="utf-8").write(json.dumps(data, indent=4, ensure_ascii=False))
        for f  in features:
            coords = f["geometry"]["coordinates"]
            lon = coords[0]
            lat = coords[1]
            info.append((lon, lat))
        return info, encontrados
    else:
        print(f"Error {response.status_code}: {response.text}")

def ruta_logistica_simple(origen, destino, vehiculo, api_key, nombre_mapa="ruta_mapa.html", evitar=None, usar_elevacion=True, instrucciones=True):
    """
    Calcula una ruta logística simple entre dos coordenadas y genera un mapa interactivo.

    Parámetros:
    - origen:   [lon, lat] de inicio
    - destino:  [lon, lat] de fin
    - vehiculo: perfil de ORS (ej: 'driving-car', 'truck', 'cycling-regular')
    - api_key:  tu clave de API de OpenRouteService
    - nombre_mapa: nombre del archivo HTML que se generará

    Retorna:
    - distancia_km: distancia en kilómetros
    - duracion_min: duración estimada en minutos
    - mapa guardado como archivo HTML
    """
    client = openrouteservice.Client(key=api_key)

# ↓ Ya no pongas esto ↓
# opciones["profile_params"] = {
#     "weightings": {
#         "speed": {
#             "type": "function",
#             "value": [[0, 30], [1000000, 90]]
#         }
#     }
# }
    opciones = {}
    if evitar:
        opciones["avoid_features"] = evitar
        
    ruta = client.directions(
        coordinates=[origen, destino],
        profile=vehiculo,
        format="geojson",
        elevation=usar_elevacion,
        instructions=instrucciones,
        extra_info=["waytype"],
        options=opciones
    )

    props = ruta["features"][0]["properties"]
    resumen = props["summary"]
    
    distancia_km = resumen["distance"] / 1000
    duracion_min = resumen["duration"] / 60
    ascenso = resumen.get("ascent", 0)
    descenso = resumen.get("descent", 0)

    print(f"📏 Distancia: {distancia_km:.2f} km")
    print(f"⏱️ Duración estimada: {duracion_min:.2f} minutos")
    print(f"📈 Ascenso: {ascenso:.2f} m")
    print(f"📉 Descenso: {descenso:.2f} m")

    # Mapa centrado entre origen y destino
    centro = [(origen[1] + destino[1]) / 2, (origen[0] + destino[0]) / 2]
    mapa = folium.Map(location=centro, zoom_start=7)

    coords_ruta = ruta["features"][0]["geometry"]["coordinates"]
    ruta_latlon = [[lat, lon] for lon, lat, *_ in coords_ruta]

    folium.PolyLine(
        ruta_latlon,
        color="blue",
        weight=5,
        tooltip=f"{distancia_km:.1f} km - {duracion_min:.1f} min"
    ).add_to(mapa)

    folium.Marker(location=[origen[1], origen[0]], tooltip=f"Origen: inicio - {reverse_geocode(origen[1], origen[0])}").add_to(mapa)
    folium.Marker(location=[destino[1], destino[0]], tooltip=f"Destino: destino - {reverse_geocode(destino[1], destino[0])}").add_to(mapa)

    # Asegura que la carpeta templates/Optimizacion-de-rutas exista
    ruta_templates = os.path.join(os.getcwd(), "templates", "Optimizacion-de-rutas", "temp")
    os.makedirs(ruta_templates, exist_ok=True)
    nombre_mapa = os.path.join(ruta_templates, nombre_mapa)
    html = os.path.basename(nombre_mapa)

    mapa.save(nombre_mapa)
    print(f"✅ Mapa guardado como {nombre_mapa}")

    return distancia_km, duracion_min, html, ascenso, descenso
#info2, encontrados = sugerencias(lon, lat)
#print(f"Total de POIs encontrados: {encontrados}")
#print(info2)
#for i in info2:
    #print("--------------------------------")
    #time.sleep(1)  # Para no saturar la API
    #print(reverse_geocode(i[1], i[0]))

#coordenadas = [
    #(4.677173, -74.142900),
    #(4.677824, -74.123845),
    #(4.662733, -74.103014),
    #(4.638812, -74.094944),
    #(4.647631, -74.062284),
    #(4.657138, -74.058831),
    #(4.664510, -74.052232)
#]

#rut = ruta("Bogotá, Colombia", coordenadas, mode="drive", simple=False, soloIdaTiempo=False, idaVeulta=True)
