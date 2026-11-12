"""Punto de entrada para servidores WSGI de producción (gunicorn, waitress).

    gunicorn -w 1 --threads 8 -b 0.0.0.0:5000 wsgi:app

IMPORTANTE: -w 1 (un solo proceso). Cada proceso arranca su propio monitor;
con varios procesos se harían comprobaciones duplicadas.
"""
from dotenv import load_dotenv

load_dotenv()

from panel import create_app  # noqa: E402

app = create_app()
