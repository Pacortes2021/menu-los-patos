"""
Envia el menu de HOY por WhatsApp usando la API oficial de Meta (WhatsApp
Cloud API), con una FOTO de referencia en el encabezado.

Como es un mensaje que iniciamos nosotros, WhatsApp obliga a usar una
PLANTILLA aprobada. Esta plantilla debe tener:
  - Encabezado (header): tipo IMAGEN
  - Cuerpo (body) con 5 variables, en este orden:
        {{1}} fecha (ej: "miércoles 10/06")
        {{2}} ensalada
        {{3}} alternativa 1
        {{4}} alternativa 2
        {{5}} postres

Variables de entorno (Secrets en GitHub):
  WA_TOKEN      token permanente (System User) de Meta
  WA_PHONE_ID   Phone Number ID del numero de WhatsApp
  WA_TO         numero(s) destino, con codigo pais sin +, separados por coma
  WA_TEMPLATE   nombre de la plantilla (def: menu_casino)
  WA_LANG       idioma de la plantilla (def: es)
  GRAPH_VERSION version del Graph API (def: v21.0)
  PEXELS_KEY    (opcional) para la foto de referencia
"""

from __future__ import annotations

import datetime
import json
import os
import pathlib
import urllib.error
import urllib.request

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("America/Santiago")
except Exception:
    TZ = None

from image_lookup import imagen_para

RAIZ = pathlib.Path(__file__).resolve().parent.parent
MENU_JSON = RAIZ / "data" / "menu.json"


def hoy_chile() -> str:
    ahora = datetime.datetime.now(TZ) if TZ else datetime.datetime.now()
    return ahora.date().isoformat()


def menu_de_hoy() -> dict | None:
    if not MENU_JSON.exists():
        return None
    data = json.loads(MENU_JSON.read_text(encoding="utf-8"))
    hoy = hoy_chile()
    for dia in data.get("dias", []):
        if dia.get("fecha") == hoy:
            return dia
    return None


def construir_payload(dia: dict, to: str, template: str, lang: str) -> dict:
    f = dia["fecha"]
    fecha = f"{dia['dia_semana']} {f[8:10]}/{f[5:7]}"
    plato = dia.get("alternativa_1") or dia.get("alternativa_2") or ""
    img = imagen_para(plato)

    body = [
        fecha,
        dia.get("ensalada") or "—",
        dia.get("alternativa_1") or "—",
        dia.get("alternativa_2") or "—",
        " · ".join(dia.get("postres") or []) or "—",
    ]
    return {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template,
            "language": {"code": lang},
            "components": [
                {
                    "type": "header",
                    "parameters": [{"type": "image", "image": {"link": img}}],
                },
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": t} for t in body],
                },
            ],
        },
    }


def enviar(payload: dict, phone_id: str, token: str, version: str) -> None:
    url = f"https://graph.facebook.com/{version}/{phone_id}/messages"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"  -> {payload['to']}: {r.status} {r.read(300).decode('utf-8','ignore')}")
    except urllib.error.HTTPError as e:
        print(f"  -> {payload['to']}: ERROR {e.code} {e.read().decode('utf-8','ignore')}")


def main() -> None:
    token = os.environ.get("WA_TOKEN")
    phone_id = os.environ.get("WA_PHONE_ID")
    to = os.environ.get("WA_TO")
    if not (token and phone_id and to):
        print("Faltan WA_TOKEN / WA_PHONE_ID / WA_TO: no se envia.")
        return

    template = os.environ.get("WA_TEMPLATE", "menu_casino")
    lang = os.environ.get("WA_LANG", "es")
    version = os.environ.get("GRAPH_VERSION", "v21.0")

    dia = menu_de_hoy()
    if not dia:
        print("Hoy no hay menu (fin de semana / feriado). No se envia.")
        return

    for numero in to.split(","):
        numero = numero.strip()
        if numero:
            payload = construir_payload(dia, numero, template, lang)
            enviar(payload, phone_id, token, version)


if __name__ == "__main__":
    main()
