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
        st.error(f"Archivo no encontrado: {path}")
        st.stop()
    return gpd.read_file(path).to_crs(epsg=4326)

try:
    reserva = load_gpkg('data/areas_protegidas.gpkg')
    rios = load_gpkg('data/rios.gpkg')
    especies = load_gpkg('data/especies.gpkg').dropna(subset=['common_name'])
    area_ha = reserva.to_crs(epsg=32718).area.sum() / 10000
    num_rios = len(rios)
except Exception as e:
    st.error(f"Error cargando datos: {e}")
    st.stop()

# 2. Mapa
m = folium.Map(location=[reserva.geometry.centroid.y.mean(), reserva.geometry.centroid.x.mean()], zoom_start=13, tiles=None)
folium.TileLayer('CartoDB positron', name='Mapa Base').add_to(m)
folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri', name='Satelital').add_to(m)

# 3. Capa DEM
try:
    with rasterio.open('data/DME_AREAS_PROTEGIDAS.tif') as src:
        dem = src.read(1)
        dem = np.where(dem == src.nodata, np.nan, dem)
        norm = plt.Normalize(vmin=4, vmax=1042)
        colored_dem = plt.get_cmap('RdYlGn_r')(norm(dem))
        folium.raster_layers.ImageOverlay(image=colored_dem, bounds=[[src.bounds.bottom, src.bounds.left], [src.bounds.top, src.bounds.right]], name="Relieve (DEM)", opacity=0.4).add_to(m)
except: pass

# 4. Capas Vectoriales
folium.GeoJson(reserva, name="Reserva", style_function=lambda x: {'fillColor': 'transparent', 'color': '#004d00', 'weight': 3}).add_to(m)
folium.GeoJson(rios, name="Ríos", style_function=lambda x: {'color': '#00BFFF', 'weight': 2, 'opacity': 0.8}).add_to(m)

# 5. Especies
for _, row in especies.iterrows():
    nombre = str(row.get('common_name', 'Especie'))
    color = '#FF1493' if 'Alerce' in nombre else ('purple' if 'Ranita' in nombre else ('orange' if 'Chucao' in nombre else 'gray'))
    folium.CircleMarker([row.geometry.y, row.geometry.x], radius=7, color=color, fill=True).add_to(m)

# 6. Elementos finales: Rosa (SVG) y Escala
# Usamos tu nueva rosa vectorial
FloatImage("https://upload.wikimedia.org/wikipedia/commons/f/fb/Rosa_de_los_vientos_51.svg", bottom=90, left=10).add_to(m)
MeasureControl(position='bottomleft').add_to(m)

# Escala fija (método infalible vía Javascript)
m.add_child(folium.Element('<script>L.control.scale({position:"bottomright", imperial:false}).addTo(map);</script>'))

# Leyenda
legend_html = '''
     <div style="position: fixed; bottom: 50px; left: 50px; z-index:9999; font-size:12px; background:white; padding:10px; border-radius:5px; border:1px solid #ccc; color: black;">
      <b>Leyenda:</b><br>
      <i style="color:#00BFFF">█</i> Ríos<br>
      <i style="color:#FF1493">●</i> Alerce
     </div>'''
m.get_root().html.add_child(folium.Element(legend_html))

folium.LayerControl(collapsed=False).add_to(m)
st_folium(m, width=900, height=600)
