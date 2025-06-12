import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
from geopy.distance import great_circle
import folium  # <- NUEVO
import requests
import time
from networkx.algorithms import approximation as approx
import gpxpy
import gpxpy.gpx
import geopandas as gpd
import csv
from pathlib import Path
#Token de locationiq
locationiq = "pk.d81a2970f82d6294a9d04107082be838"
#Token de POIs
POIs = "5b3ce3597851110001cf6248c78a74e4d1fd423588a0378499a42c6d"

def segundos_a_tiempo(segundos):
    """Convierte segundos a formato: HH:MM:SS o Dd HH:MM:SS si hay días"""
    segundos = int(round(segundos))
    dias = segundos // 86400
    tiempo = time.strftime('%Hh %Mm %Ss', time.gmtime(segundos % 86400))
    return f"{dias}d {tiempo}" if dias > 0 else tiempo


def obtener_coordenadas(ciudad):
    ciudad = ciudad.replace("#", "%23")
    url = f"https://us1.locationiq.com/v1/search?key={locationiq}&q={ciudad}&format=json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()[0]
        return float(data['lat']), float(data['lon'])
    else:
        return("Error al obtener las coordenadas", response.text)
        

def reverse_geocode(lat, lon):
    url = f"https://us1.locationiq.com/v1/reverse?key={locationiq}&lat={lat}&lon={lon}&format=json"
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.json().get('display_name')
    return "Error al obtener dirección"

def sugerencias(lon, lat):
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
            "category_ids": [ 596 ]
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

def ruta (place, coordenadas, mode = "drive", simple =False, soloIdaTiempo = False, idaVeulta = False):
    
    ox.settings.log_console = True
    ox.settings.use_cache = True
    ox.settings.cache_folder = Path("./osmnx_cache")
    
    def cache (place, mode):
        cache_file = f"{place}_{mode}.graphml"
        cache_path = ox.settings.cache_folder / cache_file
        
        if cache_path.exists():
            print("✅ Grafo encontrado en caché. Cargando...")
            return ox.load_graphml(cache_path)
        else:
            print("⏳ Descargando grafo (esto puede tomar unos segundos)...")
            G = ox.graph_from_place(place, network_type=mode)
            ox.save_graphml(G, filepath=cache_path)  # Guardar en caché
            return G
    
    def actualizar_grafo(ciudad, modo_transporte, fuerza_redescarga=False):
        if fuerza_redescarga:
            p = ox.settings.cache_folder / f"{ciudad}_{modo_transporte}.graphml"
            if p.exists(): p.unlink()
        return cache(ciudad, modo_transporte)
    
    def agregar_pesos_velocidad(G):
        """Añade 'speed_kph' y 'travel_time' (s) a cada arista"""
        G = ox.add_edge_speeds(G)
        G = ox.add_edge_travel_times(G)
        return G
    
    def get_shortest_path(G, origen, destino, peso='travel_time'):
        """Camino más rápido entre dos nodos usando 'travel_time'"""
        return nx.shortest_path(G, source=origen, target=destino, weight=peso)
    
    def resolver_tsp_velocidad(G, nodos, ciclo=True):
        """TSP por menor tiempo de viaje ('travel_time')"""
        # 1. Construir grafo métrico entre nodos clave
        metric_G = nx.Graph()
        for i in range(len(nodos)):
            for j in range(i+1, len(nodos)):
                u, v = nodos[i], nodos[j]
                try:
                    t = nx.shortest_path_length(G, u, v, weight='travel_time')
                    metric_G.add_edge(u, v, distance=t)
                except nx.NetworkXNoPath:
                    print(f"⚠️ No ruta {u}<->{v}")
        # 2. Resolver TSP
        tsp = approx.traveling_salesman_problem(metric_G, weight='distance', cycle=ciclo)
        # 3. Reconstruir ruta real
        ruta = []
        for k in range(len(tsp)-1):
            sub = nx.shortest_path(G, tsp[k], tsp[k+1], weight='travel_time')
            ruta.extend(sub[:-1])
        ruta.append(tsp[-1])
        return ruta

    def exportar_ruta_gpx(G, ruta, nombre="ruta"):
        gpx = gpxpy.gpx.GPX()
        track = gpxpy.gpx.GPXTrack(name=nombre)
        gpx.tracks.append(track)
        segment = gpxpy.gpx.GPXTrackSegment()
        track.segments.append(segment)

        for node in ruta:
            y, x = G.nodes[node]['y'], G.nodes[node]['x']
            segment.points.append(gpxpy.gpx.GPXTrackPoint(y, x))

        with open(f'{nombre}.gpx', 'w') as f:
            f.write(gpx.to_xml())
    
    def exportar_ruta_csv(G, ruta, nombre="ruta"):
        with open(f"{nombre}.csv", mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["latitud", "longitud"])
            for node in ruta:
                y, x = G.nodes[node]['y'], G.nodes[node]['x']
                writer.writerow([y, x])
    
    place = place
    mode = mode
    G = actualizar_grafo(place, mode)
    G = agregar_pesos_velocidad(G)
    
    nombres = [reverse_geocode(lat, lon) for lat, lon in coordenadas]
    
    nodos = [ox.distance.nearest_nodes(G, X=lon, Y=lat) for lat, lon in coordenadas]
    
    # 4. Elección de ruta: descomenta la opción que quieras
    try:
        # Ruta simple (solo ida) entre primer y último punto por menor tiempo
        if simple:
            ruta = get_shortest_path(G, nodos[0], nodos[-1])

        # Ruta TSP (solo ida) optimizada por tiempo
        if soloIdaTiempo:
            ruta = resolver_tsp_velocidad(G, nodos, ciclo=False)

        # Por defecto: TSP ida y vuelta por velocidad
        if idaVeulta:
            ruta = resolver_tsp_velocidad(G, nodos, ciclo=True)
    except:
        return "❌ Debes seleccionar un modo de ruta"    
    tiempo_total = sum(
        nx.shortest_path_length(G, ruta[i], ruta[i+1], weight='travel_time')
        for i in range(len(ruta)-1)
    )
    
    distancia_total = sum(G[ruta[i]][ruta[i+1]][0]['length'] for i in range(len(ruta)-1))
    
    lat_center = sum(lat for lat, lon in coordenadas)/len(coordenadas)
    
    lon_center = sum(lon for lat, lon in coordenadas)/len(coordenadas)
    
    mapa = folium.Map(location=[lat_center, lon_center], zoom_start=13)
    
    for u, v in zip(ruta[:-1], ruta[1:]):
        pu = (G.nodes[u]['y'], G.nodes[u]['x'])
        pv = (G.nodes[v]['y'], G.nodes[v]['x'])
        folium.PolyLine([pu, pv], color='red', weight=5).add_to(mapa)

    for (lat, lon), nombre in zip(coordenadas, nombres):
        folium.Marker([lat, lon], popup=nombre).add_to(mapa)
    mapa.save("mapa_personalizado.html")
    #ox.save_graphml(G, filepath="grafo_usado.graphml")
    exportar_ruta_gpx(G, ruta)
    exportar_ruta_csv(G, ruta)
    return {
        "tiempo_estimado": segundos_a_tiempo(tiempo_total),
        "distancia_km": f"{distancia_total/1000:.2f} km",
        "nodos_visitados": len(set(ruta)),
        "tipo_ruta": "Simple" if simple else "TSP ida" if soloIdaTiempo else "TSP ida y vuelta",
        
    }

#lat, lon = obtener_coordenadas("Carretera Turbaco - Arjona, Turbaco, Bolívar, Caribe, Colombia")


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

#print(rut)