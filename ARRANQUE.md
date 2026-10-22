# Arranque del proyecto Aula

Este documento reúne el mapa y los comandos del proyecto en su estado actual.
Para el camino más corto para levantar el servicio, consulta
[MANUAL-ARRANQUE.md](MANUAL-ARRANQUE.md).

## Arranque del proyecto Aula

Aula contiene una API FastAPI para matrícula y un laboratorio guiado por
estaciones, gestionado desde `aula_cli`. La matrícula ya tiene una ruta
funcional; la consulta de expediente sigue reservada para S2. La API guarda las
matrículas en memoria mientras el proceso está vivo y registra las decisiones
en un fichero JSONL.

S1 es la primera rebanada vertical: completar las transiciones de estado,
construir y probar la imagen, añadir el pipeline de entrega y registrar el
tiempo de trabajo. La situación se comprueba en el repositorio con la CLI; el
estado local puede variar entre copias.

## Dónde está cada cosa

Ejecuta los comandos desde la raíz del repositorio.

| Ruta | Contenido |
|---|---|
| `src/aula/api/main.py` | Aplicación FastAPI, endpoints y validación de entrada |
| `src/aula/dominio/` | Modelos y estados de matrícula |
| `src/aula/reglas/` | Reglas de matrícula, carga de planes y cálculos académicos |
| `src/aula/auditoria.py` | Escritura y lectura de la traza de decisiones |
| `src/aula/legado/` | Calculadora de expediente anterior; no modificar fuera de S5 |
| `tests/` | Pruebas de API, reglas y bootstrap |
| `datos/planes/` | Planes académicos usados por la aplicación |
| `specs/` | Especificaciones funcionales |
| `labs/` | Guías, criterios, verificadores y pistas de cada estación |
| `aula_cli/` | Comandos para estado, guía, verificación y progreso del laboratorio |
| `agentes/conformidad/` | Evaluador local del agente de conformidad |
| `.devcontainer/devcontainer.json` | Configuración del entorno de desarrollo |
| `Dockerfile` | Imagen OCI de producción multi-stage |
| `.github/workflows/ci.yml` | Tests, cobertura y coordinación de CI |
| `.github/workflows/imagen.yml` | Build y prueba de humo del contenedor |
| `.github/workflows/publicar-imagen.yml` | Tests y publicación privada en GHCR desde `main` o tags `v*` |
| `requirements.txt` | Dependencias de aplicación y pruebas |
| `requirements-prod.txt` | Dependencias mínimas para la imagen de producción |

## Preparar el entorno

Se necesita Python 3.11 o posterior para trabajar localmente. Crea un entorno
virtual e instala las dependencias de desarrollo:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

El devcontainer usa Python 3.11. Al crearse instala `requirements.txt`, Claude
Code y genera el corpus local. Configura `PYTHONPATH` para que se puedan
importar los módulos del proyecto y establece `AULA_TRAZA` en
`.aula/auditoria.jsonl`.

El Dockerfile de producción usa Python 3.12 slim y una construcción
multi-stage: primero instala solo `requirements-prod.txt` en un entorno virtual;
después copia ese entorno, el código de `src/` y los planes académicos a la
imagen final. Añade el entorno virtual a `PATH`, fija `PYTHONPATH=/aula`,
`PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1` y la traza en
`/aula/.aula/auditoria.jsonl`. Elimina pip y las cachés de bytecode de la imagen,
ejecuta como el usuario sin privilegios `appuser`, publica el puerto 8000 y
comprueba la salud llamando a `/salud`. Su comando de inicio ejecuta Uvicorn en
`0.0.0.0:8000`. No incluye las dependencias de pruebas ni todos los datos de
desarrollo.

## Ejecutar pruebas

Suite completa:

```bash
python3 -m pytest tests/ -q
```

Pruebas de API:

```bash
python3 -m pytest tests/test_api.py -v
```

Para medir el umbral de cobertura de dominio indicado por S1:

```bash
python3 -m pytest tests/ -q --cov=src/aula/dominio --cov-report=term-missing
```

La cobertura requerida por el entregable de S1 es superior al 60% del módulo de
dominio.

## Iniciar aplicación

La API se puede ejecutar localmente sin configuración adicional, pero para
crear matrículas hay que definir las dos fechas ISO-8601 de la ventana vigente:

```bash
export MATRICULA_INICIO="2026-09-01T00:00:00Z"
export MATRICULA_FIN="2027-08-31T23:59:59Z"
python3 -m uvicorn src.aula.api.main:app --reload
```

