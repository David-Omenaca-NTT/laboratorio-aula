# SPEC-003: integracion del agente de conformidad en PR

Version: v0.1.0 | Estado: activa

## Proposito

Verificar que el agente de conformidad puede evaluar una entrada de PR con criterios declarados, comprobar su cobertura y emitir un veredicto JSON utilizable por CI.

## Criterios de aceptacion

- CA-01: dada una PR con un criterio declarado, un test que lo cubre y cambios dentro de las rutas autorizadas, cuando se ejecuta el agente en modo JSON, entonces devuelve el veredicto `conforme` y el criterio figura como cubierto.

## Fuera de alcance

Rutas: .github/workflows/ci.yml, herramientas/conformidad_pr.py, labs/S4b-flotilla/flotilla.md, specs/SPEC-003-agente-conformidad-pr.md, tests/test_agente_conformidad_pr.py