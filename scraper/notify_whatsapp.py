"""
Envia el menu de HOY por WhatsApp usando CallMeBot (gratis, para uso personal).

Requiere dos variables de entorno (se configuran como Secrets en GitHub):
  CALLMEBOT_PHONE   numero con codigo de pais, sin +  (ej: 56912345678)
  CALLMEBOT_APIKEY  la apikey que te entrega CallMeBot al activarlo

Si hoy no hay menu (fin de semana / feriado), no envia nada.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import urllib.parse
import urllib.request

RAIZ = pathlib.Path(__file__).resolve().parent.parent
MENU_JSON = RAIZ / "data" / "menu.json"


def menu_de_hoy() -> dict | None:
    data = json.loads(MENU_JSON.read_text(encoding="utf-8"))
    for dia in data["dias"]:
        if dia["fecha"] == data["hoy"]:
            return dia
    return None


def formatear(dia: dict) -> str:
    f = dia["fecha"]
    d, m = f[8:10], f[5:7]
    lineas = [f"\U0001F986 *Casino Los Patos* — {dia['dia_semana']} {d}/{m}"]
    if dia.get("ensalada"):
        lineas.append(f"\U0001F957 {dia['ensalada']}")
    if dia.get("alternativa_1"):
        lineas.append(f"1️⃣ {dia['alternativa_1']}")
    if dia.get("alternativa_2"):
        lineas.append(f"2️⃣ {dia['alternativa_2']}")
    if dia.get("postres"):
        lineas.append(f"\U0001F370 {' · '.join(dia['postres'])}")
    return "\n".join(lineas)


def enviar(texto: str, phone: str, apikey: str) -> None:
    params = urllib.parse.urlencode(
        {"phone": phone, "text": texto, "apikey": apikey}
    )
    url = f"https://api.callmebot.com/whatsapp.php?{params}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        print("CallMeBot:", resp.status, resp.read(200).decode("utf-8", "ignore"))


def main() -> None:
    phone = os.environ.get("CALLMEBOT_PHONE")
    apikey = os.environ.get("CALLMEBOT_APIKEY")
    if not phone or not apikey:
        print("Sin CALLMEBOT_PHONE/CALLMEBOT_APIKEY: no se envia WhatsApp.")
        return

    dia = menu_de_hoy()
    if not dia:
        print("Hoy no hay menu (fin de semana / feriado). No se envia.")
        return

    texto = formatear(dia)
    print("Mensaje:\n" + texto)
    enviar(texto, phone, apikey)


if __name__ == "__main__":
    sys.exit(main())
