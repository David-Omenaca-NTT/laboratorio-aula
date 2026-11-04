"""Script sencillo para evaluar el agente de triaje.

La evaluación real de la estación puede usar un dorado externo. Este módulo
permite ejecutar casos locales si existen y reportar métricas básicas.
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import date
from pathlib import Path

from .agente import clasificar_fallo

RAIZ = Path(__file__).resolve().parents[2]


def _spec_esperado(caso: dict) -> str | None:
    trazabilidad = caso.get("trazabilidad")
    if isinstance(trazabilidad, dict):
        spec = trazabilidad.get("spec")
        if isinstance(spec, str) and spec.strip():
            return spec.strip().upper()
    spec = caso.get("spec")
    if isinstance(spec, str) and spec.strip():
        return spec.strip().upper()
    return None


def _handoff_esperado(caso: dict, etiqueta: str) -> bool:
    return etiqueta == "cobertura_spec" and _spec_esperado(caso) is not None


def ejecutar(directorio: Path) -> dict:
    etiquetas = json.loads((directorio / "etiquetas.json").read_text(encoding="utf-8"))
    detalle = []
    aciertos_clasificacion = 0
    aciertos_spec = 0
    aciertos_handoff = 0
    vp = fp = vn = fn = 0
    latencias = []

    for ident, etiqueta in sorted(etiquetas.items()):
        caso = json.loads((directorio / f"{ident}.json").read_text(encoding="utf-8"))
        t0 = time.perf_counter()
        resultado = clasificar_fallo(caso.get("run_id"), contexto=caso)
        latencias.append((time.perf_counter() - t0) * 1000.0)

        esperado_spec = _spec_esperado(caso)
        esperado_handoff = _handoff_esperado(caso, etiqueta)
        predicho = resultado.clasificacion
        predicho_spec = resultado.spec_id
        predicho_handoff = bool(resultado.handoff)

        clasificacion_ok = predicho == etiqueta
        spec_ok = predicho_spec == esperado_spec
        handoff_ok = predicho_handoff == esperado_handoff

        if clasificacion_ok:
            aciertos_clasificacion += 1
        if spec_ok:
            aciertos_spec += 1
        if handoff_ok:
            aciertos_handoff += 1

        if predicho_handoff and esperado_handoff:
            vp += 1
        elif predicho_handoff and not esperado_handoff:
            fp += 1
        elif not predicho_handoff and esperado_handoff:
            fn += 1
        else:
            vn += 1

        detalle.append({
            "caso": ident,
            "esperado": {
                "clasificacion": etiqueta,
                "spec_id": esperado_spec,
                "handoff": esperado_handoff,
            },
            "obtenido": {
                "clasificacion": predicho,
                "spec_id": predicho_spec,
                "handoff": predicho_handoff,
            },
            "resultado": {
                "clasificacion": clasificacion_ok,
                "spec_id": spec_ok,
                "handoff": handoff_ok,
            },
        })

    total = len(etiquetas)
    accuracy_clasificacion = (aciertos_clasificacion / total) if total else 0.0
    accuracy_spec_id = (aciertos_spec / total) if total else 0.0
    accuracy_handoff = (aciertos_handoff / total) if total else 0.0

    precision = (vp / (vp + fp)) if (vp + fp) else 0.0
    recall = (vp / (vp + fn)) if (vp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {
        "agente": "triaje",
        "fecha": date.today().isoformat(),
        "casos": total,
        "accuracy_clasificacion": round(accuracy_clasificacion, 3),
        "accuracy_spec_id": round(accuracy_spec_id, 3),
        "accuracy_handoff": round(accuracy_handoff, 3),
        "matriz_handoff": {"vp": vp, "fp": fp, "vn": vn, "fn": fn},
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "latencia_media_ms": round(sum(latencias) / len(latencias), 3) if latencias else 0.0,
        "coste_usd_por_ejecucion": 0.0,
        "juez": "offline",
        "detalle": detalle,
    }


def principal(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dorado", default="evals/dorado_ejemplo_triaje")
    ap.add_argument("--guardar", action="store_true", help="guardar el informe en evals/informes/")
    args = ap.parse_args(argv)
    directorio = RAIZ / args.dorado
    if not (directorio / "etiquetas.json").is_file():
        print("Evaluacion privada no configurada. El conjunto dorado no se entrega en la semilla.")
        return 2
    informe = ejecutar(directorio)
    print(json.dumps({k: v for k, v in informe.items() if k != "detalle"}, ensure_ascii=False, indent=2))
    if args.guardar:
        destino = RAIZ / "evals" / "informes"
        destino.mkdir(parents=True, exist_ok=True)
        ruta = destino / f"evaluacion-{time.strftime('%Y%m%d-%H%M%S')}.json"
        ruta.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"\ninforme guardado en {ruta.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
