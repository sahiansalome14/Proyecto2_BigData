"""Interfaz Streamlit: todos los datos se piden a la API por HTTP."""
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

import api_client

st.set_page_config(page_title="Explorador de Exoplanetas", layout="wide")
st.title("Explorador de Exoplanetas")

try:
    categorias = [s["size_category"] for s in api_client.size_statistics()]
except requests.RequestException as e:
    st.error(f"No se pudo conectar con la API: {e}")
    st.stop()

# A. Buscar, B. filtrar por tamaño, C. similares a la Tierra
with st.form("filtros"):
    col1, col2, col3 = st.columns([3, 2, 1])
    nombre = col1.text_input("Nombre del planeta", placeholder="Kepler-22")
    tamano = col2.selectbox("Categoría de tamaño", ["Todas"] + sorted(categorias))
    tierra = col3.checkbox("Similares a la Tierra")
    buscar = st.form_submit_button("Buscar")

# D. Resultados
try:
    res = api_client.search_planets(nombre.strip(), "" if tamano == "Todas" else tamano, tierra)
except requests.RequestException as e:
    st.error(f"Error al consultar la API: {e}")
    st.stop()

st.write(f"{res['total']} planetas encontrados (se muestran hasta {res['limit']}).")
if res["planets"]:
    st.dataframe(pd.DataFrame(res["planets"]).drop(columns=["is_earth_similar"]), width="stretch")
else:
    st.info("No hay planetas con esos filtros.")

stats = pd.DataFrame(api_client.size_statistics())
fig = px.bar(stats, x="size_category", y="count", color="size_category",
             labels={"size_category": "Categoría de tamaño", "count": "Cantidad de planetas"},
             title="Cantidad de planetas por categoría de tamaño")
fig.update_layout(showlegend=False)
st.plotly_chart(fig, width="stretch")
