"""
Envia el menu de HOY por WhatsApp usando CallMeBot (gratis, para uso personal).

Requiere dos variables de entorno (se configuran como Secrets en GitHub):
  CALLMEBOT_PHONE   numero con codigo de pais, sin +  (ej: 56912345678)
  CALLMEBOT_APIKEY  la apikey que te entrega CallMeBot al activarlo

Si hoy no hay menu (fin de semana / feriado), no envia nada.
"""

from __future__ import annotations

import datetime
import json
import os
import pathlib
import sys
import time
import urllib.parse
import datetime
import json
import os
import pathlib
import sys
import time
import urllib.parse
import urllib.request

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("America/Santiago")
except Exception:
    TZ = None

RAIZ = pathlib.Path(__file__).resolve().parent.parent
MENU_JSON = RAIZ / "data" / "menu.json"


def hoy_chile() -> str:
    ahora = datetime.datetime.now(TZ) if TZ else datetime.datetime.now()
    return ahora.date().isoformat()


def menu_de_hoy() -> dict | None:
    if not MENU_JSON.exists():
        print(f"Error: no existe el archivo {MENU_JSON}", file=sys.stderr)
        return None
    data = json.loads(MENU_JSON.read_text(encoding="utf-8"))
    hoy = hoy_chile()
    for dia in data.get("dias", []):
        if dia.get("fecha") == hoy:
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


def enviar(texto: str, phone: str, apikey: str) -> bool:
    params = urllib.parse.urlencode(
        {"phone": phone, "text": texto, "apikey": apikey}
    )
    url = f"https://api.callmebot.com/whatsapp.php?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (menu-los-patos)"})

    max_intentos = 3
    for intento in range(1, max_intentos + 1):
        try:
            print(f"Enviando WhatsApp vía CallMeBot (intento {intento}/{max_intentos})...")
            with urllib.request.urlopen(req, timeout=30) as resp:
                cuerpo = resp.read().decode("utf-8", "ignore")
                print(f"CallMeBot (status {resp.status}): {cuerpo}")
                if "error" in cuerpo.lower() or "invalid" in cuerpo.lower():
                    print("AVISO: CallMeBot devolvió error en el contenido.", file=sys.stderr)
                else:
                    return True
        except Exception as e:
            print(f"Error en intento {intento}: {e}", file=sys.stderr)

        if intento < max_intentos:
            espera = intento * 5
            print(f"Esperando {espera} segundos antes de reintentar...")
            time.sleep(espera)

    return False


def main() -> None:
    phone = os.environ.get("CALLMEBOT_PHONE")
    apikey = os.environ.get("CALLMEBOT_APIKEY")
    if not phone or not apikey:
        print("Sin CALLMEBOT_PHONE/CALLMEBOT_APIKEY: no se envia WhatsApp.")
        return

    hoy = hoy_chile()
    dia = menu_de_hoy()
    if not dia:
        print(f"Hoy ({hoy}) no hay menú cargado o es fin de semana. No se envía.")
        return

    texto = formatear(dia)
    print("Mensaje a enviar:\n" + texto)
    if enviar(texto, phone, apikey):
        print(f"Notificación de hoy ({hoy}) enviada exitosamente.")
    else:
        print("No se pudo enviar la notificación tras todos los intentos.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
