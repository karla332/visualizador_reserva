import streamlit as st
import geopandas as gpd
import folium
import rasterio
from streamlit_folium import st_folium

st.set_page_config(layout="wide")
st.title("🌿 Visualizador Ambiental: Reserva Nacional Alerce Costero")

# 1. Cargar datos vectoriales
try:
    reserva = gpd.read_file('data/areas_protegidas.gpkg').to_crs(epsg=4326)
    rios = gpd.read_file('data/rios.geojson').to_crs(epsg=4326)
    especies = gpd.read_file('data/especies.gpkg').to_crs(epsg=4326)
except Exception as e:
    st.error(f"Error cargando archivos: {e}")
    st.stop()

# 2. Mapa base centrado
centro = [reserva.geometry.centroid.y.mean(), reserva.geometry.centroid.x.mean()]
m = folium.Map(location=centro, zoom_start=13, tiles="CartoDB positron")

# 3. Carga del DEM (Raster)
try:
    with rasterio.open('data/DME_AREAS_PROTEGIDAS.tif') as src:
        bounds = src.bounds
        folium.raster_layers.ImageOverlay(
            image=src.read(1),
            bounds=[[bounds.bottom, bounds.left], [bounds.top, bounds.right]],
            name="Relieve (DEM)",
            opacity=0.6
        ).add_to(m)
except Exception as e:
    st.sidebar.warning(f"No se pudo cargar el DEM: {e}")

# 4. Crear grupos de capas
grupo_reserva = folium.FeatureGroup(name="Reserva").add_to(m)
grupo_rios = folium.FeatureGroup(name="Red Hídrica").add_to(m)
grupo_especies = folium.FeatureGroup(name="Biodiversidad").add_to(m)

# 5. Dibujar capas
folium.GeoJson(reserva, style_function=lambda x: {'fillColor': 'green', 'color': 'black', 'weight': 3}).add_to(grupo_reserva)

folium.GeoJson(rios, style_function=lambda x: {'color': 'white', 'weight': 6, 'opacity': 0.8}).add_to(grupo_rios)
folium.GeoJson(rios, style_function=lambda x: {'color': '#00BFFF', 'weight': 3, 'opacity': 1.0}).add_to(grupo_rios)

# Especies con colores únicos
for _, row in especies.iterrows():
    if row.geometry:
        nombre = str(row.get('common_name', 'Especie'))
        url_foto = row.get('image_url', '')
        url_web = row.get('url', '#')
        
        if 'Ranita' in nombre: color = 'red'
        elif 'Alerce' in nombre: color = 'green'
        elif 'Chucao' in nombre: color = 'brown'
        elif 'Zorro' in nombre: color = 'yellow'
        else: color = 'purple'

        popup_html = f"""
        <div style="width: 200px; font-family: sans-serif;">
            <h4 style="margin: 0;">{nombre}</h4>
            <a href="{url_foto}" target="_blank"><img src="{url_foto}" style="width:100%; border-radius: 8px;"></a>
            <br><br><a href="{url_web}" target="_blank">Ver detalles</a>
        </div>
        """
        folium.CircleMarker([row.geometry.y, row.geometry.x], radius=8, color=color, fill=True, fill_color=color, popup=folium.Popup(popup_html, max_width=250)).add_to(grupo_especies)

# 6. Panel de capas
folium.LayerControl(collapsed=False).add_to(m)
st_folium(m, width=900, height=600)
        
        # Lógica de colores según especie
        if 'Ranita' in nombre:
            color = 'orange'
        elif 'Alerce' in nombre:
            color = 'green'
        elif 'Chucao' in nombre:
            color = 'brown'
        else:
            color = 'gray'
        
        # Estructura del Popup profesional con imagen
        popup_html = f"""
        <div style="width: 220px;">
            <h4 style="margin: 0; color: #333;">{nombre}</h4>
            <img src="{row['image_url']}" style="width:100%; border-radius: 8px; margin-top: 5px; border: 1px solid #ccc;">
            <br><br>
            <a href="{row['url']}" target="_blank" style="text-decoration: none; color: blue;">Ver en iNaturalist</a>
        </div>
        """
        
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=7, 
            color=color, 
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=250)
        ).add_to(m)

# Mostrar el mapa final en Streamlit
st_folium(m, width=900, height=500)
