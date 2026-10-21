from decimal import Decimal

from aula.dominio.modelos import (
    Asignatura,
    EstadoRegistro,
    Expediente,
    Plan,
    RegistroAcademico,
)
from aula.reglas.media import (
    creditos_superados,
    nota_media_ponderada,
    progreso,
)


def crear_plan(asignaturas, creditos_titulo=30):
    entidades = {
        codigo: Asignatura(codigo, codigo, creditos, 1)
        for codigo, creditos in asignaturas.items()
    }
    return Plan(
        codigo="PLAN-TEST",
        version="1",
        creditos_titulo=creditos_titulo,
        limite_creditos_curso=60,
        max_convocatorias=6,
        umbral_final_carrera=30,
        asignaturas=entidades,
    )


def test_ca01_media_ponderada_de_asignaturas_aprobadas():
    """cubre: SPEC-002/CA-01"""
    plan = crear_plan({"MAT-01": 3, "HIS-01": 1})
    expediente = Expediente(
        estudiante_id="estudiante-1",
        plan="PLAN-TEST",
        registros=[
            RegistroAcademico(
                "MAT-01", "2024-2025", 1, EstadoRegistro.APROBADA, Decimal("8")
            ),
            RegistroAcademico(
                "HIS-01", "2024-2025", 1, EstadoRegistro.APROBADA, Decimal("5")
            ),
        ],
    )

    assert nota_media_ponderada(expediente, plan) == Decimal("7.25")


def test_ca02_asignatura_repetida_utiliza_ultimo_aprobado():
    """cubre: SPEC-002/CA-02"""
    plan = crear_plan({"MAT-01": 3, "HIS-01": 1})
    expediente = Expediente(
        estudiante_id="estudiante-2",
        plan="PLAN-TEST",
        registros=[
            RegistroAcademico(
                "MAT-01", "2022-2023", 1, EstadoRegistro.APROBADA, Decimal("9")
            ),
            RegistroAcademico(
                "MAT-01", "2022-2023", 2, EstadoRegistro.SUSPENSA, Decimal("4")
            ),
            RegistroAcademico(
                "MAT-01", "2023-2024", 1, EstadoRegistro.APROBADA, Decimal("7")
            ),
            RegistroAcademico(
                "MAT-01", "2023-2024", 2, EstadoRegistro.NO_PRESENTADO
            ),
            RegistroAcademico(
                "HIS-01", "2023-2024", 1, EstadoRegistro.APROBADA, Decimal("5")
            ),
        ],
    )

    assert nota_media_ponderada(expediente, plan) == Decimal("6.50")


def test_ca03_convalidada_segun_tenga_o_no_calificacion():
    """cubre: SPEC-002/CA-03"""
    plan = crear_plan(
        {"MAT-01": 2, "HIS-01": 2, "IDI-01": 3}
    )
    con_calificacion = Expediente(
        estudiante_id="estudiante-3",
        plan="PLAN-TEST",
        registros=[
            RegistroAcademico(
                "MAT-01", "2024-2025", 1, EstadoRegistro.APROBADA, Decimal("4")
            ),
            RegistroAcademico(
                "HIS-01", "2024-2025", 0, EstadoRegistro.CONVALIDADA, Decimal("10")
            ),
            RegistroAcademico(
                "IDI-01", "2024-2025", 0, EstadoRegistro.CONVALIDADA
            ),
        ],
    )
    sin_calificacion = Expediente(
        estudiante_id="estudiante-4",
        plan="PLAN-TEST",
        registros=[
            RegistroAcademico(
                "MAT-01", "2024-2025", 1, EstadoRegistro.APROBADA, Decimal("4")
            ),
            RegistroAcademico(
                "IDI-01", "2024-2025", 0, EstadoRegistro.CONVALIDADA
            ),
        ],
    )

    assert nota_media_ponderada(con_calificacion, plan) == Decimal("7.00")
    assert nota_media_ponderada(sin_calificacion, plan) == Decimal("4.00")


