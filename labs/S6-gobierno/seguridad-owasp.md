# Evaluación OWASP de la flotilla

## Alcance

Revisión de Conformidad, Triaje y Modernización frente al OWASP Top 10 for LLM Applications, usando únicamente evidencia del repositorio.

La flotilla actual es determinista y no realiza inferencia mediante LLM. No usa prompts de sistema, RAG, embeddings ni entrenamiento; no se atribuyen controles inexistentes para esos mecanismos.

## Resultado

El riesgo principal es LLM06 — Excessive Agency, aplicado al exceso de permisos, funcionalidad o autonomía. Está parcialmente controlado mediante ARM, separación de responsabilidades y gates, pero algunos controles siguen siendo declarativos u organizativos.

## Matriz OWASP Top 10

| Riesgo | Estado | Evidencia | Riesgo residual |
|---|---|---|---|
| LLM01 — Prompt Injection | NO APLICA | No hay LLM ni inferencia por prompts en `agentes/*/agente.py`. | Las entradas y evidencias podrían manipularse, aunque no mediante prompt injection de un modelo. |
| LLM02 — Sensitive Information Disclosure | PARCIALMENTE CONTROLADO | `manifiestos/*.yaml` declara datos accesibles/prohibidos y los workflows analizados aplican permisos explícitos principalmente de lectura. | No existe aislamiento técnico completo de secretos ni garantía independiente de las restricciones de lectura. |
| LLM03 — Supply Chain Vulnerabilities | PARCIALMENTE CONTROLADO | `requirements.txt` fija versiones de dependencias principales y los workflows usan acciones versionadas. | No hay auditoría de dependencias ni pinning de acciones por SHA. |
| LLM04 — Data and Model Poisoning | NO APLICA al modelo | No hay entrenamiento, fine-tuning, RAG ni modelo externo. | Los casos dorados e informes podrían alterarse si no se refuerza su integridad. |
| LLM05 — Improper Output Handling | PARCIALMENTE CONTROLADO | Los agentes devuelven estructuras; Modernización normaliza rutas y rechaza rutas absolutas o con `..`. | Falta una validación común de salidas y handoffs antes de consumirlos. |
| LLM06 — Excessive Agency | PARCIALMENTE CONTROLADO | ARM, niveles N2/N3, separación de responsabilidades, permisos de lectura, SHA y caducidad de evaluación. | No todas las capacidades contractuales están implementadas; algunos controles de escritura, rama y revisión no están técnicamente demostrados. |
| LLM07 — System Prompt Leakage | NO APLICA | No existen prompts de sistema ni llamadas a modelos. | No aplica al diseño determinista actual. |
| LLM08 — Vector and Embedding Weaknesses | NO APLICA | No hay vector store, embeddings ni recuperación semántica. | No aplica mientras no se introduzca RAG. |
| LLM09 — Misinformation | PARCIALMENTE CONTROLADO | Evaluaciones offline persistidas en `evals/informes/` con métricas y casos dorados. | Las métricas no garantizan corrección ante entradas nuevas; falta confianza calibrada y revisión formal. |
| LLM10 — Unbounded Consumption | PARCIALMENTE CONTROLADO | Los agentes y evaluadores son deterministas y declaran juez offline y coste 0.0 USD. | No hay límites específicos de tiempo, concurrencia, volumen o consumo de CI. |

## LLM06 — Excessive Agency

La mitigación existente relaciona:

- niveles de autonomía N2/N3 y ARM por agente;
- herramientas y datos declarados explícitamente;
- SHA-256 del código y caducidad de la evaluación;
- separación de responsabilidades entre Conformidad, Triaje y Modernización;
- worktrees, permisos de lectura y restricciones de modificación;
- gate de manifiestos que valida presencia, estructura, hash y vigencia;
- protección de `main` mediante ruleset y gates; la revisión humana permanece como control aplicable cuando corresponde y no se considera técnicamente demostrada en todos los flujos.

`agentes/flotilla/contrato.json` declara capacidades de escritura en comentarios o ramas que no están todas demostradas en la implementación. No deben considerarse controles efectivos sin evidencia adicional.

## Controles acreditados

- Flotilla determinista y offline, sin inferencia LLM.
- ARM individual para los tres agentes.
- SHA-256 de código y evaluación con caducidad.
- Separación de agentes y responsabilidades.
- Restricciones documentadas y controles locales de modificación.
- Gate de manifiestos con bloqueo por ausencia, hash o evaluación caducada.
- Evaluaciones persistidas con métricas por agente.
- Permisos de lectura en los workflows analizados.

## Riesgos residuales

- Aislamiento técnico de secretos.
- Validación común de handoffs y salidas.
- Supply chain más fuerte.
- Integridad adicional de evaluaciones e informes.
- Límites operativos y de recursos.
- Correspondencia verificable entre capacidades contractuales y capacidades realmente implementadas.
- Demostración técnica completa de protección de rama y revisión humana.

## Riesgos no aplicables

No aplican al diseño actual los riesgos ligados a mecanismos inexistentes: prompt injection contra un LLM, fuga de system prompts, debilidades de vectores o embeddings y poisoning de un modelo entrenado.

Esto no elimina los riesgos tradicionales de manipulación de entradas, integridad de evaluaciones o autorización excesiva.

## Conclusión

La postura OWASP de la flotilla es **PARCIALMENTE CONTROLADA**. S6 acredita identidad de release, límites declarados, separación, evaluación y gates, pero todavía no demuestra aislamiento técnico completo, validación común de salidas, supply chain robusta ni límites operativos.
