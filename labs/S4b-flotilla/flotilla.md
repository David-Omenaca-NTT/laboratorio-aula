# S4b — Flotilla multiagente

## 1. Diagrama de flotilla

La estación S4b tiene como objetivo organizar una flotilla de tres agentes especializados que colaboran sobre un contexto compartido a través del servidor MCP `aula-contexto`.

La arquitectura se compone de tres elementos principales:

- **Servidor MCP `aula-contexto`:** proporciona una interfaz común para consultar especificaciones, trazabilidad, resultados de tests y planes del proyecto.
- **Agentes especializados:** conformidad, triaje y modernización, cada uno con responsabilidades y niveles de autonomía definidos.
- **Revisión humana:** supervisa los resultados y resuelve los conflictos que exceden los permisos asignados a los agentes.

Cada agente trabaja en un *Git worktree* independiente. Esto permite aislar sus modificaciones y reducir los conflictos derivados de trabajar simultáneamente sobre el mismo repositorio.

<div align="center">
  <img src="./imágenes diagrama/s4b-diagramas Diagrama de flotilla.png" alt="Diagrama de flotilla S4b" width="800" />
  <p><em>Figura 1. Arquitectura general de la flotilla multiagente.</em></p>
</div>

El servidor MCP actúa como punto común de acceso al contexto, mientras que cada agente se ocupa de una tarea concreta. Los resultados pueden pasar por una revisión humana antes de su aceptación o integración.

## 2. Diferencias entre S4a y S4b

La principal diferencia entre S4a y S4b se encuentra en el alcance del trabajo y en la forma de organizar los agentes.

En **S4a** se desarrolla y evalúa un agente individual de conformidad, cuya responsabilidad consiste en comprobar si una solicitud de cambios (*pull request*) cumple los criterios de una especificación.

En **S4b**, este enfoque evoluciona hacia una flotilla multiagente, en la que intervienen tres agentes con funciones diferentes. La dificultad ya no consiste únicamente en el funcionamiento individual de cada agente, sino también en su coordinación.

<div align="center">
  <img src="./imágenes diagrama/s4b-diagramas Diferencias entre s4a y s4b.png" alt="Comparación entre S4a y S4b" width="800" />
  <p><em>Figura 2. Diferencias entre el agente individual de S4a y la flotilla de S4b.</em></p>
</div>

| Característica | S4a | S4b |
|---|---|---|
| Organización | Agente individual | Flotilla multiagente |
| Objetivo | Evaluar conformidad | Coordinar tareas especializadas |
| Espacio de trabajo | Entorno del agente | Worktrees aislados por agente |
| Coordinación | Centrada en una tarea | Handoffs y contrato compartido |
| Supervisión | Evaluación del agente | Revisión de resultados y conflictos |

Por tanto, S4b amplía el trabajo realizado en S4a e introduce nuevos conceptos de arquitectura y coordinación.

## 3. Arquitectura de agentes

La flotilla está formada por tres agentes especializados, conectados al mismo servidor MCP.

Cada agente tiene una responsabilidad, un nivel de autonomía y un espacio de trabajo independiente.

<div align="center">
  <img src="./imágenes diagrama/s4b-diagramas Arquitectura Agentes.png" alt="Arquitectura y responsabilidades de los agentes" width="800" />
  <p><em>Figura 3. Distribución de agentes, niveles de autonomía y worktrees.</em></p>
</div>

### Agente de conformidad — Nivel N3 — Worktree A

Su función es revisar una PR y comprobar si los cambios realizados cumplen los criterios de aceptación de la especificación correspondiente.

Recibe como entrada una PR y un identificador de especificación (`spec_id`), y genera como salida un veredicto estructurado.

### Agente de triaje — Nivel N2 — Worktree B

Su función es analizar fallos de un pipeline y proponer posibles causas.

Recibe como entrada el identificador de una ejecución fallida (`run_id`) y genera una clasificación del fallo junto con una hipótesis sobre su origen.

Si el fallo está relacionado con la cobertura de una especificación, transfiere la información correspondiente al agente de conformidad.

### Agente de modernización — Nivel N3 — Worktree C

Su función es preparar propuestas de refactorización sobre código legado.

Recibe la ruta del módulo que se quiere modernizar y una batería de pruebas de caracterización. Su salida es una propuesta de refactorización en una rama propia.

Cuando abre una PR, comunica su identificador y la especificación relacionada al agente de conformidad para su revisión.

Los worktrees permiten trabajar de forma aislada, pero no sustituyen las reglas de coordinación y control de cambios establecidas en el contrato.

## 4. Contrato de contexto y comunicación entre agentes

El contrato de contexto define las reglas que deben respetar los tres agentes para colaborar.

En el proyecto se representa mediante el archivo `agentes/flotilla/contrato.json`, que recoge la identificación de la flotilla, el contexto compartido, las entradas y salidas, los permisos, los handoffs y la resolución de conflictos.

El servidor MCP utilizado por los agentes se denomina `aula-contexto` y expone cinco herramientas:

