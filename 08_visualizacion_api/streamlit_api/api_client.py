"""Cliente HTTP de la API (API Gateway). Streamlit solo habla con este módulo."""
import os

import requests

API_URL = os.getenv("API_URL", "http://localhost:3000").rstrip("/")  # URL del API Gateway


def _get(path, params=None):
    r = requests.get(f"{API_URL}{path}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def search_planets(q="", size_category="", earth_like=False, sort=""):
    params = {}
    if sort:
        params["sort"] = sort
    if q:
        params["q"] = q
    if size_category:
        params["size_category"] = size_category
    if earth_like:
        params["earth_like"] = "true"
    return _get("/planets", params)


def size_statistics():
    return _get("/statistics/size")["statistics"]


def largest_planets(n=10):
    """Los n planetas de mayor radio, usando solo /planets (las categorías de radio más grande)."""
    rows = []
    for cat in ("Otro / No clasificado", "Gigante gaseoso"):
        rows += search_planets(size_category=cat)["planets"]
    rows = [r for r in rows if r["pl_rade"] is not None]
    return sorted(rows, key=lambda r: r["pl_rade"], reverse=True)[:n]


def closest_systems(n=10):
    """Los n sistemas (estrellas) más cercanos. Requiere que la Lambda soporte sort=sy_dist."""
    res = search_planets(sort="sy_dist")
    if res.get("sort") != "sy_dist":
        raise RuntimeError("La Lambda desplegada no soporta sort=sy_dist; actualiza su código.")
    sistemas = {}
    for p in res["planets"]:  # ya vienen ordenados por distancia; se conserva el primero de cada estrella
        sistemas.setdefault(p["hostname"], p["sy_dist"])
    return [{"hostname": h, "sy_dist": d} for h, d in list(sistemas.items())[:n]]
