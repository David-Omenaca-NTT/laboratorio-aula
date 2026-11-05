import json

from aula.legado import calculadora_expediente_v1 as legado


def crear_plan(tmp_path, creditos, creditos_titulo=30):
    ruta = tmp_path / "plan.json"
    ruta.write_text(
        json.dumps(
            {
                "creditos_titulo": creditos_titulo,
                "asignaturas": [
                    {"codigo": codigo, "creditos": cantidad}
                    for codigo, cantidad in creditos.items()
                ],
            }
        ),
        encoding="utf-8",
    )
    return legado.cargar_plan(str(ruta))


def registro(codigo, estado, convocatoria=1, nota=None):
    return {
        "codigo_asignatura": codigo,
        "estado": estado,
        "convocatoria": convocatoria,
        "nota": nota,
    }


def expediente(registros):
    return {"estudiante_id": "estudiante-test", "registros": registros}


def test_expediente_vacio_devuelve_media_creditos_y_progreso_cero(tmp_path):
    plan, mapa = crear_plan(tmp_path, {"MAT-01": 3})
    vacio = expediente([])

    assert legado.media(vacio, mapa) == 0.0
    assert legado.creditos_superados(vacio, mapa) == 0
    assert legado.progreso(vacio, plan, mapa) == 0.0


def test_media_usa_la_ultima_convocatoria_aprobada(tmp_path):
    _, mapa = crear_plan(tmp_path, {"MAT-01": 3})
    caso = expediente(
        [
            registro("MAT-01", "aprobada", convocatoria=2, nota=7.0),
            registro("MAT-01", "aprobada", convocatoria=4, nota=8.5),
            registro("MAT-01", "suspensa", convocatoria=5, nota=3.0),
        ]
    )

    assert legado.media(caso, mapa) == 8.5


def test_creditos_superados_no_duplica_una_asignatura(tmp_path):
    _, mapa = crear_plan(tmp_path, {"MAT-01": 6})
    caso = expediente(
        [
            registro("MAT-01", "aprobada", convocatoria=2, nota=6.0),
            registro("MAT-01", "aprobada", convocatoria=4, nota=8.0),
        ]
    )

    assert legado.creditos_superados(caso, mapa) == 6


def test_convalidacion_cuenta_como_creditos_superados(tmp_path):
    _, mapa = crear_plan(tmp_path, {"HIS-01": 4})
    caso = expediente([registro("HIS-01", "convalidada", convocatoria=0)])

    assert legado.creditos_superados(caso, mapa) == 4


def test_progreso_es_porcentaje_de_creditos_superados(tmp_path):
    plan, mapa = crear_plan(
        tmp_path,
        {"MAT-01": 4, "HIS-01": 3, "BIO-01": 2},
        creditos_titulo=30,
    )
    caso = expediente(
        [
            registro("MAT-01", "aprobada", nota=8.0),
            registro("HIS-01", "convalidada", convocatoria=0),
            registro("BIO-01", "suspensa", nota=4.0),
        ]
    )

    assert legado.progreso(caso, plan, mapa) == 23.33


def test_puede_matricular_limita_a_seis_convocatorias():
    cinco_convocatorias = expediente(
        [
            registro("MAT-01", "suspensa", convocatoria=convocatoria)
            for convocatoria in range(1, 6)
        ]
    )
    seis_convocatorias = expediente(
        [
            registro("MAT-01", "suspensa", convocatoria=convocatoria)
            for convocatoria in range(1, 7)
        ]
    )

    assert legado.puede_matricular(cinco_convocatorias, "MAT-01") is True
    assert legado.puede_matricular(seis_convocatorias, "MAT-01") is False


def test_calcular_conserva_el_punto_de_entrada_historico(tmp_path):
    crear_plan(tmp_path, {"MAT-01": 3})
    caso = expediente([registro("MAT-01", "aprobada", nota=8.0)])

    resultado = legado.calcular(caso, str(tmp_path / "plan.json"))

    assert resultado == {
        "estudiante_id": "estudiante-test",
        "nota_media": 8.0,
        "creditos_superados": 3,
        "progreso_pct": 10.0,
    }


def test_no_documentado_1_convalidacion_suma_al_numerador_no_al_denominador(
    tmp_path,
):
    _, mapa = crear_plan(tmp_path, {"MAT-01": 2, "HIS-01": 4})
    caso = expediente(
        [
            registro("MAT-01", "aprobada", nota=7.0),
            registro("HIS-01", "convalidada", convocatoria=0),
        ]
    )

    assert legado.media(caso, mapa) == 17.0


def test_no_documentado_2_redondea_cada_nota_antes_de_acumular(tmp_path):
    _, mapa = crear_plan(tmp_path, {"MAT-01": 1, "HIS-01": 1})
    caso = expediente(
        [
            registro("MAT-01", "aprobada", nota=6.0),
            registro("HIS-01", "aprobada", nota=6.014),
        ]
    )

    assert legado.media(caso, mapa) == 6.0
