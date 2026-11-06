# Desviaciones conocidas

## D-01 - Convalidaciones

### Comportamiento legado

Toda asignatura convalidada:

- suma `5 x creditos` al numerador;
- no suma esos creditos al denominador;
- aplica este comportamiento tenga o no tenga calificacion numerica.

### Comportamiento nuevo

Una asignatura convalidada:

- si tiene calificacion numerica, participa en la nota media usando su nota real y sus creditos en el denominador;
- si no tiene calificacion numerica, no participa en la nota media;
- cuenta como creditos superados en ambos casos.

### Referencia

`SPEC-002 / CA-03`

### Naturaleza

Correccion deliberada del comportamiento heredado para aplicar la semantica definida por la especificacion.

### Efecto aguas abajo

La nota media puede cambiar respecto al sistema legado, especialmente en expedientes con asignaturas convalidadas.

Esto puede afectar a procesos que utilicen la media como criterio de ordenacion o corte, como clasificaciones de expedientes o becas.

Los creditos superados y el porcentaje de progreso no deben presentar diferencias atribuibles a esta desviacion.

---

## D-02 - Redondeo

### Comportamiento legado

1. Ejecuta `round(nota, 2)`.
2. Acumula posteriormente el valor ya redondeado.

### Comportamiento nuevo

1. Acumula los valores exactos.
2. Calcula la media.
3. Aplica `ROUND_HALF_UP` unicamente al resultado final.

### Referencia

`SPEC-002 / INV-01 + CA-04`

### Naturaleza

Correccion deliberada del comportamiento heredado.

### Efecto aguas abajo

Determinados expedientes situados en fronteras de redondeo pueden cambiar de resultado.

---

## D-03 - Redondeo del porcentaje de progreso

### Comportamiento legado

El porcentaje de progreso se calcula utilizando aritmética de coma flotante
binaria:

`round((creditos_superados * 100.0) / creditos_titulo, 2)`

En determinados valores frontera, la representación binaria puede situar el
resultado ligeramente por encima o por debajo de su valor decimal exacto y
producir un redondeo diferente.

### Comportamiento nuevo

El motor moderno utiliza aritmética `Decimal`, calcula el porcentaje de
créditos superados sobre los créditos totales del título y aplica el redondeo
una sola vez al final mediante `ROUND_HALF_UP`.

### Referencia

`SPEC-002 / INV-01 + INV-02 + CA-06`

### Naturaleza

Corrección deliberada del comportamiento heredado para cumplir las invariantes
de cálculo decimal y redondeo establecidas por la especificación.

### Efecto aguas abajo

Determinados expedientes situados en fronteras de redondeo pueden presentar una
diferencia de `0.01` en `progreso_pct`. Los créditos superados no se modifican.
