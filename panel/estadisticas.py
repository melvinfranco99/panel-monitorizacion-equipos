"""Cálculos sobre el historial: disponibilidad (uptime) y series para gráficas."""
from datetime import datetime, timedelta

from .monitor import FORMATO_FECHA


def _desde(horas):
    return (datetime.now() - timedelta(hours=horas)).strftime(FORMATO_FECHA)


def disponibilidad(conexion, equipo_id, horas):
    """% de comprobaciones con respuesta en las últimas 'horas'. None si no hay datos.

    Disponibilidad = comprobaciones OK / comprobaciones totales x 100
    """
    fila = conexion.execute(
        "SELECT AVG(responde) * 100 AS uptime FROM comprobaciones WHERE equipo_id = ? AND fecha >= ?",
        (equipo_id, _desde(horas)),
    ).fetchone()
    return None if fila["uptime"] is None else round(fila["uptime"], 2)


def disponibilidad_global(conexion, horas=24):
    fila = conexion.execute(
        """SELECT AVG(c.responde) * 100 AS uptime FROM comprobaciones c
           JOIN equipos e ON e.id = c.equipo_id WHERE e.activo = 1 AND c.fecha >= ?""",
        (_desde(horas),),
    ).fetchone()
    return None if fila["uptime"] is None else round(fila["uptime"], 2)


def disponibilidad_por_equipo(conexion, horas=24):
    """Diccionario {equipo_id: uptime} con una sola consulta (GROUP BY)."""
    filas = conexion.execute(
        """SELECT equipo_id, AVG(responde) * 100 AS uptime FROM comprobaciones
           WHERE fecha >= ? GROUP BY equipo_id""",
        (_desde(horas),),
    ).fetchall()
    return {f["equipo_id"]: round(f["uptime"], 2) for f in filas}


def serie_por_tramos(conexion, equipo_id, horas=24):
    """Agrupa el historial en tramos (1 h si son 24 h, 6 h si es una semana...).

    Devuelve una lista ordenada de dicts {inicio, uptime, latencia, muestras};
    los tramos sin datos aparecen con uptime None (barra gris en la gráfica).
    """
    tramo_horas = 1 if horas <= 48 else 6 if horas <= 24 * 7 else 24
    ahora = datetime.now().replace(minute=0, second=0, microsecond=0)
    n_tramos = max(1, horas // tramo_horas)
    primer_inicio = ahora - timedelta(hours=tramo_horas * (n_tramos - 1))
    primer_inicio = primer_inicio.replace(hour=primer_inicio.hour - primer_inicio.hour % tramo_horas)

    filas = conexion.execute(
        "SELECT fecha, responde, latencia_ms FROM comprobaciones WHERE equipo_id = ? AND fecha >= ? ORDER BY fecha",
        (equipo_id, primer_inicio.strftime(FORMATO_FECHA)),
    ).fetchall()

    tramos = []
    for i in range(n_tramos + 1):
        inicio = primer_inicio + timedelta(hours=tramo_horas * i)
        if inicio > datetime.now():
            break
        tramos.append({"inicio": inicio, "ok": 0, "total": 0, "suma_lat": 0.0, "n_lat": 0})

    for fila in filas:
        fecha = datetime.strptime(fila["fecha"], FORMATO_FECHA)
        indice = int((fecha - primer_inicio).total_seconds() // (tramo_horas * 3600))
        if 0 <= indice < len(tramos):
            t = tramos[indice]
            t["total"] += 1
            t["ok"] += fila["responde"]
            if fila["latencia_ms"] is not None:
                t["suma_lat"] += fila["latencia_ms"]
                t["n_lat"] += 1

    return [{
        "inicio": t["inicio"].strftime("%Y-%m-%d %H:%M"),
        "uptime": round(t["ok"] / t["total"] * 100, 2) if t["total"] else None,
        "latencia": round(t["suma_lat"] / t["n_lat"], 2) if t["n_lat"] else None,
        "muestras": t["total"],
    } for t in tramos]


def ultimas_latencias(conexion, equipo_id, limite=120):
    """Últimas N comprobaciones (para la gráfica de latencia detallada)."""
    filas = conexion.execute(
        "SELECT fecha, responde, latencia_ms FROM comprobaciones WHERE equipo_id = ? ORDER BY id DESC LIMIT ?",
        (equipo_id, limite),
    ).fetchall()
    return [dict(f) for f in reversed(filas)]
