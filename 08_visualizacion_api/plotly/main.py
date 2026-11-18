"""Genera graficos/dashboard.html: una sola app con pestañas, indicadores y los cuatro gráficos."""
from pathlib import Path

from plotly.offline import get_plotlyjs

from data_loader import load_exoplanets
from visualizaciones import (descubrimientos_por_anio, distribucion_por_tamano,
                             estrellas_con_mas_planetas, masa_vs_radio)

SALIDA = Path(__file__).parent / "graficos"
PESTANAS = [
    ("Estrellas", estrellas_con_mas_planetas),
    ("Tamaños", distribucion_por_tamano),
    ("Masa y radio", masa_vs_radio),
    ("Descubrimientos", descubrimientos_por_anio),
]

PLANTILLA = """<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Exoplanetas</title>
<style>
body{{margin:0;background:#0b1026;color:#e8ecff;font-family:Segoe UI,Arial,sans-serif}}
header{{padding:20px 32px 0}} h1{{margin:0 0 4px;font-size:26px}} p.sub{{margin:0;color:#9aa4d6}}
.kpis{{display:flex;gap:16px;flex-wrap:wrap;padding:16px 32px}}
.kpi{{background:#141b3d;border-radius:10px;padding:12px 20px;min-width:150px}}
.kpi b{{display:block;font-size:24px}} .kpi span{{color:#9aa4d6;font-size:13px}}
nav{{display:flex;gap:8px;padding:0 32px;border-bottom:1px solid #26305e}}
nav button{{background:none;border:0;color:#9aa4d6;font-size:15px;padding:10px 16px;cursor:pointer;border-bottom:3px solid transparent}}
nav button.on{{color:#fff;border-color:#7c5cff}}
section{{display:none;padding:16px 32px}} section.on{{display:block}}
</style><script>{plotlyjs}</script></head><body>
<header><h1>Exoplanetas confirmados</h1><p class="sub">Análisis descriptivo </p></header>
<div class="kpis">{kpis}</div><nav>{botones}</nav>{secciones}
<script>
function ver(i){{document.querySelectorAll('nav button,section').forEach(e=>e.classList.remove('on'));
document.querySelectorAll('nav button')[i].classList.add('on');
const s=document.getElementById('p'+i);s.classList.add('on');
s.querySelectorAll('.plotly-graph-div').forEach(g=>Plotly.Plots.resize(g));}}
ver(0);
</script></body></html>"""


def kpis(df):
    datos = [(len(df), "Exoplanetas"), (df["hostname"].nunique(), "Estrellas"),
             (int(df["is_multiplanet_system"].sum()), "En sistemas multiplanetarios"),
             (int(df["is_earth_similar"].sum()), "Similares a la Tierra"),
             (int(df["disc_year"].mode().iloc[0]), "Año con más descubrimientos")]
    return "".join(f'<div class="kpi"><b>{v:,}</b><span>{t}</span></div>'.replace(",", ".") for v, t in datos)


if __name__ == "__main__":
    df = load_exoplanets()
    print(f"Registros leídos: {len(df)}")
    botones, secciones = [], []
    for i, (nombre, crear) in enumerate(PESTANAS):
        fig = crear(df)
        cuerpo = (fig.to_html(full_html=False, include_plotlyjs=False, default_height="600px")
                  if fig else "<p>No hay datos válidos para este gráfico.</p>")
        botones.append(f'<button onclick="ver({i})">{nombre}</button>')
        secciones.append(f'<section id="p{i}">{cuerpo}</section>')
    SALIDA.mkdir(exist_ok=True)
    (SALIDA / "dashboard.html").write_text(
        PLANTILLA.format(plotlyjs=get_plotlyjs(), kpis=kpis(df), botones="".join(botones),
                         secciones="".join(secciones)), encoding="utf-8")
    print("[ok] graficos/dashboard.html")
