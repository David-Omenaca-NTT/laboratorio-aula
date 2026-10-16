# Bitacora de S1

Registro provisional reconstruido del historial Git. Las horas son estimaciones
de actividad, no mediciones; los commits marcan hitos y no prueban tiempo
efectivo. Horario local asumido: Europe/Madrid (CEST, UTC+2 en estas fechas).
Revisa y corrige las duraciones con quien hizo el trabajo.

Importante: el historial incluye trabajo asistido por agentes. Por tanto, estas
entradas documentan el trabajo realizado, pero no constituyen una linea base
"sin agentes" comparable para S2/S3.

| Fecha | Franja aproximada | Tarea | Duracion estimada | Evidencia |
|---|---|---|---:|---|
| 2026-10-08 | 17:26-17:42 | Crear pruebas de API para matricula/expediente y ajustar dependencias de test (`httpx`). | 0 h 30 min | Commits `b9694c6`, `6d905f5`; sesion hasta `cb2250b`. |
| 2026-10-09 | 09:54-10:25 | Revisar documentacion S1, incorporar el Dockerfile multi-stage y ampliar pruebas de matricula. | 1 h 00 min | Commits `a6c32f3`, `de72575`, `7363acd`; horas convertidas desde UTC. |
| 2026-10-09 | 10:28-13:52 | Corregir ejecucion de tests/Actions, optimizar la imagen y revisar la integracion de los cambios. | 2 h 00 min | Commits `a15f28e`, `1cb9c57`; merges de PR #7 a #11 y sesiones asociadas; horas convertidas desde UTC. |
| 2026-10-15 | 14:19-15:20 | Mover la imagen y sus dependencias a la raiz, separar CI del workflow reutilizable de imagen, anadir smoke test y actualizar el arranque. | 1 h 00 min | Historial de sesion y comprobaciones locales de build, `/salud` y `POST /matriculas`. |
| 2026-10-15 | 15:27-15:37 UTC (aprox.) | Confirmar la publicacion privada en GHCR tras la PR #14 y actualizar el arranque para distinguir el paquete de los artifacts de Actions. | 0 h 10 min | [Ejecucion de publicacion #3](https://github.com/David-Omenaca-NTT/laboratorio-aula/actions/runs/38759020775); commit `6155524` en `docs/s1-ghcr-publicacion`. Trabajo asistido; duracion estimada. |

**Total provisional estimado: 4 h 40 min.** No sumar este total a una medicion de linea base sin agentes sin validar primero las franjas y separar el trabajo
asistido.

## Pendiente de registrar

Anota cada tarea nueva al terminarla, con la duracion observada y sin reconstruir
el tiempo de memoria:

| Fecha | Tarea | Duracion real | Observaciones |
|---|---|---:|---|
| AAAA-MM-DD | Implementar y probar las transiciones de estado de matricula | — | Pendiente |
| AAAA-MM-DD | Validar con la persona responsable las estimaciones reconstruidas de S1 | — | Pendiente; las duraciones actuales siguen siendo provisionales. |
