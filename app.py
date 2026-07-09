import streamlit as st
import geopandas as gpd
import folium
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from streamlit_folium import st_folium

# Configuración de página
st.set_page_config(layout="wide")
st.title("🌿 Visualizador Ambiental: Reserva Nacional Alerce Costero")

# 1. Cargar datos
try:
    reserva = gpd.read_file('data/areas_protegidas.gpkg').to_crs(epsg=4326)
    rios = gpd.read_file('data/rios.geojson').to_crs(epsg=4326)
    especies = gpd.read_file('data/especies.gpkg').to_crs(epsg=4326)
except Exception as e:
    st.error(f"Error cargando archivos: {e}")
    st.stop()

# 2. Mapa base
centro = [reserva.geometry.centroid.y.mean(), reserva.geometry.centroid.x.mean()]
m = folium.Map(location=centro, zoom_start=13, tiles="CartoDB positron")

# 3. DEM (Estilo QGIS)
try:
    with rasterio.open('data/DME_AREAS_PROTEGIDAS.tif') as src:
        dem_data = src.read(1)
        dem_data = np.where(dem_data == src.nodata, np.nan, dem_data)
        cmap = plt.get_cmap('terrain')
        norm = plt.Normalize(vmin=np.nanmin(dem_data), vmax=np.nanmax(dem_data))
        colored_dem = cmap(norm(dem_data))
        bounds = src.bounds
        folium.raster_layers.ImageOverlay(
            image=colored_dem,
            bounds=[[bounds.bottom, bounds.left], [bounds.top, bounds.right]],
            name="Relieve (DEM)",
            opacity=0.6
        ).add_to(m)
except Exception as e:
    st.sidebar.warning(f"No se pudo cargar el DEM: {e}")

# 4. Capas vectoriales
folium.GeoJson(
    reserva, 
    name="Reserva", 
    style_function=lambda x: {'fillColor': 'transparent', 'color': '#004d00', 'weight': 2}
).add_to(m)

folium.GeoJson(
    rios, 
    name="Ríos", 
    style_function=lambda x: {'color': '#00BFFF', 'weight': 2}
).add_to(m)

# 5. Especies con Imágenes
for _, row in especies.iterrows():
    if row.geometry:
        nombre = str(row.get('common_name', 'Especie'))
        url_foto = row.get('image_url', '') # Verifica que esta columna sea la correcta en tu archivo
        
        if 'Alerce' in nombre: color = 'green'
        elif 'Ranita' in nombre: color = 'red'
        elif 'Chucao' in nombre: color = 'brown'
        else: color = 'purple'

        # Popup con imagen
        html_popup = f"""
        <div style="width: 150px;">
            <h4 style="margin: 0;">{nombre}</h4>
            <img src="{url_foto}" style="width:100%; border-radius: 5px; margin-top: 5px;">
        </div>
        """
        
        folium.CircleMarker(
            [row.geometry.y, row.geometry.x], 
            radius=6, 
            color=color, 
            fill=True,
            popup=folium.Popup(html_popup, max_width=200)
        ).add_to(m)

# 6. Control de capas y renderizado
folium.LayerControl(collapsed=False).add_to(m)
st_folium(m, width=900, height=600)
