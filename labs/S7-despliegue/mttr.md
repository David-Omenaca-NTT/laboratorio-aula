# MTTR y retrospectiva S7

## Fórmula

**MTTR = instante de recuperación − instante de detección**

La detección es la primera señal comprobable del fallo. La recuperación es la
primera comprobación posterior que confirma que el servicio volvió a funcionar.
Registrar ambos instantes con zona horaria y fuente; sin ellos no se calcula
una duración.

## Rondas

| Ronda | Diagnóstico | Instante de detección | Instante de recuperación | MTTR | Evidencia y estado |
|---|---|---|---|---|---|
| Ronda 1 — Manual | Diagnóstico y recuperación manual, sin Triaje; ejecución pendiente de evidencia. | Pendiente de medición | Pendiente de medición | Pendiente de medición | No hay marcas de tiempo ni evidencia registrada de recuperación. |
| Ronda 2 — Triaje v2 | Diagnóstico asistido por Triaje v2; recuperó JUnit y clasificó el fallo como `tests`. | Pendiente de medición | Pendiente de medición | Pendiente de medición | [CI experimental 44546344178](https://github.com/David-Omenaca-NTT/aula-triaje/actions/runs/44546344178): 111 tests, 105 correctos y 6 fallidos. Detección y clasificación validadas; recuperación y tiempos pendientes. |

El run 44546344178 prueba que CI detectó los tests fallidos y que Triaje v2
recuperó y clasificó la evidencia. No aporta el instante de recuperación ni un
MTTR.

## Retrospectiva del experimento de Triaje v2

### Hipótesis inicial observada

En el experimento original, Triaje no recuperó JUnit y reportó
`pytest_disponible: false`. Clasificó el incidente como `cobertura_spec` y
propuso un handoff incorrecto a Conformidad. Esa fue la hipótesis inicial del
diagnóstico automatizado, no una causa confirmada.

### Evidencias observadas

- CI reportó 111 tests: 105 correctos, 6 fallidos, 0 errores y 0 omitidos.
- En la validación integrada posterior a la corrección: `JUnit disponible: true`,
  clasificación `tests`, `spec_id: null` y `handoff: null`.
- Triaje v2 recuperó el artifact JUnit y no confundió referencias a `SPEC-002`
  con un problema de cobertura.
- La corrección se integró mediante [PR #44](https://github.com/David-Omenaca-NTT/aula-triaje/pull/44)
  y el commit de merge
  [`f9a2a3061e66d518d7ba6532ca86115db541993a`](https://github.com/David-Omenaca-NTT/aula-triaje/commit/f9a2a3061e66d518d7ba6532ca86115db541993a).

### Causa real

El defecto controlado sustituyó una división por una multiplicación en
`nota_media_ponderada()`, lo que provocó seis tests fallidos. El defecto de
Triaje era distinto: no recuperaba JUnit y clasificaba mal un fallo que CI ya
había detectado.

### Diferencia entre hipótesis y causa

`cobertura_spec` fue una interpretación errónea de Triaje causada por la
ausencia del artifact. La causa del fallo experimental fue la mutación
aritmética. JUnit permitió distinguir el fallo de tests de un supuesto problema
de cobertura y evitó el handoff incorrecto.

### Lecciones aprendidas

- La detección de CI y la recuperación de sus artifacts son partes distintas
  del diagnóstico y deben validarse por separado.
- La clasificación debe basarse en resultados JUnit estructurados, no en
  referencias textuales a una especificación.
- Una clasificación correcta no equivale a recuperación del servicio ni a
  rollback efectivo.
- El run valida detección, recuperación de evidencia y clasificación; no aporta
  tiempos de recuperación. Ambas rondas y el MTTR quedan pendientes de medición.
- La mutación es un defecto controlado del experimento, no código apto para
  producción.
