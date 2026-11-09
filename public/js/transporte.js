/* ==========================================================================
   Página "Transporte"
   1. Genera la tabla editable (costos, oferta, demanda) estilo Taha.
   2. Valida en el cliente y envía los datos por fetch (JSON) a /api/transporte.
   3. Dibuja la solución inicial paso a paso, las iteraciones MODI (con el
      ciclo +/− resaltado) y la solución óptima.
   ========================================================================== */
"use strict";

(() => {
  const { el, fmt } = Comun;

  const form = document.getElementById("form-transporte");
  const inpM = document.getElementById("num-origenes");
  const inpN = document.getElementById("num-destinos");
  const contTabla = document.getElementById("contenedor-tabla");
  const selMetodo = document.getElementById("metodo-inicial");
  const msg = document.getElementById("mensaje-form");
  const resultados = document.getElementById("resultados");
  const btnResolver = document.getElementById("btn-resolver");
  const btnComparar = document.getElementById("btn-comparar");

  // Ejemplo SunRay Transport (Taha): 3 silos y 4 molinos.
  const EJEMPLO = {
    nombresO: ["Silo 1", "Silo 2", "Silo 3"],
    nombresD: ["Molino 1", "Molino 2", "Molino 3", "Molino 4"],
    costos: [[10, 2, 20, 11], [12, 7, 9, 20], [4, 14, 16, 18]],
    oferta: [15, 25, 10],
    demanda: [5, 15, 15, 15],
  };

  // ------------------------------------------------------------------------
  // Tabla de entrada
  // ------------------------------------------------------------------------
  /** Lee los valores actuales (como texto) para conservarlos al regenerar. */
  function valoresActuales() {
    const q = (sel) => [...contTabla.querySelectorAll(sel)];
    return {
      nombresO: q("input.nombre-o").map((x) => x.value),
      nombresD: q("input.nombre-d").map((x) => x.value),
      costos: q("tbody tr").map((tr) => [...tr.querySelectorAll("input.costo")].map((x) => x.value)),
      oferta: q("input.oferta").map((x) => x.value),
      demanda: q("input.demanda").map((x) => x.value),
    };
  }

  function generarTabla(m, n, datos = {}) {
    const v = (arr, i, def = "") => (arr && arr[i] !== undefined ? arr[i] : def);
    const tabla = el("table", { class: "tabla-entrada" });

    const cab = el("tr", {}, el("th", { class: "esquina", scope: "col" }, el("span", { class: "sr" }, "Origen")));
    for (let j = 0; j < n; j++) {
      cab.append(el("th", { scope: "col" }, el("input", {
        type: "text", class: "nombre nombre-d", value: v(datos.nombresD, j, `D${j + 1}`),
        "aria-label": `Nombre del destino ${j + 1}`, maxlength: "30",
      })));
    }
    cab.append(el("th", { scope: "col", class: "col-oferta" }, "Oferta"));
    tabla.append(el("thead", {}, cab));

    const cuerpo = el("tbody");
    for (let i = 0; i < m; i++) {
      const tr = el("tr", {}, el("th", { scope: "row" }, el("input", {
        type: "text", class: "nombre nombre-o", value: v(datos.nombresO, i, `O${i + 1}`),
        "aria-label": `Nombre del origen ${i + 1}`, maxlength: "30",
      })));
      for (let j = 0; j < n; j++) {
        tr.append(el("td", {}, el("input", {
          type: "text", inputmode: "decimal", class: "costo", value: v(datos.costos && datos.costos[i], j),
          "aria-label": `Costo del origen ${i + 1} al destino ${j + 1}`, placeholder: "0",
        })));
      }
      tr.append(el("td", { class: "col-oferta" }, el("input", {
        type: "text", inputmode: "decimal", class: "oferta", value: v(datos.oferta, i),
        "aria-label": `Oferta del origen ${i + 1}`, placeholder: "0",
      })));
      cuerpo.append(tr);
    }
    tabla.append(cuerpo);

    const pie = el("tr", { class: "fila-demanda" }, el("th", { scope: "row" }, "Demanda"));
    for (let j = 0; j < n; j++) {
      pie.append(el("td", {}, el("input", {
        type: "text", inputmode: "decimal", class: "demanda", value: v(datos.demanda, j),
        "aria-label": `Demanda del destino ${j + 1}`, placeholder: "0",
      })));
    }
    pie.append(el("td", { class: "ayuda", id: "totales" }));
    tabla.append(el("tfoot", {}, pie));

    contTabla.replaceChildren(tabla);
    actualizarTotales();
  }

  function actualizarTotales() {
    const suma = (sel) => [...contTabla.querySelectorAll(sel)]
      .reduce((s, x) => s + (Comun.aNumero(x.value).valor || 0), 0);
    const o = suma("input.oferta"), d = suma("input.demanda");
    const celda = document.getElementById("totales");
    if (celda) {
      celda.textContent = `Σ ${fmt(o)} / ${fmt(d)}`;
      celda.title = o === d ? "Balanceado" : "No balanceado: se agregará un ficticio";
    }
  }

  function generarDesdeControles(conservar = true) {
    const m = Comun.leerDimension(inpM), n = Comun.leerDimension(inpN);
    if (!m || !n) {
      Comun.mensaje(msg, "El número de orígenes y de destinos debe ser un entero entre 1 y 10.");
      return false;
    }
    Comun.mensaje(msg, "");
    generarTabla(m, n, conservar ? valoresActuales() : {});
    return true;
  }

  /** Lee y valida el formulario. Devuelve el objeto JSON o null. */
  function leerDatos() {
    const filas = [...contTabla.querySelectorAll("tbody tr")];
    const todos = [...contTabla.querySelectorAll("input.costo, input.oferta, input.demanda")];
    const val = Comun.validarInputs(todos);
    if (!val.ok) {
      Comun.mensaje(msg, val.mensaje);
      val.primero && val.primero.focus();
      return null;
    }
    const num = (x) => Comun.aNumero(x.value).valor;
    const datos = {
      costos: filas.map((tr) => [...tr.querySelectorAll("input.costo")].map(num)),
      oferta: [...contTabla.querySelectorAll("input.oferta")].map(num),
      demanda: [...contTabla.querySelectorAll("input.demanda")].map(num),
      metodo_inicial: selMetodo.value,
      objetivo: Comun.objetivoSeleccionado(form),
      nombres_origenes: [...contTabla.querySelectorAll("input.nombre-o")].map((x) => x.value.trim()),
      nombres_destinos: [...contTabla.querySelectorAll("input.nombre-d")].map((x) => x.value.trim()),
    };
    const sum = (a) => a.reduce((s, x) => s + x, 0);
    if (sum(datos.oferta) <= 0 || sum(datos.demanda) <= 0) {
      Comun.mensaje(msg, "La oferta total y la demanda total deben ser mayores que 0.");
      return null;
    }
    Comun.mensaje(msg, "");
    return datos;
  }

  // ------------------------------------------------------------------------
  // Tabla de solución (reutilizada en pasos, iteraciones y óptimo)
  // ------------------------------------------------------------------------
  /**
   * Construye una tabla de transporte.
   * op: { X, basicas, reducidos, u, v, entrante, ciclo, signos, elegida,
   *       filasTachadas, colsTachadas, penF, penC, lineaElegida,
   *       oferta, demanda, etqOferta, etqDemanda }
   */
  function tablaSolucion(d, op) {
    const m = d.costos.length, n = d.costos[0].length;
    const esBasica = new Set((op.basicas || []).map(([i, j]) => `${i},${j}`));
    const signo = new Map();
    (op.ciclo || []).forEach(([i, j], k) => signo.set(`${i},${j}`, op.signos[k]));
    const tachF = op.filasTachadas || new Set();
    const tachC = op.colsTachadas || new Set();
    const linea = op.lineaElegida;
    const hayU = Array.isArray(op.u), hayPen = !!(op.penF || op.penC);

    const tabla = el("table", { class: "tabla-solucion" });
    const cab = el("tr", {}, el("th", { scope: "col" }, ""));
    if (hayU) cab.append(el("th", { scope: "col", class: "multiplicador" }, "uᵢ"));
    d.nombres_destinos.forEach((nom, j) => cab.append(el("th", {
      scope: "col", class: [tachC.has(j) ? "tachada" : "", nom === "Ficticio" ? "ficticio-etq" : ""].join(" "),
    }, nom)));
    cab.append(el("th", { scope: "col" }, op.etqOferta || "Oferta"));
    if (hayPen) cab.append(el("th", { scope: "col" }, "Penal."));
    const thead = el("thead", {}, cab);
    if (Array.isArray(op.v)) {
      const fv = el("tr", {}, el("th", { scope: "row" }, ""), el("th", { class: "multiplicador" }, "vⱼ →"));
      op.v.forEach((x) => fv.append(el("th", { class: "multiplicador" }, fmt(x))));
      fv.append(el("th", {}, ""));
      thead.append(fv);
    }
    tabla.append(thead);

    const cuerpo = el("tbody");
    for (let i = 0; i < m; i++) {
      const nom = d.nombres_origenes[i];
      const tr = el("tr", {}, el("th", {
        scope: "row", class: [tachF.has(i) ? "tachada" : "", nom === "Ficticio" ? "ficticio-etq" : ""].join(" "),
      }, nom));
      if (hayU) tr.append(el("th", { class: "multiplicador" }, fmt(op.u[i])));
      for (let j = 0; j < n; j++) {
        const clave = `${i},${j}`;
        const basica = esBasica.has(clave);
        const clases = ["celda"];
        if (basica) clases.push("basica");
        if (tachF.has(i) || tachC.has(j)) clases.push("tachada");
        if (op.entrante && op.entrante[0] === i && op.entrante[1] === j) clases.push("entrante");
        if (op.elegida && op.elegida[0] === i && op.elegida[1] === j) clases.push("elegida");
        const td = el("td", { class: clases.join(" "), "data-i": i, "data-j": j });
        td.append(el("span", { class: "costo", title: "Costo unitario" }, fmt(d.costos[i][j])));
        if (signo.has(clave)) {
          const s = signo.get(clave);
          td.append(el("span", { class: `signo ${s === "+" ? "mas" : "menos"}`, "aria-label": s === "+" ? "más" : "menos" }, s === "+" ? "+" : "−"));
        }
        if (basica) {
          td.append(el("span", { class: "valor" }, fmt(op.X[i][j])));
        } else if (op.reducidos) {
          const r = op.reducidos[i][j];
          td.append(el("span", { class: `reducido${r < 0 ? " negativo" : ""}`, title: "Costo reducido dᵢⱼ" }, fmt(r)));
        }
        tr.append(td);
      }
      tr.append(el("td", { class: "total" }, fmt((op.oferta || d.oferta)[i])));
      if (hayPen) {
        const p = op.penF ? op.penF[i] : null;
        const esMax = linea && linea.tipo === "fila" && linea.indice === i;
        tr.append(el("td", { class: `total penalizacion${esMax ? " max" : ""}` }, p === null || p === undefined ? "—" : fmt(p)));
      }
      cuerpo.append(tr);
    }
    tabla.append(cuerpo);

    const pie = el("tr", {}, el("th", { scope: "row" }, op.etqDemanda || "Demanda"));
    if (hayU) pie.append(el("th", {}, ""));
    (op.demanda || d.demanda).forEach((x) => pie.append(el("td", { class: "total" }, fmt(x))));
    pie.append(el("td", { class: "total" }, ""));
    if (hayPen) pie.append(el("td", { class: "total" }, ""));
    const pies = el("tfoot", {}, pie);
    if (hayPen) {
      const fp = el("tr", {}, el("th", { scope: "row" }, "Penal."));
      for (let j = 0; j < n; j++) {
        const p = op.penC ? op.penC[j] : null;
        const esMax = linea && linea.tipo === "columna" && linea.indice === j;
        fp.append(el("td", { class: `total penalizacion${esMax ? " max" : ""}` }, p === null || p === undefined ? "—" : fmt(p)));
      }
      fp.append(el("td", { class: "total" }, ""), el("td", { class: "total" }, ""));
      pies.append(fp);
    }
    tabla.append(pies);

    // Contenedor con SVG para dibujar el ciclo encima de la tabla.
    const lienzo = el("div", { class: "lienzo-ciclo" }, tabla);
    if (op.ciclo && op.ciclo.length) {
      lienzo.dataset.ciclo = JSON.stringify(op.ciclo);
      lienzo.append(document.createElementNS("http://www.w3.org/2000/svg", "svg"));
    }
    return el("div", { class: "envoltura-tabla" }, lienzo);
  }

  /** Dibuja el ciclo (+/−) uniendo los centros de sus celdas. */
  function dibujarCiclo(lienzo) {
    const svg = lienzo.querySelector("svg");
    if (!svg || !lienzo.offsetWidth) return;
    const base = lienzo.getBoundingClientRect();
    const puntos = JSON.parse(lienzo.dataset.ciclo).map(([i, j]) => {
      const td = lienzo.querySelector(`td[data-i="${i}"][data-j="${j}"]`);
      const r = td.getBoundingClientRect();
      return `${(r.left - base.left + r.width / 2).toFixed(1)},${(r.top - base.top + r.height / 2).toFixed(1)}`;
    });
    puntos.push(puntos[0]);
    svg.setAttribute("width", base.width);
    svg.setAttribute("height", base.height);
    svg.innerHTML = `<polyline points="${puntos.join(" ")}"></polyline>`;
  }

  function redibujarCiclos(raiz = resultados) {
    requestAnimationFrame(() => raiz.querySelectorAll(".lienzo-ciclo[data-ciclo]").forEach(dibujarCiclo));
  }
  window.addEventListener("resize", () => redibujarCiclos());

  function acordeon(titulo, etiqueta, contenido, abierto = false) {
    const det = el("details", { class: "acordeon", open: abierto },
      el("summary", {}, el("span", {}, titulo), etiqueta ? el("span", { class: "etq-iter" }, etiqueta) : null),
      el("div", { class: "contenido" }, contenido));
    det.addEventListener("toggle", () => det.open && redibujarCiclos(det));
    return det;
  }

  function leyenda(items) {
    const mapa = {
      basica: ["l-basica", "Celda básica"], entrante: ["l-entrante", "Celda entrante"],
      mas: ["l-mas", "Signo + del ciclo"], menos: ["l-menos", "Signo − del ciclo"],
      tachada: ["l-tachada", "Línea tachada"],
    };
    return el("div", { class: "leyenda" }, items.map((k) => el("span", { class: mapa[k][0] }, mapa[k][1])));
  }

  // ------------------------------------------------------------------------
  // Render de resultados
  // ------------------------------------------------------------------------
  function seccionInicial(d) {
    const ini = d.inicial;
    const m = d.costos.length, n = d.costos[0].length;
    const X = Array.from({ length: m }, () => Array(n).fill(0));
    const basicas = [];
    const tachF = new Set(), tachC = new Set();

    const lista = el("ol", { class: "pasos" });
    for (const p of ini.pasos) {
      const [i, j] = p.celda;
      // La tabla muestra el estado del paso: líneas tachadas antes del paso,
      // la celda elegida y la asignación acumulada.
      X[i][j] = p.cantidad;
      basicas.push([i, j]);
      const ofertaAntes = p.oferta_restante.slice();
      const demandaAntes = p.demanda_restante.slice();
      ofertaAntes[i] += p.cantidad;
      demandaAntes[j] += p.cantidad;
      lista.append(el("li", {},
        el("p", {}, el("strong", {}, `Paso ${p.numero}. `), p.descripcion),
        tablaSolucion(d, {
          X: X.map((f) => f.slice()), basicas: basicas.slice(), elegida: p.celda,
          filasTachadas: new Set(tachF), colsTachadas: new Set(tachC),
          penF: p.penalizaciones_filas, penC: p.penalizaciones_columnas,
          lineaElegida: p.linea_elegida,
          oferta: ofertaAntes, demanda: demandaAntes,
          etqOferta: "Oferta disp.", etqDemanda: "Demanda disp.",
        })));
      if (p.tachado === "fila" || p.tachado === "ambas") tachF.add(i);
      if (p.tachado === "columna" || p.tachado === "ambas") tachC.add(j);
    }

    const leyendaPasos = ["basica", "tachada"];
    return el("section", { class: "tarjeta" },
      el("h2", {}, `Solución inicial: ${ini.nombre_metodo}`),
      el("div", { class: "resumen" }, Comun.cifra(etqCosto(d) + " inicial", fmt(ini.costo_total)),
        Comun.cifra("Variables básicas", `${ini.basicas.length} (m + n − 1 = ${m + n - 1})`)),
      leyenda(["basica"]),
      tablaSolucion(d, { X: ini.asignacion, basicas: ini.basicas }),
      acordeon("Paso a paso del método", `${ini.pasos.length} pasos`,
        [ini.metodo === "vogel"
          ? el("p", { class: "ayuda" }, "Las penalizaciones se calculan con las celdas no tachadas; la línea elegida aparece resaltada.")
          : null,
        leyenda(leyendaPasos), lista]));
  }

  function seccionModi(d) {
    const its = d.optimo.iteraciones;
    const cont = el("div");
    if (d.objetivo === "max") {
      cont.append(el("p", { class: "mensaje mensaje-aviso" },
        "Maximización: MODI trabaja con la matriz C' = −C, por eso u, v y los costos reducidos se refieren a −C. Los totales se muestran en beneficios."));
    }
    if (d.optimo.basicas_agregadas && d.optimo.basicas_agregadas.length) {
      cont.append(el("p", { class: "mensaje mensaje-aviso" },
        "Se agregaron celdas básicas con valor 0 (ε) para completar m + n − 1 básicas."));
    }
    its.forEach((it, k) => {
      const contenido = [
        leyenda(it.optima ? ["basica"] : ["basica", "entrante", "mas", "menos"]),
        tablaSolucion(d, {
          X: it.asignacion, basicas: it.basicas, reducidos: it.costos_reducidos,
          u: it.u, v: it.v, entrante: it.celda_entrante, ciclo: it.ciclo, signos: it.signos,
        }),
        el("p", { class: "ayuda" }, "En las celdas no básicas se muestra el costo reducido dᵢⱼ = cᵢⱼ − uᵢ − vⱼ (en rojo si es negativo)."),
        el("p", {}, it.descripcion),
      ];
      if (!it.optima) {
        const nombreCelda = ([i, j]) => `${d.nombres_origenes[i]} → ${d.nombres_destinos[j]}`;
        contenido.push(el("p", {},
          el("strong", {}, "Ciclo: "),
          it.ciclo.map((c, idx) => `${it.signos[idx] === "+" ? "+" : "−"}(${nombreCelda(c)})`).join("  ·  ")));
        contenido.push(el("p", {}, `θ = ${fmt(it.theta)} · ${etqCosto(d)} tras la iteración: `, el("strong", {}, fmt(it.costo))));
      }
      const titulo = it.optima ? `Iteración ${k + 1}: prueba de optimalidad` : `Iteración ${k + 1}`;
      const etiqueta = it.optima ? "óptima ✓" : `entra (${it.celda_entrante[0] + 1},${it.celda_entrante[1] + 1}) · θ = ${fmt(it.theta)}`;
      cont.append(acordeon(titulo, etiqueta, contenido, k === 0));
    });
    return el("section", { class: "tarjeta" },
      el("h2", {}, "Iteraciones MODI (método de multiplicadores)"),
      el("p", { class: "ayuda" }, "Con u₁ = 0 se resuelve uᵢ + vⱼ = cᵢⱼ en las celdas básicas."),
      cont);
  }

  function seccionOptima(d) {
    const op = d.optimo;
    const lista = el("ul", { class: "envios" });
    for (const e of op.envios) {
      let texto;
      if (e.ficticio && e.destino === "Ficticio") {
        texto = `${fmt(e.cantidad)} unidades de ${e.origen} no se envían (oferta sobrante, destino ficticio).`;
      } else if (e.ficticio) {
        texto = `${fmt(e.cantidad)} unidades de demanda de ${e.destino} quedan sin satisfacer (origen ficticio).`;
      } else {
        texto = `Enviar ${fmt(e.cantidad)} unidades de ${e.origen} a ${e.destino} (${fmt(e.costo_unitario)} × ${fmt(e.cantidad)} = ${fmt(e.subtotal)}).`;
      }
      lista.append(el("li", { class: e.ficticio ? "ficticio" : "" }, texto));
    }
    return el("section", { class: "tarjeta" },
      el("h2", {}, "Solución óptima"),
      el("div", { class: "resumen" },
        Comun.cifra(etqCosto(d) + " óptimo", fmt(op.costo_total)),
        Comun.insigniaScipy(d.verificacion_scipy, etqCosto(d).toLowerCase())),
      leyenda(["basica"]),
      tablaSolucion(d, { X: op.asignacion, basicas: op.basicas }),
      el("h3", {}, "Plan de envíos"), lista);
  }

  const etqCosto = (d) => (d.objetivo === "max" ? "Beneficio" : "Costo");

  function renderResultado(d) {
    const avisos = [];
    if (!d.balanceado) {
      avisos.push(el("p", { class: "mensaje mensaje-aviso" },
        d.ficticio === "destino"
          ? `Problema no balanceado: la oferta supera a la demanda en ${fmt(d.cantidad_ficticia)} unidades. Se agregó un destino ficticio con costo 0.`
          : `Problema no balanceado: la demanda supera a la oferta en ${fmt(d.cantidad_ficticia)} unidades. Se agregó un origen ficticio con costo 0.`));
    }
    const resumen = el("section", { class: "tarjeta" },
      el("h2", {}, "Resumen"),
      el("div", { class: "resumen" },
        Comun.cifra(`${etqCosto(d)} inicial (${d.inicial.nombre_metodo})`, fmt(d.inicial.costo_total)),
        Comun.cifra(`${etqCosto(d)} óptimo`, fmt(d.optimo.costo_total)),
        Comun.cifra("Iteraciones MODI", String(d.optimo.numero_iteraciones)),
        Comun.insigniaScipy(d.verificacion_scipy, etqCosto(d).toLowerCase())),
      avisos);
    resultados.replaceChildren(resumen, seccionInicial(d), seccionModi(d), seccionOptima(d));
    redibujarCiclos();
    resumen.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function renderComparacion(d) {
    const max = d.objetivo === "max";
    const mejor = d.metodos.reduce((a, b) => ((max ? b.costo_inicial > a.costo_inicial : b.costo_inicial < a.costo_inicial) ? b : a));
    const etq = max ? "Beneficio" : "Costo";
    const tabla = el("table", { class: "tabla-simple" },
      el("thead", {}, el("tr", {},
        el("th", { scope: "col" }, "Método inicial"),
        el("th", { scope: "col", class: "num" }, `${etq} inicial`),
        el("th", { scope: "col", class: "num" }, "Iteraciones MODI"),
        el("th", { scope: "col", class: "num" }, `${etq} óptimo`))),
      el("tbody", {}, d.metodos.map((f) => el("tr", { class: f.costo_inicial === mejor.costo_inicial ? "mejor" : "" },
        el("td", {}, f.nombre_metodo),
        el("td", { class: "num" }, fmt(f.costo_inicial)),
        el("td", { class: "num" }, String(f.iteraciones)),
        el("td", { class: "num" }, fmt(f.costo_optimo))))));
    const sec = el("section", { class: "tarjeta" },
      el("h2", {}, "Comparación de métodos iniciales"),
      el("p", { class: "ayuda" }, "Resaltada: la mejor solución inicial. Todos los métodos llegan al mismo óptimo con MODI."),
      d.ficticio ? el("p", { class: "mensaje mensaje-aviso" }, `Se agregó un ${d.ficticio} ficticio para balancear el problema.`) : null,
      el("div", { class: "envoltura-tabla" }, tabla));
    resultados.replaceChildren(sec);
    sec.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function mostrarError(e) {
    Comun.mensaje(msg, e.message);
    msg.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  // ------------------------------------------------------------------------
  // Eventos
  // ------------------------------------------------------------------------
  document.getElementById("btn-generar").addEventListener("click", () => generarDesdeControles(true));
  contTabla.addEventListener("input", (e) => {
    e.target.removeAttribute("aria-invalid");
    actualizarTotales();
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const datos = leerDatos();
    if (!datos) return;
    await Comun.conCarga(btnResolver, async () => {
      try { renderResultado(await Comun.enviarJSON("/api/transporte", datos)); }
      catch (err) { mostrarError(err); }
    });
  });

  btnComparar.addEventListener("click", async () => {
    const datos = leerDatos();
    if (!datos) return;
    await Comun.conCarga(btnComparar, async () => {
      try { renderComparacion(await Comun.enviarJSON("/api/comparar", datos)); }
      catch (err) { mostrarError(err); }
    });
  });

  document.getElementById("btn-ejemplo").addEventListener("click", () => {
    inpM.value = 3; inpN.value = 4;
    selMetodo.value = "vogel";
    form.querySelector('input[name="objetivo"][value="min"]').checked = true;
    generarTabla(3, 4, EJEMPLO);
    Comun.mensaje(msg, "");
    resultados.replaceChildren();
  });

  document.getElementById("btn-limpiar").addEventListener("click", () => {
    if (!generarDesdeControles(false)) return;
    resultados.replaceChildren();
  });

  // Tabla inicial vacía de 3×4
  generarTabla(Number(inpM.value), Number(inpN.value));
})();
