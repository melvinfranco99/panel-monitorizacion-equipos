"""Configuración de la aplicación.

Todos los valores se leen de variables de entorno (o del fichero .env),
para no tener contraseñas ni rutas escritas dentro del código.
"""
import os


def _bool(nombre, por_defecto=False):
    """Convierte una variable de entorno tipo '1', 'true', 'si' en True/False."""
    valor = os.environ.get(nombre)
    if valor is None:
        return por_defecto
    return valor.strip().lower() in ("1", "true", "si", "sí", "yes", "on")


class Config:
    # Clave para firmar la cookie de sesión. En producción SIEMPRE hay que cambiarla.
    SECRET_KEY = os.environ.get("SECRET_KEY", "clave-de-desarrollo-cambiala")

    # Ruta del fichero SQLite donde se guardan equipos e historial.
    DATABASE = os.environ.get("MONITOR_DB", os.path.join("instance", "monitor.db"))

    # Cada cuántos segundos se comprueban todos los equipos.
    INTERVALO = int(os.environ.get("MONITOR_INTERVALO", "30"))

    # Tiempo máximo (segundos) que se espera la respuesta de un equipo.
    TIMEOUT = float(os.environ.get("MONITOR_TIMEOUT", "1"))

    # Fallos seguidos necesarios para marcar un equipo como CAÍDO.
    # Con 2 evitamos falsas alarmas por perder un único paquete.
    FALLOS_PARA_CAIDO = int(os.environ.get("MONITOR_FALLOS_PARA_CAIDO", "2"))

    # Días que se conserva el historial antes de borrarlo.
    RETENCION_DIAS = int(os.environ.get("MONITOR_RETENCION_DIAS", "30"))

    # Modo demo: simula respuestas sin tocar la red (útil para presentar).
    MODO_DEMO = _bool("MONITOR_MODO_DEMO")

    # Arrancar o no el hilo que hace las comprobaciones (en los tests se desactiva).
    PLANIFICADOR = _bool("MONITOR_PLANIFICADOR", True)

    # Si es True, también hay que iniciar sesión para VER el panel.
    LOGIN_LECTURA = _bool("MONITOR_LOGIN_LECTURA")

    # Usuario administrador (para añadir, editar y borrar equipos).
    ADMIN_USUARIO = os.environ.get("MONITOR_ADMIN_USUARIO", "admin")
    ADMIN_PASSWORD = os.environ.get("MONITOR_ADMIN_PASSWORD", "admin")

    # Avisos opcionales por Telegram cuando un equipo cae o se recupera.
    TELEGRAM_TOKEN = os.environ.get("MONITOR_TELEGRAM_TOKEN", "")
    TELEGRAM_CHAT_ID = os.environ.get("MONITOR_TELEGRAM_CHAT_ID", "")
