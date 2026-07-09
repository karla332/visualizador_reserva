import streamlit as st
import geopandas as gpd
import folium
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from streamlit_folium import st_folium

# Configuración
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

# 2. Sidebar: Filtros y Estadísticas
st.sidebar.header("🎛️ Controles y Análisis")

# Filtro de Especies
especies_unicas = sorted(especies['common_name'].unique().tolist())
seleccion = st.sidebar.multiselect("Filtrar por especie:", especies_unicas, default=especies_unicas)

# Estadísticas en el panel lateral
st.sidebar.subheader("📊 Estadísticas")
st.sidebar.metric("Total Especies Cargadas", len(especies))
st.sidebar.metric("Ríos identificados", len(rios))

# Leyenda explicativa (Expansible)
with st.sidebar.expander("ℹ️ Acerca de los datos"):
    st.write("""
    **Reserva Alerce Costero:** Datos vectoriales protegidos.
    **Red Hídrica:** Capa hidrológica clave para la biodiversidad.
    **Especies:** Observaciones de fauna y flora.
    """)

# 3. Mapa base
centro = [reserva.geometry.centroid.y.mean(), reserva.geometry.centroid.x.mean()]
m = folium.Map(location=centro, zoom_start=13, tiles=None)

folium.TileLayer('CartoDB positron', name='Mapa Base').add_to(m)
folium.TileLayer(
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr='Esri',
    name='Mapa Satelital'
).add_to(m)

# 4. DEM
try:
    with rasterio.open('data/DME_AREAS_PROTEGIDAS.tif') as src:
        dem_data = src.read(1)
        dem_data = np.where(dem_data == src.nodata, np.nan, dem_data)
        cmap = plt.get_cmap('terrain')
        norm = plt.Normalize(vmin=np.nanmin(dem_data), vmax=np.nanmax(dem_data))
        colored_dem = cmap(norm(dem_data))
        bounds = src.bounds
        folium.raster_layers.ImageOverlay(
            image=colored_dem, bounds=[[bounds.bottom, bounds.left], [bounds.top, bounds.right]],
            name="Relieve (DEM)", opacity=0.5
        ).add_to(m)
except:
    pass

# 5. Capas
folium.GeoJson(reserva, name="Reserva", style_function=lambda x: {'fillColor': 'transparent', 'color': '#004d00', 'weight': 2}).add_to(m)
folium.GeoJson(rios, name="Ríos", style_function=lambda x: {'color': '#00BFFF', 'weight': 2}).add_to(m)

# 6. Especies (Filtradas)
filtradas = especies[especies['common_name'].isin(seleccion)]
for _, row in filtradas.iterrows():
    nombre = str(row.get('common_name', 'Especie'))
    url = row.get('image_url', '')
    color = 'green' if 'Alerce' in nombre else ('red' if 'Ranita' in nombre else ('brown' if 'Chucao' in nombre else 'purple'))
    
    html = f'<div style="width:150px;"><h4>{nombre}</h4><img src="{url}" style="width:100%; border-radius:5px;"></div>'
    folium.CircleMarker([row.geometry.y, row.geometry.x], radius=6, color=color, fill=True, popup=folium.Popup(html, max_width=200)).add_to(m)

folium.LayerControl(collapsed=False).add_to(m)
st_folium(m, width=900, height=600)