Las fechas son ejemplos: sustitúyelas por las del periodo vigente.
`MATRICULA_INICIO` y `MATRICULA_FIN` no tienen valores por defecto. Si falta
alguna o no es válida, `POST /matriculas` devuelve `503`; fuera de la ventana
devuelve `422`. `AULA_TRAZA` es opcional y cambia la ruta del fichero de
auditoría, cuyo valor local por defecto es `.aula/auditoria.jsonl`.

La API queda en <http://127.0.0.1:8000>. Comprueba `/salud` o abre la
documentación interactiva en `/docs`. Las variables de entorno se configuran
en el proceso del servidor, no dentro del JSON. Para registrar una matrícula,
envía un `POST` a `/matriculas` con los campos de entrada que admite la API:

```bash
curl -X POST "http://127.0.0.1:8000/matriculas" \
  -H "Content-Type: application/json" \
  -d '{
    "estudiante_id": "EST001",
    "curso_academico": "2026-2027",
    "codigos": ["MAT101"]
  }'
```

`plan_aplicado`, `version_plan_aplicada`, `estado`, `lineas` y
`creditos_admitidos` forman parte de la respuesta del POST; no se envían en el
cuerpo de la solicitud.

En la imagen de producción, pasa las fechas al crear el contenedor; el
Dockerfile no fija fechas de matrícula:

```bash
docker build -t aula:local .
docker run --rm -p 8000:8000 \
  -e MATRICULA_INICIO="2026-09-01T00:00:00Z" \
  -e MATRICULA_FIN="2027-08-31T23:59:59Z" \
  aula:local
```

Las matrículas se conservan en memoria y se pierden al reiniciar el servicio.
La consulta `GET /expedientes/{estudiante_id}` responde `501` mientras se
completa S2. Detén Uvicorn con `Ctrl+C`.

## Consultar el laboratorio

La CLI lee el progreso local de `.aula/progreso.json`. Consulta el estado y la
guía, y ejecuta el verificador de la estación cuando quieras:

```bash
python3 -m aula_cli estado
python3 -m aula_cli guia
python3 -m aula_cli guia S1
python3 -m aula_cli check
python3 -m aula_cli check S1
```

`check` incrementa el contador de intentos en `.aula/progreso.json`. El comando
`python3 -m agentes.conformidad.evaluar` evalúa el agente aparte; en esta copia
no está configurado el conjunto dorado privado y el evaluador lo informa sin
producir métricas.

Para ver las pistas, consultar criterios o registrar el tiempo de trabajo:

```bash
python3 -m aula_cli pista S1
python3 -m aula_cli bitacora "descripción de la tarea y tiempo empleado"
```

La estación activa por defecto se determina por el primer hito que no esté
sellado. `check S1` permite consultar S1 explícitamente aunque otra estación
aparezca como activa. Para cerrar una estación, sigue su guía y usa `cerrar`
solo cuando el verificador esté verde.

## Qué falta para terminar S1

El último resultado local de `python3 -m aula_cli check S1` fue:

| Criterio | Resultado | Qué demuestra realmente |
|---|---|---|
| S1-01 | OK | La suite completa pasa. |
| S1-02 | OK, comprobación superficial | Existe `estados.py` y el símbolo `TRANSICIONES`; no valida la lógica. |
| S1-03 | OK | Hay un Dockerfile multi-stage en la raíz. |
| S1-04 | OK, comprobación superficial | `ci.yml` contiene un nombre que coincide con el patrón de build; no verifica que el job remoto haya terminado bien. |
| S1-05 | OK | Hay al menos 15 tests. |
| S1-06 | OK | La bitácora contiene fechas. Las horas reconstruidas son provisionales y requieren confirmación. |

Por tanto, **que `check S1` salga verde no demuestra que S1 esté terminado**.
En particular, `transiciones_validas` y `transicionar` en
`src/aula/dominio/estados.py` aún lanzan `NotImplementedError`; hay que
implementar y probar las transiciones y la inmutabilidad del plan confirmado.
La bitácora [de S1](./labs/S1-rebanada-vertical/bitacora.md) fue reconstruida
del historial Git, incluye trabajo asistido y no es una línea base validada
"sin agentes".

El Dockerfile multi-stage está en la raíz. `ci.yml` ejecuta los tests en Python
3.12, exige más del 60 % de cobertura del dominio (umbral configurado: 61 %) y,
si pasan, invoca `imagen.yml`. Ese workflow construye la imagen y prueba
`/salud` y un `POST /matriculas`. La cobertura local medida fue 85,42 %.

