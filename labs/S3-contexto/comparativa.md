# Comparativa de motores de agente: Claude Code frente a OpenCode

## Encargo común

Escenario de comparación: implementar el criterio CA-05 de SPEC-001. Cuando el
grupo de una asignatura está completo, esa línea queda en lista de espera, no
consume créditos del límite y la evaluación continúa con las demás asignaturas.
El cambio debe incluir tests, respetar los invariantes del proyecto y no tocar
rutas fuera del alcance de la spec.

Los apartados siguientes son expectativas para un ejercicio hipotético con las
mismas instrucciones, el mismo estado inicial y los mismos tests. No son
resultados observados ni mediciones de los motores.

## Resultado teórico esperado

| Aspecto | Claude Code: expectativa | OpenCode: expectativa |
|---------|--------------------------|-----------------------|
| Comprensión del encargo | Debería extraer CA-05 y sus límites de la spec antes de editar. | Debería llegar al mismo alcance si recibe la spec y las mismas instrucciones. |
| Implementación | Debería modificar la lógica mínima para poner la línea en espera sin consumir créditos y continuar el proceso. | Se espera el mismo comportamiento funcional y un cambio de alcance equivalente. |
| Tests | Debería añadir cobertura para grupo completo, créditos no consumidos y continuidad de las demás líneas. | Se esperan los mismos casos y resultados de prueba. |
| Contexto del repositorio | Se espera que use `CLAUDE.md` y los perfiles de `.claude/` si están cargados y habilitados. | Se espera que se le proporcione explícitamente el mismo contrato, spec y reglas si no los carga automáticamente. |
| Protección de rutas | Se espera que aplique los permisos y hooks configurados para Claude Code. | Se espera que respete las mismas restricciones mediante los controles disponibles o las instrucciones recibidas. |
| Revisión | El perfil revisor debería examinar solo el diff, aplicar la checklist y no editar. | Se espera que un revisor equivalente examine el mismo diff con la misma checklist y sin editar. |

La expectativa de paridad es funcional: ambos deberían producir un cambio que
respete la spec y pase los mismos tests. Las diferencias en la forma de cargar
contexto o aplicar controles son hipótesis del escenario, no una conclusión
sobre capacidades, calidad, seguridad o coste.

## Criterio de elección

Para este repositorio, la decisión defendible es exigir el mismo contrato
versionado, los mismos criterios de aceptación, los mismos tests y una revisión
del diff independientemente del motor. Si una herramienta no carga alguna
instrucción o control automáticamente, el flujo debe entregárselo de forma
explícita o aplicar una protección equivalente fuera de esa herramienta.

No se declara un ganador: sin ejecutar ambos motores bajo condiciones
equivalentes, no hay base para comparar la calidad real de sus diffs, su coste
ni la eficacia de sus controles.

## Ciclo simulado de escritor y revisor con Orca

Este es un recorrido hipotético para mostrar cómo se aplicaría el patrón de la
guía. No se presenta como una ejecución real de Orca ni como evidencia de un
diff o de tests producidos por agentes.

1. **Preparación del coordinador:** Orca parte de una misma revisión limpia y
   crea dos worktrees aislados: uno para el escritor y otro para el revisor.
   Ambos reciben el encargo común, SPEC-001, `CLAUDE.md` y las reglas de rutas.
2. **Trabajo en paralelo:** el escritor implementa CA-05 y sus tests en su
   worktree. El revisor recibe el alcance y prepara la revisión; no modifica
   archivos ni comparte el directorio de trabajo del escritor.
3. **Entrega del escritor:** el escritor entrega el diff y la salida de tests.
   Orca pasa esos artefactos al revisor, conservando la separación entre
   worktrees.
4. **Revisión independiente:** el revisor comprueba el diff con la checklist de
   nueve puntos de la plantilla de PR, prestando atención a los límites de la
   spec, los tests y los invariantes. Devuelve un veredicto con observaciones
   justificadas por líneas concretas, sin editar el cambio.
5. **Corrección y nueva validación:** si hay observaciones, el escritor las
   resuelve en su worktree y vuelve a ejecutar los tests. El revisor inspecciona
   el diff actualizado.
6. **Integración:** solo tras el veredicto y la validación, Orca propone integrar
   el cambio; una persona revisa y aprueba la integración.

**Resultado esperado del ciclo:** un diff acotado, tests ejecutados y un
veredicto separado del trabajo de implementación. En una ejecución real se
deberían conservar la revisión base, los identificadores de ambos worktrees,
el diff, las salidas de tests, las observaciones del revisor y la decisión de
integración. No se inventan esos artefactos en esta simulación.

## Estado del entregable

Este documento aporta una comparación teórica con criterios explícitos y un
ciclo simulado escritor/revisor. No sustituye la evidencia de ejecutar el mismo
encargo con ambos motores ni la evidencia de ejecutar Orca en worktrees
paralelos.
