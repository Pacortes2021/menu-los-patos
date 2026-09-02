"""
Busca una foto de referencia para el plato del dia usando la API de Pexels
(gratis, requiere una API key gratuita en https://www.pexels.com/api/).

Si no hay key o no encuentra nada, devuelve una imagen generica de almuerzo.
La foto es solo referencial: no es el plato real del casino.
"""

from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request

PEXELS_KEY = os.environ.get("PEXELS_KEY")
# Foto generica de un plato servido (Pexels, libre de uso).
FALLBACK = "https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg?auto=compress&w=900"


def query_desde_plato(plato: str) -> str:
    """Convierte 'Merluza apanada con Arroz primavera' -> 'merluza apanada'."""
    d = plato.lower()
    d = re.split(r"\bcon\b|\bc/|\(|/", d)[0]          # corta guarniciones y aclaraciones
    d = re.sub(r"[^a-záéíóúñ\s]", " ", d)             # deja solo letras
    palabras = [p for p in d.split() if len(p) > 2]
    return " ".join(palabras[:3]).strip()


def imagen_para(plato: str | None) -> str:
    """Devuelve una URL de imagen referencial para el plato dado."""
    if not PEXELS_KEY or not plato:
        return FALLBACK
    q = query_desde_plato(plato) or "almuerzo"
    url = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode(
        {"query": f"{q} comida", "per_page": 1, "orientation": "landscape"}
    )
    req = urllib.request.Request(url, headers={"Authorization": PEXELS_KEY})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.load(r)
        fotos = data.get("photos") or []
        if fotos:
            return fotos[0]["src"].get("large") or fotos[0]["src"]["original"]
    except Exception as e:  # noqa: BLE001
        print(f"  aviso: Pexels fallo ({e}); uso imagen generica.")
    return FALLBACK


if __name__ == "__main__":
    import sys
    plato = sys.argv[1] if len(sys.argv) > 1 else "Merluza apanada con arroz"
    print(query_desde_plato(plato), "->", imagen_para(plato))
