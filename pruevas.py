import openrouteservice
import folium

def ruta_logistica_simple(origen, destino, vehiculo, api_key, nombre_mapa="ruta_mapa.html"):
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

    ruta = client.directions(
        coordinates=[origen, destino],
        profile=vehiculo,
        format="geojson"
    )

    segmento = ruta["features"][0]["properties"]["segments"][0]
    distancia_km = segmento["distance"] / 1000
    duracion_min = segmento["duration"] / 60

    print(f"🚗 Vehículo: {vehiculo}")
    print(f"📏 Distancia: {distancia_km:.2f} km")
    print(f"⏱️ Duración estimada: {duracion_min:.2f} minutos")

    # Mapa centrado entre origen y destino
    centro = [(origen[1] + destino[1]) / 2, (origen[0] + destino[0]) / 2]
    mapa = folium.Map(location=centro, zoom_start=7)

    coords_ruta = ruta["features"][0]["geometry"]["coordinates"]
    ruta_latlon = [[lat, lon] for lon, lat in coords_ruta]

    folium.PolyLine(
        ruta_latlon,
        color="blue",
        weight=5,
        tooltip=f"{distancia_km:.1f} km - {duracion_min:.1f} min"
    ).add_to(mapa)

    folium.Marker(location=[origen[1], origen[0]], tooltip="Origen").add_to(mapa)
    folium.Marker(location=[destino[1], destino[0]], tooltip="Destino").add_to(mapa)

    mapa.save(nombre_mapa)
    print(f"✅ Mapa guardado como {nombre_mapa}")

    return distancia_km, duracion_min

origen = [-74.08175, 4.60971]    # Bogotá
destino = [-75.56359, 6.24782]   # Medellín
vehiculo = "driving-car"
api_key = "5b3ce3597851110001cf6248c78a74e4d1fd423588a0378499a42c6d"

distancia, duracion = ruta_logistica_simple(origen, destino, vehiculo, api_key)
