# SPEC-002: cálculo de expediente

Versión: v0.1.0 | Estado: activa
Autor: plantilla del laboratorio | Revisor: pendiente

> Especificación de partida para S2. Antes de implementar, registra las preguntas
> que necesiten una decisión de negocio y acuerda la resolución con el mentor.

## Propósito

Calcular el estado académico de un estudiante respecto de su plan: nota media
ponderada por créditos, créditos superados y porcentaje de título completado.
De la nota media dependen procesos aguas abajo, entre ellos la ordenación para
becas, así que la reproducibilidad exacta del número es un requisito, no un detalle.

## Entradas y salidas

| Elemento | Tipo | Restricciones |
|----------|------|---------------|
| Expediente | lista de registros académicos | Un registro por convocatoria consumida o convalidación |
| Plan | plan versionado | Determina créditos por asignatura y créditos del título |
| Nota media | decimal | Exactamente dos decimales, redondeo half-up |
| Créditos superados | entero | |
| Progreso | decimal | Porcentaje con dos decimales |

## Invariantes

- INV-01: el redondeo se aplica una sola vez y al final del cálculo. Ningún valor intermedio se redondea.
- INV-02: el cálculo usa aritmética decimal, nunca coma flotante binaria.
- INV-03: el resultado es determinista: el mismo expediente y el mismo plan producen siempre el mismo número, con independencia del orden de los registros.

## Criterios de aceptación

- CA-01: dado un expediente con asignaturas aprobadas en primera convocatoria, cuando se calcula la nota media, entonces es la media de las notas ponderada por los créditos de cada asignatura, con dos decimales.
- CA-02: dada una asignatura repetida y finalmente aprobada, cuando se calcula la nota media, entonces su calificación se incorpora conforme a la normativa académica vigente.
- CA-03: dada una asignatura convalidada, cuando se calcula la nota media, entonces recibe el tratamiento previsto para las convalidaciones.
- CA-04: dado cualquier expediente, cuando se calcula la nota media, entonces el redondeo a dos decimales se aplica una sola vez sobre el cociente final y nunca sobre cada asignatura.
- CA-05: dada una asignatura convalidada, cuando se calculan los créditos superados, entonces sus créditos sí cuentan como superados.
- CA-06: dado un expediente, cuando se calcula el progreso, entonces es el porcentaje de créditos superados sobre los créditos del título, con dos decimales.
- CA-07: dado un expediente sin ninguna asignatura computable, cuando se calcula la nota media, entonces devuelve 0,00 sin error.

## Casos límite

| Caso | Resultado esperado |
|------|--------------------|
| Expediente vacío | Nota media 0,00, créditos 0, progreso 0,00 |
| Todas las asignaturas convalidadas sin calificación numérica | Nota media 0,00; sus créditos cuentan como superados |
| Asignatura aprobada en convocatoria 2 y también en convocatoria 4 | Se computa la calificación del último registro aprobado |
| Nota con más de dos decimales en origen | Se conserva íntegra en el numerador y solo se redondea el cociente final |
| Media exactamente en el punto medio, por ejemplo 7,005 | Redondeo half-up a 7,01 |

## Fuera de alcance

Rutas: src/aula/reglas/media.py, tests/test_media_expediente.py, specs/SPEC-002-expediente.md

- Menciones, matrículas de honor y premios extraordinarios.
- Reconocimiento de créditos por actividades no académicas.
- Media de acceso a máster, que usa otra normativa.
- Decisión de convalidar, que es un proceso previo.

## Ambigüedades detectadas y resolución

| # | Ambigüedad | Resolución adoptada | Alternativas descartadas y por qué |
|---|-----------|---------------------|-------------------------------------|
| A-01 | CA-02 no determina qué calificación debe utilizarse para calcular la nota media cuando una asignatura tiene varias convocatorias y más de un registro aprobado. La referencia genérica a la "normativa académica vigente" no permite obtener un resultado determinista sin concretar dicha regla. | Para cada asignatura se computará una única calificación: la correspondiente al último registro aprobado, determinado por curso académico y convocatoria. Los intentos suspensos o no presentados permanecen en el expediente y consumen convocatoria cuando corresponda, pero no participan en la nota media. Los créditos de la asignatura se ponderan una sola vez. | Se descarta utilizar la primera nota aprobada porque ignoraría una superación posterior; utilizar la mejor nota porque introduciría una política favorable no establecida en la especificación; y computar todas las convocatorias porque supondría ponderar varias veces los créditos de una misma asignatura. Como referencia se ha consultado el tratamiento académico de la Universidad de Zaragoza. |
| A-02 | CA-03 indica que una asignatura convalidada recibirá "el tratamiento previsto para las convalidaciones", pero no especifica si participa en la nota media ni cómo actuar cuando existe o no una calificación numérica asociada. | Se adopta un tratamiento inspirado en la normativa de reconocimiento de créditos de la Universidad de Zaragoza: una asignatura convalidada con calificación numérica participa en la nota media utilizando dicha calificación. Si carece de calificación numérica, no participa ni en el numerador ni en el denominador de la nota media. En ambos casos sus créditos cuentan como superados. | Se descarta excluir siempre las convalidaciones de la nota media porque impediría incorporar aquellas que disponen de calificación de origen; y se descarta obligar a que toda convalidación tenga nota porque el modelo admite registros sin calificación y existen reconocimientos sin calificación numérica. |