"""
Envia el menu de HOY por WhatsApp usando CallMeBot (gratis, para uso personal).

Requiere dos variables de entorno (se configuran como Secrets en GitHub):
  CALLMEBOT_PHONE   numero con codigo de pais, sin +  (ej: 56912345678)
  CALLMEBOT_APIKEY  la apikey que te entrega CallMeBot al activarlo

Si hoy no hay menu (fin de semana / feriado), no envia nada.
El archivo data/estado.json evita envios duplicados si el workflow
se dispara mas de una vez en el mismo dia (cron-job.org + schedule de respaldo).
"""

from __future__ import annotations

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
MENU_JSON  = RAIZ / "data" / "menu.json"
ESTADO_JSON = RAIZ / "data" / "estado.json"


# ---------------------------------------------------------------------------
# Helpers de fecha y estado
# ---------------------------------------------------------------------------

def hoy_chile() -> str:
    ahora = datetime.datetime.now(TZ) if TZ else datetime.datetime.now()
    return ahora.date().isoformat()


def ya_enviado_hoy() -> bool:
    """Devuelve True si ya se envio el WhatsApp exitosamente hoy."""
    if not ESTADO_JSON.exists():
        return False
    try:
        data = json.loads(ESTADO_JSON.read_text(encoding="utf-8"))
        return data.get("ultimo_envio") == hoy_chile()
    except Exception:
        return False


def registrar_envio() -> None:
    """Escribe estado.json marcando el envio de hoy."""
    ESTADO_JSON.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now(TZ if TZ else None).isoformat(timespec="seconds")
    ESTADO_JSON.write_text(
        json.dumps({"ultimo_envio": hoy_chile(), "timestamp": ts}, indent=2),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Lectura del menu
# ---------------------------------------------------------------------------

def menu_de_hoy() -> dict | None:
    if not MENU_JSON.exists():
        print(f"Error: no existe {MENU_JSON}", file=sys.stderr)
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
    sep = " \u00b7 "
    lineas = [f"\U0001F986 *Casino Los Patos* \u2014 {dia['dia_semana']} {d}/{m}"]
    if dia.get("ensalada"):
        lineas.append(f"\U0001F957 {dia['ensalada']}")
    if dia.get("alternativa_1"):
        lineas.append(f"1\ufe0f\u20e3 {dia['alternativa_1']}")
    if dia.get("alternativa_2"):
        lineas.append(f"2\ufe0f\u20e3 {dia['alternativa_2']}")
    if dia.get("postres"):
        postres_str = sep.join(dia["postres"])
        lineas.append(f"\U0001F370 {postres_str}")
    return "\n".join(lineas)


# ---------------------------------------------------------------------------
# Envio WhatsApp
# ---------------------------------------------------------------------------

def enviar(texto: str, phone: str, apikey: str) -> bool:
    params = urllib.parse.urlencode({"phone": phone, "text": texto, "apikey": apikey})
    url = f"https://api.callmebot.com/whatsapp.php?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (menu-los-patos)"})

    for intento in range(1, 4):
        try:
            print(f"Enviando WhatsApp via CallMeBot (intento {intento}/3)...")
            with urllib.request.urlopen(req, timeout=30) as resp:
                cuerpo = resp.read().decode("utf-8", "ignore")
                print(f"CallMeBot (status {resp.status}): {cuerpo}")
                if "error" not in cuerpo.lower() and "invalid" not in cuerpo.lower():
                    return True
                print("AVISO: CallMeBot respondio con error en el cuerpo.", file=sys.stderr)
        except Exception as exc:
            print(f"Error en intento {intento}: {exc}", file=sys.stderr)

        if intento < 3:
            espera = intento * 5
            print(f"Reintentando en {espera}s...")
            time.sleep(espera)

    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    phone  = os.environ.get("CALLMEBOT_PHONE")
    apikey = os.environ.get("CALLMEBOT_APIKEY")
    if not phone or not apikey:
        print("Sin CALLMEBOT_PHONE/CALLMEBOT_APIKEY: no se envia WhatsApp.")
        return

    hoy = hoy_chile()

    # Proteccion anti-duplicado: si ya se envio hoy (por cualquier trigger), salir.
    if ya_enviado_hoy():
        print(f"[{hoy}] Ya fue enviado hoy. Omitiendo ejecucion duplicada.")
        return

    dia = menu_de_hoy()
    if not dia:
        print(f"[{hoy}] Sin menu para hoy (fin de semana o feriado). No se envia.")
        return

    texto = formatear(dia)
    print("Mensaje:\n" + texto)

    if enviar(texto, phone, apikey):
        registrar_envio()
        print(f"[{hoy}] Notificacion enviada y registrada correctamente.")
    else:
        print("Fallo el envio tras 3 intentos.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
