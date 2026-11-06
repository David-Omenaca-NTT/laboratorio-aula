import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from aula.dominio.modelos import EstadoRegistro, Expediente, RegistroAcademico
from aula.legado import calculadora_expediente_v1 as legado
from aula.reglas.media import creditos_superados, nota_media_ponderada, progreso
from aula.reglas.planes import cargar_plan
from herramientas.generar_corpus import generar


RAIZ = Path(__file__).resolve().parents[1]
RUTA_PLAN = RAIZ / "datos" / "planes" / "PLAN-2024.json"
RUTA_CORPUS = RAIZ / "datos" / "expedientes_sinteticos.json"
HUELLA_REFERENCIA = (
    "c637d871a0f7057f1f87004cb3de7c5484e1c9a05f9e8997b08fada91023a36d"
)


def cargar_corpus():
    return json.loads(RUTA_CORPUS.read_text(encoding="utf-8"))


def adaptar_expediente(datos):
    return Expediente(
        estudiante_id=datos["estudiante_id"],
        plan=datos["plan"],
        registros=[
            RegistroAcademico(
                codigo_asignatura=registro["codigo_asignatura"],
                curso_academico=registro["curso_academico"],
                convocatoria=registro["convocatoria"],
                estado=EstadoRegistro(registro["estado"]),
                nota=(
                    Decimal(str(registro["nota"]))
                    if registro["nota"] is not None
                    else None
                ),
            )
            for registro in datos["registros"]
        ],
    )


def _redondear_legado(nota):
    return round(float(nota), 2)


def _media(expediente, plan, convalidaciones_legado=False, redondear=False):
    numerador = 0.0
    denominador = 0
    codigos = list(dict.fromkeys(r.codigo_asignatura for r in expediente.registros))
    for codigo in codigos:
        registros = expediente.registros_de(codigo)
        convalidada = any(r.estado is EstadoRegistro.CONVALIDADA for r in registros)
        if convalidada and convalidaciones_legado:
            numerador += 5.0 * plan.asignatura(codigo).creditos
            continue
        registro = expediente.ultimo_intento_aprobado(codigo)
        if registro is None and not convalidaciones_legado:
            registro = next(
                (r for r in registros
                 if r.estado is EstadoRegistro.CONVALIDADA and r.nota is not None),
                None,
            )
        if registro is None or registro.nota is None:
            continue
        nota = float(registro.nota)
        if redondear:
            nota = _redondear_legado(nota)
        numerador += nota * plan.asignatura(codigo).creditos
        denominador += plan.asignatura(codigo).creditos
    if denominador == 0:
        return 0.0
    resultado = numerador / denominador
    if convalidaciones_legado or redondear:
        return round(resultado, 2)
    return Decimal(str(resultado)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _progreso_legado(expediente, plan):
    return round(
        (creditos_superados(expediente, plan) * 100.0) / plan.creditos_titulo,
        2,
    )


def resultado_moderno(expediente, plan):
    return {
        "estudiante_id": expediente.estudiante_id,
        "nota_media": nota_media_ponderada(expediente, plan),
        "creditos_superados": creditos_superados(expediente, plan),
        "progreso_pct": progreso(expediente, plan),
    }


def clasificar_diferencia(resultado_legado, resultado_moderno, expediente, plan):
    resultado_legado_normalizado = {
        **resultado_legado,
        "nota_media": Decimal(str(resultado_legado["nota_media"])),
        "progreso_pct": Decimal(str(resultado_legado["progreso_pct"])),
    }
    variantes = {
        "D-01": _media(expediente, plan, convalidaciones_legado=True),
        "D-02": _media(expediente, plan, redondear=True),
        "D-01 + D-02": _media(
            expediente, plan, convalidaciones_legado=True, redondear=True
        ),
    }
    causas = []
    if resultado_legado["creditos_superados"] != resultado_moderno["creditos_superados"]:
        causas.append("no justificada: creditos_superados")
    if resultado_legado_normalizado["nota_media"] != resultado_moderno["nota_media"]:
        objetivo = resultado_legado_normalizado["nota_media"]
        causa_media = next(
            (causa for causa in ("D-01", "D-02", "D-01 + D-02")
             if Decimal(str(variantes[causa])) == objetivo),
            None,
        )
        causas.append(causa_media or "no justificada: nota_media")
    if resultado_legado_normalizado["progreso_pct"] != resultado_moderno["progreso_pct"]:
        progreso_historico = _progreso_legado(expediente, plan)
        if Decimal(str(progreso_historico)) == resultado_legado_normalizado["progreso_pct"]:
            causas.append("D-03")
        else:
            causas.append("no justificada: progreso_pct")
    return causas, variantes


def test_refactor_legado_conserva_fingerprint_sobre_500_expedientes():
    expedientes = generar()
    legado._CACHE.clear()
    resultados = legado.calcular_lote(expedientes, str(RUTA_PLAN))
    assert len(resultados) == 500
    assert [r["estudiante_id"] for r in resultados] == [f"EST-{i:04d}" for i in range(500)]
    assert all(set(r) == {"estudiante_id", "nota_media", "creditos_superados", "progreso_pct"} for r in resultados)
    serializado = json.dumps(
        resultados, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    assert hashlib.sha256(serializado).hexdigest() == HUELLA_REFERENCIA


def test_corpus_sintetico_es_reproducible():
    corpus = cargar_corpus()
    assert len(corpus) == 500
    assert [e["estudiante_id"] for e in corpus] == [f"EST-{i:04d}" for i in range(500)]
    assert corpus == generar()


def test_equivalencia_controlada_legado_vs_moderno():
    corpus = cargar_corpus()
    plan = cargar_plan("PLAN-2024", RAIZ / "datos" / "planes")
    legado._CACHE.clear()
    resultados_legado = legado.calcular_lote(corpus, str(RUTA_PLAN))
    iguales = 0
    contadores = {"D-01": 0, "D-02": 0, "D-01 + D-02": 0, "D-03": 0}
    no_justificadas = []
    for datos, resultado_legado in zip(corpus, resultados_legado):
        expediente = adaptar_expediente(datos)
        resultado_moderno_actual = resultado_moderno(expediente, plan)
        resultado_legado_comparable = {
            **resultado_legado,
            "nota_media": Decimal(str(resultado_legado["nota_media"])),
            "progreso_pct": Decimal(str(resultado_legado["progreso_pct"])),
        }
        causas, variantes = clasificar_diferencia(
            resultado_legado, resultado_moderno_actual, expediente, plan
        )
        if resultado_legado_comparable == resultado_moderno_actual:
            iguales += 1
        else:
            causas_no_justificadas = [c for c in causas if c.startswith("no justificada")]
            for causa in causas:
                if causa in contadores:
                    contadores[causa] += 1
            if causas_no_justificadas:
                no_justificadas.append({
                "estudiante_id": expediente.estudiante_id,
                "legado": resultado_legado,
                "moderno": resultado_moderno_actual,
                "registros": datos["registros"],
                "causas": causas,
                "contrafactuales": variantes,
                })
    print({"iguales": iguales, **contadores, "no_justificadas": len(no_justificadas)})
    assert not no_justificadas, json.dumps(no_justificadas, ensure_ascii=False, default=str, indent=2)
