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

# 1. Carga de datos
def load_gpkg(path):
    if not os.path.exists(path):
        st.error(f"Archivo no encontrado: {path}")
        st.stop()
    return gpd.read_file(path, driver='GPKG').to_crs(epsg=4326)

try:
    reserva = load_gpkg('data/areas_protegidas.gpkg')
    rios = load_gpkg('data/rios.gpkg')
    especies = load_gpkg('data/especies.gpkg').dropna(subset=['common_name'])
except Exception as e:
    st.error(f"Error cargando datos: {e}")
    st.stop()

# 2. Sidebar
st.sidebar.header("🎛️ Análisis")
seleccion = st.sidebar.multiselect("Filtrar especies:", sorted(especies['common_name'].unique().tolist()), default=especies['common_name'].unique().tolist())

# 3. Mapa Base
m = folium.Map(location=[reserva.geometry.centroid.y.mean(), reserva.geometry.centroid.x.mean()], zoom_start=13, tiles=None)
folium.TileLayer('CartoDB positron', name='Mapa Base').add_to(m)
folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri', name='Satelital').add_to(m)

# 4. Capa DEM (Tu relieve)
try:
    with rasterio.open('data/DME_AREAS_PROTEGIDAS.tif') as src:
        dem = src.read(1)
        dem = np.where(dem == src.nodata, np.nan, dem)
        norm = plt.Normalize(vmin=4, vmax=1042)
        colored_dem = plt.get_cmap('RdYlGn_r')(norm(dem))
        folium.raster_layers.ImageOverlay(image=colored_dem, bounds=[[src.bounds.bottom, src.bounds.left], [src.bounds.top, src.bounds.right]], name="Relieve (DEM)", opacity=0.4).add_to(m)
except: pass

# 5. Capas Vectoriales
folium.GeoJson(reserva, name="Reserva", style_function=lambda x: {'fillColor': 'transparent', 'color': '#004d00', 'weight': 3}).add_to(m)
folium.GeoJson(rios, name="Ríos", style_function=lambda x: {'color': '#00BFFF', 'weight': 2}).add_to(m)

# 6. Especies
for _, row in especies[especies['common_name'].isin(seleccion)].iterrows():
    nombre = str(row.get('common_name', 'Especie'))
    color = '#FF1493' if 'Alerce' in nombre else ('purple' if 'Ranita' in nombre else ('orange' if 'Chucao' in nombre else 'gray'))
    folium.CircleMarker([row.geometry.y, row.geometry.x], radius=7, color=color, fill=True).add_to(m)

# 7. Elementos Fijos (Rosa + Escala JS + Leyenda)
FloatImage("https://raw.githubusercontent.com/sjauregui/folium_examples/master/north_arrow.png", bottom=90, left=10).add_to(m)
MeasureControl(position='bottomleft').add_to(m)
m.add_child(folium.Element('<script>L.control.scale({position:"bottomright", imperial:false}).addTo(map);</script>'))

legend_html = '''<div style="position: fixed; bottom: 50px; right: 50px; z-index:9999; background:white; padding:10px; border:1px solid #ccc; color: black;">
<b>Leyenda:</b><br>
<i style="color:#00BFFF">●</i> Ríos<br>
<i style="color:#00FF00">■</i> Árido (verde fuerte)<br>
<i style="color:#FF0000">■</i> Denso (rojo fuerte)<br>
<i style="color:#FF1493">●</i> Alerce<br>
<i style="color:purple">●</i> Ranita<br>
<i style="color:orange">●</i> Chucao</div>'''
m.get_root().html.add_child(folium.Element(legend_html))

folium.LayerControl(collapsed=False).add_to(m)
st_folium(m, width=900, height=600)
