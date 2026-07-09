import streamlit as st
import geopandas as gpd
import folium
from folium.plugins import MeasureControl
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from streamlit_folium import st_folium
import os

st.set_page_config(layout="wide")
st.title("🌿 Visualizador Ambiental: Reserva Nacional Alerce Costero")

# 1. Carga de datos
def load_gpkg(path):
    if not os.path.exists(path):
        st.error(f"Archivo no encontrado: {path}")
        st.stop()
    return gpd.read_file(path).to_crs(epsg=4326)

try:
    reserva = load_gpkg('data/areas_protegidas.gpkg')
    rios = load_gpkg('data/rios.gpkg')
    especies = load_gpkg('data/especies.gpkg').dropna(subset=['common_name'])
except Exception as e:
    st.error(f"Error cargando datos: {e}")
    st.stop()

# 2. Mapa: Iniciamos con OpenStreetMap (más estable)
m = folium.Map(location=[reserva.geometry.centroid.y.mean(), reserva.geometry.centroid.x.mean()], zoom_start=13)

# 3. Capas
folium.GeoJson(reserva, name="Reserva", style_function=lambda x: {'color': '#004d00', 'weight': 3, 'fill': False}).add_to(m)
folium.GeoJson(rios, name="Ríos", style_function=lambda x: {'color': '#00BFFF', 'weight': 2}).add_to(m)

for _, row in especies.iterrows():
    nombre = str(row.get('common_name', 'Especie'))
    color = '#FF1493' if 'Alerce' in nombre else ('purple' if 'Ranita' in nombre else ('orange' if 'Chucao' in nombre else 'gray'))
    folium.CircleMarker([row.geometry.y, row.geometry.x], radius=7, color=color, fill=True).add_to(m)

# 4. Elementos finales
rosa_html = '''
<div style="position: fixed; top: 50px; left: 50px; z-index:9999;">
<img src="https://upload.wikimedia.org/wikipedia/commons/f/fb/Rosa_de_los_vientos_51.svg" style="width:120px;">
</div>'''
m.get_root().html.add_child(folium.Element(rosa_html))

MeasureControl(position='bottomleft').add_to(m)

# 5. Renderizado final (Forzamos ancho total)
st_folium(m, width=1400, height=700)
