"""
Construye data/menu.json con el menu (regimen comun) del mes actual.

- Toma la fecha de hoy en horario de Chile (America/Santiago).
- Scrapea todos los dias del mes actual.
- Si quedan pocos dias para fin de mes, scrapea tambien el mes siguiente,
  para que la "semana que viene" siempre este cubierta.
- Guarda solo los dias que tienen menu (los fines de semana se descartan).
"""

from __future__ import annotations

import calendar
import datetime
import json
import pathlib
import sys

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("America/Santiago")
except Exception:  # pragma: no cover - fallback si falta tzdata
    TZ = None

from scrape import fetch_dia, MenuDia  # noqa: E402

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "data" / "menu.json"


def hoy_chile() -> datetime.date:
    ahora = datetime.datetime.now(TZ) if TZ else datetime.datetime.now()
    return ahora.date()


def necesita_scraping(forzar: bool = False) -> bool:
    """Verifica si es estrictamente necesario consultar la web de la DISE."""
    if forzar:
        return True
    if not SALIDA.exists():
        return True

    hoy = hoy_chile()
    hoy_iso = hoy.isoformat()

    try:
        data = json.loads(SALIDA.read_text(encoding="utf-8"))
    except Exception:
        return True

    dias = data.get("dias", [])
    if not dias:
        return True

    fechas_disponibles = {d.get("fecha") for d in dias if isinstance(d, dict)}

    # 1. Si hoy es dia habil (lunes a viernes) y no esta en el archivo, necesitamos scrapear
    es_dia_habil = hoy.weekday() < 5
    if es_dia_habil and hoy_iso not in fechas_disponibles:
        return True

    # 2. Si quedan <=3 dias de mes y aun no tenemos el proximo mes cargado, intentamos traerlo
    _, ultimo = calendar.monthrange(hoy.year, hoy.month)
    if ultimo - hoy.day <= 3:
        sig_mes = 1 if hoy.month == 12 else hoy.month + 1
        sig_anio = hoy.year + 1 if hoy.month == 12 else hoy.year
        prefijo_sig = f"{sig_anio:04d}-{sig_mes:02d}-"
        tiene_sig_mes = any(f.startswith(prefijo_sig) for f in fechas_disponibles)
        if not tiene_sig_mes:
            return True

    return False


def scrapear_mes(mes: int, anio: int) -> list[MenuDia]:
    _, ultimo = calendar.monthrange(anio, mes)
    dias: list[MenuDia] = []
    for d in range(1, ultimo + 1):
        try:
            m = fetch_dia(d, mes, anio)
        except Exception as e:  # noqa: BLE001
            print(f"  aviso: fallo {d}/{mes}/{anio}: {e}", file=sys.stderr)
            continue
        if m.hay_menu:
            dias.append(m)
    return dias


def construir(forzar: bool = False) -> dict | None:
    hoy = hoy_chile()

    if not necesita_scraping(forzar=forzar):
        print(f"Cache valido: el menu de hoy ({hoy.isoformat()}) y del mes ya esta guardado. Omitiendo scraping.")
        return None

    print(f"Iniciando scraping mensual para {hoy.strftime('%B %Y')}...")

    # Cargar dias previamente conocidos para no borrarlos si la DISE tiene un fallo temporal
    dias_map: dict[str, dict] = {}
    if SALIDA.exists():
        try:
            previo = json.loads(SALIDA.read_text(encoding="utf-8"))
            for d in previo.get("dias", []):
                if isinstance(d, dict) and "fecha" in d:
                    dias_map[d["fecha"]] = d
        except Exception:
            pass

    nuevos_dias = scrapear_mes(hoy.month, hoy.year)

    # Si faltan <=5 dias para fin de mes, sumar el mes siguiente.
    _, ultimo = calendar.monthrange(hoy.year, hoy.month)
    if ultimo - hoy.day <= 5:
        sig_mes = 1 if hoy.month == 12 else hoy.month + 1
        sig_anio = hoy.year + 1 if hoy.month == 12 else hoy.year
        nuevos_dias += scrapear_mes(sig_mes, sig_anio)

    # Incorporar los nuevos dias obtenidos del sitio
    for m in nuevos_dias:
        dias_map[m.fecha] = m.to_dict()

    # Filtrar para mantener desde el inicio del mes actual en adelante
    primer_dia_mes = f"{hoy.year:04d}-{hoy.month:02d}-01"
    lista_dias = [d for d in dias_map.values() if d.get("fecha", "") >= primer_dia_mes]
    lista_dias.sort(key=lambda m: m["fecha"])

    return {
        "generado": datetime.datetime.now(TZ if TZ else None).isoformat(timespec="seconds"),
        "fuente": "https://dise.udec.cl/?q=node/171",
        "hoy": hoy.isoformat(),
        "total_dias": len(lista_dias),
        "dias": lista_dias,
    }


def main() -> None:
    forzar = "--force" in sys.argv or "-f" in sys.argv
    data = construir(forzar=forzar)
    if data is not None:
        SALIDA.parent.mkdir(parents=True, exist_ok=True)
        SALIDA.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"OK -> {SALIDA} ({data['total_dias']} dias con menu, hoy={data['hoy']})")


if __name__ == "__main__":
    main()
