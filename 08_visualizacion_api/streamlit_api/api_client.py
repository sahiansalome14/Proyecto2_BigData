"""Cliente HTTP de la API (API Gateway). Streamlit solo habla con este módulo."""
import os

import requests

API_URL = os.getenv("API_URL", "http://localhost:3000").rstrip("/")  # URL del API Gateway


def _get(path, params=None):
    r = requests.get(f"{API_URL}{path}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def search_planets(q="", size_category="", earth_like=False):
    params = {}
    if q:
        params["q"] = q
    if size_category:
        params["size_category"] = size_category
    if earth_like:
        params["earth_like"] = "true"
    return _get("/planets", params)


def size_statistics():
    return _get("/statistics/size")["statistics"]
