# Procedimiento de reversión S7

## Alcance

El workflow de S7 construye la imagen en el runner, publica el servicio solo
en `127.0.0.1:18000` y elimina el contenedor y la imagen al finalizar. No hay
un servicio persistente al que aplicar rollback. Este procedimiento documenta
la recuperación de una ejecución efímera mediante una revisión estable.

## Condiciones que desencadenan la reversión

Detener la versión candidata y recuperar la última revisión estable si se da
cualquiera de estas condiciones:

- El contenedor no permanece activo o `GET /salud` no devuelve `estado: ok`.
- `POST /matriculas` no devuelve HTTP 201 con una matrícula validada.
- La validación de observabilidad falla: falta el evento esperado o no coincide
  el `correlation_id` entre el acceso HTTP y el evento de negocio.
- Los tests de la versión candidata fallan y bloquean su aceptación.

## Identificación de la última versión estable

1. Localizar la ejecución más reciente del workflow `S7 despliegue efímero`
   sobre `main` que haya terminado correctamente.
2. Registrar el SHA completo indicado en su evidencia `metadata.txt` (`sha`).
   Ese SHA identifica el código del que se reconstruye la imagen estable; no
   usar una etiqueta mutable como criterio de selección.
3. Si no existe una ejecución exitosa verificable, no se considera identificada
   una versión estable y no se debe elegir una por suposición.

## Procedimiento de recuperación

1. Detener y eliminar el contenedor candidato con
   `docker rm --force <nombre-del-contenedor>`.
2. Comprobar que `127.0.0.1:18000` ya no responde desde el runner.
3. Obtener el checkout del SHA estable y construir localmente:
   `docker build --tag aula:s7-<sha> <checkout-del-sha>`.
4. Arrancar esa imagen con el puerto enlazado a loopback
   (`127.0.0.1:18000:8000`) y las variables de matrícula que requiere el
   workflow.
5. Ejecutar las comprobaciones posteriores. Si la imagen no está disponible,
   reconstruirla desde el SHA verificado. No descargar ni publicar una imagen.

## Comprobaciones posteriores

- `GET /salud` responde correctamente y su JSON contiene `estado: ok`.
- `POST /matriculas` devuelve HTTP 201 y una matrícula validada con `MAT101`
  admitida.
- Los logs contienen las solicitudes y el evento `matricula.created`; los
  eventos de la operación comparten el `correlation_id`.
- La evidencia registra el SHA de la revisión recuperada.
- Al finalizar, se eliminan el contenedor y la imagen temporal.

## Estado: documentado frente a probado

**Documentado:** condiciones de reversión, selección de SHA estable,
recuperación local y verificaciones posteriores.

**Probado:** no hay evidencia de una ejecución que haya aplicado esta
reversión a una revisión anterior. El despliegue efímero y sus smoke tests no
demuestran por sí solos que el procedimiento de recuperación haya funcionado.

## Limitaciones del despliegue efímero

El runner de CI es temporal y sus recursos no proporcionan rollback persistente.
Este procedimiento no cubre tráfico real, balanceadores, estado externo ni
migraciones de datos. Para considerar probado el rollback debe registrarse una
ejecución que lo active y confirme el servicio recuperado.
