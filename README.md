# 🦆 Menú Los Patos

Lee automáticamente el menú del Casino Los Patos (DISE UdeC) y te lo entrega
todos los días por **WhatsApp** y en un **widget del iPhone**. Solo régimen común.

Todo corre gratis en GitHub Actions. Costo: $0.

## ¿Cómo funciona?

```
dise.udec.cl  →  scraper (Python)  →  data/menu.json  →  WhatsApp + widget iPhone
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
| `widget/menu-widget.js` | Widget de Scriptable para el iPhone |
| `.github/workflows/daily.yml` | Lo ejecuta solo, lun–vie en la mañana |
| `data/menu.json` | El menú ya procesado (lo genera el robot) |

## Probar en tu computador

```bash
pip install -r requirements.txt
cd scraper
python build.py          # genera ../data/menu.json
```

## Fase 1 — Dejarlo automático (GitHub)

1. Crea una cuenta en https://github.com (gratis) si no tienes.
2. Crea un repo nuevo (ej. `menu-los-patos`) y sube esta carpeta.
3. Listo: la pestaña **Actions** ejecutará el robot lun–vie. También puedes
   correrlo a mano con **Run workflow**.

> Horario: el cron está en UTC. `0 12 * * 1-5` = 08:00 Chile en invierno
> (09:00 en verano). Cambia el número en `daily.yml` para ajustar la hora.

## Fase 2 — WhatsApp (CallMeBot)

1. Agrega a tus contactos el número **+34 644 51 95 23** (CallMeBot).
2. Envíale por WhatsApp el mensaje: `I allow callmebot to send me messages`
3. Te responderá con tu **apikey**.
4. En tu repo de GitHub: **Settings → Secrets and variables → Actions → New secret**
   y crea dos secretos:
   - `CALLMEBOT_PHONE` → tu número con código país sin `+` (ej. `56912345678`)
   - `CALLMEBOT_APIKEY` → la apikey que te dieron
5. Desde mañana te llegará el menú a la hora del cron.

> ¿Quieres compartirlo con compañeros? Se puede migrar a la API oficial de Meta
> (número de prueba gratis, hasta 5 personas). Ver Fase 4.

## Fase 3 — Widget en el iPhone (Scriptable)

1. Instala **Scriptable** desde la App Store (gratis).
2. Abre `widget/menu-widget.js`, copia su contenido en un script nuevo.
3. Cambia `RAW_URL` por la URL de tu `menu.json`:
   `https://raw.githubusercontent.com/Pacortes2021/menu-los-patos/main/data/menu.json`
4. Mantén presionada la pantalla de inicio → **+** → Scriptable → widget mediano →
   en "Script" elige este. iOS lo refresca solo cada cierto rato.

## Fase 4 — Ideas para después

- Menú de la semana en el widget (toque para ver el detalle).
- Manejo de feriados.
- Filtro "solo veggie".
- Compartir por WhatsApp con la API oficial de Meta.

## Nota

Proyecto personal/educativo. Los datos son del sitio público de DISE UdeC; si el
sitio cambia de formato, hay que ajustar el parser de `scrape.py` (el robot avisa
en el log si un día viene vacío).
