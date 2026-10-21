# Bitacora de S2

Registra preguntas de negocio, decisiones acordadas y evidencia de verificacion.

## Preguntas y dudas detectadas antes de implementar

### Q-01 — Naturaleza de los criterios de la plantilla

**Pregunta:** ¿Los criterios que vienen por defecto en el repositorio semilla están
mal redactados o contienen ambigüedades deliberadas que deben resolverse?

**Motivo:** Necesito distinguir entre un error de redacción y una decisión de negocio
que la especificación ha dejado abierta intencionadamente.

**Conclusión:** La guía de S2 confirma que existen ambigüedades deliberadas que deben
detectarse y resolverse antes de implementar.

### Q-02 — Flujo de trabajo Spec-Driven Development

**Pregunta:** ¿Tengo que decidir qué criterios están bien y cuáles no y, según eso,
hacer o no tests?

**Motivo:** Necesito determinar qué relación debe existir entre especificación,
criterios de aceptación, tests e implementación.

**Conclusión:** Los criterios ambiguos no se eliminan ni se dejan sin probar.
Primero debe cerrarse su significado en la especificación y después traducirse
a tests para mantener la trazabilidad completa.

### Q-03 — Funcionamiento del expediente académico

**Pregunta:** ¿Qué reglas debe seguir un expediente académico para diferenciar
correctamente el progreso académico de la nota media?

**Motivo:** Evitar asumir como correctas reglas incompletas de la plantilla y
comprender el tratamiento de créditos, calificaciones, asignaturas repetidas
y convalidadas.

**Resolución:** Las decisiones de CA-02 y CA-03 están documentadas en
[SPEC-002-expediente.md](../../specs/SPEC-002-expediente.md), ambigüedades
A-01 y A-02, y cubiertas por tests. No consta evidencia de validación externa
por parte del mentor; esa aprobación no se da por hecha.

### Q-04 — Terminología matemática de CA-04

**Pregunta:** ¿El valor sobre el que se aplica el redondeo final puede denominarse
"coeficiente"?

**Conclusión:** Se mantiene el término "cociente" utilizado por la SPEC: es el
resultado final de dividir la suma ponderada de calificaciones entre los créditos
computables. El redondeo se realiza una sola vez sobre dicho resultado.

### Q-05 — Significado de "asignatura computable" en CA-07

**Pregunta:** ¿Qué significa que una asignatura sea computable para la nota media?

**Motivo:** La SPEC utiliza el concepto pero su alcance depende del tratamiento
que se acuerde para asignaturas repetidas y convalidadas.

**Resolución:** Definido por las decisiones A-01 y A-02 de
[SPEC-002-expediente.md](../../specs/SPEC-002-expediente.md). Una asignatura
aprobada computa una vez con su último aprobado; una convalidación participa en
la media solo cuando tiene calificación numérica. No consta validación externa.

## Preguntas que requieren decisión de negocio

### QN-01 — Asignaturas repetidas (CA-02)

**Pregunta:** Cuando una asignatura tiene varias convocatorias y más de un registro
aprobado, ¿qué calificación debe utilizarse para calcular la nota media?

**Alternativas consideradas:**
- primer aprobado;
- último aprobado;
- mejor calificación;
- todas las convocatorias.

**Propuesta:** Utilizar únicamente el último registro aprobado, determinado de
forma estable por curso académico y convocatoria, y ponderar los créditos de la
asignatura una sola vez.

**Estado:** Resolución adoptada y recogida en SPEC-002/A-01; pendiente de
validación externa, sin evidencia de aprobación del mentor.

### QN-02 — Asignaturas convalidadas (CA-03)

**Pregunta:** ¿Cómo participa una asignatura convalidada en la nota media cuando
tiene calificación numérica y cuando carece de ella?

**Alternativas consideradas:**
- excluir siempre las convalidaciones de la media;
- incluir siempre las convalidaciones;
- distinguir entre convalidaciones con y sin calificación.

**Propuesta:** Si tiene calificación numérica, participa en la nota media con esa
calificación. Si no tiene calificación, no participa en el numerador ni en el
denominador de la media. En ambos casos sus créditos cuentan como superados.

**Estado:** Resolución adoptada y recogida en SPEC-002/A-02; pendiente de
validación externa, sin evidencia de aprobación del mentor.

## Decisión de negocio: plan de matrícula confirmado (SPEC-001/INV-03)

Antes de confirmar una matrícula se pueden cambiar el plan aplicado y su
versión. Desde la primera transición a `CONFIRMADA`, ambos quedan bloqueados de
forma permanente, incluidos los estados `EN_CURSO`, `CALIFICADA` y `CERRADA`.
Si una matrícula confirmada pasa a `ANULADA`, el bloqueo continúa. Una
adaptación a un plan nuevo se tramita por separado y no modifica
retroactivamente la matrícula original.

La matrícula debe conservar si alguna vez fue confirmada: el estado actual
`ANULADA` por sí solo no permite distinguir una anulación anterior a la
confirmación de otra posterior. El modelo debe activar esa marca también al
construirse directamente en `CONFIRMADA`, `EN_CURSO`, `CALIFICADA` o `CERRADA`,
y no permitir que código externo la desactive.

**Pruebas acordadas:** cambio de plan y versión antes de confirmar; rechazo de
cambios por transición y por asignación directa tras confirmar; conservación
del bloqueo tras anular; protección desde la construcción en estados
confirmados o posteriores; e imposibilidad de desactivar externamente la marca
de confirmación.

La resolución está recogida en SPEC-001/A-04 y cubierta por tests etiquetados
`cubre: SPEC-001/INV-03`. No consta evidencia de validación externa del mentor;
la aprobación de la decisión de negocio no se interpreta como aprobación
externa.

### Tiempo dedicado a S2

**Actividades realizadas:**
- Análisis de SPEC-001 y SPEC-002.
- Resolución de ambigüedades y decisiones de negocio.
- Diseño y ejecución de pruebas.
- Implementación incremental de los criterios de aceptación.
- Corrección de los invariantes INV-02 e INV-03.
- Verificación de la suite y comprobación de trazabilidad.
- Actualización de especificaciones y bitácora.

**Tiempo efectivo:** 10 horas aproximadamente, la mayoría en entender la lógica y reglas de negocio.

**Uso de IA:** apoyo en el análisis de requisitos, generación y revisión de pruebas, implementación y detección de errores.

**Reflexión:** la mayor parte del esfuerzo no estuvo en escribir código, sino en interpretar correctamente las reglas de negocio, resolver ambigüedades y comprobar que los tests realmente verificaban lo especificado.