import hashlib
import json
from pathlib import Path

from aula.legado import calculadora_expediente_v1 as legado
from herramientas.generar_corpus import generar


RAIZ = Path(__file__).resolve().parents[1]
RUTA_PLAN = RAIZ / "datos" / "planes" / "PLAN-2024.json"
HUELLA_REFERENCIA = (
    "c637d871a0f7057f1f87004cb3de7c5484e1c9a05f9e8997b08fada91023a36d"
)


def test_equivalencia_legacy_sobre_500_expedientes():
    expedientes = generar()
    legado._CACHE.clear()

    resultados = legado.calcular_lote(expedientes, str(RUTA_PLAN))

    assert len(resultados) == 500
    assert [resultado["estudiante_id"] for resultado in resultados] == [
        f"EST-{indice:04d}" for indice in range(500)
    ]
    assert all(
        set(resultado)
        == {"estudiante_id", "nota_media", "creditos_superados", "progreso_pct"}
        for resultado in resultados
    )

    serializado = json.dumps(
        resultados,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    huella = hashlib.sha256(serializado).hexdigest()

    assert huella == HUELLA_REFERENCIA, (
        "Las salidas del legado han cambiado respecto al corpus previo al refactor."
    )
