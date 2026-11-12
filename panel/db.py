"""Acceso a la base de datos SQLite.

Usamos el módulo sqlite3 que viene con Python: no hace falta instalar
ningún servidor de base de datos, todo se guarda en un único fichero.
"""
import os
import sqlite3

from flask import current_app, g

ESQUEMA = """
-- Equipos que se vigilan (ordenadores, servidores, routers...)
CREATE TABLE IF NOT EXISTS equipos (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre               TEXT    NOT NULL,
    ip                   TEXT    NOT NULL UNIQUE,     -- IP o nombre DNS
    tipo                 TEXT    NOT NULL DEFAULT 'ordenador',
    puerto               INTEGER,                     -- si se indica: comprobación TCP
    ubicacion            TEXT    DEFAULT '',
    descripcion          TEXT    DEFAULT '',
    activo               INTEGER NOT NULL DEFAULT 1,  -- 0 = no se comprueba
    estado               TEXT    NOT NULL DEFAULT 'desconocido',  -- up / down / desconocido
    latencia_ms          REAL,
    fallos_consecutivos  INTEGER NOT NULL DEFAULT 0,
    ultima_comprobacion  TEXT,
    creado               TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Una fila por cada comprobación realizada: es el HISTORIAL.
CREATE TABLE IF NOT EXISTS comprobaciones (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    equipo_id   INTEGER NOT NULL REFERENCES equipos(id) ON DELETE CASCADE,
    fecha       TEXT    NOT NULL,
    responde    INTEGER NOT NULL,  -- 1 = sí, 0 = no
    latencia_ms REAL
);
CREATE INDEX IF NOT EXISTS idx_comprobaciones_equipo_fecha
    ON comprobaciones (equipo_id, fecha);

-- Cambios de estado (caídas y recuperaciones): las INCIDENCIAS.
CREATE TABLE IF NOT EXISTS eventos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    equipo_id       INTEGER NOT NULL REFERENCES equipos(id) ON DELETE CASCADE,
    fecha           TEXT    NOT NULL,
    estado_anterior TEXT,
    estado_nuevo    TEXT    NOT NULL
);
"""


def conectar(ruta):
    """Abre una conexión nueva a SQLite (la usa también el hilo monitor)."""
    carpeta = os.path.dirname(ruta)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    conexion = sqlite3.connect(ruta, timeout=10)
    conexion.row_factory = sqlite3.Row          # filas accesibles por nombre: fila["ip"]
    conexion.execute("PRAGMA foreign_keys = ON")  # para que funcione ON DELETE CASCADE
    conexion.execute("PRAGMA journal_mode = WAL")  # lecturas y escrituras a la vez
    return conexion


def inicializar(ruta):
    """Crea las tablas si no existen."""
    with conectar(ruta) as conexion:
        conexion.executescript(ESQUEMA)


def get_db():
    """Conexión para la petición web actual (se cierra al terminar la petición)."""
    if "db" not in g:
        g.db = conectar(current_app.config["DATABASE"])
    return g.db


def cerrar_db(_error=None):
    conexion = g.pop("db", None)
    if conexion is not None:
        conexion.close()
