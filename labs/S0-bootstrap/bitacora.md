# Bitacora de S0

## 2026-10-08

### CI y suite de tests

- **Tarea:** revisar por que fallaba `python -m aula_cli check S0 --prediccion pasa` y anadir ejecucion de pytest al workflow.
- **Tiempo dedicado:** no registrado.
- **Intentos:** el progreso local registra 4 intentos y 4 predicciones, con 2 aciertos. No se conserva el detalle de cada intento.
- **Resultado:** se reprodujo el fallo S0-04 porque el workflow no ejecutaba pytest. En el estado actual, `ci.yml` tiene un job `tests` que instala `requirements.txt` y ejecuta `python -m pytest tests/ -q`.
- **Decision:** usar un job de GitHub Actions con `actions/checkout`, `actions/setup-python` y las dependencias declaradas por el proyecto, en vez de incorporar una accion externa de CI.

### Test de estructura y validacion local

- **Tarea:** anadir un test descubrible por pytest y probar la ejecucion local.
- **Tiempo dedicado:** no registrado.
- **Intentos:** se encontro primero que el Python local no tenia pytest instalado. Tras instalar las dependencias, el estudiante informa que la ejecucion por terminal funciono.
- **Resultado:** existe `tests/test_s0.py`, que comprueba la existencia de `ci.yml` y `CODEOWNERS`. Esta prueba no ejecuta el verificador completo de S0.
- **Decision:** instalar las dependencias desde `requirements.txt` antes de ejecutar pytest; no sustituir la prueba por un ejemplo vacio.

### Estado y pendientes

- **Tarea:** registrar el estado de la estacion y la verificacion externa.
- **Tiempo dedicado:** no registrado.
- **Intentos:** el estado local de `.aula/progreso.json` registra S0 como sellada a las 13:19 UTC, con 4 intentos y 2 aciertos de 4 predicciones.
- **Resultado:** los commits de la rama `ci/s0` incluyen `df89057` (`ci: cambios a nuestra configuracion CI`) y `85b4220` (`test: añade prueba de estructura S0`). No se pudo comprobar el estado de la PR ni de GitHub Actions desde esta sesion porque `gh` no tiene autenticacion configurada.
- **Decision:** considerar pendiente la confirmacion del workflow en Actions y la validacion externa del entregable de la estacion; no dar por verificados los checks remotos sin evidencia.
