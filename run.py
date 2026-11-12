"""Arranca el panel en modo desarrollo / uso doméstico.

    python run.py                 -> http://localhost:5000
    python run.py --puerto 8080   -> otro puerto

Para un servidor de empresa usa gunicorn (ver docs/uso.html).
"""
import argparse

from dotenv import load_dotenv

load_dotenv()  # lee el fichero .env si existe (antes de importar la configuración)

from panel import create_app  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Panel de monitorización de equipos")
    parser.add_argument("--host", default="0.0.0.0",
                        help="0.0.0.0 = accesible desde la red; 127.0.0.1 = solo este equipo")
    parser.add_argument("--puerto", type=int, default=5000)
    args = parser.parse_args()

    app = create_app()
    # use_reloader=False: el recargador de Flask arrancaría el monitor DOS veces.
    app.run(host=args.host, port=args.puerto, debug=False, use_reloader=False)
