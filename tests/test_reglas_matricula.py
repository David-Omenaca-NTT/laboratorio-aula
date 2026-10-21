from dataclasses import replace

import pytest

from aula import auditoria
from aula.dominio.estados import PlanInmutable, transicionar
from aula.dominio.modelos import EstadoMatricula, Matricula
from aula.reglas.motor import (Grupo, VentanaCerrada, VentanaMatricula,
                               creditos_superados, evaluar_solicitud,
                               ordenar_por_prioridad)
from utilidades import expediente, plan, registro, solicitud


@pytest.fixture(autouse=True)
def traza(monkeypatch, tmp_path):
    monkeypatch.setattr(auditoria, "RUTA_TRAZA", tmp_path / "auditoria.jsonl")


def ventana():
    return VentanaMatricula("2026-09-01T00:00:00Z", "2026-09-30T23:59:59Z")


def matricula(estado=EstadoMatricula.SOLICITADA):
    return Matricula(
        estudiante_id="EST-0001",
        curso_academico="2026-2027",
        plan_aplicado="PLAN-2024",
        version_plan_aplicada="1",
        estado=estado,
    )


def test_ventana_inclusiva_y_rechazo_auditado():
    """cubre: SPEC-001/CA-01; los límites son inclusivos y fuera se rechaza."""
    p, v = plan(), ventana()
    assert v.contiene(v.inicio) and v.contiene(v.fin)
    with pytest.raises(VentanaCerrada):
        evaluar_solicitud(solicitud(["MAT101"], momento="2026-08-31T23:59:59Z"),
                          expediente(), p, v, {})
    assert len(auditoria.leer_traza()) == 1


def test_prerrequisito_y_asignatura_superada():
    """cubre: SPEC-001/CA-02; cubre: SPEC-001/CA-08."""
    p, v, e = plan(), ventana(), expediente()
    m = evaluar_solicitud(solicitud(["PRG102", "MAT101"]), e, p, v, {})
    assert "PRG101" in m.lineas[0].motivo_rechazo and m.lineas[1].admitida
    m = evaluar_solicitud(solicitud(["MAT101"]), expediente(registro("MAT101", "aprobada")),
                          p, v, {})
    assert m.lineas[0].motivo_rechazo == "asignatura ya superada"


def test_cada_codigo_solicitado_produce_una_linea_incluso_repetidos():
    """cubre: SPEC-001/INV-02"""
    codigos = ["MAT101", "PRG101", "MAT101"]
    m = evaluar_solicitud(
        solicitud(codigos), expediente(), plan(), ventana(), {},
    )

    assert len(m.lineas) == len(codigos)
    assert [linea.codigo_asignatura for linea in m.lineas] == codigos


def test_inv03_permite_cambiar_plan_y_version_antes_de_confirmar():
    """cubre: SPEC-001/INV-03"""
    m = matricula()

    m.plan_aplicado = "PLAN-2025"
    m.version_plan_aplicada = "2"

    assert (m.plan_aplicado, m.version_plan_aplicada) == ("PLAN-2025", "2")


def test_inv03_transicion_rechaza_cambio_de_plan_tras_confirmar():
    """cubre: SPEC-001/INV-03"""
    m = matricula()
    transicionar(m, EstadoMatricula.VALIDADA)
    transicionar(m, EstadoMatricula.CONFIRMADA)

    with pytest.raises(PlanInmutable):
        transicionar(m, EstadoMatricula.EN_CURSO, nuevo_plan="PLAN-2025")

    assert (m.plan_aplicado, m.version_plan_aplicada) == ("PLAN-2024", "1")


def test_inv03_asignacion_directa_no_cambia_plan_ni_version_confirmados():
    """cubre: SPEC-001/INV-03"""
    m = matricula()
    transicionar(m, EstadoMatricula.VALIDADA)
    transicionar(m, EstadoMatricula.CONFIRMADA)

    with pytest.raises(PlanInmutable):
        m.plan_aplicado = "PLAN-2025"
    with pytest.raises(PlanInmutable):
        m.version_plan_aplicada = "2"

    assert (m.plan_aplicado, m.version_plan_aplicada) == ("PLAN-2024", "1")


