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

# 5.
