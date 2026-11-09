import pytest

from agentes.modernizacion.agente import analizar


RUTA = "src/aula/legado/calculadora_expediente_v1.py"
BATERIA = "tests/test_caracterizacion_legado.py"


def caso_base(**cambios):
    caso = {
        "ruta": RUTA,
        "bateria": BATERIA,
        "spec_id": "SPEC-002",
        "resultado_caracterizacion": {"status": "passed"},
        "resultado_equivalencia": {"status": "passed"},
        "archivos_modificados": [RUTA],
        "desviaciones": [],
    }
    caso.update(cambios)
    return caso


@pytest.mark.parametrize(
    ("cambios", "esperada"),
    [
        ({"resultado_caracterizacion": {"status": "failed"}}, "caracterizacion_rota"),
        ({"resultado_equivalencia": {"status": "failed"}}, "equivalencia_rota"),
        ({"archivos_modificados": [RUTA, "README.md"]}, "fuera_de_alcance"),
        ({"desviaciones": [{"descripcion": "x", "justificacion": ""}]},
         "desviacion_no_justificada"),
        ({"resultado_equivalencia": {"status": "unknown"}}, "evidencia_insuficiente"),
    ],
)
def test_decisiones_segun_precedencia(cambios, esperada):
    assert analizar(caso_base(**cambios))["decision"] == esperada


def test_handoff_solo_para_aprobable_y_spec_explicita():
    resultado = analizar(caso_base())

    assert resultado["decision"] == "aprobable"
    assert resultado["handoff"] == {"a": "conformidad", "spec_id": "SPEC-002"}


def test_una_desviacion_justificada_no_bloquea_aprobacion():
    resultado = analizar(caso_base(
        desviaciones=[{"descripcion": "Se conserva CSV", "justificacion": "Compatibilidad"}]
    ))

    assert resultado["decision"] == "aprobable"


def test_campos_de_raiz_prevalecen_sobre_contexto():
    entrada = {
        "contexto": caso_base(resultado_caracterizacion={"status": "failed"}),
        "resultado_caracterizacion": {"status": "passed"},
    }

    assert analizar(entrada)["decision"] == "aprobable"


def test_contexto_anidado_y_estados_de_evidencia_desconocidos():
    resultado = analizar({"contexto": caso_base(resultado_caracterizacion={"status": "unknown"})})

    assert resultado["decision"] == "evidencia_insuficiente"
    assert resultado["caracterizacion_verde"] is None
    assert resultado["handoff"] is None


def test_normaliza_separadores_y_rechaza_traversal():
    resultado = analizar(caso_base(
        archivos_modificados=[RUTA.replace("/", "\\") + "\\..\\..\\README.md"]
    ))

    assert resultado["decision"] == "fuera_de_alcance"
    assert resultado["archivos_fuera_de_permitidos"]


def test_entrada_no_objeto_es_evidencia_insuficiente():
    assert analizar("no es un objeto")["decision"] == "evidencia_insuficiente"
