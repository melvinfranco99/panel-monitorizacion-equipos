"""El MONITOR: un hilo en segundo plano que comprueba los equipos cada X segundos.

Flujo de un ciclo:
  1. Lee de la BD los equipos activos.
  2. Los comprueba TODOS A LA VEZ con un pool de hilos (si no, 50 equipos
     caídos x 1 s de espera = 50 s por ciclo).
  3. Guarda cada resultado en 'comprobaciones' (historial).
  4. Recalcula el estado del equipo; si cambia (cae o se recupera) lo apunta
     en 'eventos' y, si está configurado, avisa por Telegram.
  5. Borra el historial más antiguo que el periodo de retención.
"""
import json
import logging
import threading
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from . import comprobador
from .db import conectar

log = logging.getLogger("panel.monitor")

FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"


def ahora():
    return datetime.now().strftime(FORMATO_FECHA)


def calcular_estado(estado_actual, fallos_consecutivos, responde, fallos_para_caido):
    """Regla de decisión del estado (función pura: fácil de probar con tests).

    - Si responde -> 'up' y el contador de fallos vuelve a 0.
    - Si no responde -> suma un fallo; pasa a 'down' solo cuando acumula
      'fallos_para_caido' fallos seguidos. Mientras tanto mantiene su estado.
    """
    if responde:
        return "up", 0
    fallos = fallos_consecutivos + 1
    if fallos >= fallos_para_caido:
        return "down", fallos
    return estado_actual, fallos


def registrar_resultado(conexion, equipo, responde, latencia, fecha, fallos_para_caido,
                        notificar=None):
    """Guarda un resultado y actualiza el estado del equipo. Devuelve el nuevo estado."""
    conexion.execute(
        "INSERT INTO comprobaciones (equipo_id, fecha, responde, latencia_ms) VALUES (?, ?, ?, ?)",
        (equipo["id"], fecha, 1 if responde else 0, latencia),
    )
    nuevo_estado, fallos = calcular_estado(equipo["estado"], equipo["fallos_consecutivos"],
                                           responde, fallos_para_caido)
    conexion.execute(
        """UPDATE equipos SET estado = ?, latencia_ms = ?, fallos_consecutivos = ?,
                              ultima_comprobacion = ? WHERE id = ?""",
        (nuevo_estado, latencia, fallos, fecha, equipo["id"]),
    )
    if nuevo_estado != equipo["estado"]:
        conexion.execute(
            "INSERT INTO eventos (equipo_id, fecha, estado_anterior, estado_nuevo) VALUES (?, ?, ?, ?)",
            (equipo["id"], fecha, equipo["estado"], nuevo_estado),
        )
        # No avisamos del primer cambio 'desconocido' -> 'up' (es el arranque).
        if notificar and not (equipo["estado"] == "desconocido" and nuevo_estado == "up"):
            notificar(equipo, nuevo_estado)
    return nuevo_estado


def enviar_telegram(token, chat_id, texto):
    """Envía un mensaje por la API HTTP de Telegram (sin librerías externas)."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    datos = urllib.parse.urlencode({"chat_id": chat_id, "text": texto}).encode()
    try:
        with urllib.request.urlopen(url, data=datos, timeout=5) as respuesta:
            return json.load(respuesta).get("ok", False)
    except OSError as error:
        log.warning("No se pudo enviar el aviso por Telegram: %s", error)
        return False


class Monitor:
    def __init__(self, config):
        self.config = config
        self._parar = threading.Event()
        self._hilo = None
        self._cerrojo = threading.Lock()   # evita dos ciclos a la vez

    # ---------- avisos ----------
    def _notificar(self, equipo, nuevo_estado):
        icono = "🔴 CAÍDO" if nuevo_estado == "down" else "🟢 RECUPERADO"
        texto = f"{icono}: {equipo['nombre']} ({equipo['ip']}) - {ahora()}"
        log.info(texto)
        if self.config["TELEGRAM_TOKEN"] and self.config["TELEGRAM_CHAT_ID"]:
            enviar_telegram(self.config["TELEGRAM_TOKEN"], self.config["TELEGRAM_CHAT_ID"], texto)

    # ---------- un ciclo completo ----------
    def ciclo(self):
        with self._cerrojo:
            conexion = conectar(self.config["DATABASE"])
            try:
                equipos = conexion.execute("SELECT * FROM equipos WHERE activo = 1").fetchall()
                if equipos:
                    timeout = self.config["TIMEOUT"]
                    demo = self.config["MODO_DEMO"]
                    with ThreadPoolExecutor(max_workers=min(64, len(equipos))) as pool:
                        resultados = list(pool.map(
                            lambda e: comprobador.comprobar_equipo(e, timeout, demo), equipos))
                    fecha = ahora()
                    for equipo, (responde, latencia) in zip(equipos, resultados):
                        registrar_resultado(conexion, equipo, responde, latencia, fecha,
                                            self.config["FALLOS_PARA_CAIDO"], self._notificar)
                limite = (datetime.now() - timedelta(days=self.config["RETENCION_DIAS"]))
                conexion.execute("DELETE FROM comprobaciones WHERE fecha < ?",
                                 (limite.strftime(FORMATO_FECHA),))
                conexion.commit()
                return len(equipos)
            finally:
                conexion.close()

    def ciclo_en_segundo_plano(self):
        """Para el botón 'Comprobar ahora': no bloquea la petición web."""
        threading.Thread(target=self._ciclo_seguro, daemon=True).start()

    def _ciclo_seguro(self):
        try:
            self.ciclo()
        except Exception:  # un error puntual no debe matar el monitor
            log.exception("Error en el ciclo de comprobación")

    # ---------- bucle infinito ----------
    def _bucle(self):
        log.info("Monitor iniciado (cada %s s, modo demo=%s)",
                 self.config["INTERVALO"], self.config["MODO_DEMO"])
        while not self._parar.is_set():
            self._ciclo_seguro()
            self._parar.wait(self.config["INTERVALO"])  # espera interrumpible

    def iniciar(self):
        if self._hilo is None:
            self._hilo = threading.Thread(target=self._bucle, name="monitor", daemon=True)
            self._hilo.start()

    def detener(self):
        self._parar.set()
