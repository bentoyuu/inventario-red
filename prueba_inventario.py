"""Pruebas unitarias con unittest (Modulo 3, seccion 3.5, diapositivas 65-68).

Ejecutar: python3 -m unittest -v prueba_inventario
unittest solo reconoce los metodos que empiezan con "test"; aqui se configura
para que reconozca los metodos que empiezan con "prueba".
"""
import os
import tempfile
import unittest
from unittest import mock

import inventario

unittest.defaultTestLoader.testMethodPrefix = "prueba"

API = {"url_base": "https://ejemplo", "ruta_token": "/token",
       "ruta_dispositivos": "/dispositivos", "verificar_ssl": False, "tiempo_espera": 5}

DISPOSITIVOS = [
    {"hostname": "sw1", "managementIpAddress": "10.10.20.175", "platformId": "C9KV",
     "softwareVersion": "17.12.1", "reachabilityStatus": "Reachable"},
    {"hostname": "sw9", "managementIpAddress": "10.10.20.199", "platformId": "C9KV",
     "softwareVersion": "17.12.1", "reachabilityStatus": "Unreachable"},
]


class PruebasInventario(unittest.TestCase):

    def prueba_token_correcto(self):
        respuesta = mock.Mock(status_code=200)
        respuesta.json.return_value = {"Token": "abc123"}
        with mock.patch("inventario.requests.post", return_value=respuesta):
            self.assertEqual(inventario.obtener_token(API, "usuario", "clave"), "abc123")

    def prueba_token_401_genera_error(self):
        respuesta = mock.Mock(status_code=401, text="Unauthorized")
        with mock.patch("inventario.requests.post", return_value=respuesta):
            with self.assertRaises(Exception):
                inventario.obtener_token(API, "usuario", "clave_incorrecta")

    def prueba_combinar_y_alertas(self):
        locales = inventario.leer_inventario_local("equipos_locales.csv")
        resultado = inventario.combinar(DISPOSITIVOS, locales)
        self.assertEqual(resultado[0]["sitio"], "Lima-Sede-Central")
        self.assertEqual(resultado[0]["alerta"], "Sin alertas")
        self.assertEqual(resultado[1]["alerta"], "Revisar conectividad")

    def prueba_resumen(self):
        resumen = inventario.resumir(inventario.combinar(DISPOSITIVOS, {}))
        self.assertEqual(resumen["total_equipos"], 2)
        self.assertEqual(resumen["por_version"]["17.12.1"], 2)

    def prueba_guardar_formatos(self):
        datos = inventario.combinar(DISPOSITIVOS, {})
        with tempfile.TemporaryDirectory() as carpeta:
            for nombre, funcion in [("x.json", inventario.guardar_json),
                                    ("x.yaml", inventario.guardar_yaml),
                                    ("x.xml", inventario.guardar_xml),
                                    ("x.csv", inventario.guardar_csv)]:
                ruta = os.path.join(carpeta, nombre)
                funcion(datos, ruta)
                self.assertTrue(os.path.getsize(ruta) > 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
