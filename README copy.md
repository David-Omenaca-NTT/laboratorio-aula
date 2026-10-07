# Aula Students: repositorio semilla

Esta es la plantilla de trabajo del estudiante, no la solucion resuelta.
El proyecto `aula` se conserva separado como referencia para el mentor.

## Arranque en Windows con Git Bash

Desde esta carpeta, no desde `src/aula`:

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
python -m aula_cli estado
python -m aula_cli guia S0
```

En PowerShell activa el entorno con `.venv\Scripts\Activate.ps1`.
En Linux/macOS utiliza `source .venv/bin/activate` y, si procede, `python3`.

El comando global `aula` no esta instalado: en las guias sustituye
`aula ...` por `python -m aula_cli ...`. `make` es opcional.

## Que recibes

- CLI, guias, pistas, verificadores y utilidades de tests.
- Lectores de specs y trazabilidad local ya disponibles para el verificador S2;
	S4a completa su exposicion por MCP, el transporte y las otras herramientas.
- Modelos, carga de planes, auditoria, datos y legado originales.
- Firmas de funciones pendientes que lanzan `NotImplementedError`.
- API de arranque: `/salud` funciona; matriculas y expedientes devuelven 501.
- Agente de conformidad v0, deliberadamente ingenuo.
- CI de sintaxis, no un pipeline de entrega ya resuelto.

No hay tests resueltos, etiquetas doradas, informes finales, progreso previo,
manifiestos, configuracion de agentes ni soluciones accesibles al estudiante.
La suite vacia termina con codigo 5 de pytest: es esperable antes de S1.

## Recorrido

| Estacion | Trabajo pendiente |
|-----------|-------------------|
| S0 | CODEOWNERS, plantilla de PR, gate de tamano, reglas de rama y revision cruzada |
| S1 | Estados, reglas de matricula, endpoint, tests, contenedor y pipeline |
| S2 | Cerrar SPEC-002, implementar calculos y trazabilidad |
| S3 | Ampliar el contrato de contexto, permisos, hooks y comparativa |
| S4a | MCP, mejorar el agente v0 y medirlo con evaluacion custodiada |
| S4b | Contrato, agentes, handoffs y worktrees |
| S5 | Caracterizacion antes del refactor, equivalencia y desviaciones |
| S6 | Manifiestos, gates, evidencias y coste |
| S7 | Despliegue, reversion, fallos inducidos y MTTR |
| S8 | Defensa y decisiones justificadas |

Empieza por [PLAYBOOK.md](PLAYBOOK.md) y [labs/S0-bootstrap/GUIA.md](labs/S0-bootstrap/GUIA.md).
Los checks iniciales deben fallar: verde no significa que esta plantilla este resuelta.
Los verificadores originales se mantienen, con sus limitaciones; el mentor debe
revisar tambien comportamiento, proteccion de ramas y evidencia operativa.

## Soluciones y desbloqueo

`cerrar` y `desbloquear` registran el estado local. No descargan ni aplican una
solucion. Pide al mentor un paquete de referencia de la estacion, conserva tu
trabajo en una rama y compara antes de incorporar esa nueva base.
Las referencias privadas no se distribuyen dentro de esta plantilla ni de su historial.

## Evaluacion del agente

El conjunto dorado y sus etiquetas no se entregan. Antes de S4a, el mentor debe
configurar una evaluacion externa que devuelva metricas sin etiquetas.
Ese servicio y su workflow no estan implementados en esta copia. El evaluador
local acepta `--dorado` solo para uso del mentor en un entorno separado.
No copies el dorado desde `aula` al repositorio del estudiante.

## Publicar la plantilla

Publica solamente el contenido de `aula-students` en un repositorio nuevo,
sin el historial de la referencia ni carpetas vecinas. Marca ese repositorio
como plantilla en GitHub y crea un repositorio por estudiante desde ella.
Configura propietarios reales en S0; las reglas de rama no se copian como archivos.
No hay remoto configurado ni repositorio independiente inicializado por esta preparacion.

## Diferencias respecto a la conversion del README de referencia

Se mantienen los verificadores y el corpus sin cambios. Ademas de vaciar tests y
artefactos, se retiran las implementaciones evaluadas y los controles ya resueltos
para que S0 y S1 tengan trabajo real. CLAUDE.md conserva sus invariantes de partida;
S3 completa permisos y contexto. Las soluciones permanecen fuera de la plantilla,
no en carpetas locales que el alumno podria leer desde el primer dia.