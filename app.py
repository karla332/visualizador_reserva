import streamlit as st
import geopandas as gpd
import folium
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from streamlit_folium import st_folium
import os

# Importamos solo lo necesario, sin plugins que fallen
from folium.plugins import FloatImage, MeasureControl

st.set_page_config(layout="wide")
st.title("🌿 Visualizador Ambiental: Reserva Nacional Alerce Costero")

# 1. Carga de datos
def load_gpkg(path):
    if not os.path.exists(path):
        st.error(f"No se encuentra: {path}")
        st.stop()
    return gpd.read_file(path).to_crs(epsg=4326)

try:
    reserva = load_gpkg('data/areas_protegidas.gpkg')
    rios = load_gpkg('data/rios.gpkg')
    especies = load_gpkg('data/especies.gpkg')
    especies = especies.dropna(subset=['common_name'])
    area_ha = reserva.to_crs(epsg=32718).area.sum() / 10000
    num_rios = len(rios)
except Exception as e:
    st.error(f"Error cargando datos: {e}")
    st.stop()

# 2. Mapa Base
m = folium.Map(location=[reserva.geometry.centroid.y.mean(), reserva.geometry.centroid.x.mean()], zoom_start=13, tiles="CartoDB positron")

# 3. Capas
folium.GeoJson(reserva, name="Reserva", style_function=lambda x: {'color': '#004d00', 'weight': 3, 'fill': False}).add_to(m)
folium.GeoJson(rios, name="Ríos", style_function=lambda x: {'color': '#00BFFF', 'weight': 2}).add_to(m)

for _, row in especies.iterrows():
    nombre = str(row.get('common_name', 'Especie'))
    color = '#FF1493' if 'Alerce' in nombre else ('purple' if 'Ranita' in nombre else ('orange' if 'Chucao' in nombre else 'gray'))
    folium.CircleMarker([row.geometry.y, row.geometry.x], radius=7, color=color, fill=True).add_to(m)

# 4. Elementos que SÍ funcionan siempre
FloatImage("https://raw.githubusercontent.com/sjauregui/folium_examples/master/north_arrow.png", bottom=90, left=10).add_to(m)
MeasureControl(position='bottomleft').add_to(m)

# Esta es la forma antigua y robusta de añadir la escala
m.add_child(folium.Element('<script>L.control.scale({position:"bottomright", imperial:false}).addTo(map);</script>'))

# Leyenda
legend_html = '''<div style="position: fixed; bottom: 50px; right: 50px; z-index:9999; background:white; padding:10px; border:1px solid #ccc;">
<b>Leyenda:</b><br><i style="color:#00BFFF">█</i> Ríos<br><i style="color:#FF1493">●</i> Alerce</div>'''
m.get_root().html.add_child(folium.Element(legend_html))

st_folium(m, width=900, height=600)
