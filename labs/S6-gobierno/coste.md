# Coste por unidad de resultado

## Objetivo

S6 pide registrar el coste en tokens y calcular el coste por criterio de
aceptación cubierto y verificado. Este documento define la unidad de resultado,
la fórmula de atribución y qué puede afirmarse con la evidencia actual, sin
confundir valores declarados con mediciones de facturación.

La [guía de S6](GUIA.md) exige el paquete de evidencia por PR, incluido el
coste en tokens, y el coste por criterio de aceptación cubierto y verificado.
La [pista 3](pistas/3-fragmento.md) concreta que se sumen los tokens de las
intervenciones del agente en la rama y se dividan entre los criterios cubiertos
y en verde.

## Alcance del coste

Los agentes actuales de Conformidad, Triaje y Modernización son deterministas y
offline: sus implementaciones aplican reglas locales y no realizan llamadas a
un LLM. Por tanto, para estas implementaciones actuales:

```text
tokens_entrada = 0
tokens_salida = 0
tokens_total = 0
coste_llm_api_usd = 0.0
```

Estos ceros describen exclusivamente el componente LLM/API, derivado de que no
hay una llamada a modelo. No son mediciones de facturación ni del coste
operativo total:

```text
coste LLM/API = 0
≠
coste operativo total = 0
```

El repositorio no dispone de telemetría suficiente para atribuir coste de CI,
runners, almacenamiento, mantenimiento u otra infraestructura. No se asignan
precios estimados a esos conceptos.

## Evidencia disponible

- [`GUIA.md`](GUIA.md) exige coste en tokens y coste por CA cubierto y
  verificado.
- [`pistas/3-fragmento.md`](pistas/3-fragmento.md) propone sumar los tokens de
  las intervenciones del agente y dividirlos entre los CA cubiertos y en verde.
- Los tres ARM declaran costes por ejecución de 0.0 USD:
  [`conformidad.yaml`](../../manifiestos/conformidad.yaml),
  [`triaje.yaml`](../../manifiestos/triaje.yaml) y
  [`modernizacion.yaml`](../../manifiestos/modernizacion.yaml). El ARM de
  Conformidad declara además un tope diario de 3.0 USD, pero no se encontró
  evidencia de que se aplique técnicamente.
- Los evaluadores
  ([Conformidad](../../agentes/conformidad/evaluar.py),
  [Triaje](../../agentes/triaje/evaluar.py) y
  [Modernización](../../agentes/modernizacion/evaluar.py)) producen métricas
  offline, latencia y el campo `coste_usd_por_ejecucion` con valor literal
  `0.0`.
- Los informes disponibles registran 15 casos para
  [Conformidad](../../evals/informes/evaluacion-20261110-174137.json), 16 para
  [Triaje](../../evals/informes/evaluacion-20261111-145352.json) y 12 para
  [Modernización](../../evals/informes/evaluacion-modernizacion-20261111-150340.json).
  Registran `coste_usd_por_ejecucion: 0.0`. Esos casos pertenecen a evaluaciones
  doradas; no son criterios de aceptación.
- [`conformidad_pr.py`](../../herramientas/conformidad_pr.py) extrae los CA
  declarados en la descripción de una PR y prepara la entrada del evaluador.
  [`agente.py`](../../agentes/conformidad/agente.py) compara los criterios
  declarados con las etiquetas de cobertura en los tests.
- [`ci.yml`](../../.github/workflows/ci.yml) ejecuta tests y exige cobertura,
  pero no registra tokens ni costes de CI, ni deja persistida una correlación de
  coste por CA para una PR y SHA.

El valor 0.0 USD de los informes y manifiestos es coherente con el diseño
offline/determinista actual. No constituye telemetría de facturación ni mide el
coste operativo total.

## Estado actual de medición

| Dato | Estado | Valor actual | Interpretación |
|---|---|---:|---|
| Tokens de entrada | DERIVABLE POR DISEÑO | 0 | Los agentes actuales no llaman a un LLM; no hay contador de tokens instrumentado. |
| Tokens de salida | DERIVABLE POR DISEÑO | 0 | Los agentes actuales no llaman a un LLM; no hay contador de tokens instrumentado. |
| Tokens totales | DERIVABLE POR DISEÑO | 0 | Suma de entrada y salida para el componente LLM; no existe telemetría persistida. |
| Coste LLM/API | DERIVABLE POR DISEÑO | 0.0 USD | No se realiza llamada a modelo en la implementación actual; no es coste operativo total medido. |
| `coste_usd_por_ejecucion` | DECLARADO | 0.0 USD en los informes | Campo emitido como literal por los evaluadores offline; no procede de facturación. |
| `medio_por_ejecucion_usd` | DECLARADO | 0.0 USD en los tres ARM | Valor del manifiesto, no una medición económica. |
| `tope_diario_usd` | DECLARADO | 3.0 USD para Conformidad; no consta para los otros dos | Declaración del ARM de Conformidad; no hay evidencia de contador, bloqueo o alerta que lo haga efectivo. |
| Coste CI | NO INSTRUMENTADO | No disponible | No se registran costes de ejecución de workflows, runners u otros servicios. |
| Latencia | MEDIDO | 1.1 ms Conformidad; 0.057 ms Triaje; 0.094 ms Modernización en los informes citados | Latencia media de evaluación offline; no equivale a coste monetario. |
| Casos de evaluación | MEDIDO | 15 Conformidad; 16 Triaje; 12 Modernización | Tamaño de los conjuntos evaluados; no son CA de una PR. |
| Coste por CA | NO INSTRUMENTADO | No calculable para una PR real | Falta una correlación persistida entre PR, SHA, CA cubiertos, CI verde y coste atribuible. |

