"""S1: completar las transiciones y proteger el plan confirmado."""
from __future__ import annotations

from .modelos import EstadoMatricula, Matricula, PlanInmutable

TRANSICIONES: dict[EstadoMatricula, set[EstadoMatricula]] = {
    EstadoMatricula.SOLICITADA: {EstadoMatricula.VALIDADA},
    EstadoMatricula.VALIDADA: {EstadoMatricula.CONFIRMADA},
    EstadoMatricula.CONFIRMADA: {
        EstadoMatricula.EN_CURSO,
        EstadoMatricula.ANULADA,
    },
}


class TransicionInvalida(Exception):
    pass


def transiciones_validas(estado: EstadoMatricula) -> set:
    return TRANSICIONES.get(estado, set()).copy()


def transicionar(matricula: Matricula, destino: EstadoMatricula,
                 nuevo_plan: str = None,
                 nueva_version: str = None) -> Matricula:
    if destino not in transiciones_validas(matricula.estado):
        raise TransicionInvalida(
            "transicion no permitida: %s -> %s"
            % (matricula.estado.value, destino.value)
        )

    if matricula.confirmada_alguna_vez:
        if (nuevo_plan is not None and nuevo_plan != matricula.plan_aplicado) or (
            nueva_version is not None
            and nueva_version != matricula.version_plan_aplicada
        ):
            raise PlanInmutable(
                "el plan y su version no pueden cambiar tras confirmar la matricula"
            )
    else:
        if nuevo_plan is not None:
            matricula.plan_aplicado = nuevo_plan
        if nueva_version is not None:
            matricula.version_plan_aplicada = nueva_version

    matricula.estado = destino
    return matricula