"""Evalua evidencia de caracterizacion y equivalencia de un refactor legado."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

DECISIONES = {
    "aprobable",
    "caracterizacion_rota",
    "equivalencia_rota",
    "fuera_de_alcance",
    "desviacion_no_justificada",
    "evidencia_insuficiente",
}
_ESTADOS = {"passed", "failed", "unknown"}
_SPEC = re.compile(r"SPEC-\d+", re.IGNORECASE)
_LEGADO = ("src", "aula", "legado")


def _normalizar_entrada(entrada: Any) -> dict[str, Any]:
    if not isinstance(entrada, dict):
        return {}
    contexto = entrada.get("contexto")
    resultado = contexto.copy() if isinstance(contexto, dict) else {}
    resultado.update({clave: valor for clave, valor in entrada.items() if clave != "contexto"})
    return resultado


def _estado(evidencia: Any) -> tuple[bool | None, str | None]:
    if not isinstance(evidencia, dict):
        return None, None
    estado = evidencia.get("status")
    if not isinstance(estado, str):
        return None, None
    estado = estado.strip().lower()
    if estado not in _ESTADOS:
        return None, None
    return {"passed": True, "failed": False, "unknown": None}[estado], estado


def _ruta_normalizada(valor: Any) -> str | None:
    if not isinstance(valor, str) or not valor.strip():
        return None
    texto = valor.strip().replace("\\", "/")
    ruta = PurePosixPath(texto)
    if ruta.is_absolute() or ".." in ruta.parts:
        return texto
    return str(ruta)


def _ruta_permitida(ruta: str | None, bateria: str | None) -> bool:
    if ruta is None:
        return False
    partes = PurePosixPath(ruta).parts
    if PurePosixPath(ruta).is_absolute() or ".." in partes or re.match(r"^[A-Za-z]:", ruta):
        return False
    return partes[:len(_LEGADO)] == _LEGADO or ruta == bateria


def _desviaciones_validas(valor: Any) -> tuple[list[dict[str, str]], bool]:
    if not isinstance(valor, list):
        return [], False
    salida = []
    validas = True
    for desviacion in valor:
        if not isinstance(desviacion, dict):
            validas = False
            continue
        descripcion = desviacion.get("descripcion")
        justificacion = desviacion.get("justificacion")
        if not isinstance(descripcion, str) or not isinstance(justificacion, str):
            validas = False
            continue
        salida.append({
            "descripcion": descripcion,
            "justificacion": justificacion,
        })
    return salida, validas


def analizar(entrada: Any) -> dict[str, Any]:
    """Devuelve una decision estructurada sin ejecutar acciones externas."""
    datos = _normalizar_entrada(entrada)
    ruta = _ruta_normalizada(datos.get("ruta"))
    bateria = _ruta_normalizada(datos.get("bateria"))
    spec_valor = datos.get("spec_id")
    spec_id = (
        spec_valor.strip().upper()
        if isinstance(spec_valor, str) and _SPEC.fullmatch(spec_valor.strip())
        else None
    )
    caracterizacion_verde, caracterizacion_estado = _estado(
        datos.get("resultado_caracterizacion")
    )
    equivalencia_verde, equivalencia_estado = _estado(
        datos.get("resultado_equivalencia")
    )

    archivos = datos.get("archivos_modificados")
    archivos_validos = isinstance(archivos, list) and all(
        isinstance(archivo, str) and bool(archivo.strip()) for archivo in archivos
    )
    archivos_a_comprobar = (
        [(archivo, _ruta_normalizada(archivo)) for archivo in archivos]
        if archivos_validos else []
    )
    if archivos_validos and ruta and ruta not in {
        normalizada for _, normalizada in archivos_a_comprobar
    }:
        archivos_a_comprobar.append((ruta, ruta))
    archivos_fuera = [
        original
        for original, normalizada in archivos_a_comprobar
        if not _ruta_permitida(normalizada, bateria)
    ] if archivos_validos else []

    desviaciones, desviaciones_validas = _desviaciones_validas(
        datos.get("desviaciones")
    )
    desviacion_sin_justificar = any(
        not desviacion["justificacion"].strip() for desviacion in desviaciones
    )
    evidencia_obligatoria_valida = (
        ruta is not None
        and bateria is not None
        and spec_id is not None
        and caracterizacion_estado is not None
        and equivalencia_estado is not None
        and archivos_validos
        and desviaciones_validas
    )

    if caracterizacion_estado == "failed":
        decision = "caracterizacion_rota"
        hipotesis = "La bateria de caracterizacion contiene fallos; el comportamiento legado no se ha preservado."
    elif equivalencia_estado == "failed":
        decision = "equivalencia_rota"
        hipotesis = "La comprobacion de equivalencia ha fallado; el refactor no conserva el comportamiento observado."
    elif archivos_fuera:
        decision = "fuera_de_alcance"
        hipotesis = "El cambio incluye archivos fuera del modulo legado y de la bateria de caracterizacion permitidos."
    elif desviacion_sin_justificar:
        decision = "desviacion_no_justificada"
        hipotesis = "Hay al menos una desviacion sin justificacion explicita."
    elif (
        not evidencia_obligatoria_valida
        or caracterizacion_verde is not True
        or equivalencia_verde is not True
    ):
        decision = "evidencia_insuficiente"
        hipotesis = "Falta evidencia valida para confirmar caracterizacion, equivalencia, alcance o especificacion."
    else:
        decision = "aprobable"
        hipotesis = "La caracterizacion y la equivalencia pasan, el cambio esta en alcance y sus desviaciones estan justificadas."

    return {
        "ruta": ruta,
        "decision": decision,
        "hipotesis": hipotesis,
        "spec_id": spec_id,
        "caracterizacion_verde": caracterizacion_verde,
        "equivalencia_verde": equivalencia_verde,
        "desviaciones": desviaciones,
        "archivos_fuera_de_permitidos": archivos_fuera,
        "handoff": (
            {"a": "conformidad", "spec_id": spec_id}
            if decision == "aprobable" else None
        ),
    }


def principal(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Agente de modernizacion")
    parser.add_argument("--entrada", required=True, help="Archivo JSON de evidencia")
    args = parser.parse_args(argv)
    entrada = json.loads(Path(args.entrada).read_text(encoding="utf-8"))
    print(json.dumps(analizar(entrada), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
