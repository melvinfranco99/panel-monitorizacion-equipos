"""Inicio de sesión del administrador y protección CSRF."""
import hmac
import secrets
from functools import wraps

from flask import abort, current_app, flash, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


def preparar(app):
    # Guardamos solo el HASH de la contraseña (nunca la contraseña en claro en memoria de sesión).
    app.config["ADMIN_HASH"] = generate_password_hash(app.config["ADMIN_PASSWORD"])
    app.config["PASSWORD_POR_DEFECTO"] = app.config["ADMIN_PASSWORD"] == "admin"

    @app.before_request
    def comprobar_csrf():
        """Todo formulario POST debe traer el token secreto que pusimos en la sesión.

        Así otra web no puede hacer que tu navegador envíe un formulario a este
        panel sin que lo sepas (ataque CSRF: Cross-Site Request Forgery).
        """
        if request.method == "POST" and not current_app.config.get("TESTING_SIN_CSRF"):
            token = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token", "")
            if not token or not hmac.compare_digest(token, session.get("csrf_token", "")):
                abort(400, "Token CSRF inválido. Recarga la página.")

    @app.context_processor
    def variables_plantillas():
        return {"csrf_token": token_csrf, "es_admin": session.get("admin", False)}


def token_csrf():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    return session["csrf_token"]


def credenciales_correctas(usuario, password):
    config = current_app.config
    usuario_ok = hmac.compare_digest(usuario.encode(), config["ADMIN_USUARIO"].encode())
    password_ok = check_password_hash(config["ADMIN_HASH"], password)
    return usuario_ok and password_ok


def login_requerido(vista):
    """Decorador: la vista solo la puede usar el administrador."""
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if not session.get("admin"):
            flash("Inicia sesión como administrador para hacer eso.", "aviso")
            return redirect(url_for("web.login", siguiente=request.path))
        return vista(*args, **kwargs)
    return envoltura


def lectura_permitida(vista):
    """Decorador: si LOGIN_LECTURA está activo, también hay que iniciar sesión para mirar."""
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if current_app.config["LOGIN_LECTURA"] and not session.get("admin"):
            if request.path.startswith("/api/"):
                abort(401)
            return redirect(url_for("web.login", siguiente=request.path))
        return vista(*args, **kwargs)
    return envoltura
