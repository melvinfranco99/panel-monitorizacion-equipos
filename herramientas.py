"""Herramientas de línea de comandos.

    python herramientas.py importar ejemplos/equipos_casa.csv
    python herramientas.py comprobar        (una ronda de comprobaciones y muestra la tabla)
    python herramientas.py demo             (carga equipos de ejemplo + 7 días de historial simulado)
"""
import argparse
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv

load_dotenv()

from panel import create_app, importar_csv  # noqa: E402
from panel.comprobador import simular  # noqa: E402
from panel.db import conectar  # noqa: E402
from panel.monitor import FORMATO_FECHA, registrar_resultado  # noqa: E402

CARPETA = os.path.dirname(os.path.abspath(__file__))


def generar_historial(ruta_bd, fallos_para_caido, dias=7, cada_minutos=10):
    """Inventa el historial de los últimos días (solo para demostraciones)."""
    conexion = conectar(ruta_bd)
    if conexion.execute("SELECT COUNT(*) FROM comprobaciones").fetchone()[0]:
        print("Ya hay historial; no se genera otro.")
        return
    momento = datetime.now() - timedelta(days=dias)
    pasos = 0
    while momento < datetime.now():
        for equipo in conexion.execute("SELECT * FROM equipos WHERE activo = 1").fetchall():
            responde, latencia = simular(equipo)
            # Una "avería" de 2 horas en el NAS hace 3 días, para que se vea en la gráfica
            if equipo["nombre"].startswith("NAS") and timedelta(days=3) > datetime.now() - momento > timedelta(days=3, hours=-2):
                responde, latencia = False, None
            registrar_resultado(conexion, equipo, responde, latencia,
                                momento.strftime(FORMATO_FECHA), fallos_para_caido)
        momento += timedelta(minutes=cada_minutos)
        pasos += 1
    conexion.commit()
    print(f"Historial simulado generado: {pasos} rondas en {dias} días.")


def main():
    parser = argparse.ArgumentParser(description="Herramientas del panel de monitorización")
    sub = parser.add_subparsers(dest="orden", required=True)
    p_imp = sub.add_parser("importar", help="importa equipos desde un CSV")
    p_imp.add_argument("csv")
    sub.add_parser("comprobar", help="hace una ronda de comprobaciones y muestra el estado")
    sub.add_parser("demo", help="carga los equipos de ejemplo de una pequeña empresa")
    args = parser.parse_args()

    # PLANIFICADOR=False: aquí no queremos el hilo en segundo plano.
    app = create_app({"PLANIFICADOR": False})
    ruta_bd = app.config["DATABASE"]

    if args.orden in ("importar", "demo"):
        ruta = args.csv if args.orden == "importar" else os.path.join(CARPETA, "ejemplos", "equipos_demo.csv")
        anadidos, saltados = importar_csv(ruta_bd, ruta)
        print(f"Añadidos: {anadidos}  ·  Saltados (repetidos o no válidos): {saltados}")
        if args.orden == "demo":
            generar_historial(ruta_bd, app.config["FALLOS_PARA_CAIDO"])

    elif args.orden == "comprobar":
        n = app.extensions["monitor"].ciclo()
        conexion = conectar(ruta_bd)
        print(f"{'ESTADO':>11}  {'DIRECCIÓN':<18} {'NOMBRE':<28} LATENCIA")
        for e in conexion.execute("SELECT * FROM equipos WHERE activo = 1 ORDER BY nombre"):
            lat = f"{e['latencia_ms']} ms" if e["latencia_ms"] is not None else "-"
            print(f"{e['estado']:>11}  {e['ip']:<18} {e['nombre']:<28} {lat}")
        print(f"\n{n} equipos comprobados (un equipo pasa a 'down' tras "
              f"{app.config['FALLOS_PARA_CAIDO']} fallos seguidos).")


if __name__ == "__main__":
    main()
