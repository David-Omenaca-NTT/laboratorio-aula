"""Evaluacion offline del agente de modernizacion contra un conjunto dorado."""
from __future__ import annotations

import argparse
import json
import time
from datetime import date
from pathlib import Path

from .agente import DECISIONES, analizar

RAIZ = Path(__file__).resolve().parents[2]


def ejecutar(directorio: Path) -> dict:
    etiquetas = json.loads((directorio / "etiquetas.json").read_text(encoding="utf-8"))
    if not isinstance(etiquetas, dict) or not etiquetas:
        raise ValueError("El conjunto dorado debe contener al menos una etiqueta")
    if any(not isinstance(etiqueta, str) or etiqueta not in DECISIONES
           for etiqueta in etiquetas.values()):
        raise ValueError("El conjunto dorado contiene una decision no reconocida")
    detalle = []
    aciertos_decision = aciertos_handoff = 0
    vp = fp = vn = fn = 0
    latencias = []

    for identificador, esperada in sorted(etiquetas.items()):
        caso = json.loads(
            (directorio / f"{identificador}.json").read_text(encoding="utf-8")
        )
        inicio = time.perf_counter()
        resultado = analizar(caso)
        latencias.append((time.perf_counter() - inicio) * 1000)
        handoff_esperado = esperada == "aprobable"
        handoff_obtenido = resultado["handoff"] is not None
        decision_ok = resultado["decision"] == esperada
        handoff_ok = handoff_obtenido == handoff_esperado
        aciertos_decision += int(decision_ok)
        aciertos_handoff += int(handoff_ok)

        if handoff_obtenido and handoff_esperado:
            vp += 1
        elif handoff_obtenido:
            fp += 1
        elif handoff_esperado:
            fn += 1
        else:
            vn += 1
        detalle.append({
            "caso": identificador,
            "esperado": {"decision": esperada, "handoff": handoff_esperado},
            "obtenido": {
                "decision": resultado["decision"],
                "handoff": handoff_obtenido,
            },
            "resultado": {"decision": decision_ok, "handoff": handoff_ok},
        })

    total = len(etiquetas)
    precision = vp / (vp + fp) if vp + fp else 0.0
    recall = vp / (vp + fn) if vp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "agente": "modernizacion",
        "fecha": date.today().isoformat(),
        "casos": total,
        "accuracy_decision": round(aciertos_decision / total, 3) if total else 0.0,
        "accuracy_handoff": round(aciertos_handoff / total, 3) if total else 0.0,
        "matriz_handoff": {"vp": vp, "fp": fp, "vn": vn, "fn": fn},
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "latencia_media_ms": round(sum(latencias) / total, 3) if total else 0.0,
        "coste_usd_por_ejecucion": 0.0,
        "juez": "offline",
        "detalle": detalle,
    }


def principal(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dorado", default="evals/dorado_ejemplo_modernizacion")
    parser.add_argument("--guardar", action="store_true")
    args = parser.parse_args(argv)
    directorio = RAIZ / args.dorado
    if not (directorio / "etiquetas.json").is_file():
        parser.error(f"No existe el conjunto dorado: {directorio}")

    informe = ejecutar(directorio)
    print(json.dumps(
        {clave: valor for clave, valor in informe.items() if clave != "detalle"},
        ensure_ascii=False,
        indent=2,
    ))
    fallos = [caso for caso in informe["detalle"] if not all(caso["resultado"].values())]
    for fallo in fallos:
        print(
            f"{fallo['caso']}: esperado {fallo['esperado']['decision']}, "
            f"obtenido {fallo['obtenido']['decision']}"
        )
    if args.guardar:
        destino = RAIZ / "evals" / "informes"
        destino.mkdir(parents=True, exist_ok=True)
        nombre = f"evaluacion-modernizacion-{time.strftime('%Y%m%d-%H%M%S')}.json"
        ruta = destino / nombre
        ruta.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\ninforme guardado en {ruta.relative_to(RAIZ)}")
    return 0 if not fallos else 1


if __name__ == "__main__":
    raise SystemExit(principal())
