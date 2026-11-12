"""Pruebas automáticas. Ejecutar con:  python -m pytest -v"""
import pytest

from panel import create_app, importar_csv
from panel.comprobador import comprobar_tcp, direccion_valida, hacer_ping
from panel.db import conectar
from panel.monitor import calcular_estado, registrar_resultado


@pytest.fixture
def app(tmp_path):
    app = create_app({
        "TESTING": True, "TESTING_SIN_CSRF": True, "PLANIFICADOR": False,
        "DATABASE": str(tmp_path / "test.db"), "MODO_DEMO": True,
        "ADMIN_PASSWORD": "secreta",
    })
    return app


@pytest.fixture
def cliente(app):
    return app.test_client()


def entrar(cliente):
    return cliente.post("/login", data={"usuario": "admin", "password": "secreta"})


# ---------- validación de direcciones (seguridad) ----------
@pytest.mark.parametrize("texto", ["192.168.1.1", "10.0.0.254", "::1", "servidor.local", "google.com"])
def test_direcciones_validas(texto):
    assert direccion_valida(texto)


@pytest.mark.parametrize("texto", ["", "-c 1000", "1.1.1.1; rm -rf /", "a b", "$(reboot)", "x|y"])
def test_direcciones_peligrosas_rechazadas(texto):
    assert not direccion_valida(texto)


# ---------- regla de estado ----------
def test_un_fallo_no_marca_caido():
    assert calcular_estado("up", 0, False, 2) == ("up", 1)


def test_dos_fallos_marcan_caido():
    assert calcular_estado("up", 1, False, 2) == ("down", 2)


def test_responder_recupera():
    assert calcular_estado("down", 5, True, 2) == ("up", 0)


# ---------- comprobaciones reales contra el propio equipo ----------
def test_ping_localhost():
    responde, latencia = hacer_ping("127.0.0.1", 1)
    assert responde and latencia is not None


def test_tcp_puerto_cerrado():
    assert comprobar_tcp("127.0.0.1", 1, 0.5) == (False, None)


# ---------- historial y eventos ----------
def test_registrar_genera_evento_al_caer(app):
    con = conectar(app.config["DATABASE"])
    con.execute("INSERT INTO equipos (nombre, ip, estado) VALUES ('PC', '10.0.0.5', 'up')")
    avisos = []
    for _ in range(2):
        equipo = con.execute("SELECT * FROM equipos").fetchone()
        registrar_resultado(con, equipo, False, None, "2026-01-01 10:00:00", 2,
                            lambda e, est: avisos.append(est))
    assert con.execute("SELECT estado FROM equipos").fetchone()["estado"] == "down"
    assert con.execute("SELECT COUNT(*) FROM comprobaciones").fetchone()[0] == 2
    assert con.execute("SELECT estado_nuevo FROM eventos").fetchone()[0] == "down"
    assert avisos == ["down"]


# ---------- web ----------
def test_pagina_principal_y_api(cliente, app):
    importar_csv(app.config["DATABASE"], "ejemplos/equipos_demo.csv")
    app.extensions["monitor"].ciclo()
    assert cliente.get("/").status_code == 200
    datos = cliente.get("/api/estado").get_json()
    assert datos["resumen"]["total"] == 12
    assert datos["resumen"]["up"] + datos["resumen"]["down"] + datos["resumen"]["desconocido"] == 12
    assert cliente.get("/api/equipos/1/historial?horas=24").get_json()["tramos"]
    assert cliente.get("/equipo/1").status_code == 200


def test_anadir_equipo_requiere_login(cliente):
    r = cliente.post("/equipos/nuevo", data={"nombre": "X", "ip": "10.0.0.9", "tipo": "router"})
    assert r.status_code == 302 and "/login" in r.headers["Location"]


def test_crud_equipo(cliente):
    entrar(cliente)
    cliente.post("/equipos/nuevo", data={"nombre": "Router", "ip": "10.0.0.1", "tipo": "router", "activo": "on"})
    equipos = cliente.get("/api/estado").get_json()["equipos"]
    assert len(equipos) == 1 and equipos[0]["nombre"] == "Router"
    cliente.post("/equipos/1/editar", data={"nombre": "Router 2", "ip": "10.0.0.1", "tipo": "router"})
    assert cliente.get("/api/estado").get_json()["equipos"][0]["nombre"] == "Router 2"
    cliente.post("/equipos/1/borrar")
    assert cliente.get("/api/estado").get_json()["equipos"] == []


def test_no_acepta_ip_maliciosa(cliente):
    entrar(cliente)
    cliente.post("/equipos/nuevo", data={"nombre": "Malo", "ip": "1.1.1.1;reboot", "tipo": "router"})
    assert cliente.get("/api/estado").get_json()["equipos"] == []


def test_login_incorrecto(cliente):
    cliente.post("/login", data={"usuario": "admin", "password": "mal"})
    with cliente.session_transaction() as s:
        assert not s.get("admin")
