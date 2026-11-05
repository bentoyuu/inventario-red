# Inventario de red automatizado - Bloque 1

Script en Python que consulta el inventario de dispositivos de **Cisco Catalyst Center**
mediante una **API REST sobre HTTPS**, lo combina con un inventario local (CSV) y genera
reportes en **JSON, YAML, XML y CSV**.

Proyecto de la unidad didáctica **DevOps: fundamentos** (Bloque 1), desarrollado en la DEVASC VM.

## Archivos
| Archivo | Descripción |
|---|---|
| `inventario.py` | Script principal: token, inventario, combinación y reportes |
| `diagnostico_api.py` | Casos de resolución de problemas de API (Módulo 4, sección 4.8) |
| `prueba_inventario.py` | Pruebas unitarias con `unittest` |
| `configuracion.yaml` | Configuración: URL, rutas, tiempo de espera y verificación SSL |
| `credenciales_ejemplo.yaml` | Plantilla de credenciales (la real no se sube a Git) |
| `equipos_locales.csv` | Inventario local: sitio y responsable de cada equipo |
| `requisitos.txt` | Librerías necesarias |

## Uso en la DEVASC VM
```bash
python3 -m venv entorno && source entorno/bin/activate    # Lab 3.1.12
pip3 install -r requisitos.txt
cp credenciales_ejemplo.yaml credenciales.yaml && chmod 600 credenciales.yaml
chmod +x inventario.py diagnostico_api.py                  # Lab 1.2.2
python3 -m unittest -v prueba_inventario
./inventario.py
./diagnostico_api.py
```

**Nota:** el certificado del sandbox no es válido para su nombre de dominio, por eso
`configuracion.yaml` usa `verificar_ssl: false`. Esto solo se acepta en laboratorio
(Módulo 4, diapositiva 55); en producción debe ser `true`.
