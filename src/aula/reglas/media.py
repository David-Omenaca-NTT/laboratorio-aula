"""S2: resolver SPEC-002 antes de implementar el calculo del expediente."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from ..dominio.modelos import EstadoRegistro, Expediente, Plan


def nota_media_ponderada(expediente: Expediente, plan: Plan) -> Decimal:
    suma_ponderada = Decimal("0")
    creditos_computados = 0

    codigos = sorted({registro.codigo_asignatura for registro in expediente.registros})
    for codigo in codigos:
        registro = expediente.ultimo_intento_aprobado(codigo)
        if registro is None:
            registro = next(
                (
                    registro
                    for registro in expediente.registros_de(codigo)
                    if registro.estado is EstadoRegistro.CONVALIDADA
                    and registro.nota is not None
                ),
                None,
            )
        if registro is not None:
            creditos = plan.asignatura(codigo).creditos
            suma_ponderada += registro.nota * creditos
            creditos_computados += creditos

    if creditos_computados == 0:
        return Decimal("0.00")

    return (suma_ponderada / creditos_computados).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def creditos_superados(expediente: Expediente, plan: Plan) -> int:
    codigos_superados = {
        registro.codigo_asignatura
        for registro in expediente.registros
        if expediente.superada(registro.codigo_asignatura)
    }
    return sum(plan.asignatura(codigo).creditos for codigo in codigos_superados)


def progreso(expediente: Expediente, plan: Plan) -> Decimal:
    porcentaje = (
        Decimal(creditos_superados(expediente, plan))
        / Decimal(plan.creditos_titulo)
        * Decimal("100")
    )
    return porcentaje.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def convocatorias_por_asignatura(expediente: Expediente, plan: Plan) -> dict:
    raise NotImplementedError("S2: resumir convocatorias")


def resumen_expediente(expediente: Expediente, plan: Plan) -> dict:
    raise NotImplementedError("S2: construir respuesta de expediente")


def es_convalidada(registro) -> bool:
    raise NotImplementedError("S2: identificar registros convalidados")