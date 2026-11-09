/* ==========================================================================
   Utilidades compartidas por transporte.js y asignacion.js
   - Creación de elementos del DOM
   - Formateo de números
   - Validación en el cliente
   - Comunicación con la API (fetch + JSON)
   ========================================================================== */
"use strict";

const Comun = (() => {
  /** Crea un elemento: el("td", {class: "x"}, "texto", otroNodo) */
  function el(etiqueta, atributos = {}, ...hijos) {
    const nodo = document.createElement(etiqueta);
    for (const [clave, valor] of Object.entries(atributos || {})) {
      if (valor === null || valor === undefined || valor === false) continue;
      if (clave === "class") nodo.className = valor;
      else if (clave === "html") nodo.innerHTML = valor;
      else if (clave.startsWith("on")) nodo.addEventListener(clave.slice(2), valor);
      else nodo.setAttribute(clave, valor === true ? "" : valor);
    }
    for (const h of hijos.flat()) {
      if (h === null || h === undefined || h === false) continue;
      nodo.append(h instanceof Node ? h : document.createTextNode(String(h)));
    }
    return nodo;
  }

  const formato = new Intl.NumberFormat("es", { maximumFractionDigits: 4 });

  /** Formatea un número con hasta 4 decimales (formato español). */
  function fmt(x) {
    if (x === null || x === undefined) return "—";
    return formato.format(Number(x));
  }

  /** Convierte el texto de un input a número (acepta coma decimal). */
  function aNumero(texto) {
    const t = String(texto).trim().replace(",", ".");
    if (t === "") return { ok: false, motivo: "vacío" };
    const v = Number(t);
    if (!Number.isFinite(v)) return { ok: false, motivo: "no numérico" };
    if (v < 0) return { ok: false, motivo: "negativo" };
    return { ok: true, valor: v };
  }

  /**
   * Valida una lista de inputs numéricos. Marca con aria-invalid los erróneos
   * y devuelve {ok, valores, mensaje}.
   */
  function validarInputs(inputs) {
    let vacios = 0, invalidos = 0, negativos = 0, primero = null;
    const valores = [];
    for (const inp of inputs) {
      const r = aNumero(inp.value);
      inp.setAttribute("aria-invalid", r.ok ? "false" : "true");
      if (!r.ok) {
        primero = primero || inp;
        if (r.motivo === "vacío") vacios++;
        else if (r.motivo === "negativo") negativos++;
        else invalidos++;
      }
      valores.push(r.ok ? r.valor : null);
    }
    const partes = [];
    if (vacios) partes.push(`${vacios} campo(s) vacío(s)`);
    if (invalidos) partes.push(`${invalidos} valor(es) no numérico(s)`);
    if (negativos) partes.push(`${negativos} valor(es) negativo(s)`);
    return {
      ok: partes.length === 0,
      valores,
      primero,
      mensaje: partes.length ? `Revisa los datos: ${partes.join(", ")}. Solo se admiten números ≥ 0.` : "",
    };
  }

  /** Lee y valida una dimensión (1–10). */
  function leerDimension(input) {
    const v = Number(input.value);
    const ok = Number.isInteger(v) && v >= 1 && v <= 10;
    input.setAttribute("aria-invalid", ok ? "false" : "true");
    return ok ? v : null;
  }

  /** Muestra u oculta un mensaje en un contenedor .mensaje */
  function mensaje(div, texto, tipo = "error") {
    if (!texto) { div.hidden = true; div.textContent = ""; return; }
    div.className = `mensaje mensaje-${tipo}`;
    div.textContent = texto;
    div.hidden = false;
  }

  /**
   * Envía datos JSON por POST y devuelve la respuesta JSON.
   * Si el servidor responde con error, lanza Error con el mensaje en español.
   */
  async function enviarJSON(url, datos) {
    let respuesta;
    try {
      respuesta = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify(datos),
      });
    } catch (e) {
      throw new Error("No se pudo conectar con el servidor. Revisa tu conexión.");
    }
    let cuerpo = null;
    try { cuerpo = await respuesta.json(); } catch (e) { /* sin JSON */ }
    if (!respuesta.ok) {
      throw new Error((cuerpo && cuerpo.error) || `Error del servidor (HTTP ${respuesta.status}).`);
    }
    return cuerpo;
  }

  /** Pone un botón en estado "cargando" mientras dura una promesa. */
  async function conCarga(boton, tarea) {
    const original = boton.innerHTML;
    boton.disabled = true;
    boton.innerHTML = '<span class="cargando" aria-hidden="true"></span> Calculando…';
    try { return await tarea(); }
    finally { boton.disabled = false; boton.innerHTML = original; }
  }

  /** Insignia de verificación con scipy. */
  function insigniaScipy(verif, etiqueta = "costo") {
    const ok = verif && verif.coincide;
    return el("span", {
      class: `insignia ${ok ? "insignia-ok" : "insignia-mal"}`,
      title: verif ? verif.metodo : "",
    }, ok
      ? `Coincide con scipy (${etiqueta} ${fmt(verif.costo_total)})`
      : `No coincide con scipy (scipy: ${fmt(verif && verif.costo_total)})`);
  }

  function cifra(etiqueta, valor) {
    return el("div", { class: "cifra" }, el("span", { class: "etiqueta" }, etiqueta), el("strong", {}, valor));
  }

  function objetivoSeleccionado(form) {
    const r = form.querySelector('input[name="objetivo"]:checked');
    return r ? r.value : "min";
  }

  return { el, fmt, aNumero, validarInputs, leerDimension, mensaje, enviarJSON, conCarga, insigniaScipy, cifra, objetivoSeleccionado };
})();