def test_inv03_anular_no_desbloquea_plan_confirmado():
    """cubre: SPEC-001/INV-03"""
    m = matricula()
    transicionar(m, EstadoMatricula.VALIDADA)
    transicionar(m, EstadoMatricula.CONFIRMADA)
    transicionar(m, EstadoMatricula.ANULADA)

    with pytest.raises(PlanInmutable):
        m.plan_aplicado = "PLAN-2025"
    with pytest.raises(PlanInmutable):
        m.version_plan_aplicada = "2"

    assert (m.plan_aplicado, m.version_plan_aplicada) == ("PLAN-2024", "1")


@pytest.mark.parametrize(
    "estado",
    [
        EstadoMatricula.CONFIRMADA,
        EstadoMatricula.EN_CURSO,
        EstadoMatricula.CALIFICADA,
        EstadoMatricula.CERRADA,
    ],
)
def test_inv03_protege_matricula_creada_en_estado_confirmado_o_posterior(estado):
    """cubre: SPEC-001/INV-03"""
    m = matricula(estado)

    with pytest.raises(PlanInmutable):
        m.plan_aplicado = "PLAN-2025"
    with pytest.raises(PlanInmutable):
        m.version_plan_aplicada = "2"

    assert (m.plan_aplicado, m.version_plan_aplicada) == ("PLAN-2024", "1")


def test_inv03_no_se_puede_desactivar_la_confirmacion_previa():
    """cubre: SPEC-001/INV-03"""
    m = matricula()
    transicionar(m, EstadoMatricula.VALIDADA)
    transicionar(m, EstadoMatricula.CONFIRMADA)

    assert m.confirmada_alguna_vez is True
    with pytest.raises(PlanInmutable):
        m.confirmada_alguna_vez = False
    assert m.confirmada_alguna_vez is True


def test_limites_creditos_y_grupo_completo():
    """cubre: SPEC-001/CA-03; cubre: SPEC-001/CA-05."""
    p, v = plan(), ventana()
    m = evaluar_solicitud(
        solicitud(["MAT101", "PRG101", "FIS101", "ALG101"]), expediente(),
        replace(p, limite_creditos_curso=15), v,
        {"MAT101": Grupo("MAT101", 1, 1)},
    )
    assert [l.en_espera or l.admitida for l in m.lineas] == [True, True, True, False]
    assert m.lineas[0].motivo_espera == "grupo completo"
    assert m.creditos_admitidos == 15
    final = replace(p, creditos_titulo=21, limite_creditos_curso=6)
    m = evaluar_solicitud(solicitud(["PRG101"]),
                          expediente(registro("MAT101", "aprobada"),
                                     registro("FIS101", "aprobada")),
                          final, v, {})
    assert m.lineas[0].admitida and m.creditos_admitidos == 9


def test_convocatorias_y_creditos_convalidados():
    """cubre: SPEC-001/CA-04; cubre: SPEC-001/CA-06."""
    p, v = plan(), ventana()
    e = expediente(*[registro("MAT101", "suspensa", convocatoria=n)
                     for n in range(1, p.max_convocatorias + 1)])
    m = evaluar_solicitud(solicitud(["MAT101"]), e, p, v, {})
    assert m.lineas[0].motivo_rechazo == "convocatorias agotadas"
    convalidado = expediente(registro("MAT101", "convalidada"))
    assert creditos_superados(convalidado, p) == 6
    assert convalidado.convocatorias_consumidas("MAT101") == 0


def test_prioridad_por_creditos_y_momento():
    """cubre: SPEC-001/CA-07; ordena por créditos y luego por fecha."""
    peticiones = [solicitud(["MAT101"], fecha, estudiante) for estudiante, fecha in (
        ("EST002", "2026-09-10T10:00:00"), ("EST003", "2026-09-10T08:00:00"),
        ("EST001", "2026-09-10T07:00:00"),
    )]
    expedientes = {
        "EST001": expediente(registro("PRG101", "aprobada"), estudiante="EST001"),
        "EST002": expediente(registro("MAT101", "aprobada"), estudiante="EST002"),
        "EST003": expediente(registro("MAT101", "aprobada"), estudiante="EST003"),
    }
    assert [s.estudiante_id for s in ordenar_por_prioridad(
        peticiones, expedientes, plan(),
    )] == ["EST001", "EST003", "EST002"]
