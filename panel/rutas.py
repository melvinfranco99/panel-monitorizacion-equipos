"""Rutas (URLs) de la aplicación: páginas HTML y API JSON."""
import sqlite3

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect,
                   render_template, request, session, url_for)

from . import estadisticas
from .comprobador import direccion_valida
from .db import get_db
from .seguridad import credenciales_correctas, lectura_permitida, login_requerido

web = Blueprint("web", __name__)

TIPOS = ["router", "switch", "servidor", "ordenador", "impresora", "otro"]


def _equipo_o_404(equipo_id):
    equipo = get_db().execute("SELECT * FROM equipos WHERE id = ?", (equipo_id,)).fetchone()
    if equipo is None:
        abort(404)
    return equipo


# ---------------------------------------------------------------- páginas
@web.route("/")
@lectura_permitida
def inicio():
    return render_template("inicio.html", tipos=TIPOS)


@web.route("/equipo/<int:equipo_id>")
@lectura_permitida
def detalle(equipo_id):
    db = get_db()
    equipo = _equipo_o_404(equipo_id)
    uptimes = {etiqueta: estadisticas.disponibilidad(db, equipo_id, horas)
               for etiqueta, horas in (("24 h", 24), ("7 días", 168), ("30 días", 720))}
    eventos = db.execute("SELECT * FROM eventos WHERE equipo_id = ? ORDER BY id DESC LIMIT 20",
                         (equipo_id,)).fetchall()
    return render_template("detalle.html", equipo=equipo, uptimes=uptimes, eventos=eventos)


@web.route("/incidencias")
@lectura_permitida
def incidencias():
    eventos = get_db().execute(
        """SELECT ev.*, e.nombre, e.ip, e.tipo FROM eventos ev
           JOIN equipos e ON e.id = ev.equipo_id
           WHERE ev.estado_anterior != 'desconocido'
           ORDER BY ev.id DESC LIMIT 200""").fetchall()
    return render_template("incidencias.html", eventos=eventos)


# ---------------------------------------------------------------- gestión de equipos
def _leer_formulario():
    """Valida el formulario. Devuelve (datos, errores)."""
    f = request.form
    datos = {
        "nombre": f.get("nombre", "").strip(),
        "ip": f.get("ip", "").strip(),
        "tipo": f.get("tipo", "otro"),
        "puerto": f.get("puerto", "").strip(),
        "ubicacion": f.get("ubicacion", "").strip(),
        "descripcion": f.get("descripcion", "").strip(),
        "activo": 1 if f.get("activo") else 0,
    }
    errores = []
    if not datos["nombre"] or len(datos["nombre"]) > 60:
        errores.append("El nombre es obligatorio (máx. 60 caracteres).")
    if not direccion_valida(datos["ip"]):
        errores.append("La dirección no es una IP ni un nombre de host válido.")
    if datos["tipo"] not in TIPOS:
        errores.append("Tipo de equipo no válido.")
    if datos["puerto"]:
        if not datos["puerto"].isdigit() or not 1 <= int(datos["puerto"]) <= 65535:
            errores.append("El puerto debe ser un número entre 1 y 65535.")
        else:
            datos["puerto"] = int(datos["puerto"])
    else:
        datos["puerto"] = None
    return datos, errores


@web.route("/equipos/nuevo", methods=["GET", "POST"])
@login_requerido
def nuevo():
    datos = {"tipo": "ordenador", "activo": 1}
    if request.method == "POST":
        datos, errores = _leer_formulario()
        if not errores:
            try:
                db = get_db()
                # Consultas con '?': los datos NUNCA se pegan al SQL -> sin inyección SQL.
                db.execute("""INSERT INTO equipos (nombre, ip, tipo, puerto, ubicacion, descripcion, activo)
                              VALUES (:nombre, :ip, :tipo, :puerto, :ubicacion, :descripcion, :activo)""", datos)
                db.commit()
                current_app.extensions["monitor"].ciclo_en_segundo_plano()
                flash(f"Equipo «{datos['nombre']}» añadido.", "ok")
                return redirect(url_for("web.inicio"))
            except sqlite3.IntegrityError:
                errores.append("Ya existe un equipo con esa dirección.")
        for e in errores:
            flash(e, "error")
    return render_template("formulario.html", datos=datos, tipos=TIPOS, titulo="Añadir equipo")


