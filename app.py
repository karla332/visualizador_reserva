import streamlit as st
import geopandas as gpd
import folium
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from streamlit_folium import st_folium
import os
from folium.plugins import FloatImage, MeasureControl

st.set_page_config(layout="wide")
st.title("🌿 Visualizador Ambiental: Reserva Nacional Alerce Costero")

# 1. Carga de datos robusta (forzando driver GPKG si es necesario)
def load_gpkg(path):
    if not os.path.exists(path):
        st.error(f"No se encuentra el archivo: {path}")
        st.stop()
    # Usamos driver='GPKG' para evitar el error de formato no reconocido
    return gpd.read_file(path, driver='GPKG').to_crs(epsg=4326)

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

# 2. Sidebar
st.sidebar.header("🎛️ Análisis")
especies_unicas = sorted(especies['common_name'].unique().tolist())
seleccion = st.sidebar.multiselect("Filtrar especies:", especies_unicas, default=especies_unicas)
st.sidebar.metric("Área Reserva", f"{area_ha:,.0f} ha")
st.sidebar.metric("Red Hídrica", f"{num_rios} tramos")

# 3. Mapa
m = folium.Map(location=[-40.16, -73.56], zoom_start=13, tiles="CartoDB positron")

# 4. Capas
folium.GeoJson(reserva, name="Reserva", style_function=lambda x: {'color': '#004d00', 'weight': 3, 'fill': False}).add_to(m)
folium.GeoJson(rios, name="Ríos", style_function=lambda x: {'color': '#00BFFF', 'weight': 2}).add_to(m)

for _, row in especies[especies['common_name'].isin(seleccion)].iterrows():
    nombre = str(row.get('common_name', 'Especie'))
    color = '#FF1493' if 'Alerce' in nombre else ('purple' if 'Ranita' in nombre else ('orange' if 'Chucao' in nombre else 'gray'))
    folium.CircleMarker([row.geometry.y, row.geometry.x], radius=7, color=color, fill=True).add_to(m)

# 5. Rosa de los vientos (vía plugin)
FloatImage("https://raw.githubusercontent.com/sjauregui/folium_examples/master/north_arrow.png", bottom=90, left=10).add_to(m)

# 6. Herramientas: Medición y Escala estática (vía JS para evitar errores)
MeasureControl(position='bottomleft').add_to(m)
# Escala estática infalible
m.add_child(folium.Element('<script>L.control.scale({position:"bottomright", imperial:false}).addTo(map);</script>'))

# 7. Leyenda con colores fuertes
legend_html = '''<div style="position: fixed; bottom: 50px; right: 50px; z-index:9999; background:white; padding:10px; border:1px solid #ccc; color: black;">
<b>Leyenda:</b><br>
<i style="color:#00BFFF">●</i> Ríos<br>
<i style="color:#00FF00">■</i> Árido<br>
<i style="color:#FF0000">■</i> Denso<br>
<i style="color:#FF1493">●</i> Alerce<br>
<i style="color:purple">●</i> Ranita<br>
<i style="color:orange">●</i> Chucao</div>'''
m.get_root().html.add_child(folium.Element(legend_html))

st_folium(m, width=900, height=600)
