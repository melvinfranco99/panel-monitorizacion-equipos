"""Panel de monitorización de equipos de red.

create_app() es la "fábrica" de la aplicación Flask: crea la app, carga la
configuración, prepara la base de datos, registra las rutas y arranca el monitor.
"""
import csv
import logging

from flask import Flask

from . import db, seguridad
from .config import Config
from .monitor import Monitor


def create_app(config_extra=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_extra:
        app.config.update(config_extra)

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    db.inicializar(app.config["DATABASE"])
    app.teardown_appcontext(db.cerrar_db)
    seguridad.preparar(app)

    from .rutas import web
    app.register_blueprint(web)

    monitor = Monitor(app.config)
    app.extensions["monitor"] = monitor
    if app.config["PLANIFICADOR"]:
        monitor.iniciar()

    return app


def importar_csv(ruta_bd, ruta_csv):
    """Importa equipos desde un CSV con columnas: nombre,ip,tipo,puerto,ubicacion,descripcion.

    Si la IP ya existe, se salta (así se puede ejecutar varias veces sin duplicar).
    Devuelve (añadidos, saltados).
    """
    from .comprobador import direccion_valida
    anadidos = saltados = 0
    conexion = db.conectar(ruta_bd)
    with open(ruta_csv, newline="", encoding="utf-8") as fichero:
        for fila in csv.DictReader(fichero):
            ip = (fila.get("ip") or "").strip()
            if not direccion_valida(ip):
                saltados += 1
                continue
            puerto = (fila.get("puerto") or "").strip()
            cursor = conexion.execute(
                """INSERT OR IGNORE INTO equipos (nombre, ip, tipo, puerto, ubicacion, descripcion)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                ((fila.get("nombre") or ip).strip(), ip, (fila.get("tipo") or "otro").strip(),
                 int(puerto) if puerto.isdigit() else None,
                 (fila.get("ubicacion") or "").strip(), (fila.get("descripcion") or "").strip()))
            if cursor.rowcount:
                anadidos += 1
            else:
                saltados += 1
    conexion.commit()
    conexion.close()
    return anadidos, saltados


__all__ = ["create_app", "importar_csv"]
