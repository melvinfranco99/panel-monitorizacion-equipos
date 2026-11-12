"""Comprobación de si un equipo responde.

Dos métodos:
  * PING (ICMP echo request / echo reply): sirve para casi cualquier equipo.
  * TCP: intenta abrir una conexión a un puerto (p. ej. 80 o 443). Útil cuando
    el equipo bloquea el ping (los Windows lo bloquean por defecto) o cuando
    queremos saber si un SERVICIO concreto está funcionando, no solo la máquina.
"""
import ipaddress
import platform
import random
import re
import socket
import subprocess
import time

# Nombre DNS válido: letras, números, guiones y puntos (no puede empezar por '-').
_PATRON_HOST = re.compile(r"^(?=.{1,253}$)[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
                          r"(\.[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*$")

# Extrae la latencia de la salida de ping: "time=12.3 ms", "tiempo<1ms", "time=4ms"
_PATRON_LATENCIA = re.compile(r"(?:time|tiempo)\s*[=<]\s*([\d.,]+)\s*ms", re.IGNORECASE)


def direccion_valida(texto):
    """True si el texto es una IP (v4/v6) o un nombre de host válido.

    Esto es importante por SEGURIDAD: el valor acaba como argumento del comando
    ping, así que no dejamos pasar espacios, ';', '|' ni nada que empiece por '-'.
    """
    texto = (texto or "").strip()
    try:
        ipaddress.ip_address(texto)
        return True
    except ValueError:
        return bool(_PATRON_HOST.match(texto))


def _comando_ping(host, timeout):
    sistema = platform.system().lower()
    if sistema == "windows":
        # -n 1: un paquete   -w: espera en milisegundos
        return ["ping", "-n", "1", "-w", str(int(timeout * 1000)), host]
    if sistema == "darwin":
        # En macOS -W va en milisegundos
        return ["ping", "-c", "1", "-W", str(int(timeout * 1000)), host]
    # Linux: -c 1: un paquete   -W: espera en segundos (mínimo 1)
    return ["ping", "-c", "1", "-W", str(max(1, round(timeout))), host]


def hacer_ping(host, timeout=1.0):
    """Lanza un ping. Devuelve (responde: bool, latencia_ms: float | None)."""
    comando = _comando_ping(host, timeout)
    inicio = time.perf_counter()
    try:
        # Lista de argumentos y SIN shell=True -> no hay inyección de comandos.
        resultado = subprocess.run(comando, capture_output=True, text=True,
                                   timeout=timeout + 2)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False, None
    transcurrido_ms = (time.perf_counter() - inicio) * 1000

    salida = resultado.stdout or ""
    if resultado.returncode != 0:
        return False, None
    # En Windows, "Host de destino inalcanzable" devuelve código 0: miramos que haya TTL.
    if platform.system().lower() == "windows" and "ttl=" not in salida.lower():
        return False, None

    coincidencia = _PATRON_LATENCIA.search(salida)
    if coincidencia:
        latencia = float(coincidencia.group(1).replace(",", "."))
    else:
        latencia = transcurrido_ms
    return True, round(latencia, 2)


def comprobar_tcp(host, puerto, timeout=1.0):
    """Intenta abrir una conexión TCP (saludo en tres pasos SYN, SYN-ACK, ACK)."""
    inicio = time.perf_counter()
    try:
        with socket.create_connection((host, int(puerto)), timeout=timeout):
            return True, round((time.perf_counter() - inicio) * 1000, 2)
    except OSError:
        return False, None


def simular(equipo):
    """Resultado inventado para el MODO DEMO (no se envía nada a la red)."""
    latencia_base = {"router": 1.5, "switch": 1.0, "servidor": 4.0,
                     "ordenador": 8.0, "impresora": 12.0}.get(equipo["tipo"], 20.0)
    # Los equipos con id múltiplo de 5 son "problemáticos": fallan a menudo.
    prob_fallo = 0.12 if equipo["id"] % 5 == 0 else 0.03
    if random.random() < prob_fallo:
        return False, None
    return True, round(latencia_base * random.uniform(0.6, 1.8), 2)


def comprobar_equipo(equipo, timeout=1.0, demo=False):
    """Decide qué método usar con un equipo y devuelve (responde, latencia_ms)."""
    if demo:
        return simular(equipo)
    if equipo["puerto"]:
        return comprobar_tcp(equipo["ip"], equipo["puerto"], timeout)
    return hacer_ping(equipo["ip"], timeout)
