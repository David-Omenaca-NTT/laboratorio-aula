# Arranque del proyecto Aula

## Dónde está cada cosa

Ejecuta los comandos desde la raíz del repositorio, `/workspaces/laboratorio-aula`.

- La API FastAPI está en `src/aula/api/main.py`. El objeto de aplicación es `app`.
- El dominio y las reglas están en `src/aula/dominio/` y `src/aula/reglas/`.
- Las pruebas automatizadas están en `tests/`: `test_api.py` cubre la API y
  `test_s0.py` comprueba la estructura del bootstrap.
- Las dependencias están en `requirements.txt`. No hay un `requirements-dev.txt`
  separado; el archivo incluye las dependencias de la aplicación y de pruebas.
- Los datos del plan y los expedientes de ejemplo están en `datos/`; las
  especificaciones, en `specs/`; y las estaciones del laboratorio, en `labs/`.
- La CLI del laboratorio está en `aula_cli/`.

## Preparar el entorno

Desde la raíz, crea y activa un entorno virtual e instala las dependencias:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Ejecutar las pruebas

Ejecuta la suite completa:

```bash
python -m pytest tests/ -q
```

Para probar solo la API:

```bash
python -m pytest tests/test_api.py -v
```

## Iniciar la aplicación

Desde la raíz y con el entorno virtual activado:

```bash
export MATRICULA_INICIO="<inicio-ISO-8601>"
export MATRICULA_FIN="<fin-ISO-8601>"
python -m uvicorn src.aula.api.main:app --reload
```

Configura los valores reales del periodo vigente; ambas variables son
obligatorias y no tienen valores por defecto. En Codespaces puedes guardarlas
como **Codespaces secrets** en la configuración de GitHub para que estén
disponibles en el entorno del codespace, o exportarlas en el terminal antes de
arrancar Uvicorn. Si cambias los secretos, reinicia el codespace.

Al arrancar el contenedor, pásalas explícitamente a Docker:

```bash
docker build -f .devcontainer/Dockerfile -t aula:latest .
docker run --rm -p 8000:8000 \
  -e MATRICULA_INICIO="<inicio-ISO-8601>" \
  -e MATRICULA_FIN="<fin-ISO-8601>" \
  aula:latest
```

Si falta alguna variable o no contiene una fecha ISO-8601 válida, el `POST`
responde `503` con un mensaje de configuración claro. En Postman, envía un
`POST` a
`http://127.0.0.1:8000/matriculas` con **Body → raw → JSON**, por ejemplo:

```json
{
  "estudiante_id": "EST001",
  "curso_academico": "2026-2027",
  "codigos": ["MAT101"]
}
```

Una matrícula válida devuelve `201` con las líneas admitidas, en espera o
rechazadas. Las matrículas se conservan en memoria mientras el servicio esté
ejecutándose y se pierden al reiniciarlo. El campo `momento` es opcional; si se
omite, se usa la fecha y hora UTC actuales.

La API queda disponible en <http://127.0.0.1:8000>. Puedes comprobar el estado
en <http://127.0.0.1:8000/salud> y consultar la documentación interactiva en
<http://127.0.0.1:8000/docs>. La consulta de expediente continúa pendiente y
responde `501`.
Detén el servidor con `Ctrl+C`.

## Consultar el laboratorio

La estación actualmente en curso es S1. Para ver el estado del laboratorio o
las instrucciones de esa estación:

```bash
python -m aula_cli estado
python -m aula_cli guia S1
```
