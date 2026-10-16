# Manual de arranque de Aula

Ejecuta los comandos desde la raíz del repositorio. Necesitas Python 3.11 o
posterior.

## Arranque local

Prepara el entorno e instala las dependencias:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Configura las fechas ISO-8601 de la ventana de matrícula y levanta la API:

```bash
export MATRICULA_INICIO="2026-09-01T00:00:00Z"
export MATRICULA_FIN="2027-08-31T23:59:59Z"
python3 -m uvicorn src.aula.api.main:app --reload
```

Sustituye esas fechas de ejemplo por las del periodo vigente.
Sin esas variables el servidor arranca, pero `POST /matriculas` responde `503`.
La API está en <http://127.0.0.1:8000>; comprueba `/salud` o abre `/docs`.
Detén el servidor con `Ctrl+C`.

## Alternativa: Docker

Desde la raíz, construye la imagen y pasa las fechas al contenedor:

```bash
docker build -t aula:local .
docker run --rm -p 8000:8000 \
  -e MATRICULA_INICIO="2026-09-01T00:00:00Z" \
  -e MATRICULA_FIN="2027-08-31T23:59:59Z" \
  aula:local
```