## Unidad de resultado

La unidad principal es un **criterio de aceptación único cubierto y verificado**.
Un CA se cuenta una sola vez para una PR y un SHA, aunque tenga más de un test
asociado.

Para esta métrica, solo se considera verificado cuando puede correlacionarse,
para la misma PR y el mismo SHA:

```text
CA declarado
    ∩
CA cubierto por Conformidad
    ∩
verificación CI satisfactoria
```

Los casos dorados, número de tests, archivos modificados y métricas de
precision/recall/F1 no sustituyen al número de CA verificados.

## Fórmula de atribución

Para una PR `p` y un SHA concreto:

```text
CA_verificados(p) =
    CA_declarados(p)
    ∩ CA_cubiertos(p)
    ∩ CA_con_CI_verde(p, SHA)
```

El consumo total de tokens atribuible a las intervenciones de agente en esa PR
se define como:

```text
tokens_totales(p) =
    tokens_entrada(p) + tokens_salida(p)
```

Entonces:

```text
tokens_por_CA(p) =
    tokens_totales(p) / |CA_verificados(p)|
```

La división solo es válida si:

```text
|CA_verificados(p)| > 0
```

Si no existen CA verificados o no puede comprobarse la correlación para el mismo
SHA, el resultado es **NO CALCULABLE**. No se divide artificialmente por 1, por
el número de tests ni por el número de casos dorados.

Cuando exista telemetría económica suficiente, puede calcularse además:

```text
coste_por_CA_usd(p) =
    coste_atribuible_usd(p) / |CA_verificados(p)|
```

`coste_atribuible_usd(p)` solo debe incluir componentes realmente medidos e
imputables a la PR, por ejemplo coste LLM/API y coste CI instrumentado. Mientras
el coste CI e infraestructura no se instrumente, esta fórmula no produce el
coste operativo completo por CA.

## Resultado actual

Para las implementaciones actuales, deterministas y sin llamadas a modelo:

```text
tokens_entrada = 0
tokens_salida = 0
tokens_total = 0
coste_llm_api_usd = 0.0
```

El coste operativo total y el coste operativo total por CA no son calculables
con los datos disponibles. Aunque los tokens del componente LLM sean cero por
diseño, no hay medición atribuible de CI, runners, almacenamiento, mantenimiento
u otra infraestructura.

## Ejemplo ilustrativo

**ILUSTRATIVO; PR hipotética, no es evidencia de una PR existente.**

```text
CA declarados: CA-01, CA-02, CA-03
CA cubiertos por Conformidad: CA-01, CA-02
CA con CI verde para el mismo SHA: CA-01, CA-02

CA verificados = 2
```

Con la arquitectura determinista actual:

```text
tokens LLM = 0
tokens por CA = 0 / 2 = 0 tokens/CA
coste LLM/API = 0.0 USD
coste LLM/API por CA = 0.0 USD/CA
```

Esto representa únicamente el componente LLM/API. No demuestra que el coste
operativo total de esa PR sea 0.

## Brechas de instrumentación

Actualmente no hay evidencia persistida que permita sumar tokens de
intervenciones por rama/PR, identificar un modelo o tarifa, imputar coste de CI
ni verificar que los CA cubiertos por Conformidad tienen CI verde para el mismo
SHA. Los informes offline describen casos de evaluación y valores declarados de
coste, no ejecuciones de trabajo de una PR.

El tope diario de 3.0 USD del ARM de Conformidad tampoco se acredita como límite
aplicado. Este documento define el cálculo, pero no implementa telemetría,
contadores, alertas, bloqueo ni atribución económica.

## Datos mínimos de evidencia

Para que el cálculo pueda convertirse en evidencia automática, habría que
persistir por ejecución, como mínimo:

- PR e identificador de ejecución;
- SHA evaluado;
- agente y versión;
- timestamp;
- CA declarados, CA cubiertos y CA verificados, con referencias a sus fuentes;
- tokens de entrada, tokens de salida y tokens totales;
- modelo y proveedor, si aplica;
- precio y versión de tarifa, si aplica;
- coste LLM/API;
- coste CI, cuando se instrumente;
- resultados de los gates y estado de CI asociados al mismo SHA.

Los registros deben permitir deduplicar CA, reproducir la fórmula y distinguir
valores medidos de valores declarados o derivados por diseño. La instrumentación
de estos datos queda fuera del alcance de este documento.

## Conclusión

En las implementaciones actuales, el componente LLM/API es **0 tokens y
0.0 USD por diseño**, porque los agentes son deterministas y no llaman a un
modelo. Esto no equivale a coste operativo total cero: el coste de CI,
infraestructura y otros componentes no está instrumentado.

Queda definido el modelo de cálculo por criterio de aceptación único cubierto y
verificado. Sin embargo, la correlación automática PR/SHA/CA/coste todavía debe
instrumentarse para obtener un coste operativo real por CA.