- `listar_specs`: consulta el catálogo de especificaciones.
- `obtener_spec`: recupera una especificación.
- `trazabilidad`: identifica criterios cubiertos y sin cubrir por pruebas.
- `resultado_tests`: ejecuta pruebas y devuelve sus resultados.
- `version_plan`: consulta la versión de un plan.

El servidor está implementado en `agentes/mcp_aula/servidor.py` y puede iniciarse mediante `make mcp`. Su registro para un cliente MCP compatible se encuentra en `.mcp.json`.

<div align="center">
  <img src="./imágenes diagrama/s4b-diagramas Contrato.png" alt="Contrato y comunicación de la flotilla" width="800" />
  <p><em>Figura 4. Contrato compartido y traspasos de información entre agentes.</em></p>
</div>

### Handoffs principales

| De | A | Cuándo | Información transferida |
|---|---|---|---|
| Triaje | Conformidad | El fallo del pipeline corresponde a cobertura de especificación | `spec_id` afectado |
| Modernización | Conformidad | Se abre una PR con el refactor | PR y `spec_id` |

Estos traspasos permiten que cada agente mantenga su especialización sin perder la información necesaria para que otro agente continúe el trabajo.

El contrato debe existir en un formato validable, como JSON o YAML. Para comprobar la sintaxis del archivo JSON puede utilizarse `python3 -m json.tool`, aunque validar su estructura completa requiere definir también reglas o un esquema.

## 5. Ejecución de la flotilla

La ejecución de S4b debe demostrar que los tres agentes pueden intervenir en un ciclo de trabajo coordinado.

<div align="center">
  <img src="./imágenes diagrama/s4b-diagramas Ejecuccion.png" alt="Secuencia de ejecución de la flotilla" width="800" />
  <p><em>Figura 5. Funciones principales durante el ciclo multiagente.</em></p>
</div>

### F1. Triaje del pipeline

El agente de triaje analiza una ejecución fallida del pipeline y determina una posible causa.

Cuando identifica un problema relacionado con la cobertura de una especificación, realiza un handoff al agente de conformidad.

### F2. Evaluación de conformidad

El agente de conformidad examina la PR y la especificación relacionada, utilizando el contexto disponible para elaborar un veredicto estructurado.

Este resultado permite determinar si los cambios cumplen los criterios establecidos o requieren correcciones.

### F3. Propuesta de modernización

El agente de modernización trabaja sobre un módulo legado en su propia rama, utilizando la batería de caracterización como referencia para preservar el comportamiento existente.

El objetivo es producir una propuesta de refactorización que pueda revisarse mediante una PR.

Cuando se abre la PR, se transfiere al agente de conformidad la información necesaria para su evaluación.

### Evidencias de ejecución

Para demostrar que el ciclo se ha realizado, se deben conservar evidencias de:

- Los worktrees utilizados.
- Las entradas y salidas de los tres agentes.
- Los handoffs efectuados.
- Las propuestas, hipótesis y veredictos generados.
- Las decisiones o aprobaciones humanas correspondientes.

**Este apartado describe el ciclo previsto. La ejecución real y sus resultados deberán acreditarse mediante la grabación exigida en S4b.**

## 6. Organigrama de resolución de conflictos

La resolución de conflictos es uno de los aspectos esenciales de la arquitectura multiagente.

El contrato establece como regla principal que **cada ruta debe tener un único agente con permiso de escritura**.

Cuando un agente necesita modificar una ruta que pertenece a otro, no debe hacerlo directamente: puede elaborar una propuesta.

Si dos agentes necesitan escribir sobre la misma ruta y no existe una solución autorizada, la ejecución debe detenerse y una persona debe decidir cómo continuar.

<div align="center">
  <img src="./imágenes diagrama/s4b-diagramas Organigrama de resolución de conflictos.png" alt="Organigrama de resolución de conflictos" width="800" />
  <p><em>Figura 6. Regla de propietario único, propuesta y escalado humano.</em></p>
</div>

El contrato de referencia establece los siguientes propietarios:

| Ruta o recurso | Responsable |
|---|---|
| `src/aula/legado/` | Modernización |
| Comentarios de PR | Conformidad |
| `src/aula/reglas/` | Solo intervención humana |

Este mecanismo evita que varios agentes sobrescriban cambios y establece responsabilidades claras.

El escalado humano es una medida de control: cuando existe un conflicto de escritura, la persona responsable evalúa las propuestas y decide cómo resolverlo.

## Conclusión

La estación S4b introduce una arquitectura multiagente en la que tres agentes especializados colaboran mediante un servidor MCP común y un contrato explícito de comunicación.

Los elementos más importantes de esta arquitectura son:

1. **Contexto compartido:** acceso común a la información mediante `aula-contexto`.
2. **Especialización:** cada agente tiene una responsabilidad definida.
3. **Aislamiento:** los worktrees separan los cambios de los agentes.
4. **Coordinación:** los handoffs permiten transferir información entre tareas.
5. **Control:** las reglas de escritura y la revisión humana permiten gestionar conflictos.

El diagrama y este documento describen el diseño de la flotilla. Para completar el entregable de S4b también es necesario disponer del contrato validable y de la grabación que demuestre un ciclo completo de funcionamiento.