import streamlit as st
import geopandas as gpd
import folium
from folium.plugins import FloatImage
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
    
    # Calcular área (UTM 18S para la zona de la reserva)
    area_ha = reserva.to_crs(epsg=32718).area.sum() / 10000
except Exception as e:
    st.error(f"Error cargando archivos: {e}")
    st.stop()

# 2. Sidebar
st.sidebar.header("🎛️ Controles")
especies_unicas = sorted(especies['common_name'].unique().tolist())
seleccion = st.sidebar.multiselect("Filtrar especies:", especies_unicas, default=especies_unicas)
st.sidebar.metric("Área Total", f"{area_ha:,.2f} ha")
st.sidebar.metric("Especies", len(especies))

# 3. Mapa base
m = folium.Map(location=[reserva.geometry.centroid.y.mean(), reserva.geometry.centroid.x.mean()], zoom_start=13, tiles=None)
folium.TileLayer('CartoDB positron', name='Mapa Base').add_to(m)
folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri', name='Satelital').add_to(m)

# 4. Flecha del Norte y Leyenda
FloatImage("https://raw.githubusercontent.com/sjauregui/folium_examples/master/north_arrow.png", bottom=85, left=5).add_to(m)

legend_html = '''
     <div style="position: fixed; bottom: 50px; left: 50px; z-index:9999; font-size:12px; background:white; padding:10px; border-radius:5px; border:1px solid #ccc;">
      <b>Leyenda:</b><br>
      <i class="fa fa-circle" style="color:green"></i> Alerce<br>
      <i class="fa fa-circle" style="color:red"></i> Ranita<br>
      <i class="fa fa-circle" style="color:brown"></i> Chucao<br>
      <i class="fa fa-circle" style="color:purple"></i> Otros
     </div>'''
m.get_root().html.add_child(folium.Element(legend_html))

# 5. DEM
try:
    with rasterio.open('data/DME_AREAS_PROTEGIDAS.tif') as src:
        dem = src.read(1)
        dem = np.where(dem == src.nodata, np.nan, dem)
        norm = plt.Normalize(vmin=np.nanmin(dem), vmax=np.nanmax(dem))
        colored_dem = plt.get_cmap('terrain')(norm(dem))
        folium.raster_layers.ImageOverlay(image=colored_dem, bounds=[[src.bounds.bottom, src.bounds.left], [src.bounds.top, src.bounds.right]], name="Relieve (DEM)", opacity=0.5).add_to(m)
except: pass

# 6. Capas
folium.GeoJson(reserva, name="Reserva", style_function=lambda x: {'fillColor': 'transparent', 'color': '#004d00', 'weight': 2}).add_to(m)
folium.GeoJson(rios, name="Ríos", style_function=lambda x: {'color': '#00BFFF', 'weight': 2}).add_to(m)

# 7. Especies (Filtradas + Imágenes)
for _, row in especies[especies['common_name'].isin(seleccion)].iterrows():
    nombre = str(row.get('common_name', 'Especie'))
    url = row.get('image_url', '')
    color = 'green' if 'Alerce' in nombre else ('red' if 'Ranita' in nombre else ('brown' if 'Chucao' in nombre else 'purple'))
    
    html = f'<div style="width:150px;"><h4>{nombre}</h4><img src="{url}" style="width:100%; border-radius:5px;"></div>'
    folium.CircleMarker([row.geometry.y, row.geometry.x], radius=6, color=color, fill=True, popup=folium.Popup(html, max_width=200)).add_to(m)

folium.LayerControl(collapsed=False).add_to(m)
st_folium(m, width=900, height=600)
