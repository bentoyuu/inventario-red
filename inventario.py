#!/usr/bin/env python3
"""Inventario de red automatizado - Proyecto EPD DevOps: fundamentos.

Consulta el inventario de dispositivos de Cisco Catalyst Center (DNA Center)
mediante API REST sobre HTTPS, lo combina con un inventario local en CSV y
guarda el resultado en JSON, YAML, XML y CSV.

Basado en:
  - Lab 4.5.5, Parte 4: funcion getAuthToken() con requests.post y autenticacion basica.
  - Modulo 4, diapositivas 22-31 y 36: solicitudes, respuestas y autenticacion.
  - Modulo 3, seccion 3.6: formatos de datos JSON, XML y YAML.
  - Lab 1.3.3, Partes 4 y 7: listas, diccionarios y acceso a archivos.
"""
import csv
import json
import os
import sys
import xml.etree.ElementTree as ET

import requests
import urllib3
import yaml


def cargar_yaml(ruta):
    """Lee un archivo YAML y devuelve un diccionario."""
    with open(ruta) as archivo:
        return yaml.safe_load(archivo)


def obtener_token(api, usuario, clave):
    """Solicita un token con autenticacion basica (igual que getAuthToken del Lab 4.5.5)."""
    respuesta = requests.post(
        f"{api['url_base']}{api['ruta_token']}",
        auth=(usuario, clave),
        verify=api["verificar_ssl"],
        timeout=api["tiempo_espera"],
    )
    if respuesta.status_code == 200:
        return respuesta.json()["Token"]
    raise Exception(f"Codigo de estado {respuesta.status_code} y texto {respuesta.text}, "
                    "mientras se solicitaba el token.")


def obtener_dispositivos(api, token):
    """Devuelve la lista de dispositivos de red (clave 'response' del JSON de la API)."""
    respuesta = requests.get(
        f"{api['url_base']}{api['ruta_dispositivos']}",
        headers={"X-Auth-Token": token, "Accept": "application/json"},
        verify=api["verificar_ssl"],
        timeout=api["tiempo_espera"],
    )
    if respuesta.status_code == 200:
        return respuesta.json()["response"]
    raise Exception(f"Codigo de estado {respuesta.status_code} y texto {respuesta.text}, "
                    "mientras se listaban los dispositivos.")


def leer_inventario_local(ruta):
    """Lee el CSV local y devuelve un diccionario {equipo: fila}."""
    inventario_local = {}
    with open(ruta) as archivo:
        for fila in csv.DictReader(archivo):
            inventario_local[fila["equipo"]] = fila
    return inventario_local


def combinar(dispositivos, inventario_local):
    """Une los datos de la API con el CSV local y marca alertas."""
    inventario = []
    for dispositivo in dispositivos:
        datos_locales = inventario_local.get(dispositivo["hostname"], {})
        equipo = {
            "equipo": dispositivo["hostname"],
            "ip_gestion": dispositivo["managementIpAddress"],
            "plataforma": dispositivo["platformId"],
            "version": dispositivo["softwareVersion"],
            "estado": dispositivo["reachabilityStatus"],
            "sitio": datos_locales.get("sitio", "NO REGISTRADO"),
            "responsable": datos_locales.get("responsable", "-"),
        }
        if equipo["estado"] != "Reachable":
            equipo["alerta"] = "Revisar conectividad"
        elif equipo["sitio"] == "NO REGISTRADO":
            equipo["alerta"] = "Registrar en inventario local"
        else:
            equipo["alerta"] = "Sin alertas"
        inventario.append(equipo)
    return inventario


def resumir(inventario):
    """Cuenta equipos por version y por estado usando diccionarios."""
    por_version = {}
    por_estado = {}
    for equipo in inventario:
        por_version[equipo["version"]] = por_version.get(equipo["version"], 0) + 1
        por_estado[equipo["estado"]] = por_estado.get(equipo["estado"], 0) + 1
    con_alerta = [e["equipo"] for e in inventario if e["alerta"] != "Sin alertas"]
    return {"total_equipos": len(inventario), "por_version": por_version,
            "por_estado": por_estado, "equipos_con_alerta": con_alerta}


def guardar_json(datos, ruta):
    with open(ruta, "w") as archivo:
        json.dump(datos, archivo, indent=4, ensure_ascii=False)


def guardar_yaml(datos, ruta):
    with open(ruta, "w") as archivo:
        yaml.safe_dump(datos, archivo, sort_keys=False, allow_unicode=True)


def guardar_csv(inventario, ruta):
    with open(ruta, "w", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(inventario[0].keys()))
        escritor.writeheader()
        escritor.writerows(inventario)


def guardar_xml(inventario, ruta):
    raiz = ET.Element("inventario")
    for equipo in inventario:
        nodo = ET.SubElement(raiz, "dispositivo", equipo=equipo["equipo"])
        for campo, valor in equipo.items():
            if campo != "equipo":
                ET.SubElement(nodo, campo).text = str(valor)
    ET.ElementTree(raiz).write(ruta, encoding="utf-8", xml_declaration=True)


def mostrar_tabla(inventario):
    print(f"\n{'EQUIPO':<8}{'IP GESTION':<15}{'VERSION':<14}{'ESTADO':<12}{'SITIO':<20}ALERTA")
    print("-" * 85)
    for e in inventario:
        print(f"{e['equipo']:<8}{e['ip_gestion']:<15}{e['version']:<14}"
              f"{e['estado']:<12}{e['sitio']:<20}{e['alerta']}")


def principal():
    configuracion = cargar_yaml("configuracion.yaml")
    api = configuracion["api"]
    archivos = configuracion["archivos"]
    if not api["verificar_ssl"]:
        # Modulo 4, diapositiva 55: solo en laboratorio. Se oculta la advertencia repetida.
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    try:
        credenciales = cargar_yaml(archivos["credenciales"])
    except FileNotFoundError:
        sys.exit("Falta credenciales.yaml: copie credenciales_ejemplo.yaml y aplique chmod 600.")
    except PermissionError:
        sys.exit("Permiso denegado al leer credenciales.yaml: revise el propietario con ls -l.")

    try:
        token = obtener_token(api, credenciales["usuario"], credenciales["clave"])
        print(f"Token obtenido: {token[:15]}...")
        dispositivos = obtener_dispositivos(api, token)
    except requests.exceptions.ConnectionError as error:
        sys.exit(f"Error de conexion (DNS, firewall, proxy o servidor apagado): {error}")
    except requests.exceptions.Timeout:
        sys.exit("El servidor de la API no respondio a tiempo.")
    except Exception as error:
        sys.exit(f"Error de la API: {error}")
    print(f"Dispositivos recibidos desde la API: {len(dispositivos)}")

    inventario = combinar(dispositivos, leer_inventario_local(archivos["inventario_local"]))
    carpeta = archivos["carpeta_salida"]
    os.makedirs(carpeta, exist_ok=True)
    guardar_json(inventario, os.path.join(carpeta, "inventario.json"))
    guardar_yaml(inventario, os.path.join(carpeta, "inventario.yaml"))
    guardar_xml(inventario, os.path.join(carpeta, "inventario.xml"))
    guardar_csv(inventario, os.path.join(carpeta, "inventario.csv"))
    resumen = resumir(inventario)
    guardar_json(resumen, os.path.join(carpeta, "resumen.json"))

    mostrar_tabla(inventario)
    print("\nResumen:", json.dumps(resumen, indent=2, ensure_ascii=False))
    print(f"Archivos generados en la carpeta '{carpeta}/'")


if __name__ == "__main__":
    principal()
