"""
Scraper del menu del Casino Los Patos (DISE UdeC).

La pagina (Drupal 7) entrega el menu de un dia via POST con los campos
`dia` y `mes` a https://dise.udec.cl/?q=node/171. El cuerpo es una tabla
con filas tipo "<strong>Etiqueta:</strong> valor".

Solo nos interesa el REGIMEN COMUN (no las dietas), segun lo pedido.
"""

from __future__ import annotations

import re
import sys
import unicodedata
from dataclasses import dataclass, asdict, field

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

URL = "https://dise.udec.cl/?q=node/171"
HEADERS = {"User-Agent": "Mozilla/5.0 (menu-los-patos scraper)"}
TIMEOUT = 25


def _obtener_sesion() -> requests.Session:
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST", "GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


SESION = _obtener_sesion()

DIAS_SEMANA = [
    "lunes", "martes", "miércoles", "jueves",
    "viernes", "sábado", "domingo",
]
MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def _norm(texto: str) -> str:
    """minusculas, sin tildes, sin espacios extra -> para comparar etiquetas."""
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto).strip().lower()


@dataclass
class MenuDia:
    fecha: str                     # YYYY-MM-DD
    dia_semana: str
    ensalada: str | None = None
    alternativa_1: str | None = None
    alternativa_2: str | None = None
    postres: list[str] = field(default_factory=list)
    hay_menu: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def _celdas_etiqueta_valor(soup: BeautifulSoup) -> dict[str, str]:
    """Recorre las celdas <td> con <strong> y devuelve {etiqueta_norm: valor}."""
    cuerpo = soup.select_one("div.field-name-body") or soup
    pares: dict[str, str] = {}
    for td in cuerpo.find_all("td"):
        strong = td.find("strong")
        if not strong:
            continue
        etiqueta = _norm(strong.get_text()).rstrip(":").strip()
        # el valor es el texto de la celda menos la etiqueta
        valor = td.get_text(" ", strip=True)
        valor = valor[len(strong.get_text(" ", strip=True)):]
        valor = re.sub(r"\s+", " ", valor).strip(" :")
        if etiqueta:
            pares[etiqueta] = valor
    return pares


def fetch_dia(dia: int, mes: int, anio: int) -> MenuDia:
    """Pide el menu de un dia y devuelve solo el regimen comun."""
    import datetime
    fecha = datetime.date(anio, mes, dia)
    menu = MenuDia(
        fecha=fecha.isoformat(),
        dia_semana=DIAS_SEMANA[fecha.weekday()],
    )

    resp = SESION.post(
        URL,
        data={"dia": str(dia), "mes": str(mes), "Submit": "Ver Menú"},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    pares = _celdas_etiqueta_valor(soup)

    def get(*claves: str) -> str | None:
        for c in claves:
            v = pares.get(c)
            if v:
                return v
        return None

    menu.ensalada = get("sopa/ensalada", "sopa / ensalada", "sopa", "ensalada")
    menu.alternativa_1 = get("alternativa i", "alternativa 1")
    menu.alternativa_2 = get("alternativa ii", "alternativa 2")
    postres = [get("postre 1", "postre1"), get("postre 2", "postre2")]
    menu.postres = [p for p in postres if p]
    menu.hay_menu = any([menu.alternativa_1, menu.alternativa_2, menu.ensalada])
    return menu


if __name__ == "__main__":
    # Sondeo: recorre los dias dados de un mes y muestra que trae cada uno.
    mes = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    anio = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
    import calendar
    _, ultimo = calendar.monthrange(anio, mes)
    print(f"Sondeo {MESES[mes-1]} {anio} (1..{ultimo}):")
    for d in range(1, ultimo + 1):
        try:
            m = fetch_dia(d, mes, anio)
        except Exception as e:  # noqa: BLE001
            print(f"  {d:2d} {('?'):9s}  ERROR: {e}")
            continue
        marca = "OK " if m.hay_menu else "-- "
        a1 = (m.alternativa_1 or "")[:55]
        print(f"  {d:2d} {m.dia_semana:9s} {marca} {a1}")
