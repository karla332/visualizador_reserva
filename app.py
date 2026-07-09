import streamlit as st
import geopandas as gpd
import folium
from folium.plugins import FloatImage
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from streamlit_folium import st_folium

st.set_page_config(layout="wide")
st.title("🌿 Visualizador Ambiental: Reserva Nacional Alerce Costero")

# 1. Carga de datos
try:
    reserva = gpd.read_file('data/areas_protegidas.gpkg').to_crs(epsg=4326)
    rios = gpd.read_file('data/rios.gpkg').to_crs(epsg=4326)
    especies = gpd.read_file('data/especies.gpkg').to_crs(epsg=4326).dropna(subset=['common_name'])
    
    area_ha = reserva.to_crs(epsg=32718).area.sum() / 10000
    num_rios = len(rios) # Calculamos la cantidad aquí
except Exception as e:
    st.error(f"Error cargando datos: {e}")
    st.stop()

# 2. Sidebar con métricas dinámicas
st.sidebar.header("🎛️ Análisis")
seleccion = st.sidebar.multiselect("Filtrar especies:", sorted(especies['common_name'].unique().tolist()), default=especies['common_name'].unique().tolist())

st.sidebar.metric("Área Reserva", f"{area_ha:,.0f} ha")
# AQUÍ MOSTRAMOS LA CANTIDAD DE RÍOS
st.sidebar.metric("Red Hídrica", f"{num_rios} tramos detectados")

# 3. Mapa base
m = folium.Map(location=[reserva.geometry.centroid.y.mean(), reserva.geometry.centroid.x.mean()], zoom_start=13, tiles=None)
folium.TileLayer('CartoDB positron', name='Mapa Base').add_to(m)
folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri', name='Satelital').add_to(m)

# 4. Leyenda Profesional
legend_html = '''
     <div style="position: fixed; bottom: 50px; left: 50px; z-index:9999; font-size:14px; background:white; padding:15px; border-radius:10px; border:2px solid #333; box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">
      <b>Leyenda</b><br>
      <i class="fa fa-minus" style="color:#00BFFF"></i> Red Hídrica<br>
      <hr style="margin:5px 0;">
      <i class="fa fa-circle" style="color:green"></i> Alerce<br>
      <i class="fa fa-circle" style="color:red"></i> Ranita<br>
      <i class="fa fa-circle" style="color:brown"></i> Chucao<br>
      <i class="fa fa-circle" style="color:purple"></i> Otros
     </div>'''
m.get_root().html.add_child(folium.Element(legend_html))

# 5. Capas con estilo destacado
folium.GeoJson(reserva, name="Reserva", style_function=lambda x: {'fillColor': 'transparent', 'color': '#004d00', 'weight': 3}).add_to(m)
folium.GeoJson(rios, name="Ríos", style_function=lambda x: {'color': '#00BFFF', 'weight': 2, 'opacity': 0.8}).add_to(m)

# 6. Especies con imágenes
for _, row in especies[especies['common_name'].isin(seleccion)].iterrows():
    nombre = str(row.get('common_name', 'Especie'))
    color = 'green' if 'Alerce' in nombre else ('red' if 'Ranita' in nombre else ('brown' if 'Chucao' in nombre else 'purple'))
    html = f'<div style="width:150px;"><h4>{nombre}</h4><img src="{row.get("image_url", "")}" style="width:100%; border-radius:5px;"></div>'
    folium.CircleMarker([row.geometry.y, row.geometry.x], radius=7, color=color, fill=True, popup=folium.Popup(html, max_width=200)).add_to(m)

folium.LayerControl(collapsed=False).add_to(m)
st_folium(m, width=900, height=600)
