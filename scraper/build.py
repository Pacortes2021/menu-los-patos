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


def construir() -> dict:
    hoy = hoy_chile()
    dias = scrapear_mes(hoy.month, hoy.year)

    # Si faltan <=5 dias para fin de mes, sumar el mes siguiente.
    _, ultimo = calendar.monthrange(hoy.year, hoy.month)
    if ultimo - hoy.day <= 5:
        sig_mes = 1 if hoy.month == 12 else hoy.month + 1
        sig_anio = hoy.year + 1 if hoy.month == 12 else hoy.year
        dias += scrapear_mes(sig_mes, sig_anio)

    dias.sort(key=lambda m: m.fecha)
    return {
        "generado": datetime.datetime.now(TZ if TZ else None).isoformat(timespec="seconds"),
        "fuente": "https://dise.udec.cl/?q=node/171",
        "hoy": hoy.isoformat(),
        "total_dias": len(dias),
        "dias": [m.to_dict() for m in dias],
    }


def main() -> None:
    data = construir()
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK -> {SALIDA} ({data['total_dias']} dias con menu, hoy={data['hoy']})")


if __name__ == "__main__":
    main()
