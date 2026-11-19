"""Dashboard Dash 'Explorador de Exoplanetas': reúne los cuatro gráficos de visualizaciones.py."""
from dash import Dash, dcc, html
from data_loader import load_exoplanets
from visualizaciones import (descubrimientos_por_anio, distribucion_por_tamano,
                             estrellas_con_mas_planetas, masa_vs_radio)

CREAR = [estrellas_con_mas_planetas, distribucion_por_tamano, masa_vs_radio, descubrimientos_por_anio]

ESTILO_PAGINA = {"background": "#0b1026", "color": "#e8ecff", "minHeight": "100vh",
                 "padding": "20px 32px", "fontFamily": "Segoe UI, Arial, sans-serif"}
ESTILO_REJILLA = {"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "16px"}
ESTILO_TAB = {"background": "#141b3d", "color": "#9aa4d6", "border": "0"}
ESTILO_TAB_ON = {"background": "#0b1026", "color": "#fff", "borderTop": "3px solid #7c5cff"}
# Índices de CREAR: cada sección muestra dos gráficos lado a lado.
SECCIONES = [("Sistemas y tamaños", (0, 1)), ("Masa-radio y descubrimientos", (2, 3))]
ESTILO_TARJETA = {"background": "#141b3d", "borderRadius": "10px", "padding": "8px"}


# Detalle corto que se muestra bajo cada gráfico (mismo orden que CREAR).
DETALLES = [
    "Las 10 estrellas con más planetas confirmados: muestra qué sistemas son los más numerosos.",
    "Proporción de exoplanetas según su tamaño, de similares a la Tierra a gigantes gaseosos.",
    "Cómo crece el radio con la masa (escala log-log); la línea punteada marca la tendencia.",
    "Cuántos exoplanetas se descubrieron cada año y con qué método.",
]


def tarjeta(fig, detalle):
    if fig is None:
        return html.Div("No hay datos válidos para este gráfico.", style=ESTILO_TARJETA)
    fig.update_layout(height=520, paper_bgcolor="#141b3d", plot_bgcolor="#141b3d")
    return html.Div([dcc.Graph(figure=fig),
                     html.P(detalle, style={"color": "#fff", "fontSize": "14px", "margin": "0 8px 8px"})],
                    style=ESTILO_TARJETA)


def crear_app() -> Dash:
    df = load_exoplanets()  # una sola lectura de S3 al iniciar
    app = Dash(__name__, title="Explorador de Exoplanetas")
    # Quita el margen blanco por defecto del navegador.
    app.index_string = app.index_string.replace("</head>", "<style>html,body{margin:0;background:#0b1026}</style></head>")
    app.layout = html.Div(style=ESTILO_PAGINA, children=[
        html.H1("Explorador de Exoplanetas", style={"margin": "0 0 4px"}),
        html.P(f"{len(df):,} exoplanetas confirmados · ".replace(",", "."),
               style={"color": "#9aa4d6", "margin": "0 0 16px"}),
        dcc.Tabs(colors={"border": "#26305e", "primary": "#7c5cff", "background": "#141b3d"}, children=[
            dcc.Tab(label=nombre, style=ESTILO_TAB, selected_style=ESTILO_TAB_ON,
                    children=html.Div([tarjeta(CREAR[i](df), DETALLES[i]) for i in grupo], style={**ESTILO_REJILLA, "marginTop": "16px"}))
            for nombre, grupo in SECCIONES
        ]),
    ])
    return app


if __name__ == "__main__":
    crear_app().run(host="127.0.0.1", port=8050, debug=False)
