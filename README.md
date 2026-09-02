# 🦆 Menú Los Patos

Lee automáticamente el menú del Casino Los Patos (DISE UdeC) y te lo entrega
todos los días por **WhatsApp**. Solo régimen común.

Todo corre gratis en GitHub Actions. Costo: $0.

## ¿Cómo funciona?

```
dise.udec.cl  →  scraper (Python)  →  data/menu.json  →  WhatsApp
                 (GitHub Actions, cada mañana)
```

El casino carga el mes completo, así que el robot trae todo el mes de una sola vez
y guarda los días que tienen menú (los fines de semana se descartan).

## Estructura

| Archivo | Qué hace |
|---|---|
| `scraper/scrape.py` | Lee y parsea el menú de un día |
| `scraper/build.py` | Arma `data/menu.json` con todo el mes |
| `scraper/notify_whatsapp.py` | Envía el menú de hoy por WhatsApp (CallMeBot) |
| `.github/workflows/daily.yml` | Lo ejecuta solo, lun–vie en la mañana |
| `data/menu.json` | El menú ya procesado (lo genera el robot) |

## Probar en tu computador

```bash
pip install -r requirements.txt
cd scraper
python build.py          # genera ../data/menu.json
```

## Configuración

### 1. GitHub Actions (Automático)

1. En tu repo, la pestaña **Actions** ejecutará el robot de lunes a viernes.
2. También puedes correrlo a mano en cualquier momento con **Run workflow**.

> Horario: el cron está configurado en `11:35 UTC` (~07:35 invierno / 08:35 verano en Chile). Puedes ajustar la hora en `.github/workflows/daily.yml`.

### 2. WhatsApp (CallMeBot)

1. Agrega a tus contactos el número **+34 644 51 95 23** (CallMeBot).
2. Envíale por WhatsApp el mensaje: `I allow callmebot to send me messages`
3. Te responderá con tu **apikey**.
4. En tu repo de GitHub: **Settings → Secrets and variables → Actions → New secret**
   y crea dos secretos:
   - `CALLMEBOT_PHONE` → tu número con código país sin `+` (ej. `56912345678`)
   - `CALLMEBOT_APIKEY` → la apikey que te dieron
5. Te llegará el menú todas las mañanas automáticamente.

## Ideas para después

- Manejo de feriados específicos.
- Filtro "solo veggie".
- Compartir por WhatsApp a grupos o más compañeros con la API oficial de Meta.

## Nota

Proyecto personal/educativo. Los datos son del sitio público de DISE UdeC; si el
sitio cambia de formato, hay que ajustar el parser de `scrape.py` (el robot avisa
en el log si un día viene vacío).