**Entregable adicional no comprobado por el verificador:** publicar la imagen
en un registry. `CRITERIOS.md` y `GUIA.md` incluyen una imagen publicada; el
workflow ya la publica de forma privada en GHCR al recibir pushes a `main` o
tags `v*`, después de tests, cobertura, build y smoke tests. La publicación
quedó confirmada tras fusionar la PR #14: el workflow
[publicar-imagen, ejecución 3](https://github.com/David-Omenaca-NTT/laboratorio-aula/actions/runs/38759020775)
terminó en verde el 15 de octubre de 2026, incluido el paso de push a GHCR.
`verificar.py` no consulta el registry ni valida que la publicación exista.

## Pasos para publicar una imagen persistente

El destino configurado es GitHub Container Registry (GHCR), con visibilidad
privada. `ci.yml` se ejecuta en pull requests y solo tiene permiso de lectura:
construye y prueba, pero no publica. `publicar-imagen.yml` se ejecuta en pushes
a `main` y tags `v*`; corre tests y cobertura, y después llama a `imagen.yml`
con `packages: write`. El workflow reutilizable construye y prueba antes de
iniciar sesión y publicar. No se publican imágenes desde pull requests.

La ejecución de Actions muestra **Artifacts –** porque no se guarda un archivo
descargable con `upload-artifact`: la imagen se publica como paquete en GHCR y
se consulta en **Packages**. No son dos nombres para el mismo resultado:
Artifacts adjunta ficheros a una ejecución; GHCR conserva imágenes de
contenedor etiquetadas. En la publicación confirmada desde `main` se generaron
`latest` y `sha-77695aa214e543dfe6c26ef81176225962138f12`.

1. **Permisos de publicación.** El workflow ya completó un push correcto a
   GHCR con el `GITHUB_TOKEN` efímero y `packages: write` limitado al job
   publicador. Si se cambia la configuración de paquetes o permisos del
   repositorio y una publicación futura falla, revisa que Actions pueda
   escribir paquetes. El job de PR solo tiene lectura y no necesita un PAT.
2. **Fusionar a `main` o crear un tag `v*`.** Tras un push a `main` se publican
   `ghcr.io/david-omenaca-ntt/laboratorio-aula:latest` y
   `ghcr.io/david-omenaca-ntt/laboratorio-aula:sha-<commit>`. Al publicar un tag
   como `v1.0.0`, se publican también `:v1.0.0` y `:sha-<commit>`.
3. **Esperar el workflow de publicación.** `publicar-imagen.yml` ejecuta la
   suite y exige cobertura de dominio superior al 60 %. Luego
   `imagen.yml` construye la imagen, comprueba `/salud` y prueba
   `POST /matriculas`. Solo si todos esos pasos pasan inicia sesión en GHCR y
   publica. Una PR no inicia sesión ni hace push.
4. **Comprobar la persistencia y descargar la imagen.** En GitHub, abre
   **Packages** y confirma que el paquete está asociado al repositorio y
   conserva visibilidad privada. La ejecución de Actions no debe mostrarlo como
   artefacto descargable. Desde un equipo autorizado para leer el paquete:

   ```bash
   docker pull ghcr.io/david-omenaca-ntt/laboratorio-aula:latest
   docker run --rm -p 8001:8000 \
     -e MATRICULA_INICIO="2026-09-01T00:00:00Z" \
     -e MATRICULA_FIN="2027-08-31T23:59:59Z" \
     ghcr.io/david-omenaca-ntt/laboratorio-aula:latest
   ```

   Comprueba `http://127.0.0.1:8001/salud`. Para autenticarte localmente,
   utiliza un token personal con permiso de lectura de paquetes:

   ```bash
   docker login ghcr.io
   ```

En la primera publicación, revisa en GitHub Packages que el paquete quedó
asociado al repositorio y que su visibilidad sea privada (los paquetes nuevos
de GHCR se crean privados). El Dockerfile incorpora la etiqueta OCI
`org.opencontainers.image.source` para asociar la imagen al repositorio. La
publicación sigue siendo una evidencia que el verificador local no comprueba. Consulta
[criterios de S1](./labs/S1-rebanada-vertical/CRITERIOS.md) y
[guía de S1](./labs/S1-rebanada-vertical/GUIA.md) antes del cierre.
