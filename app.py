import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# Configuración de página para vista amplia
st.set_page_config(layout="wide")

st.title("🌿 Visualizador Ambiental: Reserva Nacional Alerce Costero")
st.markdown("Esta plataforma integra datos de biodiversidad, red hidrográfica y análisis de relieve.")

# 1. Cargar datos (Asegúrate de que la carpeta 'data/' esté en el mismo lugar que este archivo)
# Si tus archivos tienen nombres distintos, cámbialos aquí:
try:
    reserva = gpd.read_file('data/areas_protegidas.gpkg')
    rios = gpd.read_file('data/rios.gpkg')
    especies = gpd.read_file('data/especies.gpkg')
except Exception as e:
    st.error(f"Error al cargar los archivos: {e}. Asegúrate de que la carpeta 'data/' existe.")

# 2. Configurar el mapa base centrado en la reserva
m = folium.Map(location=[-40.15, -73.55], zoom_start=12, tiles="OpenStreetMap")

# 3. Sidebar para control de capas
st.sidebar.header("Control de Capas")
ver_rios = st.sidebar.checkbox("Mostrar Red Hídrica", True)
ver_especies = st.sidebar.checkbox("Mostrar Biodiversidad", True)

# Añadir Reserva al mapa (Polígono)
folium.GeoJson(reserva, name="Reserva", style_function=lambda x: {'fillColor': 'green', 'color': 'black', 'weight': 2}).add_to(m)

# Añadir Ríos (Líneas)
if ver_rios:
    folium.GeoJson(rios, name="Ríos", style_function=lambda x: {'color': 'blue', 'weight': 1.5}).add_to(m)

# 4. Añadir Especies con colores y Popups de fotos
if ver_especies:
    for _, row in especies.iterrows():
        nombre = row['common_name']
        
        # Lógica de colores según especie
        if 'Ranita' in nombre:
            color = 'orange'
        elif 'Alerce' in nombre:
            color = 'green'
        elif 'Chucao' in nombre:
            color = 'brown'
        else:
            color = 'gray'
        
        # Estructura del Popup profesional con imagen
        popup_html = f"""
        <div style="width: 220px;">
            <h4 style="margin: 0; color: #333;">{nombre}</h4>
            <img src="{row['image_url']}" style="width:100%; border-radius: 8px; margin-top: 5px; border: 1px solid #ccc;">
            <br><br>
            <a href="{row['url']}" target="_blank" style="text-decoration: none; color: blue;">Ver en iNaturalist</a>
        </div>
        """
        
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=7, 
            color=color, 
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=250)
        ).add_to(m)

# Mostrar el mapa final en Streamlit
st_folium(m, width=900, height=500)