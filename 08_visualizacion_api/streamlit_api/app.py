"""Interfaz Streamlit: todos los datos se piden a la API por HTTP."""
import pandas as pd
import plotly.express as px
import requests  #biblioteca de python para hacer solicitudes http 
import streamlit as st

import api_client
# configuración inicial de streamlit
st.set_page_config(page_title="Explorador de Exoplanetas", layout="wide")

# Seccion de estilo para la app.
st.markdown("""
<style>
.stApp{background:#0b1026;color:#e8ecff}
[data-testid="stForm"]{background:#141b3d;border:1px solid #26305e;border-radius:12px;padding:24px}
[data-testid="stForm"] input,[data-testid="stForm"] [data-baseweb="select"]>div{background:#0b1026!important;color:#e8ecff}
[data-testid="stFormSubmitButton"] button{background:#38bdf8;color:#04121f;border:0;font-weight:600;width:100%}
.sub{color:#9aa4d6;margin:-8px 0 20px}
.block-container{max-width:100%!important;padding-left:2rem;padding-right:2rem}
</style>
""", unsafe_allow_html=True)

st.title("Explorador de Exoplanetas")
st.markdown('<p class="sub">Busca exoplanetas, compara sus características y descubre sistemas planetarios.</p>',
            unsafe_allow_html=True)

try:  #obtenemos una lista solo con las categorias de cada planeta
    categorias = [s["size_category"] for s in api_client.size_statistics()]  #llamamos a la funcion definida (estamos pidiendo las estadísticas de los exoplanetas a nuestra API)
except requests.RequestException as e:
    st.error(f"No se pudo conectar con la API: {e}")
    st.stop()

# A. Buscar, B. filtrar por tamaño, C. similares a la Tierra
with st.form("filtros"):
    st.subheader(" Encuentra un exoplaneta")
    col1, col2, col3 = st.columns(3)  # se divide el espacio entre 3 columnas 
    nombre = col1.text_input("Nombre del planeta", placeholder="Ej. K2-183 b, Kepler-22 b...") #buscador por nombre
    tamano = col2.selectbox("Categoría de tamaño", ["Todas"] + sorted(categorias))  #muestra todas las categorias que peude elegir
    tierra = col3.checkbox("Solo similares a la Tierra") 
    buscar = st.form_submit_button("Buscar exoplanetas")

# D. consultar la api con los filtros (nombre,categoria,tierra)
try:
    res = api_client.search_planets(nombre.strip(), "" if tamano == "Todas" else tamano, tierra)
except requests.RequestException as e:
    st.error(f"Error al consultar la API: {e}")
    st.stop()

st.subheader("Resultados del catálogo") #cuantos planetas encontró la api
st.write(f"{res['total']} planetas encontrados (se muestran hasta {res['limit']}).")
if res["planets"]: #comprobar que si se trajo algo de la api (convertirlos en tabla/mensaje error)
    st.dataframe(pd.DataFrame(res["planets"]).drop(columns=["is_earth_similar"]), width="stretch")
else:
    st.info("No hay planetas con esos filtros.")

# grafica de api.estadisticas -> grafico de barras -> cuántos exoplanetas existen en cada categoría de tamaño
stats = pd.DataFrame(api_client.size_statistics())
fig = px.bar(stats, x="size_category", y="count", color="size_category",
             labels={"size_category": "Categoría de tamaño", "count": "Cantidad de planetas"},
             title="Cantidad de planetas por categoría de tamaño")
fig.update_layout(showlegend=False, template="plotly_dark", paper_bgcolor="#141b3d", plot_bgcolor="#141b3d")
st.plotly_chart(fig, width="stretch")

#  los diez exoplanetas de mayor radio, círculos proporcionales al radio.
st.subheader("Los 10 exoplanetas de mayor radio")
grandes = api_client.largest_planets()
if grandes:
    rmax = max(p["pl_rade"] for p in grandes)
    tonos = ["#c9a98a", "#d3a08f", "#c9b79a", "#cfa98c", "#b98a6b"]
    items = ""
    for i, p in enumerate(grandes):
        d = max(30, round(150 * p["pl_rade"] / rmax))  # diámetro proporcional al radio
        masa = f"{p['pl_bmasse']:.1f} M⊕" if p["pl_bmasse"] is not None else "sin dato"
        items += (f'<div style="text-align:center;min-width:110px">'
                  f'<b>{p["pl_name"]}</b><br><small style="color:#9aa4d6">Radio: {p["pl_rade"]:.1f} R⊕<br>Masa: {masa}</small>'
                  f'<div style="width:{d}px;height:{d}px;border-radius:50%;background:{tonos[i % 5]};margin:12px auto 0"></div></div>')
    st.markdown(f'<div style="display:flex;gap:20px;align-items:flex-end;flex-wrap:wrap;background:#141b3d;'
                f'border-radius:12px;padding:24px">{items}</div>', unsafe_allow_html=True)
    st.caption("Tamaño de los círculos proporcional al radio (R⊕ = radios terrestres).")

# Muestra los 10 sistemas planetarios más cercanos a la Tierra.
st.subheader("Los 10 sistemas planetarios más cercanos a la Tierra")
try:  #llama a la api con su metodo de sistemas mas cercanos y converite en df
    cercanos = pd.DataFrame(api_client.closest_systems()).sort_values("sy_dist", ascending=False)
    fig2 = px.bar(cercanos, x="sy_dist", y="hostname", orientation="h", color="sy_dist",
                  color_continuous_scale="Viridis_r",
                  labels={"sy_dist": "Distancia (parsecs)", "hostname": "Estrella"})
    fig2.update_traces(hovertemplate="Estrella: %{y}<br>Distancia: %{x:.2f} pc<extra></extra>")
    fig2.update_coloraxes(showscale=False)
    st.plotly_chart(fig2, width="stretch")
except (requests.RequestException, RuntimeError) as e:
    st.warning(f"No se pudo cargar este gráfico: {e}")
