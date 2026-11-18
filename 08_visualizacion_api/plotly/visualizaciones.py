"""Creación de los cuatro gráficos con Plotly. Cada función devuelve una Figure o None si no hay datos."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

TEMPLATE = "plotly_dark"
BG = "#0b1026"
PALETA = px.colors.qualitative.Vivid
ORDEN_TAMANO = ["Similar a la Tierra", "Super-Tierra", "Subneptuniano",
                "Neptuniano", "Gigante gaseoso", "Otro / No clasificado"]


def _estilo(fig, titulo):
    fig.update_layout(template=TEMPLATE, paper_bgcolor=BG, plot_bgcolor=BG,
                      title=titulo, font=dict(family="Segoe UI, Arial", size=13))
    return fig


def _orden(categorias):
    """Orden de Kopparapu para las categorías presentes; las desconocidas van al final."""
    conocidas = [c for c in ORDEN_TAMANO if c in set(categorias)]
    return conocidas + sorted(set(categorias) - set(conocidas))


def estrellas_con_mas_planetas(df):
    d = df.dropna(subset=["hostname", "pl_name"])
    if d.empty:
        return None
    top = (d.groupby("hostname")["pl_name"].nunique().nlargest(10)
           .sort_values().reset_index(name="planetas"))
    fig = px.bar(top, x="planetas", y="hostname", orientation="h", color="planetas",
                 color_continuous_scale="Viridis",
                 labels={"planetas": "Planetas confirmados", "hostname": "Estrella"})
    fig.update_traces(hovertemplate="Estrella: %{y}<br>Planetas: %{x}<extra></extra>")
    fig.update_coloraxes(showscale=False)
    return _estilo(fig, "Top 10 estrellas con más exoplanetas confirmados")


def distribucion_por_tamano(df):
    d = df.dropna(subset=["size_category"])
    if d.empty:
        return None
    conteo = d["size_category"].value_counts().reindex(_orden(d["size_category"])).reset_index()
    conteo.columns = ["categoria", "cantidad"]
    fig = go.Figure(go.Pie(labels=conteo["categoria"], values=conteo["cantidad"], hole=0.5,
                           sort=False, marker=dict(colors=PALETA),
                           textinfo="value+percent",
                           hovertemplate="%{label}<br>Cantidad: %{value}<br>%{percent}<extra></extra>"))
    return _estilo(fig, "Distribución de exoplanetas por categoría de tamaño")


def masa_vs_radio(df):
    d = df.dropna(subset=["pl_bmasse", "pl_rade", "size_category"])
    d = d[(d["pl_bmasse"] > 0) & (d["pl_rade"] > 0)]  # requisito de la escala logarítmica
    if len(d) < 3:
        return None
    lx, ly = np.log10(d["pl_bmasse"]), np.log10(d["pl_rade"])
    r = np.corrcoef(lx, ly)[0, 1]  # Pearson sobre log10: coherente con los ejes log-log
    fig = px.scatter(d, x="pl_bmasse", y="pl_rade", color="size_category",
                     category_orders={"size_category": _orden(d["size_category"])},
                     color_discrete_sequence=PALETA, log_x=True, log_y=True, opacity=0.75,
                     custom_data=["pl_name", "size_category"],
                     labels={"pl_bmasse": "Masa (masas terrestres)", "pl_rade": "Radio (radios terrestres)",
                             "size_category": "Categoría"})
    fig.update_traces(hovertemplate="<b>%{customdata[0]}</b><br>Masa: %{x:.2f} M⊕<br>"
                                    "Radio: %{y:.2f} R⊕<br>Categoría: %{customdata[1]}<extra></extra>")
    if abs(r) >= 0.3:  # solo se dibuja la tendencia si hay relación apreciable
        m, b = np.polyfit(lx, ly, 1)
        xs = np.linspace(lx.min(), lx.max(), 50)
        fig.add_trace(go.Scatter(x=10 ** xs, y=10 ** (m * xs + b), mode="lines", name="Tendencia (log-log)",
                                 line=dict(color="white", dash="dash"), hoverinfo="skip"))
    return _estilo(fig, f"Relación masa–radio (Pearson sobre log10 = {r:.3f}, n = {len(d)})")


def descubrimientos_por_anio(df):
    d = df.dropna(subset=["disc_year", "discoverymethod"])
    if d.empty:
        return None
    c = d.groupby(["disc_year", "discoverymethod"]).size().reset_index(name="cantidad")
    c["disc_year"] = c["disc_year"].astype(int)
    fig = px.line(c, x="disc_year", y="cantidad", color="discoverymethod", markers=True,
                  color_discrete_sequence=PALETA,
                  labels={"disc_year": "Año de descubrimiento", "cantidad": "Exoplanetas descubiertos",
                          "discoverymethod": "Método"})
    fig.update_traces(hovertemplate="Año: %{x}<br>Método: %{fullData.name}<br>Cantidad: %{y}<extra></extra>")
    return _estilo(fig, "Descubrimientos de exoplanetas por año y método")
