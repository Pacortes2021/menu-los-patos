// Widget de Scriptable — Menu Casino Los Patos (DISE UdeC)
// 1) Edita RAW_URL con la URL de tu menu.json publicado en GitHub.
//    Ejemplo: https://raw.githubusercontent.com/TU_USUARIO/menu-los-patos/main/data/menu.json
// 2) En el iPhone: pega este codigo en un script nuevo de Scriptable.
// 3) Agrega un widget de Scriptable a la pantalla de inicio y eligelo.

const RAW_URL = "https://raw.githubusercontent.com/Pacortes2021/menu-los-patos/main/data/menu.json";

const AZUL = new Color("#173961");
const CELESTE = new Color("#85B7EB");
const BLANCO = new Color("#FFFFFF");
const CLARO = new Color("#D9E6F5");

async function cargar() {
  const req = new Request(RAW_URL);
  req.timeoutInterval = 15;
  return await req.loadJSON();
}

function menuDeHoy(data) {
  let dia = data.dias.find((d) => d.fecha === data.hoy);
  if (dia) return { dia, esHoy: true };
  // Si hoy no hay (fin de semana), mostrar el proximo dia disponible.
  const prox = data.dias.find((d) => d.fecha > data.hoy);
  return { dia: prox || null, esHoy: false };
}

function etiquetaFecha(dia, esHoy) {
  const partes = dia.fecha.split("-");
  const dm = `${partes[2]}/${partes[1]}`;
  return (esHoy ? "Hoy" : "Próximo") + ` · ${dia.dia_semana} ${dm}`;
}

function fila(stack, emoji, texto, color, size) {
  const t = stack.addText(`${emoji}  ${texto}`);
  t.font = Font.systemFont(size);
  t.textColor = color;
  t.lineLimit = 2;
}

async function construir() {
  const w = new ListWidget();
  w.backgroundColor = AZUL;
  w.setPadding(14, 16, 14, 16);

  let data;
  try {
    data = await cargar();
  } catch (e) {
    const err = w.addText("No pude cargar el menú 😕");
    err.textColor = BLANCO;
    return w;
  }

  const { dia, esHoy } = menuDeHoy(data);

  const titulo = w.addText("🦆 Casino Los Patos");
  titulo.font = Font.semiboldSystemFont(15);
  titulo.textColor = BLANCO;

  if (!dia) {
    w.addSpacer(6);
    const s = w.addText("Sin menú disponible.");
    s.textColor = CLARO;
    return w;
  }

  const fecha = w.addText(etiquetaFecha(dia, esHoy));
  fecha.font = Font.systemFont(11);
  fecha.textColor = CELESTE;

  w.addSpacer(8);

  if (dia.ensalada) fila(w, "🥗", dia.ensalada, CLARO, 11);
  if (dia.alternativa_1) fila(w, "1️⃣", dia.alternativa_1, BLANCO, 13);
  if (dia.alternativa_2) fila(w, "2️⃣", dia.alternativa_2, BLANCO, 13);
  if (dia.postres && dia.postres.length) {
    w.addSpacer(4);
    fila(w, "🍰", dia.postres.join(" · "), CLARO, 11);
  }

  w.addSpacer();
  return w;
}

const widget = await construir();
if (config.runsInWidget) {
  Script.setWidget(widget);
} else {
  widget.presentMedium();
}
Script.complete();
