/* ==========================================================================
   Página "Asignación" (método húngaro)
   Genera la matriz editable, valida, envía por fetch (JSON) a
   /api/asignacion y muestra la asignación óptima y los pasos del método.
   ========================================================================== */
"use strict";

(() => {
  const { el, fmt } = Comun;

  const form = document.getElementById("form-asignacion");
  const inpF = document.getElementById("num-filas");
  const inpC = document.getElementById("num-columnas");
  const contTabla = document.getElementById("contenedor-tabla");
  const msg = document.getElementById("mensaje-form");
  const resultados = document.getElementById("resultados");
  const btnResolver = document.getElementById("btn-resolver");

  // Ejemplo de Taha: 3 niños y 3 tareas (costos en $).
  const EJEMPLO = {
    nombresF: ["Juan", "Karen", "Terri"],
    nombresC: ["Podar", "Pintar", "Lavar autos"],
    costos: [[15, 10, 9], [9, 15, 10], [10, 12, 8]],
  };

  // ------------------------------------------------------------------------
  // Matriz de entrada
  // ------------------------------------------------------------------------
  function valoresActuales() {
    const q = (sel) => [...contTabla.querySelectorAll(sel)];
    return {
      nombresF: q("input.nombre-f").map((x) => x.value),
      nombresC: q("input.nombre-c").map((x) => x.value),
      costos: q("tbody tr").map((tr) => [...tr.querySelectorAll("input.costo")].map((x) => x.value)),
    };
  }

  function generarTabla(nf, nc, datos = {}) {
    const v = (arr, i, def = "") => (arr && arr[i] !== undefined ? arr[i] : def);
    const tabla = el("table", { class: "tabla-entrada" });
    const cab = el("tr", {}, el("th", { class: "esquina" }, el("span", { class: "sr" }, "Agente")));
    for (let j = 0; j < nc; j++) {
      cab.append(el("th", { scope: "col" }, el("input", {
        type: "text", class: "nombre nombre-c", value: v(datos.nombresC, j, `T${j + 1}`),
        "aria-label": `Nombre de la tarea ${j + 1}`, maxlength: "30",
      })));
    }
    tabla.append(el("thead", {}, cab));
    const cuerpo = el("tbody");
    for (let i = 0; i < nf; i++) {
      const tr = el("tr", {}, el("th", { scope: "row" }, el("input", {
        type: "text", class: "nombre nombre-f", value: v(datos.nombresF, i, `A${i + 1}`),
        "aria-label": `Nombre del agente ${i + 1}`, maxlength: "30",
      })));
      for (let j = 0; j < nc; j++) {
        tr.append(el("td", {}, el("input", {
          type: "text", inputmode: "decimal", class: "costo", value: v(datos.costos && datos.costos[i], j),
          "aria-label": `Costo del agente ${i + 1} en la tarea ${j + 1}`, placeholder: "0",
        })));
      }
      cuerpo.append(tr);
    }
    tabla.append(cuerpo);
    contTabla.replaceChildren(tabla);
  }

  function generarDesdeControles(conservar = true) {
    const nf = Comun.leerDimension(inpF), nc = Comun.leerDimension(inpC);
    if (!nf || !nc) {
      Comun.mensaje(msg, "El número de filas y de columnas debe ser un entero entre 1 y 10.");
      return false;
    }
    Comun.mensaje(msg, "");
    generarTabla(nf, nc, conservar ? valoresActuales() : {});
    return true;
  }

  function leerDatos() {
    const inputs = [...contTabla.querySelectorAll("input.costo")];
    const val = Comun.validarInputs(inputs);
    if (!val.ok) {
      Comun.mensaje(msg, val.mensaje);
      val.primero && val.primero.focus();
      return null;
    }
    Comun.mensaje(msg, "");
    const num = (x) => Comun.aNumero(x.value).valor;
    return {
      costos: [...contTabla.querySelectorAll("tbody tr")].map((tr) => [...tr.querySelectorAll("input.costo")].map(num)),
      objetivo: Comun.objetivoSeleccionado(form),
      nombres_filas: [...contTabla.querySelectorAll("input.nombre-f")].map((x) => x.value.trim()),
      nombres_columnas: [...contTabla.querySelectorAll("input.nombre-c")].map((x) => x.value.trim()),
    };
  }

  // ------------------------------------------------------------------------
  // Render
  // ------------------------------------------------------------------------
  /**
   * Matriz de un paso del húngaro.
   * op: { filasCub, colsCub, seleccion, minimosF, minimosC }
   */
  function tablaMatriz(d, matriz, op = {}) {
    const N = matriz.length;
    const nf = d.costos.length, nc = d.costos[0].length;
    const nomF = (i) => (i < nf ? d.nombres_filas[i] : "Ficticia");
    const nomC = (j) => (j < nc ? d.nombres_columnas[j] : "Ficticia");
    const filasCub = new Set(op.filasCub || []);
    const colsCub = new Set(op.colsCub || []);
    const sel = new Set((op.seleccion || []).map(([i, j]) => `${i},${j}`));

    const cab = el("tr", {}, el("th", {}, ""));
    for (let j = 0; j < N; j++) {
      cab.append(el("th", { scope: "col", class: `${colsCub.has(j) ? "cubierta" : ""} ${j >= nc ? "ficticia" : ""}` }, nomC(j)));
    }
    if (op.minimosF) cab.append(el("th", { scope: "col" }, "Mín. fila"));
    const cuerpo = el("tbody");
    for (let i = 0; i < N; i++) {
      const tr = el("tr", {}, el("th", { scope: "row", class: `${filasCub.has(i) ? "cubierta" : ""} ${i >= nf ? "ficticia" : ""}` }, nomF(i)));
      for (let j = 0; j < N; j++) {
        const x = matriz[i][j];
        const clases = ["celda-h"];
        if (x === 0) clases.push("cero");
        const cf = filasCub.has(i), cc = colsCub.has(j);
        if (cf && cc) clases.push("doble");
        else if (cf || cc) clases.push("cubierta");
        if (sel.has(`${i},${j}`)) clases.push("asignada");
        tr.append(el("td", { class: clases.join(" ") }, fmt(x)));
      }
      if (op.minimosF) tr.append(el("td", { class: "total penalizacion" }, fmt(op.minimosF[i])));
      cuerpo.append(tr);
    }
    const tabla = el("table", { class: "tabla-solucion" }, el("thead", {}, cab), cuerpo);
    if (op.minimosC) {
      const fila = el("tr", {}, el("th", { scope: "row" }, "Mín. col."));
      op.minimosC.forEach((x) => fila.append(el("td", { class: "total penalizacion" }, fmt(x))));
      tabla.append(el("tfoot", {}, fila));
    }
    return el("div", { class: "envoltura-tabla" }, tabla);
  }

  function renderResultado(d) {
    const max = d.objetivo === "max";
    const etq = max ? "Beneficio" : "Costo";
    const asignadas = d.asignacion;

    // Tabla original (n×m, sin ficticios) con las celdas asignadas resaltadas
    const nf = d.costos.length, nc = d.costos[0].length;
    const sel = new Set(asignadas.map(([i, j]) => `${i},${j}`));
    const cab = el("tr", {}, el("th", {}, ""), d.nombres_columnas.map((n) => el("th", { scope: "col" }, n)));
    const cuerpo = el("tbody", {}, d.costos.map((fila, i) => el("tr", {},
      el("th", { scope: "row" }, d.nombres_filas[i]),
      fila.map((x, j) => el("td", { class: `celda-h${sel.has(`${i},${j}`) ? " asignada" : ""}` }, fmt(x))))));
    const original = el("div", { class: "envoltura-tabla" },
      el("table", { class: "tabla-solucion" }, el("thead", {}, cab), cuerpo));

    const lista = el("ul", { class: "envios" }, asignadas.map(([i, j]) => el("li", {},
      `${d.nombres_filas[i]} → ${d.nombres_columnas[j]} (${etq.toLowerCase()} ${fmt(d.costos[i][j])})`)));
    for (const [i, j] of d.asignacion_ficticia || []) {
      if (i < nf) lista.append(el("li", { class: "ficticio" }, `${d.nombres_filas[i]} queda sin tarea (columna ficticia).`));
      else if (j < nc) lista.append(el("li", { class: "ficticio" }, `${d.nombres_columnas[j]} queda sin asignar (fila ficticia).`));
    }

    const resumen = el("section", { class: "tarjeta" },
      el("h2", {}, "Asignación óptima"),
      el("div", { class: "resumen" },
        Comun.cifra(`${etq} total`, fmt(d.costo_total)),
        Comun.insigniaScipy(d.verificacion_scipy, etq.toLowerCase())),
      el("div", { class: "leyenda" }, el("span", { class: "l-mas" }, "Celda asignada")),
      original,
      el("h3", {}, "Asignaciones"), lista);

    const pasos = el("ol", { class: "pasos" });
    d.pasos.forEach((p, k) => {
      let tabla;
      if (p.tipo === "reduccion_filas") tabla = tablaMatriz(d, p.matriz, { minimosF: p.minimos });
      else if (p.tipo === "reduccion_columnas") tabla = tablaMatriz(d, p.matriz, { minimosC: p.minimos });
      else if (p.tipo === "cobertura") tabla = tablaMatriz(d, p.matriz, { filasCub: p.filas_cubiertas, colsCub: p.columnas_cubiertas });
      else if (p.tipo === "asignacion") tabla = tablaMatriz(d, p.matriz, { seleccion: p.seleccion });
      else tabla = tablaMatriz(d, p.matriz);
      pasos.append(el("li", {},
        el("h3", {}, `${k + 1}. ${p.titulo}`),
        el("p", {}, p.descripcion),
        tabla));
    });

    const seccionPasos = el("section", { class: "tarjeta" },
      el("h2", {}, "Paso a paso del método húngaro"),
      el("div", { class: "leyenda" },
        el("span", { class: "l-cubierta" }, "Fila/columna cubierta por una línea"),
        el("span", { class: "l-mas" }, "Cero elegido en la asignación")),
      pasos);

    resultados.replaceChildren(resumen, seccionPasos);
    resumen.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  // ------------------------------------------------------------------------
  // Eventos
  // ------------------------------------------------------------------------
  document.getElementById("btn-generar").addEventListener("click", () => generarDesdeControles(true));
  contTabla.addEventListener("input", (e) => e.target.removeAttribute("aria-invalid"));

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const datos = leerDatos();
    if (!datos) return;
    await Comun.conCarga(btnResolver, async () => {
      try { renderResultado(await Comun.enviarJSON("/api/asignacion", datos)); }
      catch (err) { Comun.mensaje(msg, err.message); }
    });
  });

  document.getElementById("btn-ejemplo").addEventListener("click", () => {
    inpF.value = 3; inpC.value = 3;
    form.querySelector('input[name="objetivo"][value="min"]').checked = true;
    generarTabla(3, 3, EJEMPLO);
    Comun.mensaje(msg, "");
    resultados.replaceChildren();
  });

  document.getElementById("btn-limpiar").addEventListener("click", () => {
    if (!generarDesdeControles(false)) return;
    resultados.replaceChildren();
  });

  generarTabla(Number(inpF.value), Number(inpC.value));
})();
