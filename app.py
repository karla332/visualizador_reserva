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

# 2. Sidebar: Filtros y Métricas
st.sidebar.header("Control de Datos")

st.write("Columnas disponibles en especies:", especies.columns.tolist())
# Filtro de Especies
especies_unicas = sorted(especies['common_name'].unique().tolist())
especies_seleccionadas = st.sidebar.multiselect(
    "Filtrar por especie:",
    options=especies_unicas,
    default=especies_unicas
)

# Métricas rápidas
col1, col2, col3 = st.columns(3)
col1.metric("Área Protegida", "1") # Puedes personalizar esto con datos reales
col2.metric("Especies Visualizadas", len(especies[especies['common_name'].isin(especies_seleccionadas)]))
col3.metric("Ríos mapeados", len(rios))

# 3. Mapa base
centro = [reserva.geometry.centroid.y.mean(), reserva.geometry.centroid.x.mean()]
m = folium.Map(location=centro, zoom_start=13, tiles=None)

# Añadir capas base
folium.TileLayer('CartoDB positron', name='Mapa Base').add_to(m)
folium.TileLayer(
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr='Esri',
    name='Mapa Satelital'
).add_to(m)

# 4. DEM (Estilo QGIS)
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
            opacity=0.5
        ).add_to(m)
except Exception as e:
    st.sidebar.warning(f"No se pudo cargar el DEM: {e}")

# 5. Capas vectoriales
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

# 6. Especies (Filtradas dinámicamente)
especies_filtradas = especies[especies['common_name'].isin(especies_seleccionadas)]

for _, row in especies_filtradas.iterrows():
    if row.geometry:
        nombre = str(row.get('common_name', 'Especie'))
        url_foto = row.get('image_url', '')
        
        # Asignación de color
        color = 'green' if 'Alerce' in nombre else ('red' if 'Ranita' in nombre else ('brown' if 'Chucao' in nombre else 'purple'))

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

# 7. Control de capas y renderizado
folium.LayerControl(collapsed=False).add_to(m)
st_folium(m, width=900, height=600)
