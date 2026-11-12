// Tema claro / oscuro
(() => {
  const raiz = document.documentElement;
  try { const t = localStorage.getItem("tema"); if (t) raiz.dataset.theme = t; } catch (e) {}
  document.addEventListener("click", (ev) => {
    if (!ev.target.closest(".tema")) return;
    const oscuro = raiz.dataset.theme ? raiz.dataset.theme === "dark"
      : matchMedia("(prefers-color-scheme: dark)").matches;
    raiz.dataset.theme = oscuro ? "light" : "dark";
    try { localStorage.setItem("tema", raiz.dataset.theme); } catch (e) {}
  });
})();

// Pestañas
document.querySelectorAll(".pestanas").forEach((grupo) => {
  const botones = grupo.querySelectorAll("button");
  botones.forEach((b) => b.addEventListener("click", () => {
    botones.forEach((x) => {
      x.setAttribute("aria-selected", x === b);
      document.getElementById(x.dataset.panel).hidden = x !== b;
    });
  }));
});

// Listas de comprobación que se recuerdan en este navegador
document.querySelectorAll(".check-lista input[type=checkbox]").forEach((c, i) => {
  const clave = "check-" + location.pathname + "-" + i;
  try { c.checked = localStorage.getItem(clave) === "1"; } catch (e) {}
  c.addEventListener("change", () => { try { localStorage.setItem(clave, c.checked ? "1" : "0"); } catch (e) {} });
});

// Demo interactiva (simula el panel en el navegador; la app real usa Flask)
(() => {
  const caja = document.getElementById("demo");
  if (!caja) return;
  const equipos = [
    ["Router principal", "192.168.1.1", 1.5], ["Switch planta baja", "192.168.1.2", 1],
    ["Servidor de ficheros", "192.168.1.10", 4], ["Servidor web", "192.168.1.11", 5],
    ["PC Recepción", "192.168.1.50", 9], ["PC Contabilidad", "192.168.1.51", 8],
    ["Impresora", "192.168.1.100", 12], ["NAS copias", "192.168.1.20", 3],
  ].map(([nombre, ip, base]) => ({ nombre, ip, base, apagado: false, fallos: 0, estado: "up", lat: base, ok: 0, total: 0 }));
  const FALLOS_PARA_CAIDO = 2;
  const log = document.getElementById("demo-log");
  const escribir = (t) => {
    const hora = new Date().toLocaleTimeString();
    log.innerHTML = `<div>[${hora}] ${t}</div>` + log.innerHTML;
  };

  function ciclo() {
    equipos.forEach((e) => {
      const responde = !e.apagado && Math.random() > 0.02;
      e.total++;
      if (responde) {
        e.ok++; e.lat = +(e.base * (0.6 + Math.random() * 1.2)).toFixed(1);
        if (e.estado === "down") escribir(`🟢 RECUPERADO: ${e.nombre} (${e.ip})`);
        e.estado = "up"; e.fallos = 0;
      } else {
        e.lat = null; e.fallos++;
        if (e.fallos >= FALLOS_PARA_CAIDO && e.estado !== "down") {
          e.estado = "down"; escribir(`🔴 CAÍDO: ${e.nombre} (${e.ip}) tras ${e.fallos} fallos seguidos`);
        } else if (e.estado === "up") {
          escribir(`⚠ ${e.nombre} no ha respondido (${e.fallos}/${FALLOS_PARA_CAIDO}), aún no se marca caído`);
        }
      }
    });
    pintar();
  }

  function pintar() {
    const up = equipos.filter((e) => e.estado === "up").length;
    const tot = equipos.reduce((a, e) => a + e.total, 0), ok = equipos.reduce((a, e) => a + e.ok, 0);
    document.getElementById("d-total").textContent = equipos.length;
    document.getElementById("d-up").textContent = up;
    document.getElementById("d-down").textContent = equipos.length - up;
    document.getElementById("d-uptime").textContent = tot ? (ok / tot * 100).toFixed(1) + " %" : "–";
    document.getElementById("demo-eq").innerHTML = equipos.map((e, i) => {
      const clase = e.estado === "down" ? "down" : e.fallos ? "warn" : "";
      const txt = e.estado === "down" ? "Caído" : e.fallos ? "Fallo reciente" : `Responde · ${e.lat} ms`;
      return `<button class="${clase}" data-i="${i}" title="Clic para ${e.apagado ? "encender" : "desenchufar"}">
        <b>${e.nombre}</b><small>${e.ip} · ${txt}</small>
        <small>${e.apagado ? "🔌 desenchufado (clic para encender)" : "clic para desenchufar"}</small></button>`;
    }).join("");
  }

  document.getElementById("demo-eq").addEventListener("click", (ev) => {
    const b = ev.target.closest("button"); if (!b) return;
    const e = equipos[b.dataset.i];
    e.apagado = !e.apagado;
    escribir(e.apagado ? `🔌 Has desenchufado ${e.nombre}` : `🔌 Has vuelto a enchufar ${e.nombre}`);
    pintar();
  });
  pintar();
  escribir("Monitor iniciado: comprobación cada 3 s (en la app real, cada 30 s)");
  setInterval(ciclo, 3000);
})();
