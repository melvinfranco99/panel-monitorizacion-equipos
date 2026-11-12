/* JavaScript del panel. Sin librerías: usa fetch() para pedir datos JSON a la API
   de Flask y redibuja la página sin recargarla (técnica AJAX). */
const Panel = (() => {
  // Iconos SVG sencillos por tipo de equipo
  const ICONOS = {
    router: '<path d="M3 14h18v5H3zM7 16.5h.01M11 16.5h.01M8 10a6 6 0 0 1 8 0M5 7a10 10 0 0 1 14 0"/>',
    switch: '<rect x="2" y="7" width="20" height="10" rx="2"/><path d="M6 12h.01M10 12h.01M14 12h.01M18 12h.01"/>',
    servidor: '<rect x="3" y="3" width="18" height="8" rx="2"/><rect x="3" y="13" width="18" height="8" rx="2"/><path d="M7 7h.01M7 17h.01"/>',
    ordenador: '<rect x="2" y="4" width="20" height="13" rx="2"/><path d="M8 21h8M12 17v4"/>',
    impresora: '<path d="M6 9V3h12v6M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="7"/>',
    otro: '<circle cx="12" cy="12" r="9"/><path d="M12 8v4M12 16h.01"/>',
  };
  const icono = (tipo) =>
    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${ICONOS[tipo] || ICONOS.otro}</svg>`;

  // Escapar texto antes de meterlo en HTML (evita XSS si un nombre lleva "<script>")
  const esc = (t) => String(t ?? "").replace(/[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const TEXTO_ESTADO = { up: "Responde", down: "Caído", desconocido: "Sin datos" };

  // ------------------------------------------------------------ página principal
  function iniciarInicio() {
    let datos = null, filtroTipo = "", texto = "";

    document.querySelectorAll("#filtros .filtro").forEach((b) =>
      b.addEventListener("click", () => {
        document.querySelectorAll("#filtros .filtro").forEach((x) => x.classList.remove("activo"));
        b.classList.add("activo");
        filtroTipo = b.dataset.tipo;
        pintar();
      }));
    document.getElementById("buscar").addEventListener("input", (e) => {
      texto = e.target.value.toLowerCase();
      pintar();
    });

    function pintar() {
      if (!datos) return;
      const r = datos.resumen;
      document.getElementById("r-total").textContent = r.total;
      document.getElementById("r-up").textContent = r.up;
      document.getElementById("r-down").textContent = r.down;
      document.getElementById("r-uptime").textContent = r.uptime_24h == null ? "–" : r.uptime_24h.toFixed(2) + " %";

      const lista = datos.equipos.filter((e) =>
        (!filtroTipo || e.tipo === filtroTipo) &&
        (!texto || e.nombre.toLowerCase().includes(texto) || e.ip.toLowerCase().includes(texto)));

      document.getElementById("vacio").classList.toggle("oculto", datos.equipos.length > 0);
      document.getElementById("rejilla").innerHTML = lista.map((e) => {
        const up = e.uptime_24h;
        const metodo = e.puerto ? `TCP ${e.puerto}` : "ping";
        return `
        <a class="equipo ${e.activo ? esc(e.estado) : "pausado"}" href="/equipo/${e.id}">
          <div class="fila">
            <span class="nombre">${icono(e.tipo)} ${esc(e.nombre)}</span>
            <span class="punto ${esc(e.estado)}" title="${TEXTO_ESTADO[e.estado] || ""}"></span>
          </div>
          <div class="fila meta"><code>${esc(e.ip)}</code><span>${metodo}</span></div>
          <div class="fila meta">
            <span>${e.activo ? (TEXTO_ESTADO[e.estado] || "") : "Pausado"}${e.latencia_ms != null ? " · " + e.latencia_ms.toFixed(1) + " ms" : ""}${e.estado === "up" && e.fallos_consecutivos > 0 ? " · ⚠ fallo reciente" : ""}</span>
            <span>${up == null ? "–" : up.toFixed(1) + " %"}</span>
          </div>
          <div class="mini-barra" title="Disponibilidad últimas 24 h"><span style="width:${up ?? 0}%"></span></div>
        </a>`;
      }).join("");
    }

    async function actualizar() {
      try {
        const resp = await fetch("/api/estado");
        if (!resp.ok) throw new Error(resp.status);
        datos = await resp.json();
        pintar();
        document.getElementById("actualizado").textContent =
          `Actualizado a las ${new Date().toLocaleTimeString()} · se comprueba cada ${datos.intervalo} s · la página se refresca sola`;
      } catch (err) {
        document.getElementById("actualizado").textContent = "No se puede contactar con el servidor del panel (" + err.message + ")";
      }
    }
    actualizar();
    setInterval(actualizar, 5000);
  }

  // ------------------------------------------------------------ página de detalle
  function iniciarDetalle(id) {
    let horas = 24;
    document.querySelectorAll("#rango .filtro").forEach((b) =>
      b.addEventListener("click", () => {
        document.querySelectorAll("#rango .filtro").forEach((x) => x.classList.remove("activo"));
        b.classList.add("activo");
        horas = Number(b.dataset.horas);
        cargar();
      }));

    async function cargar() {
      const resp = await fetch(`/api/equipos/${id}/historial?horas=${horas}`);
      const d = await resp.json();
      pintarBarras(d.tramos);
      pintarGrafica(d.recientes);
    }

    function pintarBarras(tramos) {
      document.getElementById("barras").innerHTML = tramos.map((t) => {
        const clase = t.uptime == null ? "" : t.uptime >= 99.9 ? "b-ok" : t.uptime >= 75 ? "b-medio" : "b-mal";
        const info = t.uptime == null ? "sin datos" : `${t.uptime} % · ${t.latencia ?? "–"} ms · ${t.muestras} comprob.`;
        return `<span class="${clase}" title="${esc(t.inicio)} → ${info}"></span>`;
      }).join("");
    }

    // Gráfica de líneas dibujada a mano en SVG (sin librerías externas)
    function pintarGrafica(puntos) {
      const caja = document.getElementById("grafica");
      if (!puntos.length) { caja.innerHTML = '<p class="nota">Aún no hay comprobaciones.</p>'; return; }
      const W = 800, H = 200, m = { izq: 40, der: 10, arr: 10, abj: 22 };
      const lats = puntos.map((p) => p.latencia_ms).filter((v) => v != null);
      const max = Math.max(1, ...lats) * 1.15;
      const x = (i) => m.izq + (i / Math.max(1, puntos.length - 1)) * (W - m.izq - m.der);
      const y = (v) => H - m.abj - (v / max) * (H - m.arr - m.abj);

      let camino = "", abierto = false;
      puntos.forEach((p, i) => {
        if (p.latencia_ms == null) { abierto = false; return; }
        camino += `${abierto ? "L" : "M"}${x(i).toFixed(1)},${y(p.latencia_ms).toFixed(1)} `;
        abierto = true;
      });
      const fallos = puntos.map((p, i) => p.responde ? "" :
        `<rect class="fallo" x="${x(i) - 2}" y="${H - m.abj - 8}" width="4" height="8"><title>${esc(p.fecha)}: sin respuesta</title></rect>`).join("");
      const lineasEje = [0, 0.5, 1].map((f) => {
        const v = max * f, yy = y(v);
        return `<line class="eje" x1="${m.izq}" x2="${W - m.der}" y1="${yy}" y2="${yy}"/>
                <text x="${m.izq - 6}" y="${yy + 4}" text-anchor="end">${v.toFixed(v < 10 ? 1 : 0)}</text>`;
      }).join("");
      const primera = puntos[0].fecha.slice(11, 16), ultima = puntos[puntos.length - 1].fecha.slice(11, 16);

      caja.innerHTML = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" role="img" aria-label="Gráfica de latencia">
        ${lineasEje}
        <path class="linea" d="${camino}"/>
        ${fallos}
        <text x="${m.izq}" y="${H - 4}">${primera}</text>
        <text x="${W - m.der}" y="${H - 4}" text-anchor="end">${ultima} · ms</text>
      </svg>`;
    }

    cargar();
    setInterval(cargar, 15000);
  }

  return { iniciarInicio, iniciarDetalle };
})();
