"""S1: implementar las reglas de matricula descritas en SPEC-001."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from ..auditoria import registrar_decision
from ..dominio.modelos import (EstadoMatricula, Expediente, LineaMatricula,
                               Matricula, Plan, SolicitudMatricula)


class VentanaCerrada(Exception):
    pass


@dataclass(frozen=True)
class VentanaMatricula:
    inicio: str
    fin: str

    def __post_init__(self):
        inicio = _fecha(self.inicio)
        fin = _fecha(self.fin)
        if inicio > fin:
            raise ValueError("el inicio de la ventana debe ser anterior o igual al fin")

    def contiene(self, momento: str) -> bool:
        instante = _fecha(momento)
        return _fecha(self.inicio) <= instante <= _fecha(self.fin)


@dataclass(frozen=True)
class Grupo:
    codigo_asignatura: str
    capacidad: int
    ocupadas: int

    @property
    def libre(self) -> bool:
        return self.ocupadas < self.capacidad


def _fecha(valor: str) -> datetime:
    if not isinstance(valor, str):
        raise ValueError("la fecha debe ser una cadena ISO-8601")
    try:
        fecha = datetime.fromisoformat(valor.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("fecha ISO-8601 no valida: %s" % valor) from error
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=timezone.utc)
    return fecha.astimezone(timezone.utc)


def creditos_superados(expediente: Expediente, plan: Plan) -> int:
    codigos_superados = {
        registro.codigo_asignatura for registro in expediente.registros
        if expediente.superada(registro.codigo_asignatura)
        and registro.codigo_asignatura in plan.asignaturas
    }
    return sum(plan.asignatura(codigo).creditos for codigo in codigos_superados)


def creditos_pendientes(expediente: Expediente, plan: Plan) -> int:
    return max(0, plan.creditos_titulo - creditos_superados(expediente, plan))


def prioridad(expediente: Expediente, plan: Plan) -> int:
    return creditos_superados(expediente, plan)


def evaluar_solicitud(solicitud: SolicitudMatricula, expediente: Expediente,
                      plan: Plan, ventana: VentanaMatricula,
                      grupos: dict) -> Matricula:
    if not solicitud.codigos:
        raise ValueError("la solicitud debe incluir al menos un codigo")
    if len(solicitud.codigos) != len(set(solicitud.codigos)):
        raise ValueError("la solicitud no puede repetir codigos")
    desconocidos = [codigo for codigo in solicitud.codigos
                    if codigo not in plan.asignaturas]
    if desconocidos:
        raise ValueError("asignaturas fuera del plan: %s" % ", ".join(desconocidos))

    if not ventana.contiene(solicitud.momento):
        registrar_decision(
            solicitud.estudiante_id, solicitud.curso_academico, plan.codigo,
            plan.version, solicitud.momento,
            {"estado": "rechazada", "motivo": "ventana de matricula cerrada"},
        )
        raise VentanaCerrada("ventana de matricula cerrada")

    limite = plan.limite_creditos_curso
    pendientes = creditos_pendientes(expediente, plan)
    if pendientes <= plan.umbral_final_carrera:
        limite = pendientes

    lineas = []
    creditos_admitidos = 0
    for codigo in solicitud.codigos:
        asignatura = plan.asignatura(codigo)
        pendientes_prerrequisitos = [
            requisito for requisito in asignatura.prerrequisitos
            if not expediente.superada(requisito)
        ]
        if expediente.superada(codigo):
            linea = LineaMatricula(
                codigo, asignatura.creditos, False,
                motivo_rechazo="asignatura ya superada",
            )
        elif pendientes_prerrequisitos:
            linea = LineaMatricula(
                codigo, asignatura.creditos, False,
                motivo_rechazo="prerrequisitos pendientes: %s"
                % ", ".join(pendientes_prerrequisitos),
            )
        elif expediente.convocatorias_consumidas(codigo) >= plan.max_convocatorias:
            linea = LineaMatricula(
                codigo, asignatura.creditos, False,
                motivo_rechazo="convocatorias agotadas",
            )
        elif codigo in grupos and not grupos[codigo].libre:
            linea = LineaMatricula(
                codigo, asignatura.creditos, False, en_espera=True,
                motivo_espera="grupo completo",
            )
        elif creditos_admitidos + asignatura.creditos > limite:
            linea = LineaMatricula(
                codigo, asignatura.creditos, False,
                motivo_rechazo="limite de creditos del curso superado",
            )
        else:
            linea = LineaMatricula(codigo, asignatura.creditos, True)
            creditos_admitidos += asignatura.creditos
        lineas.append(linea)

    matricula = Matricula(
        estudiante_id=solicitud.estudiante_id,
        curso_academico=solicitud.curso_academico,
        plan_aplicado=plan.codigo,
        version_plan_aplicada=plan.version,
        estado=EstadoMatricula.VALIDADA,
        lineas=lineas,
    )
    registrar_decision(
        solicitud.estudiante_id, solicitud.curso_academico, plan.codigo,
        plan.version, solicitud.momento,
        {
            "estado": matricula.estado.value,
            "lineas": [
                {
                    "codigo_asignatura": linea.codigo_asignatura,
                    "creditos": linea.creditos,
                    "admitida": linea.admitida,
                    "en_espera": linea.en_espera,
                    "motivo_rechazo": linea.motivo_rechazo,
                    "motivo_espera": linea.motivo_espera,
                }
                for linea in matricula.lineas
            ],
        },
    )
    return matricula


def ordenar_por_prioridad(solicitudes: list, expedientes: dict, plan: Plan) -> list:
    return sorted(
        solicitudes,
        key=lambda solicitud: (
            -prioridad(expedientes[solicitud.estudiante_id], plan),
            _fecha(solicitud.momento),
        ),
    )