def test_ca04_redondeo_se_aplica_solo_al_cociente_final():
    """cubre: SPEC-002/CA-04; cubre: SPEC-002/INV-01"""
    plan = crear_plan({"MAT-01": 1, "HIS-01": 1})
    expediente = Expediente(
        estudiante_id="estudiante-5",
        plan="PLAN-TEST",
        registros=[
            RegistroAcademico(
                "MAT-01", "2024-2025", 1, EstadoRegistro.APROBADA, Decimal("6")
            ),
            RegistroAcademico(
                "HIS-01",
                "2024-2025",
                1,
                EstadoRegistro.APROBADA,
                Decimal("6.005"),
            ),
        ],
    )

    assert nota_media_ponderada(expediente, plan) == Decimal("6.00")


def test_ca05_convalidada_cuenta_como_creditos_superados():
    """cubre: SPEC-002/CA-05"""
    plan = crear_plan({"MAT-01": 4, "HIS-01": 3})
    expediente = Expediente(
        estudiante_id="estudiante-6",
        plan="PLAN-TEST",
        registros=[
            RegistroAcademico(
                "MAT-01", "2024-2025", 0, EstadoRegistro.CONVALIDADA
            ),
            RegistroAcademico(
                "HIS-01", "2024-2025", 1, EstadoRegistro.SUSPENSA, Decimal("3")
            ),
        ],
    )

    assert creditos_superados(expediente, plan) == 4


def test_ca06_progreso_es_porcentaje_de_creditos_superados():
    """cubre: SPEC-002/CA-06"""
    plan = crear_plan(
        {"MAT-01": 3, "HIS-01": 3, "IDI-01": 2},
        creditos_titulo=25,
    )
    expediente = Expediente(
        estudiante_id="estudiante-7",
        plan="PLAN-TEST",
        registros=[
            RegistroAcademico(
                "MAT-01", "2024-2025", 1, EstadoRegistro.APROBADA, Decimal("8")
            ),
            RegistroAcademico(
                "HIS-01", "2024-2025", 0, EstadoRegistro.CONVALIDADA
            ),
            RegistroAcademico(
                "IDI-01", "2024-2025", 1, EstadoRegistro.SUSPENSA, Decimal("4")
            ),
        ],
    )

    assert progreso(expediente, plan) == Decimal("24.00")


def test_ca07_sin_asignaturas_computables_media_es_cero():
    """cubre: SPEC-002/CA-07"""
    plan = crear_plan({"MAT-01": 3}, creditos_titulo=25)
    expediente = Expediente(
        estudiante_id="estudiante-8",
        plan="PLAN-TEST",
        registros=[],
    )

    assert nota_media_ponderada(expediente, plan) == Decimal("0.00")


def test_calculo_utiliza_decimal():
    """cubre: SPEC-002/INV-02"""
    plan = crear_plan({"MAT-01": 3})
    expediente = Expediente(
        estudiante_id="estudiante-9",
        plan="PLAN-TEST",
        registros=[
            RegistroAcademico(
                "MAT-01",
                "2024-2025",
                1,
                EstadoRegistro.APROBADA,
                Decimal("7.005"),
            ),
        ],
    )

    media = nota_media_ponderada(expediente, plan)

    assert isinstance(media, Decimal)
    assert media == Decimal("7.01")


def test_media_no_depende_del_orden_de_los_registros():
    """cubre: SPEC-002/INV-03"""
    plan = crear_plan({"MAT-01": 3, "HIS-01": 2, "IDI-01": 1})
    registros = [
        RegistroAcademico(
            "MAT-01", "2024-2025", 1, EstadoRegistro.APROBADA, Decimal("8.10")
        ),
        RegistroAcademico(
            "HIS-01", "2024-2025", 1, EstadoRegistro.APROBADA, Decimal("6.30")
        ),
        RegistroAcademico(
            "IDI-01", "2024-2025", 1, EstadoRegistro.APROBADA, Decimal("9.00")
        ),
    ]
    expediente = Expediente("estudiante-10", "PLAN-TEST", registros)
    expediente_invertido = Expediente(
        "estudiante-10", "PLAN-TEST", list(reversed(registros))
    )

    assert nota_media_ponderada(expediente, plan) == Decimal("7.65")
    assert nota_media_ponderada(expediente_invertido, plan) == Decimal("7.65")