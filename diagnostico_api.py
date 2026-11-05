#!/usr/bin/env python3
"""Diagnostico y resolucion de problemas de llamadas a la API.

Reproduce los casos del Modulo 4, seccion 4.8 (diapositivas 52-65) contra la
API de Catalyst Center y muestra, para cada uno, el codigo de estado o el
error, el cuerpo de la respuesta y como resolverlo (diapositiva 58: comprobar
el codigo de retorno, comprobar el cuerpo y usar la referencia de codigos).
"""
import requests
import urllib3
import yaml

with open("configuracion.yaml") as archivo:
    API = yaml.safe_load(archivo)["api"]
with open("credenciales.yaml") as archivo:
    CREDENCIALES = yaml.safe_load(archivo)

URL_BASE = API["url_base"]
AUTENTICACION = (CREDENCIALES["usuario"], CREDENCIALES["clave"])
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def probar(numero, titulo, solucion, metodo, url, **opciones):
    """Ejecuta una solicitud y muestra el resultado del caso."""
    opciones.setdefault("verify", False)
    opciones.setdefault("timeout", 10)
    print(f"\n[{numero}] {titulo}")
    try:
        respuesta = requests.request(metodo, url, **opciones)
        print(f"    Codigo de estado: {respuesta.status_code}")
        print(f"    Cuerpo: {respuesta.text[:90]}")
        return respuesta
    except requests.exceptions.RequestException as error:
        print(f"    Error: {type(error).__name__}")
        print(f"    Detalle: {str(error)[:90]}")
    finally:
        print(f"    Solucion: {solucion}")


def principal():
    # Errores del lado del cliente (diapositivas 52-55)
    probar(1, "URL sin esquema (diap. 52)",
           "Agregar 'https://' al inicio de la URL.",
           "GET", "sandboxdnac.cisco.com" + API["ruta_dispositivos"])
    probar(2, "Nombre de dominio incorrecto (diap. 53)",
           "Corregir el nombre del servidor; comprobar con ping o nslookup.",
           "GET", "https://sandboxdnac-incorrecto.cisco.com")
    probar(3, "Certificado SSL invalido con verificacion activa (diap. 54)",
           "Corregir el certificado; en laboratorio usar verify=False (diap. 55).",
           "POST", URL_BASE + API["ruta_token"], auth=AUTENTICACION, verify=True)
    respuesta = probar(4, "Misma solicitud con verify=False en laboratorio (diap. 55)",
                       "Funciona: el problema era solo la validacion del certificado.",
                       "POST", URL_BASE + API["ruta_token"], auth=AUTENTICACION)
    exito = respuesta is not None and respuesta.status_code == 200
    token = respuesta.json()["Token"] if exito else ""

    # Codigos de estado 4xx y 2xx (diapositivas 29 y 58-62)
    probar(5, "Credenciales incorrectas: 401 (diap. 61)",
           "Revisar usuario y clave en credenciales.yaml.",
           "POST", URL_BASE + API["ruta_token"], auth=(CREDENCIALES["usuario"], "incorrecta"))
    probar(6, "Solicitud sin token: 401 (diap. 61)",
           "Enviar la cabecera X-Auth-Token obtenida al autenticarse.",
           "GET", URL_BASE + API["ruta_dispositivos"])
    probar(7, "Recurso inexistente: 404 (diap. 29)",
           "Revisar la ruta en la documentacion de la API.",
           "GET", URL_BASE + "/dna/intent/api/v1/no-existe", headers={"X-Auth-Token": token})
    probar(8, "Solicitud correcta: 200 (diap. 29)",
           "Ninguna: la API respondio correctamente.",
           "GET", URL_BASE + API["ruta_dispositivos"], headers={"X-Auth-Token": token})

    # Error del lado del servidor (diapositivas 56-57)
    probar(9, "Servidor de la API que no responde (diap. 56)",
           "Verificar que el servidor este encendido y accesible; avisar al administrador.",
           "GET", "https://10.255.255.1/api", timeout=5)


if __name__ == "__main__":
    principal()