@web.route("/equipos/<int:equipo_id>/editar", methods=["GET", "POST"])
@login_requerido
def editar(equipo_id):
    datos = dict(_equipo_o_404(equipo_id))
    if request.method == "POST":
        nuevos, errores = _leer_formulario()
        if not errores:
            try:
                db = get_db()
                nuevos["id"] = equipo_id
                db.execute("""UPDATE equipos SET nombre=:nombre, ip=:ip, tipo=:tipo, puerto=:puerto,
                              ubicacion=:ubicacion, descripcion=:descripcion, activo=:activo
                              WHERE id=:id""", nuevos)
                db.commit()
                flash("Cambios guardados.", "ok")
                return redirect(url_for("web.detalle", equipo_id=equipo_id))
            except sqlite3.IntegrityError:
                errores.append("Ya existe un equipo con esa dirección.")
        datos.update(nuevos)
        for e in errores:
            flash(e, "error")
    return render_template("formulario.html", datos=datos, tipos=TIPOS, titulo="Editar equipo")


@web.route("/equipos/<int:equipo_id>/borrar", methods=["POST"])
@login_requerido
def borrar(equipo_id):
    equipo = _equipo_o_404(equipo_id)
    db = get_db()
    db.execute("DELETE FROM equipos WHERE id = ?", (equipo_id,))
    db.commit()
    flash(f"Equipo «{equipo['nombre']}» eliminado junto con su historial.", "ok")
    return redirect(url_for("web.inicio"))


@web.route("/comprobar-ahora", methods=["POST"])
@login_requerido
def comprobar_ahora():
    current_app.extensions["monitor"].ciclo_en_segundo_plano()
    flash("Comprobación lanzada. Los resultados aparecerán en unos segundos.", "ok")
    return redirect(request.referrer or url_for("web.inicio"))


# ---------------------------------------------------------------- sesión
@web.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if credenciales_correctas(request.form.get("usuario", ""), request.form.get("password", "")):
            session.clear()
            session["admin"] = True
            flash("Sesión iniciada.", "ok")
            siguiente = request.args.get("siguiente", "")
            # Solo redirigimos a rutas internas (evita "open redirect").
            if not siguiente.startswith("/") or siguiente.startswith("//"):
                siguiente = url_for("web.inicio")
            return redirect(siguiente)
        flash("Usuario o contraseña incorrectos.", "error")
    return render_template("login.html")


@web.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Sesión cerrada.", "ok")
    return redirect(url_for("web.inicio"))


# ---------------------------------------------------------------- API JSON
@web.route("/api/estado")
@lectura_permitida
def api_estado():
    """Estado actual de todos los equipos. La página principal lo pide cada pocos segundos."""
    db = get_db()
    uptimes = estadisticas.disponibilidad_por_equipo(db, 24)
    equipos = []
    for fila in db.execute("SELECT * FROM equipos ORDER BY tipo = 'otro', "
                           "CASE tipo WHEN 'router' THEN 0 WHEN 'switch' THEN 1 WHEN 'servidor' THEN 2 "
                           "WHEN 'ordenador' THEN 3 ELSE 4 END, nombre"):
        e = dict(fila)
        e["uptime_24h"] = uptimes.get(e["id"])
        equipos.append(e)
    activos = [e for e in equipos if e["activo"]]
    return jsonify({
        "equipos": equipos,
        "resumen": {
            "total": len(activos),
            "up": sum(e["estado"] == "up" for e in activos),
            "down": sum(e["estado"] == "down" for e in activos),
            "desconocido": sum(e["estado"] == "desconocido" for e in activos),
            "uptime_24h": estadisticas.disponibilidad_global(db, 24),
        },
        "intervalo": current_app.config["INTERVALO"],
        "modo_demo": current_app.config["MODO_DEMO"],
    })


@web.route("/api/equipos/<int:equipo_id>/historial")
@lectura_permitida
def api_historial(equipo_id):
    _equipo_o_404(equipo_id)
    horas = min(max(request.args.get("horas", 24, type=int), 1), 720)
    db = get_db()
    return jsonify({
        "horas": horas,
        "tramos": estadisticas.serie_por_tramos(db, equipo_id, horas),
        "recientes": estadisticas.ultimas_latencias(db, equipo_id, 120),
    })


@web.app_errorhandler(404)
def no_encontrado(_e):
    return render_template("error.html", codigo=404, mensaje="Página no encontrada"), 404
