import streamlit as st
import geopandas as gpd
import folium
from folium.plugins import FloatImage, MeasureControl
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
        st.error(f"No se encuentra el archivo: {path}")
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

# 2. Sidebar
st.sidebar.header("🎛️ Análisis")
especies_unicas = sorted(especies['common_name'].unique().tolist())
seleccion = st.sidebar.multiselect("Filtrar especies:", especies_unicas, default=especies_unicas)
st.sidebar.metric("Área Reserva", f"{area_ha:,.0f} ha")
st.sidebar.metric("Red Hídrica", f"{num_rios} tramos")

# 3. Mapa
m = folium.Map(location=[reserva.geometry.centroid.y.mean(), reserva.geometry.centroid.x.mean()], zoom_start=13, tiles=None)
folium.TileLayer('CartoDB positron', name='Mapa Base').add_to(m)
folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri', name='Satelital').add_to(m)

# 4. Capa DEM
try:
    with rasterio.open('data/DME_AREAS_PROTEGIDAS.tif') as src:
        dem = src.read(1)
        dem = np.where(dem == src.nodata, np.nan, dem)
        norm = plt.Normalize(vmin=4, vmax=1042)
        colored_dem = plt.get_cmap('RdYlGn_r')(norm(dem))
        folium.raster_layers.ImageOverlay(image=colored_dem, bounds=[[src.bounds.bottom, src.bounds.left], [src.bounds.top, src.bounds.right]], name="Relieve (DEM)", opacity=0.4).add_to(m)
except: pass

# 5. Capas vectoriales
folium.GeoJson(reserva, name="Reserva", style_function=lambda x: {'fillColor': 'transparent', 'color': '#004d00', 'weight': 3}).add_to(m)
folium.GeoJson(rios, name="Ríos", style_function=lambda x: {'color': '#00BFFF', 'weight': 2, 'opacity': 0.8}).add_to(m)

# 6. Especies con Imágenes
for _, row in especies[especies['common_name'].isin(seleccion)].iterrows():
    nombre = str(row.get('common_name', 'Especie'))
    color = '#FF1493' if 'Alerce' in nombre else ('purple' if 'Ranita' in nombre else ('orange' if 'Chucao' in nombre else 'gray'))
    html = f'<div style="width:150px;"><h4>{nombre}</h4><img src="{row.get("image_url", "")}" style="width:100%; border-radius:5px;"></div>'
    folium.CircleMarker([row.geometry.y, row.geometry.x], radius=7, color=color, fill=True, popup=folium.Popup(html, max_width=200)).add_to(m)

# 7. Elementos finales
FloatImage("https://raw.githubusercontent.com/sjauregui/folium_examples/master/north_arrow.png", bottom=90, left=10).add_to(m)
folium.ControlScale(position='bottomleft').add_to(m)

legend_html = '''
     <div style="position: fixed; bottom: 50px; left: 50px; z-index:9999; font-size:12px; background:white; padding:10px; border-radius:5px; border:1px solid #ccc; color: black;">
      <b style="color: black;">Leyenda:</b><br>
      <i class="fa fa-minus" style="color:#00BFFF"></i> <span style="color: black;">Ríos</span><br>
      <i class="fa fa-square" style="color:green"></i> <span style="color: black;">Árido</span><br>
      <i class="fa fa-square" style="color:red"></i> <span style="color: black;">Denso</span><br>
      <i class="fa fa-circle" style="color:#FF1493"></i> <span style="color: black;">Alerce</span><br>
      <i class="fa fa-circle" style="color:purple"></i> <span style="color: black;">Ranita</span><br>
      <i class="fa fa-circle" style="color:orange"></i> <span style="color: black;">Chucao</span>
     </div>'''
m.get_root().html.add_child(folium.Element(legend_html))

folium.LayerControl(collapsed=False).add_to(m)
st_folium(m, width=900, height=600)
